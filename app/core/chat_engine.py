import asyncio
from app.core.order_state import Order
from app.core.validator import MenuValidator
from app.llm.client import LLMClient
from app.llm.prompts import get_system_prompt
from app.core.models import ActionType, LLMResponse, LLMItem, ChatResponse, Size, Modifications
from app.core import rules

class ChatEngine:
    def __init__(self):
        self.validator = MenuValidator()
        self.llm_client = LLMClient()
        
        full_menu = {
            "deals": self.validator.menus.get("deals"),
            "ingredients": self.validator.menus.get("ingredients"),
            "upsells": self.validator.menus.get("upsells"),
        }
        self.system_prompt = get_system_prompt(full_menu)
   
        small_deal_items, big_deal_items = self._load_deal_items()
        self.order = Order(small_deal_items=small_deal_items, big_deal_items=big_deal_items)
        
        self.history = []
        self.upsell_state = {
            "combo_offered": False,
            "sauce_offered": False,
            "dessert_offered": False,
        }
        self.lock = asyncio.Lock()
        self.known_burgers = self._load_known_burgers()

    def _load_deal_items(self):
        deals_section = self.validator.menus.get("deals", {}).get("deals", [])
        small = set()
        big = set()
        for d in deals_section:
            if d.get("name") == "Small Double Deal":
                small = set(d.get("possible_items", []))
            elif d.get("name") == "Big Double Deal":
                big = set(d.get("possible_items", []))
        return small, big

    def _load_known_burgers(self):
        known = set()
        items_menu = self.validator.menus.get("deals", {}).get("items", [])
        for item in items_menu:
            if isinstance(item, dict):
                known.add(item.get("name", "").lower())
        return known

    def start_session(self) -> str:
        greeting = "Welcome to McDonald's! What can I get you started with?"
        self.history.append({"role": "assistant", "content": greeting})
        return greeting

    async def process_message(self, user_input: str) -> ChatResponse:
        async with self.lock:
            self.history.append({"role": "user", "content": user_input})
            llm_response = await self.llm_client.process_user_message(
                self.history, self.system_prompt
            )
            
            if llm_response.action == ActionType.FINISH:
                return self._handle_finish(llm_response)
            elif llm_response.action == ActionType.CLARIFY:
                return self._handle_clarify(llm_response)
            elif llm_response.action == ActionType.ADD_TO_ORDER:
                return self._handle_add_to_order(llm_response)
            
            return ChatResponse(response_text="Error processing request.")


    def _handle_finish(self, resp: LLMResponse) -> ChatResponse:
        response_text = resp.message_to_user or "Order completed!"
        return ChatResponse(
            response_text=response_text,
            is_finished=True,
            order_summary=self.order.get_summary_string(),
            total_price=self.order.total()
        )

    def _handle_clarify(self, resp: LLMResponse) -> ChatResponse:
        response_text = resp.message_to_user or "Could you please clarify that?"
        self.history.append({"role": "assistant", "content": response_text})
        return ChatResponse(response_text=response_text, is_finished=False)

    def _handle_add_to_order(self, resp: LLMResponse) -> ChatResponse:
        response_text = self._process_items(resp)
        return ChatResponse(response_text=response_text, is_finished=False)

    def _check_burger_in_items(self, items: list) -> bool:
        keywords = ["burger", "mac", "mcchicken", "fish", "sandwich", "tasty", "royal"]
        exclusions = ["pie", "flurry", "sundae", "shake", "fries", "coke", "fanta", "sprite", "coffee", "tea", "water", "juice", "sauce", "dip", "cone", "cookie", "muffin", "donut"]
        for i in items:
            name = i.get("name", "").lower()
            if any(exc in name for exc in exclusions): continue
            if any(k in name for k in keywords): return True
            if name in self.known_burgers: return True
        return False

    def _generate_upsell(self, new_items: list) -> str:
        all_items = self.order.items
        
        new_burgers_count = sum(1 for x in new_items if self._check_burger_in_items([x]))
        is_part_of_deal = new_burgers_count >= 2
        
        has_burger_total = self._check_burger_in_items(all_items)
        has_combo_total = any(i.get("type") in ["combo", "deal"] for i in all_items)
        new_burger = self._check_burger_in_items(new_items)
        new_combo = any(i.get("type") in ["combo", "deal"] for i in new_items)

        if new_burger and not new_combo and not is_part_of_deal:
            self.upsell_state["combo_offered"] = True
            return "Would you like to make that a meal?"
            
        if has_combo_total and not self.upsell_state["sauce_offered"]:
            self.upsell_state["sauce_offered"] = True
            return "Would you like to add some dipping sauces?"
        
        if (has_burger_total or has_combo_total) and not self.upsell_state["dessert_offered"]:
            self.upsell_state["dessert_offered"] = True
            return "How about a McFlurry or Apple Pie for dessert?"
        return ""

    def _clean_component_name(self, name: str) -> str:
        if not name: return ""
        return name.lower().replace("small", "").replace("medium", "").replace("large", "").strip()

    def _extract_size_from_string(self, text: str) -> str:
        text = text.lower()
        if "large" in text: return "Large "
        if "medium" in text: return "Medium "
        if "small" in text: return "Small "
        return ""

    def _get_mod_list(self, mods: Modifications | dict, key: str) -> list:
        if isinstance(mods, dict): return mods.get(key, [])
        return getattr(mods, key, [])


    def _resolve_component(self, name: str, size_enum: Size | None, main_size_prefix: str) -> dict:
        """Helper to find component in menu and determine its full name with size."""
        clean_name = self._clean_component_name(name)
        found = self.validator.find(clean_name) or self.validator.find(name)
        entry = found[1] if found else None
        
        base_name = entry["name"] if entry else name.title()

        size_prefix = size_enum.value.title() + " " if size_enum else main_size_prefix
        if not size_prefix:
            size_prefix = self._extract_size_from_string(name)
            
        return {
            "name": f"{size_prefix}{base_name}",
            "entry": entry,
            "ingredients_added": []
        }

    def _route_ingredients(self, item: LLMItem, components: dict):
        """Distributes ingredients between main item, side, and drink."""
        adds = self._get_mod_list(item.modifications, "add")
        side_comp = components.get("side")
        drink_comp = components.get("drink")
        
        main_added = []

        for add_name in adds:
            p = self.validator.ingredients_map.get(add_name.lower(), 0.0)
            ingr_tuple = (add_name, p)
            add_lower = add_name.lower()
            assigned = False
            
            if side_comp:
                poss = []
                entry = side_comp.get("entry")
                if entry: poss = [x.lower() for x in entry.get("possible_ingredients", [])]
                
                if "fries" in side_comp["name"].lower() and ("mayo" in add_lower or "sauce" in add_lower or "ketchup" in add_lower):
                     poss.append(add_lower)
                
                if any(add_lower in x or x in add_lower for x in poss):
                    side_comp["ingredients_added"].append(ingr_tuple)
                    assigned = True

            if not assigned and drink_comp:
                poss = []
                entry = drink_comp.get("entry")
                if entry: poss = [x.lower() for x in entry.get("possible_ingredients", [])]
                
                if "ice" in add_lower: poss.append("ice")
                if "lemon" in add_lower: poss.append("lemon")
                
                if any(add_lower in x or x in add_lower for x in poss):
                    drink_comp["ingredients_added"].append(ingr_tuple)
                    assigned = True
            
            if not assigned:
                main_added.append(ingr_tuple)
        
        return main_added

    def _construct_order_item(self, item: LLMItem, entry: dict) -> dict:
        base_price = float(entry.get("price", 0.0))
        final_price = rules.apply_size_price(base_price, item.size)
        
        main_size_prefix = ""
        if item.size:
            main_size_prefix = item.size.value.title() + " "

        components = {}
        
        if "slots" in entry and item.combo_details:
            raw_side = item.combo_details.side or "French Fries"
            components["side"] = self._resolve_component(raw_side, item.combo_details.side_size, main_size_prefix)
            
            raw_drink = item.combo_details.drink or ""
            components["drink"] = self._resolve_component(raw_drink, item.combo_details.drink_size, main_size_prefix)

        main_added_ingr = self._route_ingredients(item, components)
        removes = self._get_mod_list(item.modifications, "remove")

        final_components = {}
        for k, v in components.items():
            final_components[k] = {
                "name": v["name"],
                "ingredients_added": v["ingredients_added"]
            }

        return {
            "type": "combo" if "slots" in entry else "item",
            "name": f"{main_size_prefix}{item.name}",
            "base_price": final_price,
            "ingredients_added": main_added_ingr,
            "ingredients_removed": removes,
            "components": final_components,
            "size": item.size,
        }

    def _handle_upgrade_replacement(self, new_item_name: str, new_item_type: str) -> dict:
        mods_to_carry = {"added": [], "removed": []}
        if new_item_type != "combo": return mods_to_carry

        base_name = new_item_name.lower().replace("meal", "").replace("combo", "")\
            .replace("large", "").replace("medium", "").replace("small", "").strip()
        
        for i, existing in enumerate(self.order.items):
            existing_name = existing["name"].lower()
            if base_name in existing_name and existing["type"] == "item":
                mods_to_carry["added"] = existing.get("ingredients_added", [])
                mods_to_carry["removed"] = existing.get("ingredients_removed", [])
                self.order.items.pop(i)
                break
        return mods_to_carry

    def _process_items(self, llm_resp: LLMResponse) -> str:
        all_valid = True
        errors = []
        entries = []

        for item in llm_resp.items:
            item_dict = item.model_dump(exclude_none=True) 
            is_valid, err_msg, entry = self.validator.validate_llm_item(item_dict)
            if not is_valid:
                all_valid = False
                errors.append(err_msg)
                entries.append(None)
            else:
                entries.append(entry)

        if not all_valid:
            error_msg = f"I couldn't process that: {', '.join(errors)}. Please try again."
            self.history.append({"role": "assistant", "content": error_msg})
            return error_msg

        added_items_objs = []
        for item, entry in zip(llm_resp.items, entries):
            item_type = "combo" if "slots" in entry else "item"
            carried_mods = self._handle_upgrade_replacement(item.name, item_type)
            order_item = self._construct_order_item(item, entry)
            
            if carried_mods["added"]: order_item["ingredients_added"].extend(carried_mods["added"])
            if carried_mods["removed"]: order_item["ingredients_removed"].extend(carried_mods["removed"])
            
            self.order.add_item(order_item)
            added_items_objs.append(order_item)

        upsell_text = self._generate_upsell(added_items_objs)
        
        item_names = [item["name"] for item in added_items_objs]
        base_msg = f"Added {', '.join(item_names)} to your order."
        
        final_msg = f"{base_msg.strip()} {upsell_text}" if upsell_text else f"{base_msg.strip()} What else can I get you?"
        self.history.append({"role": "assistant", "content": final_msg})
        return final_msg
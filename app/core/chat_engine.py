from app.core.validator import MenuValidator
from app.core.order_state import Order
from app.llm.client import LLMClient
from app.llm.prompts import get_system_prompt
from app.core.rules import apply_size_price

class ChatEngine:
    def __init__(self):
        self.validator = MenuValidator()
        self.order = Order()
        self.llm_client = LLMClient()
        full_menu = {
            "deals": self.validator.menus.get("deals"),
            "ingredients": self.validator.menus.get("ingredients"),
            "upsells": self.validator.menus.get("upsells"),
        }
        self.system_prompt = get_system_prompt(full_menu)
        self.history = []
        
        self.upsell_state = {
            "combo_offered": False,
            "sauce_offered": False,
            "dessert_offered": False
        }

    def _generate_upsell(self, new_items: list) -> str:
        """
        Аналізує нові додані товари та повертає текст пропозиції (Upsell).
        """
        upsell_msg = ""
        
        has_burger = any(i["type"] == "item" and "burger" in i.get("name", "").lower() for i in new_items)
        has_combo = any(i["type"] == "combo" or i["type"] == "deal" for i in new_items)
        
        if has_burger and not has_combo and not self.upsell_state["combo_offered"]:
            upsell_msg = " Would you like to make that a meal?"
            self.upsell_state["combo_offered"] = True
      
        elif has_combo and not self.upsell_state["sauce_offered"]:
            upsell_msg = " Would you like to add some dipping sauces?"
            self.upsell_state["sauce_offered"] = True
        
        elif (has_burger or has_combo) and not self.upsell_state["dessert_offered"]:
            upsell_msg = " How about a McFlurry or Apple Pie for dessert?"
            self.upsell_state["dessert_offered"] = True
            
        return upsell_msg

    def start(self):
        print("System: Welcome to McDonald's! What can I get you started with?")
        self.history.append({"role": "assistant", "content": "Welcome to McDonald's! What can I get you started with?"})

        while True:
            user_input = input("You: ").strip()
            self.history.append({"role": "user", "content": user_input})
            
            llm_response = self.llm_client.process_user_message(self.history, self.system_prompt)
            
            action = llm_response.get("action")
            message = llm_response.get("message_to_user", "")
            items = llm_response.get("items", [])

            if action == "finish":
                self.order.show()
                print(f"System: Your order total is ${self.order.total():.2f}")
                break

            if action == "clarify":
                if not message:
                    message = "Could you please clarify your order?"
                
                print(f"System: {message}")
                self.history.append({"role": "assistant", "content": message})
                continue

            if action == "add_to_order":
                all_valid = True
                validation_errors = []
                
                for item in items:
                    is_valid, err_msg, entry = self.validator.validate_llm_item(item)
                    if not is_valid:
                        all_valid = False
                        validation_errors.append(err_msg)
                    else:
                        item["_entry_ref"] = entry 

                if not all_valid:
                    error_resp = f"I couldn't process that: {', '.join(validation_errors)}. Please try again."
                    print(f"System: {error_resp}")
                    self.history.append({"role": "assistant", "content": error_resp})
                    continue

                added_items_objs = []
                for item in items:
                    entry = item["_entry_ref"]
                    name = item["name"]
                    size = item.get("size")
                    base_price = float(entry.get("price", 0.0))
                    
                    final_price = apply_size_price(base_price, size)
                    
                    mods = item.get("modifications", {})
                    added_ingr = []
                    for add_name in mods.get("add", []):
                        p = self.validator.ingredients_map.get(add_name.lower(), 0.0)
                        added_ingr.append((add_name, p))
                    removed_ingr = mods.get("remove", [])

                    components = {}
                    if "slots" in entry:
                         combo_d = item.get("combo_details", {})
                         components["side"] = {"name": combo_d.get("side", "French Fries")}
                         components["drink"] = {"name": combo_d.get("drink", "")}

                    order_item = {
                        "type": "combo" if "slots" in entry else "item",
                        "name": f"{size.capitalize() + ' ' if size else ''}{name}",
                        "base_price": final_price,
                        "ingredients_added": added_ingr,
                        "ingredients_removed": removed_ingr,
                        "components": components,
                        "size": size
                    }
                    self.order.add_item(order_item)
                    added_items_objs.append(order_item)

                
                upsell_text = self._generate_upsell(added_items_objs)
               
                final_response = f"{message}{upsell_text}"
                print(f"System: {final_response}")
                self.history.append({"role": "assistant", "content": final_response})
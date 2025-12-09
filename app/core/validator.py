from app.menu.loader import load_all_menus
from app.config import settings
import re

class MenuValidator:
    def __init__(self):
        paths = {
            "deals": settings.MENU_DEALS_PATH,
            "ingredients": settings.MENU_INGREDIENTS_PATH,
            "upsells": settings.MENU_UPSELLS_PATH,
            "virtual": settings.MENU_VIRTUAL_PATH,
        }
        self.menus = load_all_menus(paths)

        self.index = self._build_index()
        self.ingredients_map = self._build_ingredients_map()

    def _norm(self, s: str) -> str:
        return s.strip().lower()

    def _build_index(self):
        idx = {}
        deals_data = self.menus.get("deals") or {}
        for key in ("items", "combos", "deals"):
            entries = deals_data.get(key, [])
            if isinstance(entries, list):
                for entry in entries:
                    if isinstance(entry, dict):
                        name = self._norm(entry.get("name", ""))
                        if name: idx[name] = ("deals", entry)

        virt = self.menus.get("virtual") or {}
        for key in ("items", "combos"):
            for entry in virt.get(key, []):
                name = self._norm(entry.get("name", ""))
                if name: idx[name] = ("virtual", entry)

        ups = self.menus.get("upsells") or {}
        for entry in ups.get("items", []):
            name = self._norm(entry.get("name", ""))
            if name and name not in idx: idx[name] = ("upsells", entry)

        ingr_data = self.menus.get("ingredients") or {}
        for key in ("items", "combos", "ingredients"):
            for entry in ingr_data.get(key, []):
                name = self._norm(entry.get("name", ""))
                if name: idx[name] = ("ingredient", entry)
        return idx

    def _build_ingredients_map(self):
        m = {}
        ingr = self.menus.get("ingredients") or {}
        for entry in ingr.get("ingredients", []):
            if isinstance(entry, dict):
                name = self._norm(entry.get("name", ""))
                price = float(entry.get("price", 0.0) or 0.0)
                if name: m[name] = price
        return m

    def find(self, token: str):
        token_n = self._norm(token)
        return self.index.get(token_n)


    def _validate_deal_constraints(self, name: str, entry: dict) -> tuple[bool, str]:
        if "possible_items" in entry and "slots" not in entry:
            return False, f"Please specify which burgers you want for the '{name}'"
        return True, ""

    def _validate_size(self, name: str, item_dict: dict, entry: dict) -> tuple[bool, str]:
        size = item_dict.get("size")
        props = entry.get("properties", []) or []
        has_size_prop = any(p.get("name") == "size" for p in props)
        
        if has_size_prop and not size:
            return False, f"Size is required for '{name}'"
        
        if size and size.lower() not in ["small", "medium", "large"]:
             return False, f"Invalid size '{size}' for '{name}'"
        
        return True, ""

    def _validate_combo_details(self, item_dict: dict, entry: dict) -> tuple[bool, str, dict | None, dict | None]:
        is_combo = "slots" in entry
        side_entry = None
        drink_entry = None

        if not is_combo:
            return True, "", None, None

        combo_details = item_dict.get("combo_details", {}) or {}
        
        drink = combo_details.get("drink")
        drink_size = combo_details.get("drink_size")
        side = combo_details.get("side")
        side_size = combo_details.get("side_size")

        if drink:
            d_found = self.find(drink)
            if not d_found: 
                return False, f"Drink '{drink}' is not on the menu", None, None
            drink_entry = d_found[1]
            
            if drink_size and drink_size.lower() not in ["small", "medium", "large"]:
                return False, f"Invalid drink size '{drink_size}'", None, None
            
        if side:
            s_found = self.find(side)
            if not s_found: 
                return False, f"Side '{side}' is not on the menu", None, None
            side_entry = s_found[1]

            if side_size and side_size.lower() not in ["small", "medium", "large"]:
                return False, f"Invalid side size '{side_size}'", None, None

        return True, "", side_entry, drink_entry

    def _validate_ingredients(self, name: str, item_dict: dict, entry: dict, side_entry: dict, drink_entry: dict) -> tuple[bool, str]:
        mods = item_dict.get("modifications", {})
        allowed_ingredients = set()
    
        for p in entry.get("possible_ingredients", []) or []:
            allowed_ingredients.add(p.lower())
        
        if side_entry:
            for p in side_entry.get("possible_ingredients", []) or []:
                allowed_ingredients.add(p.lower())

        if drink_entry:
            for p in drink_entry.get("possible_ingredients", []) or []:
                allowed_ingredients.add(p.lower())

        for add in mods.get("add", []):
            add_lower = add.lower()
            found_ingr = False
            
            if add_lower in allowed_ingredients:
                found_ingr = True
            else:
                for p_item in allowed_ingredients:
                    if add_lower in p_item or p_item in add_lower:
                        found_ingr = True
                        break
            
            if not found_ingr:
                if add_lower in self.ingredients_map:
                    continue
                return False, f"Cannot add '{add}' to '{name}' (ingredient not allowed)"
        
        return True, ""

    def validate_llm_item(self, item_dict: dict) -> tuple[bool, str, dict | None]:
        name = item_dict.get("name")
        if not name:
            return False, "Item name missing", None

        found = self.find(name)
        if not found:
            return False, f"Item '{name}' not found in menu", None
        
        src, entry = found

        ok, err = self._validate_deal_constraints(name, entry)
        if not ok: return False, err, None
        
        ok, err = self._validate_size(name, item_dict, entry)
        if not ok: return False, err, None

        ok, err, side_entry, drink_entry = self._validate_combo_details(item_dict, entry)
        if not ok: return False, err, None

        ok, err = self._validate_ingredients(name, item_dict, entry, side_entry, drink_entry)
        if not ok: return False, err, None

        return True, "", entry
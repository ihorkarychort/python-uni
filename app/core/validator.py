from app.menu.loader import load_all_menus
from app import config
import re

class MenuValidator:
    def __init__(self):
        paths = {
            "deals": config.MENU_DEALS_PATH,
            "ingredients": config.MENU_INGREDIENTS_PATH,
            "upsells": config.MENU_UPSELLS_PATH,
            "virtual": config.MENU_VIRTUAL_PATH,
        }
        self.menus = load_all_menus(paths)

        self.index = self._build_index()
        self.name_to_entry = dict(self.index)
        self.ingredients_map = self._build_ingredients_map()

    def _norm(self, s: str) -> str:
        return s.strip().lower()

    def _build_index(self):
        idx = {}
        
        deals_data = self.menus.get("deals") or {}
        for key in ("items", "combos", "deals"):
            entries = deals_data.get(key, [])
            if not isinstance(entries, list):
                continue
            for entry in entries:
                if not isinstance(entry, dict):
                    continue
                name = self._norm(entry.get("name", ""))
                if name:
                    idx[name] = ("deals", entry)

        virt = self.menus.get("virtual") or {}
        for entry in virt.get("items", []):
            if not isinstance(entry, dict):
                continue
            name = self._norm(entry.get("name", ""))
            if name:
                idx[name] = ("virtual", entry)
        
        for entry in virt.get("combos", []):
            if not isinstance(entry, dict): continue
            name = self._norm(entry.get("name", ""))
            if name: idx[name] = ("virtual", entry)

        ups = self.menus.get("upsells") or {}
        for entry in ups.get("items", []):
            if not isinstance(entry, dict):
                continue
            name = self._norm(entry.get("name", ""))
            if name:
                if name not in idx:
                    idx[name] = ("upsells", entry)

        ingr_data = self.menus.get("ingredients") or {}
        
        for entry in ingr_data.get("items", []):
            if not isinstance(entry, dict): continue
            name = self._norm(entry.get("name", ""))
            if name:
                idx[name] = ("ingredient_item", entry)
        for entry in ingr_data.get("combos", []):
            if not isinstance(entry, dict): continue
            name = self._norm(entry.get("name", ""))
            if name:
                idx[name] = ("ingredient_combo", entry)

        for entry in ingr_data.get("ingredients", []):
            if not isinstance(entry, dict):
                continue
            name = self._norm(entry.get("name", ""))
            if name:
                idx[name] = ("ingredient", entry)

        return idx

    def _build_ingredients_map(self):
        m = {}
        ingr = self.menus.get("ingredients") or {}
        for entry in ingr.get("ingredients", []):
            if not isinstance(entry, dict):
                continue
            name = self._norm(entry.get("name", ""))
            try:
                price = float(entry.get("price", 0.0) or 0.0)
            except Exception:
                price = 0.0
            if name:
                m[name] = price
        return m

    def find(self, token: str):
        token_n = self._norm(token)
        if token_n in self.index:
            return self.index[token_n]
        return None

    def parse_sentence(self, sentence: str):
        cleaned = re.sub(r'[.,;:!?()"]', ' ', sentence.lower())
        words = cleaned.split()
        sizes = {"small", "medium", "large"}
        pending_size = None
        result = []
        i = 0

        names_sorted = sorted(self.index.keys(), key=lambda n: (-len(n.split()), -len(n)))

        while i < len(words):
            w = words[i]
            if w in sizes:
                pending_size = w
                i += 1
                continue

            found = None
            for name in names_sorted:
                name_words = name.split()
                ln = len(name_words)
                if i + ln <= len(words) and words[i:i + ln] == name_words:
                    src, entry = self.index[name]
                    found = (src, entry, name_words)
                    break

            if found:
                src, entry, name_words = found
                result.append({
                    "src": src,
                    "entry": entry,
                    "size": pending_size
                })
                pending_size = None
                i += len(name_words)
                continue

            i += 1

        return result

    def validate_llm_item(self, item_dict: dict) -> tuple[bool, str, dict | None]:
        name = item_dict.get("name")
        if not name:
            return False, "Item name missing", None

        found = self.find(name)
        if not found:
            return False, f"Item '{name}' not found in menu", None
        
        src, entry = found
       
        size = item_dict.get("size")
        props = entry.get("properties", []) or []
        has_size_prop = any(p.get("name") == "size" for p in props)
        
        if has_size_prop and not size:
            return False, f"Size is required for '{name}'", None
        
        if size and size.lower() not in ["small", "medium", "large"]:
             return False, f"Invalid size '{size}' for '{name}'", None

        is_combo = "slots" in entry or entry.get("possible_items")
        
        if is_combo and "slots" in entry:
            combo_details = item_dict.get("combo_details", {})
            if not combo_details:
                return False, f"Combo '{name}' requires details (side and drink)", None
            
            drink = combo_details.get("drink")
            if not drink:
                return False, f"Drink choice missing for '{name}'", None
            if not self.find(drink):
                 return False, f"Drink '{drink}' is not on the menu", None
            
            side = combo_details.get("side")
            if side and not self.find(side):
                 return False, f"Side '{side}' is not on the menu", None

        mods = item_dict.get("modifications", {})
        possible_raw = entry.get("possible_ingredients", []) or []
        possible = [p.lower() for p in possible_raw]
        
        for add in mods.get("add", []):
            if add.lower() not in possible:
                found_ingr = False
                for p_item in possible:
                    if add.lower() in p_item or p_item in add.lower():
                        found_ingr = True
                        break
                
                if not found_ingr:
                    return False, f"Cannot add '{add}' to '{name}' (not available)", None

        return True, "", entry
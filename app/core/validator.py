from app.menu.loader import load_all_menus
from app import config

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

    def _norm(self, s: str) -> str:
        return s.strip().lower()

    def _build_index(self):
        idx = {}
      
        deals_data = self.menus.get("deals") or {}
        for key in ("items", "combos", "deals"):
            for entry in deals_data.get(key, []) if isinstance(deals_data.get(key, []), list) else []:
                name = self._norm(entry.get("name") or entry.get("name", ""))
                if name:
                    idx[name] = ("deals", entry)

       
        virt = self.menus.get("virtual") or {}
        for entry in virt.get("items", []):
            name = self._norm(entry.get("name", ""))
            if name:
                idx[name] = ("virtual", entry)

    
        ups = self.menus.get("upsells") or {}
        for entry in ups.get("items", []):
            name = self._norm(entry.get("name", ""))
            if name:
                idx[name] = ("upsells", entry)

        ingr = self.menus.get("ingredients") or {}
        for entry in ingr.get("ingredients", []):
            name = self._norm(entry.get("name", ""))
            if name:
                idx[name] = ("ingredient", entry)

        return idx

    def find(self, token: str):
        token_n = self._norm(token)
        if token_n in self.index:
            return self.index[token_n]
        for name, val in self.index.items():
            if name in token_n or token_n in name:
                return val

        return None

    def extract_items_from_sentence(self, sentence: str):

        s = self._norm(sentence)
        found = []
        used_positions = set()
        names_sorted = sorted(self.index.keys(), key=lambda x: -len(x))
        for name in names_sorted:
            if name in s:
                src, entry = self.index[name]
                found.append((src, entry))
                s = s.replace(name, " ")
        return found

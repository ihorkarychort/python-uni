from typing import List, Dict

class Order:
    def __init__(self):
        self.items: List[Dict] = []
        # Список бургерів, які беруть участь у Double Deals
        # (Назви з menu_deals.yaml -> deals -> possible_items)
        self.double_deal_candidates = {
            "Hamburger", "Cheeseburger", "McChicken", "Filet-O-Fish", # Small items
            "Double Cheeseburger", "Big Mac", "Royal Cheeseburger", "Big Tasty" # Big items
        }

    def add_item(self, item: Dict):
        self.items.append(item)

    def total(self) -> float:
        total_price = 0.0
        
        # 1. Розділяємо товари на "кандидатів на знижку" та інші
        deal_candidates = []
        others = []

        for idx, item in enumerate(self.items):
            # Пропускаємо combos/deals, вони мають фіксовану ціну
            if item.get("type") == "combo" or item.get("type") == "deal":
                others.append(item)
                continue
            
            # Перевіряємо чи це бургер (за назвою)
            if item.get("name") in self.double_deal_candidates:
                deal_candidates.append(item)
            else:
                others.append(item)

        # 2. Групуємо кандитатів у пари для знижки 20%
        # (Спрощена логіка: беремо кожні два бургера і даємо знижку на їх базу)
        while len(deal_candidates) >= 2:
            item1 = deal_candidates.pop(0)
            item2 = deal_candidates.pop(0)
            
            price1 = self._calculate_single_item_price(item1)
            price2 = self._calculate_single_item_price(item2)
            
            # Знижка 20% на суму цих двох
            pair_total = (price1 + price2) * 0.8
            total_price += pair_total
        
        # Додаємо залишок (непарний бургер)
        for item in deal_candidates:
            total_price += self._calculate_single_item_price(item)
            
        # 3. Додаємо решту товарів (напої, фрі, комбо)
        for item in others:
            total_price += self._calculate_single_item_price(item)

        return round(total_price, 2)

    def _calculate_single_item_price(self, item: dict) -> float:
        base = float(item.get("base_price", 0.0) or 0.0)
        extras_cost = 0.0
        
        # Top level extras
        for extra in item.get("ingredients_added", []) or []:
            if isinstance(extra, (list, tuple)) and len(extra) >= 2:
                extras_cost += float(extra[1] or 0.0)
        
        # Component extras (для комбо)
        comps = item.get("components") or {}
        for comp in comps.values():
            if not comp: continue
            # У структурі LLM side/drink можуть бути словниками
            # Якщо ми додали extras до side:
            for extra in comp.get("ingredients_added", []) or []:
                 if isinstance(extra, (list, tuple)) and len(extra) >= 2:
                    extras_cost += float(extra[1] or 0.0)
                    
        return base + extras_cost

    def show(self):
        print("\n🧾 Order summary:")
        for it in self.items:
            # Спрощений вивід для ясності
            name = it.get("name")
            base = it.get("base_price", 0.0)
            
            # Формуємо рядок змін
            mods = []
            rem = it.get("ingredients_removed", [])
            add = it.get("ingredients_added", [])
            
            if rem: mods.append(f"removed: {', '.join(rem)}")
            if add: 
                add_str = ", ".join([f"{e[0]} (+${e[1]:.2f})" for e in add])
                mods.append(f"added: {add_str}")
            
            mods_str = f" ({'; '.join(mods)})" if mods else ""
            print(f"- {name}: ${base:.2f}{mods_str}")

        print(f"Total (with discounts applied): ${self.total():.2f}\n")
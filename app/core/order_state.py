from typing import List, Dict, Set

class Order:
    def __init__(self, small_deal_items: Set[str] = None, big_deal_items: Set[str] = None):
        self.items: List[Dict] = []
        self.small_deal_items = small_deal_items or set()
        self.big_deal_items = big_deal_items or set()

    def add_item(self, item: Dict):
        self.items.append(item)

    def _get_clean_name(self, name: str) -> str:
        return name.replace("Large", "").replace("Medium", "").replace("Small", "").strip()

    def _calculate_single_item_price(self, item: dict) -> float:
        base = float(item.get("base_price", 0.0) or 0.0)
        extras_cost = 0.0
        
        def sum_mods(mods):
            return sum(float(x[1] or 0.0) for x in mods if isinstance(x, (list, tuple)) and len(x) >= 2)

        extras_cost += sum_mods(item.get("ingredients_added", []) or [])
        
        for comp in (item.get("components") or {}).values():
            if comp: extras_cost += sum_mods(comp.get("ingredients_added", []) or [])
                    
        return base + extras_cost

    def _classify_items(self):
        small_pool, big_pool, others = [], [], []
        for item in self.items:
            clean_name = self._get_clean_name(item.get("name", ""))
            if item.get("type") == "item":
                if clean_name in self.small_deal_items: small_pool.append(item)
                elif clean_name in self.big_deal_items: big_pool.append(item)
                else: others.append(item)
            else:
                others.append(item)
        return small_pool, big_pool, others

    def _calculate_pool_price(self, pool: list, discount_mult: float) -> float:
        total = 0.0
        while len(pool) >= 2:
            item1 = pool.pop(0)
            item2 = pool.pop(0)
            p1 = self._calculate_single_item_price(item1)
            p2 = self._calculate_single_item_price(item2)
            total += (p1 + p2) * discount_mult

        for item in pool:
            total += self._calculate_single_item_price(item)
        return total

    def total(self) -> float:
        small_pool, big_pool, others = self._classify_items()
        t_small = self._calculate_pool_price(list(small_pool), 0.8)
        t_big = self._calculate_pool_price(list(big_pool), 0.8)
        
        t_others = sum(self._calculate_single_item_price(i) for i in others)
        
        return round(t_small + t_big + t_others, 2)

    def _format_mods(self, item: dict, prefix=" ") -> str:
        mods = []
        rem = item.get("ingredients_removed", [])
        add = item.get("ingredients_added", [])
        
        if rem: mods.append(f"NO {', '.join(rem)}")
        if add: 
            add_str = ", ".join([f"{e[0]}" for e in add])
            mods.append(f"ADD {add_str}")
            
        return f"{prefix}({'; '.join(mods)})" if mods else ""

    def _format_item_line(self, item: dict, lines: list, is_deal_component=False):
        name = item.get("name")
        
        if is_deal_component:
            mods = self._format_mods(item, prefix="")
            lines.append(f"    {name} {mods}")
        else:
            full_price = self._calculate_single_item_price(item)
            lines.append(f"- {name}: ${full_price:.2f}")
            
            comps = item.get("components", {})
            if comps:
                main_name = self._get_clean_name(name.replace("Meal", "").replace("Combo", "").strip())
                main_mods = self._format_mods(item, prefix="")
                lines.append(f"    {main_name} {main_mods}")

                for key in ["side", "drink"]:
                    comp = comps.get(key)
                    if comp:
                        c_name = comp.get("name")
                        c_mods = self._format_mods(comp, prefix="")
                        lines.append(f"    {c_name} {c_mods}")
            else:
                main_mods = self._format_mods(item)
                if main_mods: lines[-1] += main_mods

    def _format_deal_group(self, pool: list, deal_name: str, lines: list):
        while len(pool) >= 2:
            item1 = pool.pop(0)
            item2 = pool.pop(0)
            p1 = self._calculate_single_item_price(item1)
            p2 = self._calculate_single_item_price(item2)
            pair_total = (p1 + p2) * 0.8
            
            lines.append(f"- {deal_name} (20% off): ${pair_total:.2f}")
            self._format_item_line(item1, lines, is_deal_component=True)
            self._format_item_line(item2, lines, is_deal_component=True)

    def get_summary_string(self) -> str:
        lines = []
        small_pool, big_pool, others = self._classify_items()

        self._format_deal_group(small_pool, "Small Double Deal", lines)
        self._format_deal_group(big_pool, "Big Double Deal", lines)

        others.extend(small_pool)
        others.extend(big_pool)
        
        for item in others:
            self._format_item_line(item, lines, is_deal_component=False)
            
        return "\n".join(lines)
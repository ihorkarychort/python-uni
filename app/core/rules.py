import re
def is_virtual(item):
    try:
        return getattr(item, "is_virtual", False) or (isinstance(item, dict) and item.get("virtual", False))
    except Exception:
        return False


def resolve_virtual_item(item, available_items):
    if isinstance(item, dict):
        vname = item.get("name", "<virtual>")
        possible = item.get("possible_items", [])
    else:
        vname = getattr(item, "name", "<virtual>")
        possible = getattr(item, "possible_items", [])

    print(f"\n'{vname}' is a virtual item. Choose one:")
    for i, name in enumerate(possible):
        print(f"{i+1}. {name}")

    while True:
        try:
            choice = int(input("Choose (number): ")) - 1
            if 0 <= choice < len(possible):
                selected_name = possible[choice].lower()
                break
            else:
                print("Invalid selection, try again.")
        except ValueError:
            print("Please enter a number.")

    found = available_items.get(selected_name)
    if found:
        _, entry = found
        return entry
    return {"name": possible[choice], "price": 0.0}

SIZE_PRICE_MODIFIERS = {"small": -0.50, "medium": 0.0, "large": 1.0}

def detect_size(user_text: str) -> str | None:
    if not user_text:
        return None
    s = user_text.lower()
    for size in SIZE_PRICE_MODIFIERS.keys():
        if re.search(rf'\b{re.escape(size)}\b', s):
            return size
    return None


def apply_size_price(base_price: float, size: str | None) -> float:
    try:
        if size is None:
            return float(base_price or 0.0)
        return float(base_price or 0.0) + float(SIZE_PRICE_MODIFIERS.get(size, 0.0))
    except Exception:
        return float(base_price or 0.0)


def parse_ingredient_list(user_input: str):
    s = user_input.lower()
    parts = re.split(r',|\band\b', s)
    to_remove = []
    to_add = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        m = re.match(r'^(no|without|remove|minus)\s+(.+)$', p)
        if m:
            name = m.group(2).strip()
            to_remove.append(name)
            continue
        m2 = re.match(r'^(add|with|extra|plus)\s+(.+)$', p)
        if m2:
            name = m2.group(2).strip()
            to_add.append(name)
            continue
        if p.startswith('no ') or p.startswith('without ') or p.startswith('remove '):
            to_remove.append(re.sub(r'^(no|without|remove|minus)\s+', '', p).strip())
        else:
            to_add.append(p.strip())
    to_remove = [ri.strip() for ri in to_remove if ri.strip()]
    to_add = [ai.strip() for ai in to_add if ai.strip()]
    return to_remove, to_add

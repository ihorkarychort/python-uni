def is_virtual(item):
    return getattr(item, "is_virtual", False)


def resolve_virtual_item(item, available_items):
    print(f"\n'{item.name}' is a virtual item. Choose one:")

    for i, name in enumerate(item.possible_items):
        print(f"{i+1}. {name}")

    choice = int(input("Choose: ")) - 1
    selected = item.possible_items[choice].lower()

    return available_items[selected]

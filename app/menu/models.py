class Item:
    def __init__(self, name, category, price, properties=None, is_virtual=False, possible_items=None):
        self.name = name
        self.category = category
        self.price = price
        self.properties = properties or []
        self.is_virtual = is_virtual
        self.possible_items = possible_items or []

    def __str__(self):
        return f"{self.name} - ${self.price:.2f}"

class Order:
    def __init__(self):
        self.items = []  

    def add_item(self, name, price):
        self.items.append((name, float(price or 0.0)))

    def total(self):
        return sum(p for _, p in self.items)

    def show(self):
        print("\n🧾 Order summary:")
        for n, p in self.items:
            print(f"- {n}: ${p:.2f}")
        print(f"Total: ${self.total():.2f}\n")

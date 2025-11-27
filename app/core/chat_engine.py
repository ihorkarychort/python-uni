from app.core.validator import MenuValidator
from app.core.order_state import Order

class ChatEngine:
    def __init__(self):
        self.validator = MenuValidator()
        self.order = Order()

    def start(self):
        print("System: Welcome to McDonald's! What can I get you started with?")

        while True:
            user_input = input("You: ").strip()
            if user_input.lower() in ("exit", "quit"):
                print("System: Bye")
                break

            if user_input.lower() in ("that's all", "done", "that's all."):
                self.order.show()
                print(f"System: Your order total is ${self.order.total():.2f}")
                break

            found = self.validator.extract_items_from_sentence(user_input)
            if not found:
                print("System: ❌ Item not found in the menu. Please specify again.")
                continue

            for src, entry in found:
                name = entry.get("name") or entry.get("includes") or entry.get("possible_items")
                price = entry.get("price", 0.0)
                if isinstance(name, list):
                    cname = entry.get("name")
                    self.order.add_item(cname, price)
                    print(f"System: ✅ Added combo: {cname}")
                else:
                    self.order.add_item(entry.get("name"), price)
                    print(f"System: ✅ Added: {entry.get('name')}")

            print("System: What else can I get you?")

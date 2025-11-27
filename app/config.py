import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

MENU_DEALS_PATH = os.path.join(DATA_DIR, "menu_deals.yaml")
MENU_INGREDIENTS_PATH = os.path.join(DATA_DIR, "menu_ingredients.yaml")
MENU_UPSELLS_PATH = os.path.join(DATA_DIR, "menu_upsells.yaml")
MENU_VIRTUAL_PATH = os.path.join(DATA_DIR, "menu_virtual_items.yaml")


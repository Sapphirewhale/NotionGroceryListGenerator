import json
from notiongrocerylistgenerator.main import NotionGroceryListGenerator
from notiongrocerylistgenerator.grocery_apis.woolworths import WoolworthsApi


def main():
    try:
        print("Generating grocery list...")
        with open("config.json", "r") as f:
            config = json.load(f)
        generator = NotionGroceryListGenerator(**config)

        ingredients = generator.get_meal_plan_ingredients()
        print("Adding missing ingredients to ingredients directory...")
        generator.sync_ingredients(ingredients)
        print("Sending ingredients list to shop")
        WoolworthsApi().add_ingredients_to_trolley(ingredients)

    except Exception as e:
        print(repr(e))
        input("Press any key to exit...")




if __name__ == "__main__":
    main()

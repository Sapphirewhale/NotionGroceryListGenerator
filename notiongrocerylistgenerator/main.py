from notiongrocerylistgenerator.notion_api import NotionApi
import os
from notiongrocerylistgenerator.Ingredient import Ingredient

class NotionGroceryListGenerator:
    def __init__(
        self,
        recipes_page: str = "",
        ingredients_directory: str = "",
        meal_plan_page: str = ""
    ) -> None:
        self.token = os.environ.get('notion_api_key')
        self._notion = NotionApi(self.token)
        self._recipes_page = recipes_page
        self._ingredients_directory = ingredients_directory
        self._meal_plan_id = meal_plan_page

    def get_grocery_list_id(self, page):
        dropdown_id = self._notion.get_blocks(page)["results"][2]["id"]
        return self._notion.get_blocks(dropdown_id)["results"][0]["id"]

    def get_recipes(self):
        r = self._notion.query(self._recipes_page)

        recipes = {}
        for record in r["results"]:
            recipes[
                record["properties"]["Dish"]["title"][0]["plain_text"].lower().strip()
            ] = record["id"]
        return recipes

    def get_ingredients_db_link(self, meal_page_id):
        blocks = self._notion.get_blocks(meal_page_id)
        for block in blocks["results"]:
            if block["type"] == "toggle":
                child_blocks = self._notion.get_blocks(block["id"])
                for child_block in child_blocks["results"]:
                    if child_block["type"] == "child_database":
                        return child_block["id"]

    def get_ingredients(self, recipes, meal):
        if "|||" in meal:
            dbid = self.get_ingredients_db_link(meal.split("|||")[-1])
        else:
            dbid = self.get_ingredients_db_link(recipes[meal])
        if dbid is None:
            return
        r = self._notion.query(dbid)

        ingredients = {}
        for record in r["results"]:
            ingredients[
                record["properties"]["Name"]["title"][0]["plain_text"].lower().strip()
            ] = Ingredient(
                record["properties"]["Name"]["title"][0]["plain_text"].lower().strip(),
                record["properties"]["Quantity"]["number"],
                recipes=meal,
            )
        return ingredients

    def get_meal_list(self):
        r = self._notion.query(self._meal_plan_id)

        meals = []
        for record in r["results"]:
            meal_name = record["properties"]["Name"]["title"][0]["plain_text"].lower().strip()
            if len(record['properties']['Recipe']['relation']) == 0:
                meals.append(meal_name)
            else:
                meals.append(meal_name + "|||" +r['results'][1]['properties']['Recipe']['relation'][0]['id'])

        return meals

    def add_dict(self, dict1, dict2):
        for key in dict1.keys():
            if key in dict2.keys():
                dict1[key] = dict1[key] + dict2[key]
        for key in dict2.keys():
            if key not in dict1.keys():
                dict1[key] = dict2[key]
        return dict1

    def post_ingredient(self, ingredient):
        payload = {
            "parent": {"database_id": self._ingredients_directory},
            "properties": {
                "Name": {
                    "title": [{"text": {"content": ingredient.name.lower().strip()}}]
                }
            },
        }

        self._notion.create_page(payload)

    def sync_ingredients(self, ingredients):
        r = self._notion.query(self._ingredients_directory)

        ingredients_list = {}
        for record in r["results"]:
            props = record["properties"]
            ingredient_name = props["Name"]["title"][0]["plain_text"].lower().strip()
            preferred_shop = props["Preferred Shop"]["select"]
            if preferred_shop != None:
                preferred_shop = preferred_shop.get("name")
            
                shop_quantity = props[f"{preferred_shop} Quantity"]["number"]

                shop_link = props[f"{preferred_shop} Link"]["rich_text"]
                if len(shop_link)>0:
                    shop_link = shop_link[0]['text']['content']
                else:
                    shop_link = None
                ingredients_list[
                    ingredient_name
                ] = (
                    preferred_shop,
                    shop_link,
                    shop_quantity
                    )
            else:
                print(f'No shop selected for {ingredient_name}, please add the details in the ingredients DB')
                ingredients_list[ingredient_name] = None
        for ingredient in ingredients.values():
            if (
                ingredient.name.lower().strip() in ingredients_list.keys()
                and ingredients_list[ingredient.name.lower().strip()] is not None
            ):
                ingredient.shop, ingredient.shop_link, ingredient.shop_quantity = ingredients_list[ingredient.name.lower().strip()]
            elif ingredient.name.lower().strip() not in ingredients_list.keys():
                print(f"Adding {ingredient.name} to the ingredient DB for the first time, please add shop details and rerun")
                self.post_ingredient(ingredient)


    def get_meal_plan_ingredients(self):
        print("Getting meal list...")
        meal_list = self.get_meal_list()
        print("Getting recipes...")
        recipes = self.get_recipes()
        ingredients = {}
        for meal in meal_list:
            print(f"Getting ingredients for {meal}...")
            if meal in recipes.keys() or "|||" in meal:
                meal_ingredients = self.get_ingredients(recipes, meal)
                if meal_ingredients != None:
                    ingredients = self.add_dict(
                        ingredients, meal_ingredients
                    )
                else:
                    print(f"{meal} doesn't have an ingredients database! Please add one so that the ingredients can be added to the shopping list")
            elif meal in ingredients.keys():
                ingredients[meal].quantity += 1
            elif meal != "leftovers":
                print(
                    f"Couldn't find {meal} in recipe list, adding directly to shopping list"
                )
                ingredients[meal] = Ingredient(meal, 1)

        return ingredients



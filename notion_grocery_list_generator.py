from datetime import datetime, timedelta
import json
import requests
import os


class NotionAPI:
    def __init__(self, token) -> None:
        self.token = token

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.token}",
            "Notion-Version": "2021-08-16",
            "Content-Type": "application/json",
        }

    def _get(self, uri):
        r = requests.get(
            uri,
            headers=self._headers(),
        )
        if r.status_code >= requests.codes.bad_request:
            print("An error occurred:")
            print(r.json())
        return r.json()

    def _post(self, uri, data={}):
        r = requests.post(uri, headers=self._headers(), data=json.dumps(data))

        if r.status_code >= requests.codes.bad_request:
            print("An error occurred:")
            print(r.json())
        return r.json()

    def get_page(self, id):
        return self._get(f"https://api.notion.com/v1/pages/{id}")

    def get_database(self, id):
        return self._get(f"https://api.notion.com/v1/databases/{id}")

    def get_blocks(self, id):
        return self._get(f"https://api.notion.com/v1/blocks/{id}/children")

    def query(self, id):
        return self._post(f"https://api.notion.com/v1/databases/{id}/query")

    def create_page(self, payload):
        return self._post("https://api.notion.com/v1/pages", payload)


class Ingredient:
    def __init__(self, name, quantity, recipes=None, shop=None) -> None:
        self.name = name
        self.quantity = quantity
        if recipes is not None and not isinstance(recipes, list):
            self.recipes = [recipes]
        elif isinstance(recipes, list):
            self.recipes = recipes
        else:
            self.recipes = []

        self.shop = shop

    def __add__(self, o):
        if not isinstance(o, Ingredient):
            return super(o)
        else:
            return Ingredient(
                self.name,
                self.quantity + o.quantity,
                self.recipes + o.recipes,
                self.shop,
            )

    def get_properties(self):
        return {
            "Name": {"title": [{"text": {"content": self.name}}]},
            "Quantity": {"number": self.quantity},
            "Recipes": {
                "multi_select": [
                    {
                        "name": rec,
                    }
                    for rec in self.recipes
                ]
            },
            "Shop": {"select": None if self.shop == None else {"name": self.shop}},
        }

    def __str__(self) -> str:
        return f"{self.name}, {self.quantity}, {self.recipes}, {self.shop}"


class NotionGroceryListGenerator:
    def __init__(
        self,
        recipes_page: str = "",
        ingredients_directory: str = "",
        meal_plan_page: str = "",
        grocery_list_page: str = "",
        token: str = "",
    ) -> None:
        self.token = token
        self._notion = NotionAPI(self.token)
        self._recipes_page = recipes_page
        self._ingredients_directory = ingredients_directory
        self._meal_plan_id = self.get_meal_plan_id(meal_plan_page)
        self._grocery_list_id = self.get_grocery_list_id(grocery_list_page)

    def get_meal_plan_id(self, page):
        dropdown_id = self._notion.get_blocks(page)["results"][1]["id"]
        return self._notion.get_blocks(dropdown_id)["results"][0]["id"]

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
        dbid = self.get_ingredients_db_link(recipes[meal])
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
            meals.append(
                record["properties"]["Name"]["title"][0]["plain_text"].lower().strip()
            )
        return meals

    def add_dict(self, dict1, dict2):
        for key in dict1.keys():
            if key in dict2.keys():
                dict1[key] = dict1[key] + dict2[key]
        for key in dict2.keys():
            if key not in dict1.keys():
                dict1[key] = dict2[key]
        return dict1

    def add_item(self, ingredient: Ingredient):
        payload = {
            "parent": {"database_id": self._grocery_list_id},
            "properties": ingredient.get_properties(),
        }

        self._notion.create_page(payload)

    def update_notion(self, shopping_list):
        for item in shopping_list.values():
            self.add_item(item)
        print(shopping_list)

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
            ingredients_list[
                record["properties"]["Name"]["title"][0]["plain_text"].lower().strip()
            ] = (
                record["properties"]["Shop"]["select"]["name"]
                if record["properties"]["Shop"]["select"] != None
                else None
            )
        for ingredient in ingredients.values():
            if (
                ingredient.name.lower().strip() in ingredients_list.keys()
                and ingredients_list[ingredient.name.lower().strip()] is not None
            ):
                ingredient.shop = ingredients_list[ingredient.name.lower().strip()]
            elif ingredient.name.lower().strip() not in ingredients_list.keys():
                self.post_ingredient(ingredient)


if __name__ == "__main__":
    try:
        print("Generating grocery list...")
        with open("config.json", "r") as f:
            config = json.load(f)
        generator = NotionGroceryListGenerator(**config)

        print("Getting meal list...")
        meal_list = generator.get_meal_list()
        print("Getting recipes...")
        recipes = generator.get_recipes()
        ingredients = {}
        for meal in meal_list:
            print(f"Getting ingredients for {meal}...")
            if meal in recipes.keys():
                ingredients = generator.add_dict(
                    ingredients, generator.get_ingredients(recipes, meal)
                )
            elif meal in ingredients.keys():
                ingredients[meal].quantity += 1
            elif meal != "leftovers":
                print(
                    f"Couldn't find {meal} in recipe list, adding directly to shopping list"
                )
                ingredients[meal] = Ingredient(meal, 1)
        print("Adding missing ingredients to ingredients directory...")
        generator.sync_ingredients(ingredients)
        print("Sending ingredients list to notion")
        generator.update_notion(ingredients)
    except Exception as e:
        print(repr(e))
        input("Press any key to exit...")

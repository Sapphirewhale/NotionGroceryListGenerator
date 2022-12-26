from datetime import datetime, timedelta
import json
import requests
import os

token = ""
recipes_page = ""
meal_plan_id = ""
grocery_list_id = ""
ingredients_directory = ""


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
            return Ingredient(self.name, self.quantity+o.quantity, self.recipes+o.recipes, self.shop)

    def __str__(self) -> str:
        return f"{self.name}, {self.quantity}, {self.recipes}, {self.shop}"


def get_recipes():
    url = f'https://api.notion.com/v1/databases/{recipes_page}/query'

    r = requests.post(url, headers={
        "Authorization": f"Bearer {token}",
        "Notion-Version": "2021-08-16"
    })

    recipes = {}
    result_dict = r.json()
    for record in result_dict['results']:
        if len(record['properties']['Ingredients']['rich_text']) > 0:
            recipes[record['properties']['Dish']['title']
                    [0]['plain_text'].lower().strip()] = record['properties']['Ingredients']['rich_text'][0]['plain_text']
    return recipes


def get_ingredients(dbid, meal):
    url = f'https://api.notion.com/v1/databases/{dbid}/query'
    r = requests.post(url, headers={
        "Authorization": f"Bearer {token}",
        "Notion-Version": "2021-08-16"
    })

    ingredients = {}
    result_dict = r.json()
    for record in result_dict['results']:
        ingredients[record['properties']['Name']['title'][0]['plain_text'].lower().strip()
                    ] = Ingredient(record['properties']['Name']['title'][0]['plain_text'].lower().strip(), record['properties']['Quantity']['number'], recipes=meal)
    return ingredients


def get_meal_list():
    url = f'https://api.notion.com/v1/databases/{meal_plan_id}/query'
    r = requests.post(url, headers={
        "Authorization": f"Bearer {token}",
        "Notion-Version": "2021-08-16"
    })

    meals = []
    result_dict = r.json()
    for record in result_dict['results']:
        meals.append(record['properties']['Name']
                     ['title'][0]['plain_text'].lower().strip())
    return meals


def add_dict(dict1, dict2):
    for key in dict1.keys():
        if key in dict2.keys():
            dict1[key] = dict1[key]+dict2[key]
    for key in dict2.keys():
        if key not in dict1.keys():
            dict1[key] = dict2[key]
    return dict1


def add_item(ingredient):
    url = 'https://api.notion.com/v1/pages'

    payload = {
        "parent": {
            "database_id": grocery_list_id
        },
        "properties": {
            "Name": {
                "title": [
                    {
                        "text": {
                            "content": ingredient.name
                        }
                    }
                ]
            },
            "Quantity": {
                "number": ingredient.quantity
            },
            "Recipes": {
                "multi_select": [{'name': rec, } for rec in ingredient.recipes]
            },
        }
    }
    if ingredient.shop != None:
        payload['properties']['Shop'] = {
            "multi_select": [{'name': ingredient.shop}]
        }
    r = requests.post(url, headers={
        "Authorization": f"Bearer {token}",
        "Notion-Version": "2021-08-16",
        "Content-Type": "application/json"
    }, data=json.dumps(payload))
    if r.status_code != 200:
        print("An error occurred:")
        print(r.json())
    else:
        print(r.status_code)


def update_notion(shopping_list):
    for item in shopping_list.values():
        add_item(item)
    print(shopping_list)


def post_ingredient(ingredient):
    url = 'https://api.notion.com/v1/pages'
    payload = {
        "parent": {
            "database_id": ingredients_directory
        },
        "properties": {
            "Name": {
                "title": [
                    {
                        "text": {
                            "content": ingredient.name.lower().strip()
                        }
                    }
                ]
            }
        }
    }

    r = requests.post(url, headers={
        "Authorization": f"Bearer {token}",
        "Notion-Version": "2021-08-16",
        "Content-Type": "application/json"
    }, data=json.dumps(payload))
    print(r)


def sync_ingredients(ingredients):
    url = f'https://api.notion.com/v1/databases/{ingredients_directory}/query'
    r = requests.post(url, headers={
        "Authorization": f"Bearer {token}",
        "Notion-Version": "2021-08-16"
    })

    ingredients_list = {}
    result_dict = r.json()
    for record in result_dict['results']:
        ingredients_list[record['properties']['Name']
                         ['title'][0]['plain_text'].lower().strip()] = record['properties']['Shop']['multi_select'][0]['name'] if len(record['properties']['Shop']['multi_select']) > 0 else None
    for ingredient in ingredients.values():
        if ingredient.name.lower().strip() in ingredients_list.keys() and ingredients_list[ingredient.name.lower().strip()] is not None:
            ingredient.shop = ingredients_list[ingredient.name.lower().strip()]
        elif ingredient.name.lower().strip() not in ingredients_list.keys():
            post_ingredient(ingredient)


url = f'https://api.notion.com/v1/databases/{grocery_list_id}/query'

r = requests.post(url, headers={
    "Authorization": f"Bearer {token}",
    "Notion-Version": "2021-08-16"
})


if __name__ == '__main__':
    try:
        if os.path.exists("./persistence.json"):
            persistence = {}
            with open("./persistence.json", 'r') as f:
                persistence = json.load(f)
            answer = input(
                "Would you like to reuse the links from the last time this script ran? (y/n):")
            if answer == 'y':
                meal_plan_id = persistence['meal_plan_id']
                grocery_list_id = persistence['grocery_list_id']
        if meal_plan_id == "" or grocery_list_id == "":
            meal_plan_url = input(
                "Please paste the link to the meal plan you need to generate a grocery list from:")
            grocery_list_url = input(
                "Please paste the link to the grocery list where you would like the generated items to be added:")
            if len(meal_plan_url.split('/')) > 0:
                print("Processing meal plan URL to get DB ID...")
                meal_plan_id = meal_plan_url.split('/')[-1].split('?v=')[0]
                print(f"Meal Plan ID: {meal_plan_id}")
            else:
                meal_plan_id = meal_plan_url

            if len(grocery_list_url.split('/')) > 0:
                print("Processing meal plan URL to get DB ID...")
                grocery_list_id = grocery_list_url.split(
                    '/')[-1].split('?v=')[0]
                print(f"Grocery List ID: {grocery_list_id}")
            else:
                grocery_list_id = grocery_list_url
            with open("./persistence.json", 'w') as f:
                json.dump({
                    'last_run': datetime.now().strftime("%c"),
                    'meal_plan_id': meal_plan_id,
                    'grocery_list_id': grocery_list_id
                }, f)

        recipes = get_recipes()
        meal_list = get_meal_list()
        ingredients = {}
        for meal in meal_list:
            if meal in recipes.keys():
                ingredients = add_dict(
                    ingredients, get_ingredients(recipes[meal], meal))
            elif meal in ingredients.keys():
                ingredients[meal].quantity += 1
            elif meal != "leftovers":
                print(
                    f"Couldn't find {meal} in recipe list, adding directly to shopping list")
                ingredients[meal] = Ingredient(meal, 1)
        sync_ingredients(ingredients)
        print([str(i) for i in ingredients.values()])
        update_notion(ingredients)
    except Exception as e:
        print(e)
        input("Press any key to exit...")

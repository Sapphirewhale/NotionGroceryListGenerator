import requests, math
from browser_cookie3 import firefox

from notiongrocerylistgenerator.Ingredient import Ingredient

trolley_url="https://www.woolworths.com.au/api/v3/ui/trolley/update"
trolley_format='{"items":[{"stockcode":779130,"quantity":5}]}'

class WoolworthsApi:

    def get_quantity(self, ingredient: Ingredient):
        return math.ceil(ingredient.quantity/ingredient.shop_quantity)


    def get_stockcode(self, ingredient: Ingredient):
        return ingredient.shop_link.split('/')[-2]

    def add_ingredients_to_trolley(self, ingredients:dict[str, Ingredient]):
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:145.0) Gecko/20100101 Firefox/145.0",
            "content-type": "application/json"
        }
        for item in ingredients.values():
            if item.shop != "Woolworths":
                continue
            body = f'{{"items": [{{"stockcode": {self.get_stockcode(item)}, "quantity": {self.get_quantity(item)} }}] }}'
            r = requests.post(trolley_url, data=body, cookies=firefox(), headers=headers)
            if r.status_code >= requests.codes.bad_request:
                print(f"Error adding {item} to grocery list: {r.text}")
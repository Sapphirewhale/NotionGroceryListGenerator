class Ingredient:
    def __init__(self, name, quantity, recipes=None, shop=None, shop_quantity=None, shop_link=None) -> None:
        self.name = name
        self.quantity = quantity
        if recipes is not None and not isinstance(recipes, list):
            self.recipes = [recipes]
        elif isinstance(recipes, list):
            self.recipes = recipes
        else:
            self.recipes = []

        self.shop = shop
        self.shop_quantity = shop_quantity
        self.shop_link = shop_link

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

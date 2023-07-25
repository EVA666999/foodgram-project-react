import json
import os
from api.models import Ingredient

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "foodgram_backend.settings")
django.setup()


def load_ingredients():
    with open("../data/ingredients.json", "r", encoding="utf-8-sig") as file:
        ingredients = json.load(file)

    Ingredient.objects.bulk_create(
        [Ingredient(name=ingredient_data["name"]) for
         ingredient_data in ingredients]
    )

    print("Данные успешно загружены в базу данных.")


if __name__ == "__main__":
    load_ingredients()

from django.core.management.base import BaseCommand
from api.models import Ingredient
import json


class Command(BaseCommand):
    help = 'Загружает ингредиенты из файла JSON в базу данных'

    def handle(self, *args, **options):
        with open("data/ingredients.json", "r", encoding="utf-8-sig") as file:
            ingredients = json.load(file)

        Ingredient.objects.bulk_create(
            [Ingredient(name=ingredient_data["name"]) for ingredient_data in
             ingredients]
        )

        self.stdout.write(self.style.SUCCESS('Ингредиенты успешно загружены'))

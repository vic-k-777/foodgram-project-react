import csv

from django.core.management.base import BaseCommand

from ...models import Ingredient


class Command(BaseCommand):
    help = "Импорт ингредиентов в из файла в БД"

    def handle(self, *args, **options):
        with open("data/ingredients.csv", encoding="utf-8") as file:
            file_reader = csv.reader(file)
            for row in file_reader:
                Ingredient.objects.get_or_create(
                    name=row[0],
                    measurement_unit=row[1],
                )

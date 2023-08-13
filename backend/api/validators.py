import re

from django.core.validators import ValidationError


def validate_recipe_name(name):
    if re.match(
        r'^[0-9!@#$%^&*()_+|~\-={}[\]:";<>,.?/]*$', name
    ):
        raise ValidationError(
            "Название рецепта не может состоять только из цифр и знаков."
        )


def validate_cooking_time(self, cooking_time):
    if int(cooking_time) < 1:
        raise ValidationError(
            "Минимальное время приготовления - одна минута."
        )
    return cooking_time


def validate_ingredients(self, ingredients):
    if not ingredients:
        raise ValidationError("Ингредиенты не должны повторяться.")
    for ingredient in ingredients:
        if int(ingredient.get('amount')) < 1:
            raise ValidationError(
                "Должен быть выбран хотя бы один ингредиент."
            )
    return ingredients

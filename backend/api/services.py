import io
from datetime import datetime

from django.db.models.aggregates import Sum
from recipes.models import RecipeIngredient


def get_shopping_list(user):
    ingredients = (
        RecipeIngredient.objects.filter(recipe__shopping_cart__user=user)
        .values("ingredient__name", "ingredient__measurement_unit")
        .annotate(amount=Sum("amount"))
    )
    today = datetime.today()
    shopping_list = (
        f"Список покупок для: {user.get_full_name()}\n\n"
        f"Дата: {today:%Y-%m-%d}\n\n"
    )
    shopping_list += "\n".join(
        [
            f'- {ingredient["ingredient__name"]} '
            f'({ingredient["ingredient__measurement_unit"]})'
            f' - {ingredient["amount"]}'
            for ingredient in ingredients
        ]
    )
    shopping_list += f"\n\nFoodgram ({today:%Y}) желает Вам приятных покупок!"

    shopping_list_bytes = io.BytesIO(shopping_list.encode("utf-8"))
    return shopping_list_bytes

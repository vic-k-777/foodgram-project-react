from io import BytesIO

from recipes.models import ShoppingCart


def get_shopping_list(user):
    purchases = (
        ShoppingCart.objects
        .filter(user=user)
        .select_related('recipe')
        .prefetch_related('recipe__ingredients')
    )
    shop_cart = dict()

    for purchase in purchases:
        for ingredient in purchase.recipe.ingredients.all():
            point_name = f'{ingredient.name} ({ingredient.measurement_unit})'
            shop_cart[point_name] = (
                shop_cart.get(point_name, 0) + ingredient.amount
            )

    file = BytesIO()
    with open(file, 'w') as f:
        for name, amount in shop_cart.items():
            f.write(f'* {name} - {amount}n')

    file.seek(0)
    return file

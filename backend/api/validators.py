
import re

from django.core.validators import ValidationError


def validate_recipe_name(name):
    if re.match(
        r'^[0-9!@#$%^&*()_+|~\-={}[\]:";<>,.?/]*$', name
    ):
        raise ValidationError(
            "Название рецепта не может состоять только из цифр и знаков."
            )

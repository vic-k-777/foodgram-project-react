from django.conf import settings
from django.contrib import admin

from recipes.models import (Favorited, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag,)
from users.models import Subscribe


class TagAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "color",
        "slug",
    )
    search_fields = (
        "name",
        "color",
        "slug",
    )
    list_filter = (
        "name",
        "color",
        "slug",
    )
    ordering = ("name",)
    empty_value_display = settings.EMPTY_VALUE_DISPLAY


class IngredientAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "measurement_unit",
    )
    search_fields = (
        "name",
        "measurement_unit",
    )
    list_filter = ("name",)
    ordering = ("id",)
    empty_value_display = settings.EMPTY_VALUE_DISPLAY


class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "author",
        "cooking_time",
        "text",
    )
    search_fields = (
        "username",
        "email",
        "first_name",
        "last_name",
    )
    list_filter = (
        "author",
        "name",
        "tags",
    )
    ordering = ("name",)
    empty_value_display = settings.EMPTY_VALUE_DISPLAY

    filter_horizontal = ("tags",)


class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "recipe",
        "ingredient",
        "amount",
    )
    search_fields = (
        "recipe",
        "ingredient",
    )
    list_filter = (
        "recipe",
        "ingredient",
    )
    empty_value_display = settings.EMPTY_VALUE_DISPLAY


class FavoritedAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "recipe")
    search_fields = (
        "user",
        "recipe",
    )
    list_filter = (
        "user",
        "recipe",
    )
    empty_value_display = settings.EMPTY_VALUE_DISPLAY


class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "recipe",
    )
    search_fields = (
        "user",
        "recipe",
    )
    list_filter = (
        "user",
        "recipe",
    )
    empty_value_display = settings.EMPTY_VALUE_DISPLAY


class SubscribeAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "author",
    )
    search_fields = ("author",)
    list_filter = (
        "user",
        "author",
    )
    empty_value_display = settings.EMPTY_VALUE_DISPLAY


admin.site.register(Tag, TagAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(RecipeIngredient, RecipeIngredientAdmin)
admin.site.register(Favorited, FavoritedAdmin)
admin.site.register(ShoppingCart, ShoppingCartAdmin)
admin.site.register(Subscribe, SubscribeAdmin)

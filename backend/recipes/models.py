import re

from django.core.validators import MinValueValidator, RegexValidator
from django.db import models
from django.db.models import UniqueConstraint

from users.models import User


class Tag(models.Model):
    """Создадим класс для Тегов"""

    name = models.CharField(
        verbose_name="Название",
        max_length=50,
        unique=True,
    )
    color = models.CharField(
        verbose_name="Цветовой HEX-код",
        max_length=7,
        unique=True,
        validators=[
            RegexValidator(
                re.compile(r"^#([a-fA-F0-9]{6})"),
                message=("Поле должно содержать HEX-код выбранного цвета."),
            )
        ],
    )
    slug = models.SlugField(
        verbose_name="Slug",
        unique=True,
    )

    class Meta:
        verbose_name = "Тег"
        verbose_name_plural = "Теги"
        ordering = ("name",)

    def __str__(self):
        return f"Тег {self.name}"


class Ingredient(models.Model):
    """Создадим класс для Ингредиентов"""

    name = models.CharField(
        verbose_name="Название",
        max_length=200,
    )
    measurement_unit = models.CharField(
        verbose_name="Единицы изменения",
        max_length=20,
    )

    class Meta:
        ordering = ("name",)
        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"
        constraints = [
            models.UniqueConstraint(
                fields=["name", "measurement_unit"], name="unique ingredient"
            )
        ]

    def __str__(self):
        return f"{self.name}, {self.measurement_unit}"


class Recipe(models.Model):
    """Создадим класс для Рецептов"""

    author = models.ForeignKey(
        User,
        verbose_name="Автор публикации (пользователь)",
        related_name="recipe",
        on_delete=models.CASCADE,
    )
    name = models.CharField(
        verbose_name="Название",
        max_length=50,
        validators=(
            
        )
    )
    image = models.ImageField(
        upload_to="recipes/",
        verbose_name="Картинка, закодированная в Base64",
    )
    text = models.TextField(
        verbose_name="Текстовое описание",
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        verbose_name="Ингредиенты",
    )
    tags = models.ManyToManyField(
        Tag, verbose_name="Список id тегов", related_name="recipes"
    )
    cooking_time = models.IntegerField(
        verbose_name="Время приготовления (в минутах)",
        validators=[
            MinValueValidator(
                1,
                message=(
                    "Минимальное время приготовления" "составляет одну минуту."
                ),
            ),
        ],
    )
    pub_date = models.DateTimeField(
        verbose_name="Дата публикации",
        auto_now_add=True,
    )

    class Meta:
        ordering = ("-pub_date",)
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"

    def __str__(self):
        return f'Рецепт "{self.name}" от {self.author}'


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="recipe_ingredient",
        verbose_name="рецепт",
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name="recipe_ingredient",
        verbose_name="ингредиент",
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name="количество",
        default=1,
        validators=(
            MinValueValidator(
                1,
                message="Должен быть выбран хотя бы один ингредиент."
            ),
        ),
    )

    class Meta:
        verbose_name = "рецепт и ингредиент"
        verbose_name_plural = "рецепты и ингредиенты"
        constraints = [
            UniqueConstraint(
                fields=[
                    "recipe",
                    "ingredient"
                ], name="recipe unique ingredient"
            )
        ]

    def __str__(self):
        return f"{self.ingredient} - {self.amount}"


class Favorited(models.Model):
    """Создадим класс для Избранного"""

    user = models.ForeignKey(
        User,
        verbose_name="Автор списка избранное",
        related_name="favorited",
        on_delete=models.CASCADE,
    )
    recipe = models.ForeignKey(
        Recipe,
        verbose_name="Рецепт в списке избранных",
        on_delete=models.CASCADE,
    )

    class Meta:
        ordering = ("user", "recipe")
        verbose_name = "Избранное"
        verbose_name_plural = "Избранные"

    def __str__(self):
        return f"{self.user} добавил {self.recipe} в избранное."


class ShoppingCart(models.Model):
    """Создадим класс для Списка покупок"""

    user = models.ForeignKey(
        User,
        verbose_name="Пользователь",
        related_name="shopping_cart",
        on_delete=models.CASCADE,
    )
    recipe = models.ForeignKey(
        Recipe,
        verbose_name="Рецепт",
        related_name="shopping_cart",
        on_delete=models.CASCADE,
    )

    class Meta:
        ordering = ("user", "recipe")
        verbose_name = "Список покупок"
        verbose_name_plural = "Списки покупок"

    def __str__(self):
        return f"{self.user} добавил {self.recipe} в cписок покупок."

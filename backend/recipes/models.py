from django.core.validators import RegexValidator
from django.db import models
from foodgram import settings
from users.models import User


class Tag(models.Model):
    """Создадим класс для Тегов"""
    name = models.CharField(
        verbose_name='Название',
        max_length=settings.TAG_MAX_LENGTH,
        unique=True,
    )
    color = models.CharField(
        verbose_name='Цветовой HEX-код',
        max_length=settings.TAG_MAX_LENGTH_COLOR_FIELD,
        unique=True,
        validators=[
            RegexValidator(
                settings.REGEX_COLOR_TAG,
                message=('Поле должно содержать HEX-код выбранного цвета.')
            )
        ]
    )
    slug = models.SlugField(
        verbose_name='Slug',
        unique=True,
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ('name',)

    def __str__(self):
        return f'Тег {self.name}'


class Ingredient(models.Model):
    """Создадим класс для Ингредиентов"""
    name = models.CharField(
        verbose_name='Название',
        max_length=settings.INGREDIENT_NAME_MAX_LENGTH,
    )
    measurement_unit = models.CharField(
        verbose_name='Единицы изменения',
        max_length=settings.INGREDIENT_MEASUREMENT_UNIT_MAX_LENGTH,
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = [
            models.UniqueConstraint(fields=['name', 'measurement_unit'],
                                    name='unique ingredient')
        ]

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class Recipe(models.Model):
    """Создадим класс для Рецептов"""
    author = models.ForeignKey(
        User,
        verbose_name='Автор публикации (пользователь)',
        related_name='recipe',
        on_delete=models.CASCADE,
    )
    name = models.CharField(
        verbose_name='Название',
        max_length=settings.RECIPE_NAME_MAX_LENGTH,
    )
    image = models.ImageField(
        upload_to='recipe/images/',
        verbose_name='Картинка, закодированная в Base64',
    )
    text = models.TextField(
        verbose_name='Текстовое описание',
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        verbose_name='Ингредиенты',
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Список id тегов',
    )
    cooking_time = models.IntegerField(
        verbose_name='Время приготовления (в минутах)',
    )
    pub_date = models.DateTimeField(
        verbose_name='Дата публикации',
        auto_now_add=True,
    )

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return f'Рецепт "{self.name}" от {self.author}'


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_ingredient',
        verbose_name='рецепт'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='recipe_ingredient',
        verbose_name='ингредиент'
    )
    amount = models.IntegerField(
        verbose_name='количество'
    )

    class Meta:
        verbose_name = 'рецепт и ингредиент'
        verbose_name_plural = 'рецепты и ингредиенты'

    def __str__(self):
        return f'{self.ingredient} - {self.amount}'


class Favorited(models.Model):
    """Создадим класс для Избранного"""
    user = models.ForeignKey(
        User,
        verbose_name='Автор списка избранное',
        related_name='favorited',
        on_delete=models.CASCADE,
    )
    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Рецепт в списке избранных',
        on_delete=models.CASCADE,
    )

    class Meta:
        ordering = ('user', 'recipe')
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные'

    def __str__(self):
        return f'{self.user} добавил {self.recipe} в избранное.'


class ShoppingCart(models.Model):
    """Создадим класс для Списка покупок"""
    user = models.ForeignKey(
        User,
        verbose_name='Пользователь',
        related_name='shopping_cart',
        on_delete=models.CASCADE
    )
    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Рецепт',
        related_name='shopping_cart',
        on_delete=models.CASCADE
    )

    class Meta:
        ordering = ('user', 'recipe')
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'

    def __str__(self):
        return f'{self.user} добавил {self.recipe} в cписок покупок.'

from django.db import transaction

from drf_base64.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import ModelSerializer
from rest_framework.validators import UniqueTogetherValidator

from recipes.models import Ingredient, Recipe, RecipeIngredient, Tag
from users.models import Subscribe, User


class CustomUserSerializer(serializers.BaseSerializer):
    """Сериализатор класса Пользователей"""
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
        )

    @property
    def user(self):
        return self.context['request'].user

    def get_is_subscribed(self, author):
        if (self.context.get('request') and not self.user.is_anonymous):
            return (Subscribe
                    .objects.
                    filter(
                        user=self.user,
                        author=author
                    ).exists())
        return False


class TagSerializer(ModelSerializer):
    """Сериализатор класса Тегов"""
    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(ModelSerializer):
    """Класс Ингредиентов"""
    class Meta:
        model = Ingredient
        fields = '__all__'


class ShortIngredientSerializer(serializers.ModelSerializer):
    """Список ингредиентов для рецепта"""

    id = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=7, decimal_places=2)

    class Meta:
        model = Ingredient
        fields = ('id', 'amount')


class GetIngredientRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор получения списка ингредиентов к рецепту"""

    name = serializers.SerializerMethodField()
    measurement_unit = serializers.SerializerMethodField()
    amount = serializers.SerializerMethodField()
    ingredient = serializers.PrimaryKeyRelatedField(
        source='ingredient.id',
        read_only=True
    )

    class Meta:
        model = RecipeIngredient
        fields = ('ingredient', 'name', 'measurement_unit', 'amount')

    def get_name(self, obj):
        return obj.ingredient.name

    def get_measurement_unit(self, obj):
        return obj.ingredient.measurement_unit

    def get_amount(self, obj):
        return obj.amount


class RecipeReadSerializer(serializers.ModelSerializer):
    """Сериализатор класса чтения рецепта"""
    tags = TagSerializer(many=True, read_only=True)
    author = CustomUserSerializer(read_only=True)
    ingredients = serializers.SerializerMethodField(read_only=True)
    image = Base64ImageField(read_only=True)
    is_favorited = serializers.BooleanField(read_only=True, default=False)
    is_in_shopping_cart = serializers.BooleanField(read_only=True)

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients', 'is_favorited',
                  'is_in_shopping_cart', 'name', 'image', 'text',
                  'cooking_time')

    @property
    def user(self):
        return self.context['request'].user

    def get_ingredients(self, obj):
        ingredients = RecipeIngredient.objects.filter(recipe=obj)
        return GetIngredientRecipeSerializer(ingredients, many=True).data


class RecipeWriteSerializer(serializers.ModelSerializer):
    """Сериализатор класса записи рецепта"""
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all(),
    )
    author = CustomUserSerializer(read_only=True)
    ingredients = ShortIngredientSerializer(many=True)
    image = Base64ImageField(max_length=None, use_url=True)

    class Meta:
        model = Recipe
        fields = '__all__'
        read_only_fields = ('author',)
        validators = [
            UniqueTogetherValidator(
                queryset=Recipe.objects.all(),
                fields=['name', 'text', 'cooking_time'],
                message=('Обязательное поле')
            ),
            UniqueTogetherValidator(
                queryset=Ingredient.objects.all(),
                fields=('ingredients'),
                message=('Ингредиенты должны быть уникальными')
            )
        ]

    def validate_tags(self, obj):
        if not obj.get('tags'):
            raise ValidationError(
                'Убедитесь, что это значение больше либо равно 1.'
            )
        return obj

    def validate_ingredients(self, obj):
        if not obj.get('ingredients'):
            raise ValidationError(
                'Убедитесь, что это значение больше либо равно 1.'
            )
        return obj

    @transaction.atomic
    def tags_and_ingredients_set(self, recipe, tags, ingredients):
        recipe.tags.set(tags)
        ingredient_ids = [ingredient['id'] for ingredient in ingredients]
        ingredients_queryset = Ingredient.objects.filter(pk__in=ingredient_ids)
        recipe_ingredients = [
            RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient,
                amount=ingredient_data['amount']
            )
            for ingredient_data, ingredient in zip(
                ingredients,
                ingredients_queryset
            )
        ]
        RecipeIngredient.objects.bulk_create(recipe_ingredients)

    @transaction.atomic
    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(author=self.context['request'].user,
                                       **validated_data)
        self.tags_and_ingredients_set(recipe, tags, ingredients)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        instance.image = validated_data.get('image', instance.image)
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get(
            'cooking_time', instance.cooking_time)
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        RecipeIngredient.objects.filter(
            recipe=instance,
            ingredient__in=instance.ingredients.all()).delete()
        self.tags_and_ingredients_set(instance, tags, ingredients)
        instance.save()
        return instance

    def to_representation(self, instance):
        return RecipeReadSerializer(instance, context=self.context).data


class RecipeShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class SubscribeSerializer(serializers.ModelSerializer):
    recipes = RecipeShortSerializer(many=True, read_only=True)
    recipes_count = serializers.SerializerMethodField(read_only=True)
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    @staticmethod
    def get_recipes_count(author):
        return author.recipes.count()

    def get_is_subscribed(self, author):
        user = self.context['request'].user
        return bool(author.follower.filter(user=user))

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'recipes',
                  'recipes', 'recipes_count')

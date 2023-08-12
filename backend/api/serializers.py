import base64

from djoser.serializers import UserCreateSerializer
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from django.core.files.base import ContentFile
from django.db import transaction

from api.validators import validate_recipe_name
from recipes.models import Ingredient, Recipe, RecipeIngredient, Tag
from users.models import Subscribe, User


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith("data:image"):
            format, imgstr = data.split(";base64,")
            ext = format.split("/")[-1]
            data = ContentFile(base64.b64decode(imgstr), name="temp." + ext)
        return super().to_internal_value(data)

    def get_file_extension(self, file_name, decoded_file):
        import imghdr

        extension = imghdr.what(file_name, decoded_file)
        extension = "jpg" if extension == "jpeg" else extension

        return extension


class CustomUserSerializer(UserCreateSerializer):
    """Сериализатор класса Пользователей"""

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = "__all__"

    def get_is_subscribed(self, author):
        if (
            self.context.get("request")
            and not self.context["request"].user.is_anonymous
        ):
            return Subscribe.objects.filter(
                user=self.context["request"].user, author=author
            ).exists()
        return False


class TagSerializer(ModelSerializer):
    """Сериализатор класса Тегов"""

    class Meta:
        model = Tag
        fields = "__all__"


class IngredientSerializer(ModelSerializer):
    """Класс Ингредиентов"""

    class Meta:
        model = Ingredient
        fields = "__all__"


class ShortIngredientSerializer(ModelSerializer):
    """Список ингредиентов для рецепта"""

    id = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=7, decimal_places=2)

    class Meta:
        model = Ingredient
        fields = ("id", "amount")


class GetIngredientRecipeSerializer(ModelSerializer):
    """Сериализатор получения списка ингредиентов к рецепту"""

    name = serializers.SerializerMethodField()
    measurement_unit = serializers.SerializerMethodField()
    amount = serializers.SerializerMethodField()
    ingredient = serializers.PrimaryKeyRelatedField(
        source="ingredient.id", read_only=True
    )

    class Meta:
        model = RecipeIngredient
        fields = ("ingredient", "name", "measurement_unit", "amount")

    def get_name(self, obj):
        return obj.ingredient.name

    def get_measurement_unit(self, obj):
        return obj.ingredient.measurement_unit

    def get_amount(self, obj):
        return obj.amount


class RecipeReadSerializer(ModelSerializer):
    """Сериализатор класса чтения рецепта"""

    tags = TagSerializer(many=True, read_only=True)
    author = CustomUserSerializer(read_only=True)
    ingredients = serializers.SerializerMethodField(read_only=True)
    image = Base64ImageField(read_only=True)
    is_favorited = serializers.BooleanField(read_only=True, default=False)
    is_in_shopping_cart = serializers.BooleanField(read_only=True)

    class Meta:
        model = Recipe
        fields = "__all__"

    @property
    def user(self):
        return self.context["request"].user

    def get_ingredients(self, obj):
        ingredients = RecipeIngredient.objects.filter(recipe=obj)
        serializer = GetIngredientRecipeSerializer(ingredients, many=True)
        return serializer.data


class RecipeWriteSerializer(ModelSerializer):
    """Сериализатор класса записи рецепта"""

    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all(),
    )
    author = CustomUserSerializer(read_only=True)
    ingredients = ShortIngredientSerializer(
        many=True,
        validators=[validate_cooking_time],
    )
    image = Base64ImageField(max_length=None, use_url=True)
    name = serializers.CharField(
        max_length=50,
        validators=[validate_recipe_name],
    )
    # cooking_time = serializers.PositiveSmallIntegerField(
    #     validators=[validate_cooking_time],
    # )

    class Meta:
        model = Recipe
        fields = "__all__"
        read_only_fields = ("author",)

    @transaction.atomic
    def tags_and_ingredients_set(self, recipe, tags, ingredients):
        recipe.tags.set(tags)
        if ingredients:
            ingredient_ids = [
                ingredient.get("id") for ingredient in ingredients
            ]
            ingredients_queryset = Ingredient.objects.filter(
                pk__in=ingredient_ids
            )
            recipe_ingredients = [
                RecipeIngredient(
                    recipe=recipe,
                    ingredient=ingredient,
                    amount=ingredient_data["amount"],
                )
                for ingredient_data, ingredient in zip(
                    ingredients, ingredients_queryset
                )
            ]
            RecipeIngredient.objects.bulk_create(recipe_ingredients)

    @transaction.atomic
    def create(self, validated_data):
        tags = validated_data.pop("tags")
        ingredients = validated_data.pop("ingredients", None)
        recipe = Recipe.objects.create(
            author=self.context["request"].user, **validated_data
        )
        self.tags_and_ingredients_set(recipe, tags, ingredients)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        instance.image = validated_data.get("image", instance.image)
        instance.name = validated_data.get("name", instance.name)
        instance.text = validated_data.get("text", instance.text)
        instance.cooking_time = validated_data.get(
            "cooking_time", instance.cooking_time
        )
        tags = validated_data.pop("tags")
        ingredients = validated_data.get("ingredients")
        RecipeIngredient.objects.filter(
            recipe=instance, ingredient__in=instance.ingredients.all()
        ).delete()
        self.tags_and_ingredients_set(instance, tags, ingredients)
        instance.save()
        return instance

    def to_representation(self, instance):
        data = super().to_representation(instance)
        return data


class RecipeShortSerializer(ModelSerializer):
    class Meta:
        model = Recipe
        fields = (
            "id",
            "name",
            "image",
            "cooking_time",
        )


class SubscribeSerializer(CustomUserSerializer):
    recipe = RecipeShortSerializer(many=True, read_only=True)
    recipes_count = serializers.SerializerMethodField(read_only=True)
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    def get_recipes_count(self, author):
        return author.recipe.count()

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        return Subscribe.objects.filter(author=obj, user=user).exists()

    def get_recipe(self, obj):
        request = self.context.get('request')
        limit = request.GET.get('recipe_limit')
        recipe = obj.recipe.all()
        if limit:
            recipe = recipe[:int(limit)]
        serializer = RecipeShortSerializer(recipe, many=True, read_only=True)
        return serializer.data

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "recipe",
            "recipes_count",
        )
        read_only_fields = (
            "email",
            "username",
            "first_name",
            "last_name",
        )

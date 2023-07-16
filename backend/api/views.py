from api.pagination import CustomPagination
from api.permissions import IsAuthenticatedOrAdmin
from api.serializers import SubscribeSerializer, UsersSerialiser
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from recipes.models import Favorited, Ingredient, Recipe, ShoppingCart, Tag
from rest_framework import exceptions, filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import SAFE_METHODS, IsAuthenticated
from rest_framework.response import Response
from users.models import Subscribe, User

from .filters import RecipeFilter
from .permissions import IsAuthorOrReadOnly
from .serializers import (IngredientSerializer, RecipeReadSerializer,
                          RecipeShortSerializer, RecipeWriteSerializer,
                          TagSerializer)


class UserViewSet(UserViewSet):
    """Вьюсет для пользователей"""
    queryset = User.objects.all()
    pagination_class = CustomPagination
    serializer_class = UsersSerialiser

    def get_user(self, id):
        return get_object_or_404(User, id=id)

    @action(detail=False, permission_classes=(IsAuthenticatedOrAdmin,))
    def subscriptions(self, request):
        queryset = User.objects.filter(following__user=request.user)
        pages = self.paginate_queryset(queryset)
        serializer = SubscribeSerializer(
            pages,
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
            detail=True,
            methods=['post'],
            serializer_class=SubscribeSerializer,
            permission_classes=(IsAuthenticatedOrAdmin,),
    )
    def subscribe(self, request, **kwargs):
        author = self.get_user(kwargs['id'])
        if request.user == author:
            raise exceptions.ValidationError(
                'Подписываться на себя запрещено.'
            )
        _, created = Subscribe.objects.get_or_create(
            user=request.user,
            author=author
        )
        if not created:
            raise exceptions.ValidationError(
                'Вы уже подписаны на этого пользователя.'
            )
        serializer = self.get_serializer(author)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def unsubscribe(self, request, **kwargs):
        author = self.get_user(kwargs['id'])
        get_object_or_404(Subscribe, user=request.user, author=author).delete()
        return Response({'detail': 'Успешная отписка'},
                        status=status.HTTP_204_NO_CONTENT)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для ингредиентов"""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (filters.SearchFilter,)
    pagination_class = None
    search_fields = ('name',)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для тегов"""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет для рецептов"""
    queryset = Recipe.objects.all()
    pagination_class = CustomPagination
    permission_classes = (IsAuthorOrReadOnly, )
    filter_backends = (DjangoFilterBackend, )
    filterset_class = RecipeFilter
    http_method_names = ['get', 'post', 'patch', 'create', 'delete']

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeReadSerializer
        return RecipeWriteSerializer

    def get_recipe(self, id):
        return get_object_or_404(Recipe, id=id)

    @action(detail=True, methods=['post'],
            permission_classes=(IsAuthenticated,))
    def favorite(self, request, pk):
        return self.add_to(Favorited, request.user, pk)

    @favorite.mapping.delete
    def unfavorite(self, request, pk):
        return self.delete_from(Favorited, request.user, pk)

    @action(detail=True, methods=['post'],
            permission_classes=(IsAuthenticated,),
            pagination_class=None)
    def shopping_cart(self, request, pk):
        return self.add_to(ShoppingCart, request.user, pk)

    @shopping_cart.mapping.delete
    def delete_from_shopping_cart(self, request, pk):
        return self.delete_from(ShoppingCart, request.user, pk)

    @action(detail=False, methods=['get'],
            permission_classes=(IsAuthenticated,))
    def download_shopping_cart(self, request):
        user = request.user
        purchases = ShoppingCart.objects.filter(user=user)
        file = 'shopping-list.txt'
        with open(file, 'w') as f:
            shop_cart = dict()
            for purchase in purchases:
                ingredients = Ingredient.objects.filter(
                    recipe=purchase.recipe.id
                )
                for r in ingredients:
                    i = Ingredient.objects.get(pk=r.ingredient.id)
                    point_name = f'{i.name} ({i.measurement_unit})'
                    if point_name in shop_cart.keys():
                        shop_cart[point_name] += r.amount
                    else:
                        shop_cart[point_name] = r.amount

            for name, amount in shop_cart.items():
                f.write(f'* {name} - {amount}\n')

        return FileResponse(open(file, 'rb'), as_attachment=True)

    def add_to(self, model, user, pk):
        if model.objects.filter(user=user, recipe__id=pk).exists():
            return Response({'errors': 'Рецепт уже добавлен!'},
                            status=status.HTTP_400_BAD_REQUEST)
        recipe = get_object_or_404(Recipe, id=pk)
        model.objects.create(user=user, recipe=recipe)
        serializer = RecipeShortSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete_from(self, model, user, pk):
        obj = model.objects.filter(user=user, recipe__id=pk)
        if obj.exists():
            obj.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({'errors': 'Рецепт уже удален!'},
                        status=status.HTTP_400_BAD_REQUEST)

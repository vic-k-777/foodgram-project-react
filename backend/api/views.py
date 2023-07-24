from django.db.models import Exists, OuterRef, Prefetch
from django.http import FileResponse
from django.shortcuts import get_object_or_404

from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import exceptions, filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import SAFE_METHODS, IsAuthenticated
from rest_framework.response import Response

from api.filters import RecipeFilter
from api.pagination import CustomPagination
from api.permissions import IsAuthorOrReadOnly
from api.serializers import (CustomUserSerializer, IngredientSerializer,
                             RecipeReadSerializer, RecipeShortSerializer,
                             RecipeWriteSerializer, SubscribeSerializer,
                             TagSerializer,)
from api.services import get_shopping_list
from recipes.models import Favorited, Ingredient, Recipe, ShoppingCart, Tag
from users.models import Subscribe, User


class CustomUserViewSet(UserViewSet):
    """Вьюсет для пользователей"""

    queryset = User.objects.all()
    pagination_class = CustomPagination
    serializer_class = CustomUserSerializer


class SubscriptionViewSet(UserViewSet):
    """Вьюсет подписок"""

    serializer_class = SubscribeSerializer
    pagination_class = CustomPagination

    @action(detail=False, permission_classes=(IsAuthenticated,))
    def subscriptions(self, request):
        queryset = User.objects.filter(following__user=request.user)
        pages = self.paginate_queryset(queryset)
        serializer = SubscribeSerializer(
            pages,
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(detail=True,
            methods=['post'],
            serializer_class=SubscribeSerializer,
            permission_classes=(IsAuthenticated,))
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
        subscribe_obj = get_object_or_404(
            Subscribe,
            user=request.user,
            author=author)
        subscribe_obj.delete()
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

    pagination_class = CustomPagination
    permission_classes = (IsAuthorOrReadOnly, )
    filter_backends = (DjangoFilterBackend, )
    filterset_class = RecipeFilter
    http_method_names = ['get', 'post', 'patch', 'create', 'delete']
    permission_classes = (IsAuthorOrReadOnly, IsAuthenticated)

    def get_queryset(self):
        queryset = Recipe.objects.all()
        if self.request.user.is_authenticated:
            queryset = queryset.annotate(
                is_favorited=Exists(Favorited.objects.filter(
                    user=self.request.user, recipe=OuterRef('pk'))
                ),
                is_in_shopping_cart=Exists(ShoppingCart.objects.filter(
                    user=self.request.user, recipe=OuterRef('pk'))
                )
            )
        queryset = queryset.select_related('author')
        queryset = queryset.prefetch_related(
            Prefetch('tags', 'ingredients'),
        )
        return queryset

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeReadSerializer
        return RecipeWriteSerializer

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

    @action(
        detail=False,
        methods=['get'],
        permission_classes=(IsAuthenticated,)
    )
    def download_shopping_cart(self, request):
        user = request.user
        file = get_shopping_list(user)
        return FileResponse(
            file, as_attachment=True, filename='shopping-list.txt'
        )

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

from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import exceptions, filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from django.db.models import Exists, OuterRef
from django.http import HttpResponse
from django.shortcuts import get_object_or_404

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
    permission_classes = (IsAuthenticated,)

    def get_user(self, id):
        return get_object_or_404(User, id=id)

    @action(detail=False,
            methods=["get"],
            )
    def subscriptions(self, request):
        # queryset = User.objects.filter(following__user=request.user)
        # pages = self.paginate_queryset(queryset)
        # serializer = SubscribeSerializer(
        #     queryset, many=True, context={"request": request}
        # )
        # return Response(serializer.data)
        user = request.user
        queryset = Subscribe.objects.filter(user=user)
        page = self.paginate_queryset(queryset)
        serializer = SubscribeSerializer(
            page, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=["post"],
        serializer_class=SubscribeSerializer,
    )
    def subscribe(self, request, **kwargs):
        author = self.get_user(kwargs["id"])
        if request.user == author:
            raise exceptions.ValidationError(
                "Подписываться на себя запрещено."
            )
        _, created = Subscribe.objects.get_or_create(
            user=request.user, author=author
        )
        if not created:
            raise exceptions.ValidationError(
                "Вы уже подписаны на этого пользователя."
            )
        serializer = self.get_serializer(author)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def unsubscribe(self, request, **kwargs):
        author = self.get_user(kwargs["id"])
        get_object_or_404(
            Subscribe,
            user=request.user,
            author=author
        ).delete()
        return Response(
            {"detail": "Успешная отписка"},
            status=status.HTTP_204_NO_CONTENT
        )


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для ингредиентов"""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (filters.SearchFilter,)
    pagination_class = None
    search_fields = ("name",)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для тегов"""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет для рецептов"""

    pagination_class = CustomPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    http_method_names = ["get", "post", "patch", "create", "delete"]
    permission_classes = (IsAuthorOrReadOnly,)

    def get_queryset(self):
        queryset = Recipe.objects.all()
        if self.request.user.is_authenticated:
            queryset = queryset.annotate(
                is_favorited=Exists(
                    Favorited.objects.filter(
                        user=self.request.user, recipe=OuterRef("pk")
                    )
                ),
                is_in_shopping_cart=Exists(
                    ShoppingCart.objects.filter(
                        user=self.request.user, recipe=OuterRef("pk")
                    )
                ),
            )
        Recipe.objects.select_related("author").prefetch_related(
            "tags", "ingredients"
        )
        return queryset

    def get_serializer_class(self):
        if self.action == "list" or self.action == "retrieve":
            return RecipeReadSerializer
        return RecipeWriteSerializer

    @action(
        detail=True, methods=["post"], permission_classes=(IsAuthenticated,)
    )
    def favorite(self, request, pk):
        return self.add_to(Favorited, request.user, pk)

    @favorite.mapping.delete
    def unfavorite(self, request, pk):
        return self.delete_from(Favorited, request.user, pk)

    @action(
        detail=True,
        methods=["post"],
        permission_classes=(IsAuthenticated,),
        pagination_class=None,
    )
    def shopping_cart(self, request, pk):
        return self.add_to(ShoppingCart, request.user, pk)

    @shopping_cart.mapping.delete
    def delete_from_shopping_cart(self, request, pk):
        return self.delete_from(ShoppingCart, request.user, pk)

    @action(
        detail=False, methods=["get"], permission_classes=(IsAuthenticated,)
    )
    def download_shopping_cart(self, request):
        user = request.user
        if not user.shopping_cart.exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)

        shopping_list_bytes = get_shopping_list(user)
        filename = f"{user.username}_shopping_list.txt"
        response = HttpResponse(content_type="text/plain")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        response.write(shopping_list_bytes.getvalue())

        return response

    def add_to(self, model, user, pk):
        if model.objects.filter(user=user, recipe__id=pk).exists():
            return Response(
                {"errors": "Рецепт уже добавлен!"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        recipe = get_object_or_404(Recipe, id=pk)
        model.objects.create(user=user, recipe=recipe)
        serializer = RecipeShortSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete_from(self, model, user, pk):
        obj = model.objects.filter(user=user, recipe__id=pk)
        if obj.exists():
            obj.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {"errors": "Рецепт уже удален!"},
            status=status.HTTP_400_BAD_REQUEST
        )

from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from users.models import User
from api.permissions import IsAuthorOrReadOnlyPermission
from .models import (Basket, Favorites, Follow,
                     Ingredient, Recipes, Tag)
from .pagination import Pagination
from .serializers import (
    ChangePasswordSerializer, ConfirmationSerializer,
    FavoritesSerializer, FollowSerializer, IngredientSerializer,
    RecipesSerializer, TagSerializer, UserMeSerializer, UserSerializer,
    BasketSerializer
)


class UserViewSet(viewsets.ModelViewSet):
    """Работа с user"""

    queryset = User.objects.all()
    serializer_class = UserSerializer
    http_method_names = ["get", "post", "patch", "delete"]
    pagination_class = Pagination
    permission_classes = [AllowAny]

    @action(methods=["post"], detail=False, url_path="set_password")
    def set_password(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        if not user.check_password(serializer.data.get("current_password")):
            raise APIException(
                detail={"current_password": ["Неверный пароль."]},
                code=status.HTTP_400_BAD_REQUEST)

        user.set_password(serializer.data.get("new_password"))
        user.save()

        response = {
            "status": "success",
            "code": status.HTTP_200_OK,
            "message": "Пароль успешно обновлен",
            "data": [],
        }
        return Response(response)


class UserMeAPIView(RetrieveAPIView):
    """Представление для эндпоинта 'me'."""

    queryset = User.objects.all()
    serializer_class = UserMeSerializer

    def get(self, request):
        user = get_object_or_404(User, username=request.user.username)
        serializer = self.get_serializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class GetToken(generics.CreateAPIView):
    """Получение токена пользователем."""

    serializer_class = ConfirmationSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data.get("email")
        password = serializer.validated_data.get("password")
        user = User.objects.filter(email=email).first()
        if user is not None and user.check_password(password):
            token, created = Token.objects.get_or_create(user=user)
            return Response({"auth_token": token.key},
                            status=status.HTTP_200_OK)
        return Response(
            {"detail": "Invalid credentials"},
            status=status.HTTP_400_BAD_REQUEST
        )


class TokenDeleteView(APIView):
    """Удаление токена пользователем."""

    def delete(self, request):
        token = request.auth
        if isinstance(token, RefreshToken):
            token.blacklist()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def post(self, request):
        return self.delete(request)


class TagViewSet(viewsets.ModelViewSet):
    """Вывод всех тегов и тегов по id"""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class RecipesViewSet(viewsets.ModelViewSet):
    """Вывод рецептов-рецептов по id,
    Создание рецепта,
    Поиск по тегам,
    Поиск по is_favorited.
    """

    queryset = Recipes.objects.all()
    serializer_class = RecipesSerializer
    pagination_class = Pagination
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ("name",)

    def get_queryset(self):
        queryset = super().get_queryset()
        is_favorited = self.request.query_params.get("is_favorited")

        if is_favorited == "1":
            user = self.request.user
            favorited_recipes = (
                Favorites.objects.filter(user=user).values_list("recipe",
                                                                flat=True))
            queryset = queryset.filter(pk__in=favorited_recipes)

        tags_names = self.request.query_params.getlist("tags__name")
        if tags_names:
            tags_filter = Q()
            for tag_name in tags_names:
                tags_filter |= Q(tags__name__icontains=tag_name)
            queryset = queryset.filter(tags_filter).distinct()

        return queryset

    def perform_create(self, serializer):
        serializer.save(author=self.request.user,
                        recipe_ingredients=self.request.data.get("ingredients")
                        )


class IngredientViewSet(viewsets.ModelViewSet):
    """
    Получить список всех ингедиентов,
    """
    permission_classes = [IsAuthenticatedOrReadOnly]
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer


class AddRecipeToShoppingCartViewSet(viewsets.ModelViewSet):
    serializer_class = BasketSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = Pagination

    def create(self, request, id):
        recipe = get_object_or_404(Recipes, pk=id)
        quantity = int(request.data.get("quantity", 1))
        cooking_time = int(request.data.get("cooking_time", 0))

        serializer = self.get_serializer(
            data={
                "recipe": recipe.id,
                "cooking_time": cooking_time
            },
            context={
                "request": request,
                "recipe": recipe,
                "quantity": quantity,
                "cooking_time": cooking_time
            }
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, id):
        recipe_id = int(id)
        baskets = Basket.objects.filter(user=request.user, recipe_id=recipe_id)

        if baskets.exists():
            baskets.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(status=status.HTTP_404_NOT_FOUND)


@api_view(["GET"])
@permission_classes([IsAuthorOrReadOnlyPermission])
def download_shopping_list(request):
    """
    Скачать рецепт из корзины.
    """
    user = request.user
    shopping_list = Basket.objects.filter(user=user)

    response = HttpResponse(content_type="text/plain")
    response["Content-Disposition"] = (
        'attachment; filename="shopping_list.txt"')

    total_quantity = {}

    for basket in shopping_list:
        recipe = basket.recipe
        recipe_ingredients = recipe.recipe_ingredients.all()
        message = "Спасибо что пользуетесь нашим сервисом!"

        for recipe_ingredient in recipe_ingredients:
            ingredient_name = recipe_ingredient.ingredient.name
            quantity = basket.quantity * recipe_ingredient.amount
            measurement_unit = recipe_ingredient.measurement_unit

            if ingredient_name in total_quantity:
                total_quantity[ingredient_name] += quantity
            else:
                total_quantity[ingredient_name] = quantity

    for ingredient_name, total_quantity in total_quantity.items():
        response.write(
            f"{ingredient_name} {total_quantity} {measurement_unit}\n")
    response.write(f"{message}")
    return response


class FavoritesViewSet(viewsets.GenericViewSet):
    """
    Добавить рецепт в кизбранное,
    Удалить рецепт из избранного.
    """

    permission_classes = [IsAuthenticatedOrReadOnly,
                          IsAuthorOrReadOnlyPermission]
    serializer_class = FavoritesSerializer
    lookup_field = "recipe_id"

    def get_queryset(self):
        return self.request.user.favorite_user.all()

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        recipe_id = self.kwargs.get("recipe_id")
        recipe = get_object_or_404(Recipes, pk=recipe_id)
        favorites_exists = Favorites.objects.filter(
            user=request.user, recipe=recipe
        ).exists()

        if favorites_exists:
            raise ValidationError({"error": "Рецепт уже добавлен в избранное"})

        if not recipe:
            return Response(
                {"error": "Рецепт не найден"}, status=status.HTTP_404_NOT_FOUND
            )

        favorites, created = Favorites.objects.get_or_create(
            user=request.user,
            recipe=recipe,
        )

        serializer = self.get_serializer(favorites)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    def destroy(self, request, *args, **kwargs):
        recipe_id = self.kwargs.get("recipe_id")
        favorites = Favorites.objects.filter(
            user=request.user, recipe_id=recipe_id
        ).first()

        if favorites:
            favorites.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(
            {"error": "Рецепт не найден в списке избранного"},
            status=status.HTTP_404_NOT_FOUND,
        )


class FollowViewSet(viewsets.ModelViewSet):
    """Получить мои подписки,
    Подписатся на пользователся-отписатся."""

    queryset = Follow.objects.all()
    serializer_class = FollowSerializer
    subscription_serializer = FollowSerializer
    pagination_class = Pagination
    permission_classes = [IsAuthenticatedOrReadOnly]

    def create(self, request, *args, **kwargs):
        user_id = self.kwargs.get("user_id")
        author = get_object_or_404(User, pk=user_id)
        follow, created = Follow.objects.get_or_create(
            user=request.user,
            author=author,
        )
        if created:
            serializer = FollowSerializer(
                follow, context={"request": request, "user_id": user_id}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        user_id = self.kwargs.get("user_id")
        follow = Follow.objects.filter(user=request.user,
                                       user_id=user_id).first()

        if follow:
            user_obj = follow.user
            follow.delete()
            serializer = UserMeSerializer(user_obj,
                                          context={"request": request})
            return Response(serializer.data)

    def get_queryset(self):
        return Follow.objects.filter(user=self.request.user)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        paginator = Pagination()
        paginated_queryset = paginator.paginate_queryset(queryset, request,
                                                         view=self)
        serializer = self.subscription_serializer(
            paginated_queryset, many=True, context={"request": request}
        )
        return paginator.get_paginated_response(serializer.data)

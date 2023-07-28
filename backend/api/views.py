from api.permissions import GuestPermission, IsAuthorOrReadOnlyPermission
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.generics import RetrieveAPIView
from rest_framework.response import Response
from rest_framework.exceptions import APIException
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from users.models import User

from .models import (Basket, Favorites, Follow,
                     Ingredient, Recipes, Tag)
from .pagination import Pagination
from .serializers import (
    BasketSerializer, ChangePasswordSerializer, ConfirmationSerializer,
    FavoritesSerializer, FollowSerializer, IngredientSerializer,
    RecipesSerializer, TagSerializer, UserMeSerializer, UserSerializer,
)


class UserRecipesViewSet(viewsets.ModelViewSet):
    """Эндпоинт для фильтрации по тегам автора"""

    serializer_class = RecipesSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["name", "tags__name"]
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        user_id = self.kwargs.get("user_id")
        return Recipes.objects.filter(author__id=user_id)


class UserViewSet(viewsets.ModelViewSet):
    """Работа с user"""

    queryset = User.objects.all()
    serializer_class = UserSerializer
    http_method_names = ["get", "post", "patch", "delete"]
    pagination_class = Pagination
    permission_classes = [GuestPermission]

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


@permission_classes([AllowAny])
class GetToken(generics.CreateAPIView):
    """Получение токена пользователем."""

    serializer_class = ConfirmationSerializer

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
        serializer.save(author=self.request.user)


class IngredientViewSet(viewsets.ModelViewSet):
    """
    Получить список всех ингедиентов,
    """

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer


class AddRecipeToShoppingCart(APIView):
    """
    Добавить рецепт в корзину,
    Удалить рецепт из корзины.
    """

    pagination_class = Pagination
    permission_classes = [IsAuthenticatedOrReadOnly]

    def post(self, request, id):
        recipe_id = int(id)
        quantity = int(request.data.get("quantity", 1))
        cooking_time = int(request.data.get("cooking_time", 0))
        recipe = get_object_or_404(Recipes, pk=recipe_id)
        ingredient = recipe.ingredients.all()

        basket = Basket.objects.create(
            recipe=recipe,
            user=request.user,
            quantity=quantity,
            cooking_time=cooking_time,
            image=recipe.image,
            ingredient=ingredient,
        )
        serializer = BasketSerializer(basket)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, id):
        try:
            recipe_id = int(id)
            basket = request.user.baskets.filter(recipe_id=recipe_id)
            if basket:
                basket.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


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
        recipe = get_object_or_404(Recipes, pk=recipe_id).first()
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
            author=author,)
        author_name = follow.author.username
        if created:
            serializer = FollowSerializer(follow,
                                          context={"request": request})
            return Response(serializer.data,
                            status=status.HTTP_201_CREATED)
        # можно оставлю else хочу что бы выводилось имя если уже подписан)
        else:
            message = f"Вы уже подписаны на {author_name}!"
            return Response(
                {"message": message}, status=status.HTTP_400_BAD_REQUEST
            )

    def destroy(self, request, *args, **kwargs):
        user_id = self.kwargs.get("user_id")
        try:
            follow = get_object_or_404(Follow, user=request.user,
                                       author_id=user_id)
            follow.delete()
            author_name = follow.author.username
            message = f"Вы успешно отписались от {author_name}!"
            return Response({"message": message},
                            status=status.HTTP_204_NO_CONTENT)
        # и тут я хочу выводить имя можно и оставить правильно)
        except Follow.DoesNotExist:
            author = get_object_or_404(User, pk=user_id)
            author_name = author.username
            message = f"Вы не подписаны на {author_name}!"
            return Response({"message": message},
                            status=status.HTTP_404_NOT_FOUND)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        paginator = Pagination()
        paginated_queryset = paginator.paginate_queryset(queryset, request,
                                                         view=self)
        serializer = self.subscription_serializer(
            paginated_queryset, many=True, context={"request": request}
        )
        return paginator.get_paginated_response(serializer.data)

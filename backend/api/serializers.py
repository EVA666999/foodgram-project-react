import base64

from django.contrib.auth.models import AnonymousUser
from django.core.files.base import ContentFile
from rest_framework import serializers
from users.models import User

from .models import (
    Basket,
    Favorites,
    Follow,
    Ingredient,
    RecipeIngredient,
    Recipes,
    Tag,
)


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith("data:image"):
            format, imgstr = data.split(";base64,")
            ext = format.split("/")[-1]

            data = ContentFile(base64.b64decode(imgstr), name="temp." + ext)

        return super().to_internal_value(data)


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "is_subscribed",
        )
        read_only_fields = ("id",)

    def create(self, validated_data):
        user = User.objects.create(
            username=validated_data["username"],
            email=validated_data["email"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
            password=validated_data["password"],
        )

        user.set_password(validated_data["password"])
        user.save()

        return user

    def get_is_subscribed(self, obj):
        current_user = self.context["request"].user

        # Если текущий пользователь является анонимным, вернуть False
        if isinstance(current_user, AnonymousUser):
            return False

        return Follow.objects.filter(user=current_user, author=obj).exists()


class UserMeSerializer(serializers.ModelSerializer):
    """Сериализатор для работы с эндпоинтом 'me'."""

    email = serializers.EmailField(
        required=True,
        max_length=254,
    )
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "password",
        )


class ChangePasswordSerializer(serializers.Serializer):
    model = User

    """
    Serializer for password change endpoint.
    """
    new_password = serializers.CharField(required=True)
    current_password = serializers.CharField(required=True)


class ConfirmationSerializer(serializers.Serializer):
    """Сериализатор кода подтверждения."""

    email = serializers.CharField(required=True)
    password = serializers.CharField(required=True)


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = "__all__"


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = "__all__"


class RecipeIngridientSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source="ingredient.id")
    name = serializers.ReadOnlyField(source="ingredient.name")
    measurement_unit = serializers.ReadOnlyField(
        source="ingredient.measurement_unit")

    class Meta:
        model = RecipeIngredient
        fields = (
            "id",
            "name",
            "measurement_unit",
            "amount",
        )


class RecipesSerializer(serializers.ModelSerializer):
    author = UserMeSerializer(many=False, required=True)
    tags = TagSerializer(many=True, required=True)
    ingredients = RecipeIngridientSerializer(many=True,
                                             source="recipeingredient_set")
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    image = Base64ImageField()

    class Meta:
        model = Recipes
        fields = "__all__"
        read_only_fields = (
            "id",
            "is_favorited",
            "is_in_shopping_cart",
        )

    def get_is_favorited(self, obj):
        user = self.context["request"].user
        return obj.is_favorite_for_user(user)

    def get_is_in_shopping_cart(self, obj):
        user = self.context["request"].user
        return obj.is_in_shopping_cart_for_user(user)

    def create(self, validated_data):
        tags_data = validated_data.pop("tags")
        ingredients_data = validated_data.pop("ingredients")

        recipe = Recipes.objects.create(**validated_data)

        recipe.tags.set(tags_data)
        recipe.ingredients.set(ingredients_data)

        return recipe


class BasketSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    recipe = serializers.CharField()
    image = serializers.SerializerMethodField()
    cooking_time = serializers.IntegerField()

    class Meta:
        model = Basket
        fields = (
            "id",
            "recipe",
            "image",
            "cooking_time",
        )

    def get_image(self, obj):
        return obj.recipe.image.url if obj.recipe.image else None


class FavoritesSerializer(serializers.ModelSerializer):
    recipes = serializers.SerializerMethodField()

    class Meta:
        model = Favorites
        fields = ("recipes",)

    def create(self, validated_data):
        recipe_id = self.context["view"].kwargs["recipe_id"]
        try:
            recipe = Recipes.objects.get(pk=recipe_id)
            favorites = Favorites.objects.create(
                user=self.context["request"].user,
                recipe=recipe,
            )
            return favorites
        except Recipes.DoesNotExist:
            raise serializers.ValidationError("Рецепт не найден")

    def get_recipes(self, favorites):
        author_recipes = favorites.recipe.author.recipes.all()
        context = self.context.copy()
        context["request"] = self.context["request"]
        return CustomRecipesSerializer(author_recipes, many=True,
                                       context=context).data


class CustomRecipesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipes
        fields = ("id", "image", "name", "cooking_time")


class FollowSerializer(serializers.ModelSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    author = UserMeSerializer(many=False, required=True)

    class Meta:
        model = Follow
        exclude = (
            "id",
            "user",
        )

    def get_recipes(self, follow):
        author_recipes = follow.author.recipes.all()
        context = self.context.copy()
        context["request"] = self.context["request"]
        return CustomRecipesSerializer(author_recipes, many=True,
                                       context=context).data

    def get_recipes_count(self, follow):
        return follow.author.recipes.count()

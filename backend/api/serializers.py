import base64

from django.contrib.auth.models import AnonymousUser
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404

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
    """Сериализатор для работы users"""
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
            "password",
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

        if isinstance(current_user, AnonymousUser):
            return False

        return obj.follower.filter(user=current_user).exists()


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

    def get_is_subscribed(self, obj):
        current_user = self.context["request"].user

        if isinstance(current_user, AnonymousUser):
            return False

        return obj.follower.filter(user=current_user).exists()

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['is_subscribed'] = self.get_is_subscribed(instance)
        rep['first_name'] = instance.first_name
        rep['last_name'] = instance.last_name
        return rep


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


MIN_AMOUNT: int = 1
MAX_AMOUNT: int = 32000


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source="ingredient.id")
    name = serializers.ReadOnlyField(source="ingredient.name")
    measurement_unit = serializers.ReadOnlyField(
        source="ingredient.measurement_unit")
    amount = serializers.DecimalField(
        max_digits=None,
        decimal_places=None,
        min_value=MIN_AMOUNT,
        max_value=MAX_AMOUNT)

    class Meta:
        model = RecipeIngredient
        fields = (
            "id",
            "name",
            "measurement_unit",
            "amount",
        )


MIN_AMOUNT: int = 1
MAX_AMOUNT: int = 32000


class RecipesSerializer(serializers.ModelSerializer):
    author = UserMeSerializer(many=False, required=False)
    tags = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(),
                                              many=True)
    ingredients = RecipeIngredientSerializer(many=True,
                                             source="recipe_ingredients")
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    cooking_time = serializers.DecimalField(
        max_digits=None,
        decimal_places=None,
        min_value=MIN_AMOUNT,
        max_value=MAX_AMOUNT)

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
        ingredients_data = validated_data.pop("recipe_ingredients")
        recipe = Recipes.objects.create(**validated_data)
        recipe.tags.set(tags_data)

        recipe_ingredients = []
        for ingredient_data in ingredients_data:
            ingredient_id = ingredient_data.get("id")
            amount = ingredient_data.get("amount")
            if ingredient_id and amount:
                recipe_ingredients.append(RecipeIngredient(
                    recipe=recipe,
                    ingredient_id=ingredient_id,
                    amount=amount,
                ))

        RecipeIngredient.objects.bulk_create(recipe_ingredients)

        return recipe

    def update(self, instance, validated_data):
        tags_data = validated_data.pop("tags")
        ingredients_data = validated_data.pop("recipe_ingredients")

        instance.name = validated_data.get("name", instance.name)
        instance.cooking_time = validated_data.get("cooking_time",
                                                   instance.cooking_time)
        instance.text = validated_data.get("text", instance.text)

        instance.tags.set(tags_data)
        instance.save()

        for ingredient_data in ingredients_data:
            ingredient_id = ingredient_data.get("id")
            amount = ingredient_data.get("amount")
            if ingredient_id and amount:
                try:
                    recipe_ingredient = RecipeIngredient.objects.get(
                        recipe=instance, ingredient_id=ingredient_id
                    )
                    recipe_ingredient.amount = amount
                    recipe_ingredient.save()
                except RecipeIngredient.DoesNotExist:
                    RecipeIngredient.objects.create(
                        recipe=instance, ingredient_id=ingredient_id,
                        amount=amount
                    )

        return instance

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        tags_data = []
        for tag in instance.tags.all():
            tag_data = {
                'id': tag.id,
                'name': tag.name,
                'color': tag.color,
                'slug': tag.slug,
            }
            tags_data.append(tag_data)
        rep['tags'] = tags_data
        return rep


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
        recipe = get_object_or_404(Recipes, pk=recipe_id)
        favorites = Favorites.objects.create(
            user=self.context["request"].user,
            recipe=recipe,)
        return favorites

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


class AuthorSerializer(serializers.ModelSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("id", "recipes", "recipes_count", "first_name", "last_name")

    def get_recipes(self, user):
        user_recipes = user.recipes.all()
        context = self.context.copy()
        context["request"] = self.context["request"]
        return CustomRecipesSerializer(user_recipes, many=True,
                                       context=context).data

    def get_recipes_count(self, user):
        return user.recipes.count()


class FollowSerializer(serializers.ModelSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    author = AuthorSerializer(many=False, read_only=True)

    class Meta:
        model = Follow
        fields = '__all__'

    def get_recipes(self, follow):
        user_recipes = follow.user.recipes.all()
        context = self.context.copy()
        context["request"] = self.context["request"]
        return CustomRecipesSerializer(user_recipes, many=True,
                                       context=context).data

    def get_recipes_count(self, follow):
        return follow.user.recipes.count()

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['id'] = instance.user.id

        author = instance.author
        user_recipes = author.recipes.all()
        context = self.context.copy()
        context["request"] = self.context["request"]
        rep['recipes'] = CustomRecipesSerializer(user_recipes, many=True,
                                                 context=context).data
        rep['recipes_count'] = author.recipes.count()

        rep['first_name'] = author.first_name
        rep['last_name'] = author.last_name

        return rep

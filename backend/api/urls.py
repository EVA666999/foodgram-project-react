from rest_framework import routers

from .views import (
    FavoritesViewSet,
    FollowViewSet,
    IngredientViewSet,
    RecipesViewSet,
    TagViewSet,
    UserViewSet,
    AddRecipeToShoppingCartViewSet
)

router = routers.DefaultRouter()

router.register(r"users", UserViewSet, basename="users")
router.register(r"tags", TagViewSet, basename="tags")
router.register(r"recipes", RecipesViewSet, basename="recipes")
router.register(r"ingredients", IngredientViewSet, basename="ingredients")
router.register(r"favorites", FavoritesViewSet, basename="favorites")
router.register(r"subscribe", FollowViewSet, basename="subscribe")
router.register(r"shopping_cart", AddRecipeToShoppingCartViewSet,
                basename="basket")

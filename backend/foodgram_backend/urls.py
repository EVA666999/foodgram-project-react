from api.urls import router
from api.views import (
    AddRecipeToShoppingCartViewSet,
    FavoritesViewSet,
    FollowViewSet,
    GetToken,
    TokenDeleteView,
    UserMeAPIView,
    download_shopping_list)

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("auth/", include("djoser.urls")),
    path("auth/", include("djoser.urls.jwt")),
    path("api/auth/token/login/", GetToken.as_view(), name="token"),
    path("api/auth/token/logout/", TokenDeleteView.as_view(),
         name="token-logout"),
    path(
        "api/recipes/<int:id>/shopping_cart/",
        AddRecipeToShoppingCartViewSet.as_view(
            {"post": "create", "delete": "destroy"}),
        name="add_to_shopping_cart",
    ),
    path(
        "api/recipes/download_shopping_cart/",
        download_shopping_list,
        name="download_shopping_cart",
    ),
    path(
        "api/recipes/<int:recipe_id>/favorite/",
        FavoritesViewSet.as_view({"post": "create", "delete": "destroy"}),
        name="favorite-recepi",
    ),
    path(
        "api/users/<int:user_id>/subscribe/",
        FollowViewSet.as_view({"post": "create", "delete": "destroy"}),
        name="subscribe",
    ),
    path('api/users/subscriptions/', FollowViewSet.as_view(
        {'get': 'list', 'delete': 'destroy'}), name='subscriptions'),
    path('subscriptions/<int:user_id>/', FollowViewSet.as_view(
        {'post': 'create', 'delete': 'destroy'}), name='subscription-detail'),
    path("api/users/me/", UserMeAPIView.as_view(), name="me"),
    path("api/", include(router.urls)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)

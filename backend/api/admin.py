from django.contrib import admin

from .models import (
    Basket,
    Favorites,
    Follow,
    Ingredient,
    RecipeIngredient,
    Recipes,
    Tag,
)


class FavoritesAdmin(admin.ModelAdmin):
    list_display = ("user", "recipe")
    list_filter = ("user",)
    search_fields = ("user__username", "recipe__name")


class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ("id", "recipe", "ingredient", "amount", "measurement_unit")
    list_filter = ("recipe", "ingredient")
    search_fields = ("recipe__name", "ingredient__name", "measurement_unit")


class RecipeIngtidientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1


class RecipesAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "author", "cooking_time")
    list_filter = ("author", "tags", "cooking_time")
    search_fields = ("name", "author__username")
    inlines = (RecipeIngtidientInline,)


class IngredientAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "measurement_unit")
    search_fields = ("name", "measurement_unit")


class TagAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "color", "slug")
    search_fields = ("name", "slug")


class FollowAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "author")
    list_filter = ("user", "author")
    search_fields = ("user__username", "author__username")


class BasketAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "recipe", "quantity", "cooking_time")
    list_filter = ("user", "recipe")
    search_fields = ("user__username", "recipe__name")


admin.site.register(RecipeIngredient, RecipeIngredientAdmin)
admin.site.register(Basket, BasketAdmin)
admin.site.register(Follow, FollowAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Favorites, FavoritesAdmin)
admin.site.register(Recipes, RecipesAdmin)

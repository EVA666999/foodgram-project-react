from django.db import models
from users.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


class Tag(models.Model):
    name = models.CharField(max_length=30)
    color = models.CharField(max_length=16)
    slug = models.SlugField(max_length=30, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Тег"
        verbose_name_plural = "Теги"
        ordering = ['name']


class Ingredient(models.Model):
    name = models.CharField(max_length=255)
    measurement_unit = models.CharField(max_length=200)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"
        ordering = ['name']


class Recipes(models.Model):
    author = models.ForeignKey(User, related_name="recipes",
                               on_delete=models.CASCADE)
    name = models.CharField(max_length=30)
    tags = models.ManyToManyField(Tag)
    image = models.ImageField(upload_to="api/media/", null=True, default=None)
    cooking_time = models.PositiveIntegerField()
    ingredients = models.ManyToManyField(
        Ingredient, through="RecipeIngredient", through_fields=("recipe",
                                                                "ingredient")
    )
    text = models.TextField()

    class Meta:
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"

    def __str__(self):
        return self.name

    def is_favorite_for_user(self, user):
        return Favorites.objects.filter(user=user, recipe=self).exists()

    def is_in_shopping_cart_for_user(self, user):
        return Basket.objects.filter(user=user, recipe=self).exists()


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipes, on_delete=models.CASCADE,
                               related_name='recipe_ingredients')
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    amount = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(32000)]
    )
    measurement_unit = models.CharField(max_length=200)

    def __str__(self):
        return f"{self.recipe.name} - {self.ingredient.name}"

    class Meta:
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"
        ordering = ['recipe__name', 'ingredient__name']


class Basket(models.Model):
    recipe = models.ForeignKey(Recipes,
                               on_delete=models.CASCADE,
                               related_name='baskets')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    cooking_time = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(32000)]
    )
    image = models.ImageField(upload_to="api/media/", null=True, default=None)
    ingredient = models.ForeignKey(
        Ingredient, on_delete=models.CASCADE, null=True, blank=True
    )

    def __str__(self):
        return f"{self.user.username}'Добавил(а) - {self.recipe.name}"

    class Meta:
        verbose_name = "Корзина"
        verbose_name_plural = "Корзина"
        ordering = ['user__username', 'recipe__name']


class Favorites(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name='favorite_user')
    recipe = models.ForeignKey(Recipes, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user.username} - Избранный рецепт: {self.recipe.name}"

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        unique_together = ("user", "recipe")


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="follower",
        verbose_name="Подписчик",
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="following",
        verbose_name="Подписан на ",
    )

    def __str__(self):
        return f"{self.user.username} - {self.author.username}"

    class Meta:
        unique_together = (("author", "user"),)
        constraints = [
            models.UniqueConstraint(
                fields=["user", "author"],
                name="unique_follow",
            )
        ]

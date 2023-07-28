# Generated by Django 4.2.3 on 2023-07-28 13:06

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0003_recipeingredient_measurement_unit"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="basket",
            options={
                "ordering": ["user__username", "recipe__name"],
                "verbose_name": "Рецепт",
                "verbose_name_plural": "Рецепты",
            },
        ),
        migrations.AlterModelOptions(
            name="favorites",
            options={
                "verbose_name": "Пользователь",
                "verbose_name_plural": "Пользователи",
            },
        ),
        migrations.AlterModelOptions(
            name="ingredient",
            options={
                "ordering": ["name"],
                "verbose_name": "Ингредиент",
                "verbose_name_plural": "Ингредиенты",
            },
        ),
        migrations.AlterModelOptions(
            name="recipeingredient",
            options={
                "ordering": ["recipe__name", "ingredient__name"],
                "verbose_name": "Рецепт",
                "verbose_name_plural": "Рецепты",
            },
        ),
        migrations.AlterModelOptions(
            name="recipes",
            options={
                "ordering": ["name"],
                "verbose_name": "Рецепт",
                "verbose_name_plural": "Рецепты",
            },
        ),
        migrations.AlterModelOptions(
            name="tag",
            options={
                "ordering": ["name"],
                "verbose_name": "Тег",
                "verbose_name_plural": "Теги",
            },
        ),
        migrations.AlterField(
            model_name="basket",
            name="cooking_time",
            field=models.PositiveSmallIntegerField(
                validators=[
                    django.core.validators.MinValueValidator(1),
                    django.core.validators.MaxValueValidator(32000),
                ]
            ),
        ),
        migrations.AlterField(
            model_name="recipeingredient",
            name="amount",
            field=models.PositiveSmallIntegerField(
                validators=[
                    django.core.validators.MinValueValidator(1),
                    django.core.validators.MaxValueValidator(32000),
                ]
            ),
        ),
    ]
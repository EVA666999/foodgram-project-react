# Generated by Django 4.2.3 on 2023-07-28 14:34

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0005_alter_basket_recipe"),
    ]

    operations = [
        migrations.AlterField(
            model_name="recipeingredient",
            name="recipe",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="recipeingredient",
                to="api.recipes",
            ),
        ),
    ]

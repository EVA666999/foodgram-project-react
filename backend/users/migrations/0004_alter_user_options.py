# Generated by Django 4.2.3 on 2023-07-28 17:09

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0003_user_is_subscribed"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="user",
            options={
                "verbose_name": "Пользователь",
                "verbose_name_plural": "Пользователи",
            },
        ),
    ]

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    is_active = models.BooleanField(default=True)
    is_subscribed = models.BooleanField(default=False)

    username = models.CharField(
        max_length=150,
        unique=True,
        blank=False,
        null=False,
        verbose_name="Пользователь",
        help_text="Имя пользователя",
    )
    password = models.CharField(
        max_length=128, blank=False, null=False, verbose_name="Пароль"
    )
    email = models.EmailField(
        max_length=255, unique=True, blank=False, null=False,
        verbose_name="Email"
    )
    first_name = models.CharField(
        max_length=30, blank=False, null=False, verbose_name="Имя"
    )
    last_name = models.CharField(
        max_length=150, blank=False, null=False, verbose_name="Фамилия"
    )

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return self.username

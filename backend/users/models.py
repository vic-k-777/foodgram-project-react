import re

from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import UniqueConstraint


class User(AbstractUser):
    """Создадим класс для Пользователей"""

    email = models.EmailField(
        verbose_name="email",
        max_length=254,
        unique=True,
        blank=False,
        null=False,
    )
    username = models.CharField(
        verbose_name="Логин",
        max_length=150,
        unique=True,
        validators=[
            RegexValidator(
                re.compile(r"^[\w.@+-]+\Z"),
                message=("Недопустимые символы в имени пользователя."),
            )
        ],
    )
    first_name = models.CharField(
        verbose_name="Имя",
        max_length=150,
    )
    last_name = models.CharField(
        verbose_name="Фамилия",
        max_length=150,
    )
    password = models.CharField(
        verbose_name="Пароль",
        max_length=150,
    )

    USERNAME_FIELD = "email"

    REQUIRED_FIELDS = [
        "username",
        "password",
        "first_name",
        "last_name",
    ]

    class Meta:
        ordering = ["-id"]
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        constraints = [
            models.UniqueConstraint(
                fields=["email", "username"], name="unique_auth"
            ),
        ]

    def __str__(self):
        return self.email


class Subscribe(models.Model):
    """Создадим класс для Подписчиков"""

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
        verbose_name="Автор",
    )

    class Meta:
        ordering = ["-id"]
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"
        constraints = [
            UniqueConstraint(fields=["user", "author"], name="unique_subscribe")
        ]

    def __str__(self):
        return f"{self.user} подписан на {self.author}"

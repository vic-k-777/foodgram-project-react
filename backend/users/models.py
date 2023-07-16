from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models
from foodgram import settings


class User(AbstractUser):
    """Создадим класс для Пользователей"""
    email = models.EmailField(
        verbose_name='email',
        max_length=settings.USER_EMAIL_MAX_LENGTH,
        unique=True,
        error_messages={
            'unique': 'Пользователь с таким e-mail уже существует.',
        }
    )
    username = models.CharField(
        verbose_name='Логин',
        max_length=settings.USER_USERNAME_MAX_LENGTH,
        unique=True,
        error_messages={
            'unique': 'Пользователь с таким username уже существует.',
        },
        validators=[
            RegexValidator(
                settings.REGEX_USER,
                message=('Недопустимые символы в имени пользователя.')
            )
        ]

    )
    first_name = models.CharField(
        verbose_name='Имя',
        max_length=settings.USER_FIRST_NAME_MAX_LENGTH,
    )
    last_name = models.CharField(
        verbose_name='Фамилия',
        max_length=settings.USER_LAST_NAME_MAX_LENGTH,
    )
    password = models.CharField(
        verbose_name='Пароль',
        max_length=settings.USER_PASSWORD_MAX_LENGTH,
    )

    USERNAME_FIELD = 'email'

    REQUIRED_FIELDS = [
        'username',
        'password',
        'first_name',
        'last_name',
    ]

    class Meta:
        ordering = ['-id']
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        constraints = [
            models.UniqueConstraint(
                fields=['email', 'username'],
                name='unique_auth'
            ),
        ]

    def __str__(self):
        return self.email


class Subscribe(models.Model):
    """Создадим класс для Подписчиков"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор'
    )

    class Meta:
        ordering = ['-id']
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

    def __str__(self):
        return f'{self.user} подписан на {self.author}'

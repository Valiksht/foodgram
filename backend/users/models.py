from django.db import models
from django.contrib.auth.models import AbstractUser

from .validators import username_validator
from backend.constants import EMAIL_LEN, NAME_LEN


class User(AbstractUser):
    """Модель пользователя."""

    email = models.EmailField(
        verbose_name='Электронная почта',
        max_length=EMAIL_LEN,
        unique=True,
        error_messages={
            'unique': "Пользователь с такой почтой уже существует."
        },
        help_text="Введите свою почту."
    )
    username = models.CharField(
        verbose_name='Ник',
        max_length=NAME_LEN,
        unique=True,
        validators=[username_validator],
        error_messages={
            'unique': "Пользователь с таким именем уже существует."
        },
        help_text="Введите уникальное имя пользователя."
    )
    password = models.CharField(max_length=254)
    first_name = models.CharField(
        verbose_name='Имя',
        max_length=NAME_LEN,
        blank=False,
        null=False
    )
    last_name = models.CharField(
        verbose_name='Фамилия',
        max_length=NAME_LEN,
        blank=False,
        null=False
    )
    avatar = models.ImageField(
        upload_to='user_images',
        null=True, blank=True,
        verbose_name='Аватарка'
    )
    is_admin = models.BooleanField(
        default=False, verbose_name='Админ'
    )
    follow = models.ManyToManyField(
        'self',
        through='Follow',
        symmetrical=False,
        related_name='followers'
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        ordering = ('username',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username

    def save(self, *args, **kwargs):
        if self.pk is None and not self.is_superuser:
            self.set_password(self.password)
        super().save(*args, **kwargs)


class Follow(models.Model):
    """Модель подписок."""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик'
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор')

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_follow'
            )
        ]

    def __str__(self):
        return f'{self.user} подписан на {self.author}'

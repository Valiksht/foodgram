from django.db import models
from django.contrib.auth import get_user_model

from .validators import tag_slug_validator
from backend.constants import MEASURENT_LEN, SLUG_LEN, RECIPE_NAME_LEN

User = get_user_model()


class Ingredient(models.Model):
    """Модель ингредиента."""

    name = models.CharField(max_length=128, verbose_name='Ингредиент')
    measurement_unit = models.CharField(
        max_length=MEASURENT_LEN,
        verbose_name='Единица измерения'
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_ingredient'
            )
        ]

    def __str__(self):
        return self.name


class Tag(models.Model):
    """Модель тегов."""

    name = models.CharField(max_length=32, verbose_name='Тег')
    slug = models.SlugField(
        max_length=SLUG_LEN,
        unique=True,
        validators=[tag_slug_validator],
        verbose_name='Слаг'
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """Модель рецептов."""

    name = models.CharField(
        max_length=RECIPE_NAME_LEN,
        verbose_name='Название рецепта'
    )
    text = models.TextField(verbose_name='Описание рецепта')
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name='Автор'
    )
    image = models.ImageField(
        upload_to='recipe_images',
        null=True,
        blank=True,
        verbose_name='Изображение'
    )
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name='Дата создания'
    )
    cooking_time = models.PositiveIntegerField(
        verbose_name='Время приготовления'
    )
    tags = models.ManyToManyField(
        Tag, verbose_name='Теги', related_name='recipes'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        verbose_name='Ингредиенты'
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    """Модель связи рецептов и ингредиентов."""

    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиенты'
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество ингредиента'
    )
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, verbose_name='Рецепты'
    )

    def __str__(self):
        return f'{self.ingredient} - {self.amount}'


class BaseShoppingFavorite(models.Model):
    """Базовая модель избранного и списка покупок."""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='%(class)s'
    )
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE,
        related_name='%(class)s'
    )

    class Meta:
        abstract = True
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_%(class)s'
            )
        ]

    def __str__(self):
        return f'{self.user} {self.recipe}'


class Favorite(BaseShoppingFavorite):
    """Модель избранного."""

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные'


class ShoppingCart(BaseShoppingFavorite):
    """Модель списка покупок."""

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'

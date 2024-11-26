import base64

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile

from .models import (
    Ingredient,
    Tag,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Favorite
)
from users.serializers import UserSerializer

User = get_user_model()


class Base64ImageField(serializers.ImageField):
    """Базовый сериализатор для загрузки изображений."""

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class BaseShopFavoriteSerializer(serializers.ModelSerializer):
    """Базовый сериализатор для добавления в список покупок и избранного."""

    recipe = serializers.PrimaryKeyRelatedField(
        queryset=Recipe.objects.all(), write_only=True
    )
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), write_only=True
    )
    id = serializers.IntegerField(source='recipe.id', read_only=True)
    name = serializers.CharField(source='recipe.name', read_only=True)
    image = serializers.ImageField(source='recipe.image', read_only=True)
    cooking_time = serializers.IntegerField(
        source='recipe.cooking_time', read_only=True
    )

    class Meta:
        fields = ['user', 'recipe', 'id', 'name', 'image', 'cooking_time']
        read_only_fields = ['id', 'name', 'image', 'cooking_time']


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов."""

    class Meta:
        model = Ingredient
        fields = ['id', 'name', 'measurement_unit']


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для тегов."""

    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug']


class AddIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для добавления ингредиентов в рецепт."""

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient'
    )
    amount = serializers.IntegerField()
    name = serializers.CharField(
        required=False,
        source='ingredient.name'
    )
    measurement_unit = serializers.CharField(
        required=False,
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ['id', 'name', 'measurement_unit', 'amount']
        read_only_fields = ['name', 'measurement_unit']


class RecipeReadSerializer(serializers.ModelSerializer):
    """Сериализатор для просмотра рецептов."""

    author = UserSerializer(read_only=True)

    ingredients = AddIngredientSerializer(
        many=True,
        read_only=True,
        source='recipeingredient_set'
    )
    tags = TagSerializer(many=True, read_only=True)
    image = Base64ImageField(required=False, allow_null=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = [
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time'
        ]

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return Favorite.objects.filter(
            user=request.user, recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return ShoppingCart.objects.filter(
            user=request.user, recipe=obj).exists()


class RecipeWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для создания и редактирования рецептов."""

    ingredients = AddIngredientSerializer(
        many=True, required=True, write_only=True)
    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all())
    image = Base64ImageField(required=True, allow_null=True)

    class Meta:
        model = Recipe
        fields = ['id', 'ingredients', 'tags', 'image',
                  'name', 'text', 'cooking_time', 'author']
        read_only_fields = ['author']

    def validate_ingredients(self, ingredients):
        ingredients_data = []
        if len(ingredients) == 0:
            raise serializers.ValidationError(
                'Нужно выбрать хотя бы один ингредиент!'
            )
        for ingredient in ingredients:
            amount = ingredient.get('amount')
            if amount <= 0:
                raise serializers.ValidationError(
                    'Количество ингредиента должно быть больше нуля!'
                )
            ingredient_id = ingredient.get('ingredient').id
            ingredients_data.append(ingredient_id)
        if len(ingredients_data) != len(set(ingredients_data)):
            raise serializers.ValidationError(
                'Ингредиенты не должны повторятся!'
            )
        return ingredients

    def validate_tags(self, tags):
        if len(tags) == 0:
            raise serializers.ValidationError(
                'Нужно выбрать хотя бы один тег!'
            )
        if len(tags) != len(set(tags)):
            raise serializers.ValidationError(
                'Теги не должны повторятся!'
            )
        return tags

    def validate_cooking_time(self, cooking_time):
        if cooking_time <= 0:
            raise serializers.ValidationError(
                'Время приготовления должно быть больше нуля!'
            )
        return cooking_time

    def add_ingredients_tags(self, recipe, ingredients, tags):
        for ingredient_data in ingredients:
            ingredient_id = ingredient_data.get('ingredient')
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient=ingredient_id,
                amount=ingredient_data.get('amount')
            )
        recipe.tags.set(tags)

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients', [])
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        self.add_ingredients_tags(recipe, ingredients, tags)
        return recipe

    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients', [])
        tags = validated_data.pop('tags', [])
        if len(ingredients) == 0 or len(tags) == 0:
            raise serializers.ValidationError(
                'Поля "ingredients" и "tags" не могут быть пустыми'
            )
        instance.image = validated_data.get('image', instance.image)
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get(
            'cooking_time', instance.cooking_time
        )
        instance.ingredients.clear()
        self.add_ingredients_tags(instance, ingredients, tags)
        return instance


class RecipeSmallSerializer(serializers.ModelSerializer):
    """Сериализатор для уменьшеного списка рецептов."""

    class Meta:
        model = Recipe
        fields = ['id', 'name', 'author', 'cooking_time']


class ShoppingCartSerializer(BaseShopFavoriteSerializer):
    """Сериализатор для списка покупок."""

    class Meta(BaseShopFavoriteSerializer.Meta):
        model = ShoppingCart
        fields = BaseShopFavoriteSerializer.Meta.fields


class FavoriteSerializer(BaseShopFavoriteSerializer):
    """Сериализатор для списка избранного."""

    class Meta(BaseShopFavoriteSerializer.Meta):
        model = Favorite
        fields = BaseShopFavoriteSerializer.Meta.fields

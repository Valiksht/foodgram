import re
import base64

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile

from backend.constants import MEUSERNAME
from .models import Follow
from api.models import Recipe


User = get_user_model()


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'password'
        ]

    def validate_username(self, value):
        if value is None:
            raise serializers.ValidationError(
                'Поле не может быть пустым'
            )
        elif value == MEUSERNAME:
            raise serializers.ValidationError('Недопустимое имя пользователя')
        elif not re.match(r'^[\w.@+-]+\Z', value):
            raise serializers.ValidationError('Недопустимые символы!')
        elif len(value) >= 150:
            raise serializers.ValidationError('Превышена максимальная длина!')
        elif User.objects.filter(username=value).exists():
            raise serializers.ValidationError('Данный username уже занят!')
        return value

    def validate_email(self, value):
        if value is None:
            raise serializers.ValidationError(
                'Поле не может быть пустым'
            )
        elif len(value) >= 254:
            raise serializers.ValidationError('Превышена максимальная длина!')
        elif User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Данный email уже занят!')
        return value

    def validate(self, attrs):
        email = attrs.get('email')
        username = attrs.get('username')
        user_email = User.objects.filter(email=email).first()
        user_username = User.objects.filter(username=username).first()
        if username is MEUSERNAME:
            raise serializers.ValidationError(
                f'Username "{username}" запрещен!'
            )
        elif user_email == user_username:
            return attrs
        else:
            raise serializers.ValidationError(
                f'Данный email: "{email}" или username "{username}" '
                f'занят другим пользователем!'
            )


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'is_subscribed',
            'first_name',
            'last_name',
            'avatar'
        ]
        read_only_fields = [
            'id',
            'username',
            'email',
            'is_subscribed',
            'first_name',
            'last_name',
            'avatar'
        ]

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return Follow.objects.filter(
            user=request.user, author=obj
        ).exists()


class SetPasswordSerializer(serializers.Serializer):
    # new_password = serializers.CharField(required=True)
    current_password = serializers.CharField(required=True)


class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = [
            'avatar'
        ]

    def validate(self, attrs):
        if 'avatar' not in attrs or attrs['avatar'] is None:
            raise serializers.ValidationError(
                {'avatar': 'Поле не может быть пустым'}
            )
        return attrs

    def to_representation(self, instance):

        representation = super().to_representation(instance)

        if instance.avatar:
            request = self.context.get('request')
            representation['avatar'] = request.build_absolute_uri(
                instance.avatar.url)
        else:
            representation['avatar'] = None

        return representation


class RecipeSmallSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ['id', 'name', 'image', 'cooking_time']

    def get_image(self, obj):
        request = self.context.get('request')
        return request.build_absolute_uri(obj.image.name)


class SubscribeSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='author.id')
    username = serializers.ReadOnlyField(source='author.username')
    first_name = serializers.ReadOnlyField(source='author.first_name')
    last_name = serializers.ReadOnlyField(source='author.last_name')
    email = serializers.ReadOnlyField(source='author.email')

    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    avatar = Base64ImageField(
        required=False, read_only=True, source='author.avatar')

    class Meta:
        model = Follow
        fields = [
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
            'avatar'
        ]
        read_only_fields = [
            all
        ]

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return Follow.objects.filter(
            user=request.user, author=obj.author
        ).exists()

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes = Recipe.objects.filter(author=obj.author)
        limit = request.query_params.get('recipes_limit')
        if limit:
            recipes = recipes[:int(limit)]
        return RecipeSmallSerializer(
            recipes, many=True,
            context={'request': self.context.get('request')}
        ).data

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj.author).count()


class TokenSerializer(serializers.ModelSerializer):
    username = serializers.CharField(max_length=150)
    token = serializers.CharField()

    class Meta:
        model = User
        fields = [
            'username',
            'token'
        ]

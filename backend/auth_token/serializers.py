from rest_framework import serializers
from django.contrib.auth import get_user_model


User = get_user_model()


class CastomTokenSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True)

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        return token

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        if email is None:
            raise serializers.ValidationError('Email не найден.')
        user = User.objects.filter(email=email).first()
        print(user.password)
        if user is None:
            raise serializers.ValidationError('Пользователь не найден')
        if not user.check_password(password):
            raise serializers.ValidationError('Некорректный пароль')
        attrs['user'] = user
        return super().validate(attrs)

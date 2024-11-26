from django.contrib.auth import get_user_model

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken

from .serializers import CastomTokenSerializer

User = get_user_model()


class CustomAuthToken(ObtainAuthToken):
    """ Вью сет, отправляющий токен."""
    serializer_class = CastomTokenSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        if user is not None:
            token, created = Token.objects.get_or_create(user=user)
            return Response(
                {'auth_token': token.key},
                status=status.HTTP_200_OK
            )
        return Response(
            {'error': 'Invalid credentials'},
            status=status.HTTP_401_UNAUTHORIZED
        )


class LogoutView(APIView):
    def post(self, request):
        request.user.auth_token.delete()
        return Response(
            {'message': 'Выход прошел успешно!'},
            status=status.HTTP_204_NO_CONTENT
        )

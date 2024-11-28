from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.decorators import action

from .models import Follow
from .serializers import (
    AvatarSerializer,
    UserCreateSerializer,
    UserSerializer,
    SubscribeSerializer
)
from api.paginations import LimitPagination


User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet пользователя"""

    queryset = User.objects.all().order_by('id')
    serializer_class = UserSerializer
    permission_classes = [AllowAny]
    pagination_class = LimitPagination

    def create(self, request, *args, **kwargs):
        serializer = UserCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                serializer.data, status=status.HTTP_201_CREATED
            )
        return Response(
            serializer.errors, status=status.HTTP_400_BAD_REQUEST
        )

    @action(
        methods=['post'],
        detail=False,
        url_path='set_password',
        permission_classes=[IsAuthenticated],
    )
    def set_password(self, request, *args, **kwargs):
        """Изменение пароля пользователя."""

        user = self.request.user
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')
        if (user.check_password(current_password)
                and new_password != current_password):
            user.set_password(new_password)
            user.save()
            return Response(
                {'detail': 'Пароль изменен!'},
                status=status.HTTP_204_NO_CONTENT
            )
        return Response(
            {'detail': 'Некорректный пароль!'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(
        methods=['post', 'delete'],
        detail=True,
        permission_classes=[IsAdminUser | IsAuthenticated],
    )
    def subscribe(self, request, *args, **kwargs):
        """Подписка на авторов."""

        author = get_object_or_404(User, pk=self.kwargs.get('pk'))
        user = self.request.user
        if user == author:
            return Response(
                'Нельзя подписаться на самого себя',
                status=status.HTTP_400_BAD_REQUEST
            )
        if request.method == 'POST':
            follow = Follow.objects.filter(user=user, author=author).first()
            if follow is None:
                serializer = SubscribeSerializer(
                    data=request.data,
                    context={'request': request, 'author': author}
                )
                serializer.is_valid(raise_exception=True)
                serializer.save(author=author, user=user)
                return Response(
                    serializer.data, status=status.HTTP_201_CREATED
                )
            else:
                return Response(
                    {'detail': 'Вы уже подписаны на этого пользователя!'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        if request.method == 'DELETE':
            follow = Follow.objects.filter(user=user, author=author)
            if follow.exists():
                follow.delete()
                return Response(
                    {'detail': 'Подписка успешно отменена.'},
                    status=status.HTTP_204_NO_CONTENT
                )
            else:
                return Response(
                    {'detail': 'Подписки не существует.'},
                    status=status.HTTP_400_BAD_REQUEST
                )


class SubscriptionsViewSet(viewsets.ModelViewSet):
    """ViewSet подписок"""

    permission_classes = [IsAuthenticated]
    serializer_class = SubscribeSerializer
    pagination_class = LimitPagination

    def get_queryset(self):
        return Follow.objects.filter(user=self.request.user)


class SelfUserViewSet(viewsets.ModelViewSet):
    """ViewSet собственной страницы пользователя"""

    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer
    pagination_class = None

    def get_object(self):
        return self.request.user

    def get_queryset(self):
        return User.objects.filter(pk=self.request.user.pk)

    @action(
        methods=['put', 'delete'],
        permission_classes=[IsAuthenticated],
        detail=False,
        url_path='avatar',
        url_name='avatar'
    )
    def avatar(self, request, *args, **kwargs):
        """Добавление, изменение или удаление аватара пользователя"""

        self.serializer_class = AvatarSerializer
        serializer = self.get_serializer(data=request.data)
        user = self.request.user
        if request.method == 'DELETE':
            user.avatar = None
            user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        if serializer.is_valid():
            user.avatar = serializer.validated_data['avatar']
            user.save()
            return Response(
                self.get_serializer(user).data,
                status=status.HTTP_200_OK
            )
        return Response(
            serializer.errors, status=status.HTTP_400_BAD_REQUEST
        )


# class SubscribeListView(APIView):
#     """ViewSet списка подписок"""

#     permission_classes = [IsAuthenticated]
#     pagination_class = LimitPagination

#     def get(self, request):
#         user = request.user
#         queryset = User.objects.filter(followers__user=user)
#         serializer = UserSerializer(queryset, many=True)
#         return Response(serializer.data)

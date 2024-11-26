from django.urls import include, path
from rest_framework import routers

from .views import UserViewSet, SelfUserViewSet, SubscriptionsViewSet

app_name = 'users'

router = routers.DefaultRouter()
router.register(r'me', SelfUserViewSet, basename='me')
router.register(r'subscriptions', SubscriptionsViewSet, basename='me')
router.register(r'', UserViewSet, basename='user')


urlpatterns = [
    path('', include(router.urls)),
]

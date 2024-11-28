from django.contrib import admin
from django.urls import include, path
from rest_framework import routers
from djoser.views import TokenCreateView, TokenDestroyView

from api.views import RecipeViewSet

router = routers.DefaultRouter()
router.register('s', RecipeViewSet, basename='shorl_link')

urlpatterns = [
    path('', include(router.urls)),
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('api/users/', include('users.urls')),
    path('api/auth/token/login/', TokenCreateView.as_view(), name='login'),
    path('api/auth/token/logout/', TokenDestroyView.as_view(), name='logout')
]

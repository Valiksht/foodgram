from django.contrib import admin
from django.urls import include, path
from rest_framework import routers

from api.views import RecipeViewSet

router = routers.DefaultRouter()
router.register('s', RecipeViewSet, basename='shorl_link')

urlpatterns = [
    path('', include(router.urls)),
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('api/users/', include('users.urls')),
    path('api/auth/', include('auth_token.urls'))
]

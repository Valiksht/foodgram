from django.urls import path

from .views import CustomAuthToken, LogoutView

app_name = 'auth_token'

urlpatterns = [
    path('token/login/', CustomAuthToken.as_view(), name='token'),
    path('token/logout/', LogoutView.as_view(), name='delete_token'),
]

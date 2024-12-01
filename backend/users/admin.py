from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Follow

class UserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name')
    search_fields = ('username', 'email')

class FollowAdmin(admin.ModelAdmin):
    list_display = ('user', 'author', 'get_follow_count')
    list_display_links = ('user', 'author')
    list_filter = ('user',)

    def get_follow_count(self, obj):
        return obj.user.follow.count()
    get_follow_count.short_description = 'Количество подписок'


admin.site.register(User, UserAdmin)
admin.site.register(Follow, FollowAdmin)

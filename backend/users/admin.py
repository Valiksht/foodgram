from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Follow


class FollowAdmin(admin.ModelAdmin):
    list_display = ('user', 'author')
    list_display_links = ('user', 'author')
    list_filter = ('user',)

    def get_recipe_count(self, obj):
        return obj.user.shoppingcart.count()
    get_recipe_count.short_description = 'Количество рецептов'


admin.site.register(User, UserAdmin)
admin.site.register(Follow, FollowAdmin)

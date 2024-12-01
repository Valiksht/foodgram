from import_export import resources
from import_export.admin import ImportExportModelAdmin
from django.contrib import admin

from .models import Ingredient, Tag, Recipe, ShoppingCart


class IngredientResource(resources.ModelResource):
    class Meta:
        model = Ingredient


class IngredientAdmin(ImportExportModelAdmin):
    resource_class = IngredientResource
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)


class TagResource(resources.ModelResource):
    class Meta:
        model = Tag


class TagAdmin(ImportExportModelAdmin):
    resource_class = TagResource
    list_display = ('name', 'slug')


class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author')
    list_display_links = ('name', 'author')
    search_fields = ('name', 'author')
    list_filter = ('tags',)


class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe', 'get_recipe_count')
    list_display_links = ('user', 'recipe')
    list_filter = ('user',)

    def get_recipe_count(self, obj):
        return obj.user.shoppingcart.count()
    get_recipe_count.short_description = 'Количество рецептов'


admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(ShoppingCart, ShoppingCartAdmin)

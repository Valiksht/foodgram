from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import (
    FilterSet,
    CharFilter,
    BooleanFilter,
    ModelMultipleChoiceFilter
)

from .models import Ingredient, Recipe, Tag


class LimitPagination(PageNumberPagination):
    page_size_query_param = 'limit'
    page_size = 6


class IngredientFilter(FilterSet):
    name = CharFilter(field_name='name', lookup_expr='startswith')

    class Meta:
        model = Ingredient
        fields = ['name']


class RecipeFilter(FilterSet):
    name = CharFilter(field_name='name', lookup_expr='startswith')
    tags = ModelMultipleChoiceFilter(
        queryset=Tag.objects.all(),
        field_name='tags__slug',
        to_field_name='slug',
        label='Тэги',
        help_text='Выберете один или несколько фильтров.'
    )
    author = CharFilter(
        field_name='author__pk',
        lookup_expr='startswith'
    )
    is_in_shopping_cart = BooleanFilter(
        field_name='is_in_shopping_cart', method='shopping_cart')
    is_favorited = BooleanFilter(
        field_name='is_favorited',
        method='favorited'
    )

    class Meta:
        model = Recipe
        fields = ['name', 'tags', 'author',
                  'is_in_shopping_cart', 'is_favorited']

    def shopping_cart(self, queryset, name, value):
        if value:
            if self.request.user.is_authenticated:
                return queryset.filter(
                    shoppingcart__user=self.request.user
                )
            return queryset.none()
        return queryset

    def favorited(self, queryset, name, value):
        if value:
            if self.request.user.is_authenticated:
                return queryset.filter(
                    favorite__user=self.request.user
                )
            return queryset.none()
        return queryset

import io
import os

from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.db.models import Prefetch, Sum
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action

from .permissions import AdminAuthorOrReadOnly
from .models import Recipe, Tag, Ingredient, ShoppingCart, Favorite
from .serializers import (
    RecipeWriteSerializer,
    RecipeReadSerializer,
    TagSerializer,
    IngredientSerializer,
    ShoppingCartSerializer,
    FavoriteSerializer
)
from .filters import IngredientFilter, RecipeFilter
from .paginations import LimitPagination
from backend.constants import X_CORD, Y_CORD, LINE_STEP

User = get_user_model()


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для работы с тегами."""

    serializer_class = TagSerializer
    queryset = Tag.objects.all()
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для работы с ингредиентами."""

    serializer_class = IngredientSerializer
    queryset = Ingredient.objects.all()
    pagination_class = None
    filter_backends = [DjangoFilterBackend]
    filterset_class = IngredientFilter


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет для работы с рецептами."""

    serializer_class = RecipeReadSerializer
    queryset = Recipe.objects.all().order_by('id')
    permission_classes = [AdminAuthorOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter
    pagination_class = LimitPagination

    def create(self, request, *args, **kwargs):
        input_serializer = RecipeWriteSerializer(data=request.data)
        if input_serializer.is_valid():
            resipe = input_serializer.save(author=request.user)
            output_serializer = RecipeReadSerializer(resipe)
            return Response(
                output_serializer.data,
                status=status.HTTP_201_CREATED
            )
        return Response(
            input_serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    def update(self, request, *args, **kwargs):
        recipe = self.get_object()
        input_serializer = RecipeWriteSerializer(
            recipe, data=request.data, partial=True)
        if input_serializer.is_valid():
            resipe = input_serializer.save()
            output_serializer = RecipeReadSerializer(resipe)
            return Response(
                output_serializer.data, status=status.HTTP_200_OK
            )
        return Response(
            input_serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    def save_shop_favorite_model(
        self, request, serializer_class, recipe, user, value, text_error
    ):
        """Метод для сохранения моделей ShoppingCart и Favorite."""

        if request.method == 'POST':
            if value.exists():
                return Response(
                    {'detail': text_error},
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer = serializer_class(
                data={'recipe': recipe.id, 'user': user.id},
                context={'request': request}
            )
            if serializer.is_valid():
                serializer.save()
                return Response(
                    serializer.data, status=status.HTTP_201_CREATED
                )
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        else:
            if value.exists():
                value.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(
        methods=['post', 'delete'],
        detail=True,
        url_path='favorite',
        permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, *args, **kwargs):
        """Добавление и удаление рецепта из избранного."""

        recipe = get_object_or_404(Recipe, id=kwargs['pk'])
        user = self.request.user
        favorite = Favorite.objects.filter(recipe=recipe, user=user)
        text_error = 'Рецепт уже добавлен в избранное.'
        return self.save_shop_favorite_model(
            request,
            FavoriteSerializer,
            recipe,
            user,
            favorite,
            text_error
        )

    @action(
        methods=['post', 'delete'],
        detail=True,
        url_path='shopping_cart',
        permission_classes=[IsAuthenticated]
    )
    def add_shopping_cart(self, request, *args, **kwargs):
        """Добавление и удаление рецепта из списка покупок."""

        recipe = get_object_or_404(Recipe, id=kwargs['pk'])
        user = self.request.user
        resipe_shopping = ShoppingCart.objects.filter(recipe=recipe, user=user)
        text_error = 'Рецепт уже добавлен в список покупок.'
        return self.save_shop_favorite_model(
            request,
            ShoppingCartSerializer,
            recipe,
            user,
            resipe_shopping,
            text_error
        )

    @action(
        methods=['get'],
        detail=False,
        url_path='download_shopping_cart'
    )
    def download_shopping_cart(self, request, *args, **kwargs):
        """Скачивание списка покупок."""

        user = self.request.user
        shopping_list = ShoppingCart.objects.filter(
            user=user
        ).prefetch_related(
            Prefetch(
                'recipe__ingredients',
                queryset=Ingredient.objects.annotate(
                    amount=Sum('recipeingredient__amount')
                )
            )
        )
        ingredients = {}
        for recipe in shopping_list:
            for item in recipe.recipe.ingredients.all():
                if item in ingredients:
                    ingredients[item.name]['amount'] += item.amount
                else:
                    ingredients[item.name] = {
                        'amount': item.amount,
                        'measurement_unit': item.measurement_unit
                    }
        buffer = io.BytesIO()
        x = X_CORD
        y = Y_CORD
        pdf_object = canvas.Canvas(buffer)
        header_font_file = os.path.abspath(os.path.join(
            '..', 'backend',
            'pdf_fonts', 'Verdana-Bold.ttf'
        ))
        pdfmetrics.registerFont(
            TTFont('Verdana-Bold', header_font_file)
        )
        font_file = os.path.abspath(os.path.join(
            '..', 'backend',
            'pdf_fonts', 'Verdana.ttf'
        ))
        pdfmetrics.registerFont(TTFont('Verdana', font_file))
        pdf_object.setFont('Verdana-Bold', 16)
        pdf_object.drawString(x, y, 'Список покупок:')
        pdf_object.setFont('Verdana', 12)
        for ingredient in ingredients:
            y -= LINE_STEP
            amount = ingredients[ingredient]['amount']
            measurement_unit = ingredients[ingredient]['measurement_unit']
            pdf_object.drawString(
                x, y, f'- {ingredient}: {amount},{measurement_unit}.')
        pdf_object.showPage()
        pdf_object.save()
        buffer.seek(0)
        return FileResponse(
            buffer, as_attachment=True, filename='shopping_cart.pdf'
        )

    @action(
        methods=['get'],
        detail=True,
        url_path='get-link'
    )
    def gen_short_link(self, request, *args, **kwargs):
        """Генерация короткой ссылки."""

        link = kwargs['pk']
        full_link = request.build_absolute_uri()
        base_link = '/'.join(full_link.split('/')[:3]) + '/'
        return Response({'short-link': f'{base_link}s/{link}/'})

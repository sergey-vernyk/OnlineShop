from django.db.models import Q
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, filters, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from common.moduls_init import redis
from goods.models import Product, Category, Property, Manufacturer
from . import serializers
from .product_filters import ProductFilter
from ..utils import get_products_sorted_by_views


class ProductSet(viewsets.ModelViewSet):
    """
    Model view, which allows to obtain all products, or products, that belongs to particular category,
    also allows performs filter products, search products, ordering products, create, delete, update product
    """
    queryset = Product.available_objects.all()
    serializer_class = serializers.ProductSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_class = ProductFilter
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    ordering = ['name']
    ordering_fields = ['price', 'promotional_price']
    search_fields = ['name', 'id']

    def get_queryset(self):
        queryset = Product.available_objects.select_related('category', 'manufacturer')
        slug = self.request.query_params.get('slug')
        if slug is not None:
            queryset = queryset.filter(category__slug=slug)

        return queryset

    @action(detail=False, methods=['GET', 'HEAD'], name='Get new products',
            url_path='new_products(?:/(?P<category_slug>[a-zA-Z-]+))?')
    def get_new_products(self, request, category_slug=None):
        """
        Action allows displaying new products with particular category or all new products
        """
        now = timezone.now()
        diff = now - timezone.timedelta(weeks=2)  # calculate the difference
        lookup = Q(created__gt=diff, category__slug=category_slug) if category_slug else Q(created__gt=diff)

        products = Product.available_objects.filter(lookup)

        # if page contains results - returns only products on this page, otherwise returns all products
        page = self.paginate_queryset(products)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(products, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['GET', 'HEAD'], name='Get promotional products',
            url_path='promo_products(?:/(?P<category_slug>[a-zA-Z-]+))?')
    def get_promotional_products(self, request, category_slug=None):
        """
        Action allows displaying promotional products with particular category or all promotional products
        """
        lookup = Q(category__slug=category_slug, promotional=True) if category_slug else Q(promotional=True)
        products = Product.available_objects.filter(lookup)

        # if page contains results - returns only products on this page, otherwise returns all products
        page = self.paginate_queryset(products)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(products, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['GET', 'HEAD'], name='Get popular products',
            url_path='popular_products(?:/(?P<category_slug>[a-zA-Z-]+))?')
    def get_popular_products(self, request, category_slug=None):
        """
        Action allows to display products in descending order of their views
        for a certain category or all products in that order
        """

        products_ids = [int(pk) for pk in redis.smembers('products_ids')]  # ids of all products
        products_ids_sorted, products = get_products_sorted_by_views(products_ids)

        if category_slug:  # products filter by category
            product_list = [
                products[pk] for pk in products_ids_sorted
                if category_slug == products[pk].category.slug
            ]
        else:
            product_list = [products[pk] for pk in products_ids_sorted]

        redis.hset('popular_prods', 'ids', ','.join(str(prod.pk) for prod in product_list))

        # if page contains results - returns only products on this page, otherwise returns all products
        page = self.paginate_queryset(product_list)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(product_list, many=True)
        return Response(serializer.data)


class ProductCategorySet(viewsets.ModelViewSet):
    """
    Model view, which allows to obtain all products categories and also create, updated or delete category
    """
    queryset = Category.objects.all()
    serializer_class = serializers.ProductsCategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class PropertySet(viewsets.ModelViewSet):
    """
    Model view, which allows to obtain all products properties and also create, updated or delete property
    """
    queryset = Property.objects.select_related('category_property', 'product').order_by('product__name')
    serializer_class = serializers.ProductPropertySerializer

    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['product__name']
    filterset_fields = ['text_value', 'numeric_value', 'name', 'category_property__name']
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class ManufacturerSet(viewsets.ModelViewSet):
    """
    Model view, which allows to obtain all products manufacturers and also create, updated or delete manufacturer
    """
    serializer_class = serializers.ManufacturersSerializer
    queryset = Manufacturer.objects.all()
    filter_backends = [filters.SearchFilter]
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    search_fields = ['name']

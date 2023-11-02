from django.db.models import Q
from django.utils import timezone
from django.utils.decorators import method_decorator
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg.openapi import Parameter
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from common.moduls_init import redis
from goods.models import Product, Category, Property, Manufacturer
from . import serializers
from .persmissions import ObjectEditPermission
from .product_filters import ProductFilter
from ..utils import get_products_sorted_by_views


@method_decorator(name='list', decorator=swagger_auto_schema(operation_summary='Get all products',
                                                             manual_parameters=[Parameter(name='category_slug',
                                                                                          in_='query',
                                                                                          type='string',
                                                                                          required=False)]))
@method_decorator(name='retrieve', decorator=swagger_auto_schema(operation_summary='Get product with {id}'))
@method_decorator(name='create', decorator=swagger_auto_schema(operation_summary='Create product'))
@method_decorator(name='partial_update',
                  decorator=swagger_auto_schema(operation_summary='Update one or several product\'s fied(s) with {id}'))
@method_decorator(name='update', decorator=swagger_auto_schema(operation_summary='Full update product with {id}'))
@method_decorator(name='destroy', decorator=swagger_auto_schema(operation_summary='Delete product with {id}'))
class ProductViewSet(viewsets.ModelViewSet):
    """
    Viewset that provides `retrieve`, `create`, `delete`, `list` and `update` product.

    * get - obtain all products.
    * post - create new product.
    * get/{id} - retrieve product with `id`.
    * patch/{id} - update one or several fields of product with `id`.
    * put/{id} - update all fields of product with id.
    * delete/{id} - delete product with `id`.
    """
    queryset = Product.available_objects.all()
    serializer_class = serializers.ProductSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_class = ProductFilter
    permission_classes = [ObjectEditPermission]
    ordering = ['name']
    ordering_fields = ['price', 'promotional_price']
    search_fields = ['name', 'id']
    remove_fields_list_for_get_request = ['comments', 'slug', 'available',
                                          'created', 'updated', 'image', 'properties']

    def get_queryset(self):
        queryset = Product.available_objects.prefetch_related('category', 'manufacturer', 'comments')
        slug = self.request.query_params.get('category_slug')
        if slug is not None:
            queryset = queryset.filter(category__slug=slug)

        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page:
            serializer = self.get_serializer(instance=page, many=True)
            serializer.child.remove_fields(self.remove_fields_list_for_get_request)  # remove fields from response
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(instance=queryset, many=True)
        serializer.child.remove_fields(self.remove_fields_list_for_get_request)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(operation_summary='Get only new products',
                         manual_parameters=[Parameter(name='category_name',
                                                      in_='query',
                                                      type='string',
                                                      required=False,
                                                      description='Category name')])
    @action(detail=False,
            methods=['GET'],
            name='Get new products',
            url_path='new_products')
    def get_new_products(self, request, version: str = 'v1'):
        """
        Get new products with particular category or get all new products.
        """
        category_name = request.query_params.get('category_name')
        now = timezone.now()
        diff = now - timezone.timedelta(weeks=2)  # calculate the difference
        lookup = Q(created__gt=diff, category__name=category_name.title()) if category_name else Q(created__gt=diff)

        products = Product.available_objects.filter(lookup)

        # if page contains results - returns only products on this page, otherwise returns all products
        page = self.paginate_queryset(products)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            serializer.child.remove_fields(self.remove_fields_list_for_get_request)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(products, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(operation_summary='Get only promotional products',
                         manual_parameters=[Parameter(name='category_name',
                                                      in_='query',
                                                      type='string',
                                                      required=False,
                                                      description='Category name')])
    @action(detail=False,
            methods=['GET'],
            name='Get promotional products',
            url_path='promo_products')
    def get_promotional_products(self, request, version: str = 'v1'):
        """
        Get promotional products with particular category or get all promotional products.
        """
        category_name = request.query_params.get('category_name')
        lookup = Q(category__name=category_name.title(), promotional=True) if category_name else Q(promotional=True)
        products = Product.available_objects.prefetch_related('comments').filter(lookup)

        # if page contains results - returns only products on this page, otherwise returns all products
        page = self.paginate_queryset(products)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            serializer.child.remove_fields(self.remove_fields_list_for_get_request)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(products, many=True)
        serializer.child.remove_fields(self.remove_fields_list_for_get_request)
        return Response(serializer.data)

    @swagger_auto_schema(operation_summary='Get only popular products (means by their views)',
                         manual_parameters=[Parameter(name='category_name',
                                                      in_='query',
                                                      type='string',
                                                      required=False,
                                                      description='Category name')])
    @action(detail=False,
            methods=['GET'],
            name='Get popular products',
            url_path='popular_products')
    def get_popular_products(self, request, version: str = 'v1'):
        """
        Get popular products in descending order either by a certain category or get all popular products.
        """

        products_ids = [int(pk) for pk in redis.smembers('products_ids')]  # ids of all products
        products_ids_sorted, products = get_products_sorted_by_views(products_ids)

        category_name = request.query_params.get('category_name')

        if category_name:  # products filter by category
            product_list = [
                products[pk] for pk in products_ids_sorted
                if category_name.lower() == products[pk].category.name.lower()
            ]
        else:
            product_list = [products[pk] for pk in products_ids_sorted]

        redis.hset('popular_prods', 'ids', ','.join(str(prod.pk) for prod in product_list))

        # if page contains results - returns only products on this page, otherwise returns all products
        page = self.paginate_queryset(product_list)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            serializer.child.remove_fields(self.remove_fields_list_for_get_request)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(product_list, many=True)
        serializer.child.remove_fields(self.remove_fields_list_for_get_request)
        return Response(serializer.data)


@method_decorator(name='list', decorator=swagger_auto_schema(operation_summary='Get all categories'))
@method_decorator(name='retrieve', decorator=swagger_auto_schema(operation_summary='Get category with {id}'))
@method_decorator(name='create', decorator=swagger_auto_schema(operation_summary='Create category'))
@method_decorator(name='update', decorator=swagger_auto_schema(operation_summary='Full update category with {id}'))
@method_decorator(name='destroy', decorator=swagger_auto_schema(operation_summary='Delete category with {id}'))
class ProductCategoryViewSet(viewsets.ModelViewSet):
    """
    Viewset that provides `retrieve`, `create`, `delete`, `list` and `update` category.

    * get - obtain all categories.
    * post - create new category.
    * get/{id} - retrieve category with `id`.
    * put/{id} - update all fields of category with id.
    * delete/{id} - delete category with `id`.
    """
    queryset = Category.objects.all()
    serializer_class = serializers.ProductCategorySerializer
    permission_classes = [ObjectEditPermission]
    http_method_names = ['get', 'head', 'post', 'put', 'delete']


@method_decorator(name='list', decorator=swagger_auto_schema(operation_summary='Get all properties',
                                                             manual_parameters=[
                                                                 Parameter(name='translations__text_value',
                                                                           type='string',
                                                                           required=False,
                                                                           in_='query',
                                                                           description='Text value'),
                                                                 Parameter(name='numeric_value',
                                                                           type='string',
                                                                           required=False,
                                                                           in_='query',
                                                                           description='Numeric value'),
                                                                 Parameter(name='category_property__translations__name',
                                                                           type='string',
                                                                           required=False,
                                                                           in_='query',
                                                                           description='Name of category property')
                                                             ]))
@method_decorator(name='retrieve', decorator=swagger_auto_schema(operation_summary='Get property with {id}'))
@method_decorator(name='create', decorator=swagger_auto_schema(operation_summary='Create property'))
@method_decorator(name='partial_update', decorator=swagger_auto_schema(
    operation_summary='Update one or several property\'s field(s) with {id}'))
@method_decorator(name='destroy', decorator=swagger_auto_schema(operation_summary='Delete property with {id}'))
class PropertyViewSet(viewsets.ModelViewSet):
    """
     Viewset that provides `retrieve`, `create`, `delete`, `list` and `update` property.

    * get - obtain all properties.
    * post - create new property.
    * get/{id} - retrieve property with `id`.
    * patch/{id} - update one or several fields of property with `id`.
    * delete/{id} - delete property with `id`.
    """
    queryset = Property.objects.select_related('category_property', 'product').order_by('product__name')
    serializer_class = serializers.ProductPropertySerializer
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['product__name']
    filterset_fields = ['translations__text_value', 'numeric_value',
                        'translations__name', 'category_property__translations__name']
    permission_classes = [IsAdminUser]
    http_method_names = ['get', 'head', 'post', 'patch', 'delete']


@method_decorator(name='list', decorator=swagger_auto_schema(operation_summary='Get all manufacturers'))
@method_decorator(name='retrieve', decorator=swagger_auto_schema(operation_summary='Get manufacturer with {id}'))
@method_decorator(name='create', decorator=swagger_auto_schema(operation_summary='Create manufacturer'))
@method_decorator(name='update', decorator=swagger_auto_schema(operation_summary='Full update manufacturer with {id}'))
@method_decorator(name='destroy', decorator=swagger_auto_schema(operation_summary='Delete manufacturer with {id}'))
class ManufacturerViewSet(viewsets.ModelViewSet):
    """
    Viewset that provides `retrieve`, `create`, `delete`, `list` and `update` manufacturer.

    * get - obtain all manufacturers.
    * post - create new manufacturer.
    * get/{id} - retrieve manufacturer with `id`.
    * put/{id} - update all fields of manufacturer with id.
    * delete/{id} - delete manufacturer with `id`.
    """
    serializer_class = serializers.ManufacturerSerializer
    queryset = Manufacturer.objects.all()
    filter_backends = [filters.SearchFilter]
    permission_classes = [ObjectEditPermission]
    search_fields = ['name']
    http_method_names = ['get', 'head', 'post', 'put', 'delete']

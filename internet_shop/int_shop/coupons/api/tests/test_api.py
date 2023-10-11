import os
import shutil
from decimal import Decimal
from random import randint

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.reverse import reverse
from rest_framework.test import APIClient, APITestCase, APIRequestFactory

from account.models import Profile
from cart.cart import Cart
from coupons.models import Category as CouponCategory, Coupon
from goods.models import Manufacturer, Product, Category
from ..serializers import CouponSerializer, CouponCategorySerializer
from ..views import CouponViewSet


class TestCouponsAPI(APITestCase):
    """
    Testing API for coupons application
    """

    def setUp(self):
        random_number = randint(1, 50)
        self.user = User.objects.create_user(username='admin_user',
                                             password='password',
                                             first_name='Admin',
                                             last_name='User',
                                             email='admin@example.com')

        self.token = Token.objects.get(user__username=self.user.username)

        self.user.set_password('password')
        self.profile = Profile.objects.create(user=self.user)

        category_coupon = CouponCategory.objects.create(name=f'coupon_category_{random_number + 2}',
                                                        slug=f'coupon-category-{random_number + 2}')

        self.coupon = Coupon.objects.create(code=f'coupon_code_{random_number + 5}',
                                            valid_from=timezone.now(),
                                            valid_to=timezone.now() + timezone.timedelta(days=10),
                                            discount=20,
                                            category=category_coupon)

        category = Category.objects.create(name=f'Category_{random_number}',
                                           slug=f'category-{random_number}')

        manufacturer = Manufacturer.objects.create(name=f'Manufacturer_{random_number}',
                                                   slug=f'manufacturer_{random_number}',
                                                   description='Description')

        self.product = Product.objects.create(name=f'Product_{random_number}',
                                              slug=f'product_{random_number}',
                                              manufacturer=manufacturer,
                                              price=Decimal('300.25'),
                                              description='Description',
                                              category=category)

        self.client = APIClient()

    def test_get_all_coupons_only_for_staff_users(self):
        """
        Checking get all coupons. To the list of coupons have access only staff users.
        """
        # user is not staff and authorized
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.get(reverse('coupons_api:coupon-list', kwargs={'version': 'v1'}))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # user is staff
        self.user.is_staff = True
        self.user.save()
        response = self.client.get(reverse('coupons_api:coupon-list', kwargs={'version': 'v1'}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        serializer = CouponSerializer(instance=self.coupon)
        view = response.renderer_context['view']
        actual_result = response.data['results'][0] if settings.REST_FRAMEWORK.get(
            'DEFAULT_PAGINATION_CLASS') or hasattr(view, 'pagination_class') else response.data
        expected_result = serializer.data
        self.assertDictEqual(actual_result, expected_result)

    def test_create_coupon_by_only_staff_users(self):
        """
        Checking create coupon, which can create only by staff users
        """

        coupon_data = {
            'code': 'super_code',
            'valid_from': timezone.now(),
            'valid_to': timezone.now() + timezone.timedelta(days=10),
            'discount': 10,
            'category': self.coupon.category.pk
        }

        # user is not staff and authorized
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.post(reverse('coupons_api:coupon-list', kwargs={'version': 'v1'}),
                                    data=coupon_data,
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # user is staff
        self.user.is_staff = True
        self.user.save()
        response = self.client.post(reverse('coupons_api:coupon-list', kwargs={'version': 'v1'}),
                                    data=coupon_data,
                                    format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created_coupon = Coupon.objects.filter(code=coupon_data['code']).exists()
        self.assertTrue(created_coupon)

        for field, value in Coupon.objects.get(code=coupon_data['code']).__dict__.items():
            if field in coupon_data:
                self.assertEqual(value, coupon_data[field])

    def test_retrieve_coupon_only_by_staff_users(self):
        """
        Checking retrieve coupon by its id only by staff users
        """
        # user is not staff and authorized
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.get(reverse('coupons_api:coupon-detail',
                                           kwargs={'pk': self.coupon.pk, 'version': 'v1'}),
                                   format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # user is staff
        self.user.is_staff = True
        self.user.save()
        response = self.client.get(reverse('coupons_api:coupon-detail',
                                           kwargs={'pk': self.coupon.pk, 'version': 'v1'}),
                                   format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        serializer = CouponSerializer(instance=self.coupon)
        self.assertDictEqual(response.data, serializer.data)

    def test_partial_update_coupon_only_by_staff_users(self):
        """
        Checking update part of info of a coupon only by staff users
        """
        coupon_data = {
            'valid_to': timezone.now() + timezone.timedelta(days=8),
            'discount': 12,
        }

        # user is not staff and authorized
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.patch(reverse('coupons_api:coupon-detail',
                                             kwargs={'pk': self.coupon.pk, 'version': 'v1'}),
                                     data=coupon_data,
                                     format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # user is staff
        self.user.is_staff = True
        self.user.save()
        response = self.client.patch(reverse('coupons_api:coupon-detail',
                                             kwargs={'pk': self.coupon.pk, 'version': 'v1'}),
                                     data=coupon_data,
                                     format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.coupon.refresh_from_db()
        self.assertEqual(self.coupon.discount, coupon_data['discount'])
        self.assertEqual(self.coupon.valid_to, coupon_data['valid_to'])

    def test_full_update_coupon_only_by_staff_users(self):
        """
        Checking full update coupon info only by staff users
        """
        coupon_data = {
            'valid_to': timezone.now() + timezone.timedelta(days=8),
            'discount': 15,
            'category': self.coupon.category.pk,
            'valid_from': timezone.now(),
            'code': self.coupon.code
        }

        # user is not staff and authorized
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.put(reverse('coupons_api:coupon-detail',
                                           kwargs={'pk': self.coupon.pk, 'version': 'v1'}),
                                   data=coupon_data,
                                   format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # user is staff
        self.user.is_staff = True
        self.user.save()
        response = self.client.put(reverse('coupons_api:coupon-detail',
                                           kwargs={'pk': self.coupon.pk, 'version': 'v1'}),
                                   data=coupon_data,
                                   format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.coupon.refresh_from_db()
        for field, value in self.coupon.__dict__.items():
            if field in coupon_data:
                self.assertEqual(value, coupon_data[field])

    def test_delete_coupon_only_by_staff_users(self):
        """
        Checking delete coupon by its id only by staff users
        """
        # user is not staff and authorized
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.delete(reverse('coupons_api:coupon-detail',
                                              kwargs={'pk': self.coupon.pk, 'version': 'v1'}))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # user is staff
        self.user.is_staff = True
        self.user.save()
        response = self.client.delete(reverse('coupons_api:coupon-detail',
                                              kwargs={'pk': self.coupon.pk, 'version': 'v1'}))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        with self.assertRaises(ObjectDoesNotExist):
            self.coupon.refresh_from_db()

    def test_apply_or_cancel_coupon(self):
        """
        Checking apply or cancel coupon to cart, pass coupon code.
        Do this actions can only if user is authenticated
        """
        # when cart is empty
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.post(reverse('coupons_api:coupon-apply_cancel_coupon',
                                            kwargs={'act': 'apply', 'code': self.coupon.code, 'version': 'v1'}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {'detail': 'Cart is empty'})

        # when cart is not empty
        request = APIRequestFactory().post(reverse('coupons_api:coupon-apply_cancel_coupon',
                                                   kwargs={'act': 'apply', 'code': self.coupon.code, 'version': 'v1'}))
        request.session = self.client.session
        request.user = self.user
        cart = Cart(request)
        cart.add(self.product)

        view_instance = CouponViewSet()
        # apply coupon
        response = view_instance.apply_or_cancel_coupon(request, 'apply', self.coupon.code)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data,
                         {'success': f"Coupon with code '{self.coupon.code}' has been successfully applied"})
        self.assertEqual(request.session['coupon_id'], self.coupon.pk)
        # cancel coupon
        response = view_instance.apply_or_cancel_coupon(request, 'cancel', self.coupon.code)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data,
                         {'success': f"Coupon with code '{self.coupon.code}' has been successfully canceled"})
        self.assertIsNone(request.session.get('coupon_id'))

        # when coupon is invalid
        response = self.client.post(reverse('coupons_api:coupon-apply_cancel_coupon',
                                            kwargs={'act': 'apply', 'code': 'invalid_code', 'version': 'v1'}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, {'error': f"Coupon with code 'invalid_code' is not found"})

    def test_get_all_coupons_categories_only_for_staff_users(self):
        """
        Checking get all coupons categories.
        To the list of coupons categories have access only staff users.
        """
        # user is not staff and authorized
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.get(reverse('coupons_api:category-list', kwargs={'version': 'v1'}))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # user is staff
        self.user.is_staff = True
        self.user.save()
        response = self.client.get(reverse('coupons_api:category-list', kwargs={'version': 'v1'}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        serializer = CouponCategorySerializer(instance=self.coupon.category)
        actual_result = response.data['results'][0] if settings.REST_FRAMEWORK.get(
            'DEFAULT_PAGINATION_CLASS') or hasattr(serializer, 'pagination_class') else response.data
        expected_result = serializer.data
        self.assertDictEqual(actual_result, expected_result)

    def test_create_coupon_category_by_only_staff_users(self):
        """
        Checking create coupon category, which can create only by staff users
        """

        category_data = {
            'name': 'new_coupon_category',
            'slug': 'new-coupon-category',
        }

        # user is not staff and authorized
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.post(reverse('coupons_api:coupon-list', kwargs={'version': 'v1'}),
                                    data=category_data,
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # user is staff
        self.user.is_staff = True
        self.user.save()
        response = self.client.post(reverse('coupons_api:category-list', kwargs={'version': 'v1'}),
                                    data=category_data,
                                    format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created_category = CouponCategory.objects.filter(name=category_data['name']).exists()
        self.assertTrue(created_category)

        for field, value in CouponCategory.objects.get(name=category_data['name']).__dict__.items():
            if field in category_data:
                self.assertEqual(value, category_data[field])

    def test_retrieve_coupon_category_only_by_staff_users(self):
        """
        Checking retrieve coupon category by its id only by staff users
        """
        # user is not staff and authorized
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.get(reverse('coupons_api:category-detail',
                                           kwargs={'pk': self.coupon.category.pk, 'version': 'v1'}),
                                   format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # user is staff
        self.user.is_staff = True
        self.user.save()
        response = self.client.get(reverse('coupons_api:category-detail',
                                           kwargs={'pk': self.coupon.category.pk, 'version': 'v1'}),
                                   format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        serializer = CouponCategorySerializer(instance=self.coupon.category)
        self.assertDictEqual(response.data, serializer.data)

    def test_partial_update_coupon_category_only_by_staff_users(self):
        """
        Checking update part of info of a coupon category only by staff users
        """
        category_data = {
            'name': 'New Category Name'
        }

        # user is not staff and authorized
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.patch(reverse('coupons_api:category-detail',
                                             kwargs={'pk': self.coupon.category.pk, 'version': 'v1'}),
                                     data=category_data,
                                     format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # user is staff
        self.user.is_staff = True
        self.user.save()
        response = self.client.patch(reverse('coupons_api:category-detail',
                                             kwargs={'pk': self.coupon.category.pk, 'version': 'v1'}),
                                     data=category_data,
                                     format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.coupon.category.refresh_from_db()
        self.assertEqual(self.coupon.category.name, category_data['name'])

    def test_full_update_coupon_category_only_by_staff_users(self):
        """
        Checking full update coupon category info only by staff users
        """
        category_data = {
            'name': 'Such a new name',
            'slug': self.product.category.slug
        }

        # user is not staff and authorized
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.put(reverse('coupons_api:category-detail',
                                           kwargs={'pk': self.coupon.category.pk, 'version': 'v1'}),
                                   data=category_data,
                                   format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # user is staff
        self.user.is_staff = True
        self.user.save()
        response = self.client.put(reverse('coupons_api:category-detail',
                                           kwargs={'pk': self.coupon.category.pk, 'version': 'v1'}),
                                   data=category_data,
                                   format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.coupon.category.refresh_from_db()
        for field, value in self.coupon.category.__dict__.items():
            if field in category_data:
                self.assertEqual(value, category_data[field])

    def test_delete_coupon_category_only_by_staff_users(self):
        """
        Checking delete coupon category by its id only by staff users
        """
        # user is not staff and authorized
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.delete(reverse('coupons_api:category-detail',
                                              kwargs={'pk': self.coupon.category.pk, 'version': 'v1'}))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # user is staff
        self.user.is_staff = True
        self.user.save()
        response = self.client.delete(reverse('coupons_api:category-detail',
                                              kwargs={'pk': self.coupon.category.pk, 'version': 'v1'}))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        with self.assertRaises(ObjectDoesNotExist):
            self.coupon.category.refresh_from_db()

    def tearDown(self):
        shutil.rmtree(os.path.join(settings.MEDIA_ROOT, f'products/product_{self.product.name}'))

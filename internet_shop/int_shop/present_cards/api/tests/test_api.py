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
from present_cards.models import Category as PresentCardCategory, PresentCard
from goods.models import Manufacturer, Product, Category
from ..serializers import PresentCardSerializer, PresentCardCategorySerializer
from ..views import PresentCardViewSet


class TestPresentCardAPI(APITestCase):
    """
    Testing API for present card application
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

        category_card = PresentCardCategory.objects.create(name=f'card_category_{random_number + 2}',
                                                           slug=f'card-category-{random_number + 2}')

        self.card = PresentCard.objects.create(code=f'card_code_{random_number + 5}',
                                               valid_from=timezone.now(),
                                               valid_to=timezone.now() + timezone.timedelta(days=10),
                                               from_email='some_email@mail.org',
                                               from_name='Adam Smith',
                                               amount=150,
                                               category=category_card)

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

    def test_get_all_present_cards_only_for_staff_users(self):
        """
        Checking get all coupons. To the list of present cards have access only staff users.
        """
        # user is not staff and authorized
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.get(reverse('present_cards_api:present_card-list', kwargs={'version': 'v1'}))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # user is staff
        self.user.is_staff = True
        self.user.save()
        response = self.client.get(reverse('present_cards_api:present_card-list', kwargs={'version': 'v1'}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        serializer = PresentCardSerializer(instance=self.card)
        view = response.renderer_context['view']
        serializer.remove_fields(view.remove_fields_list_for_get_request)
        actual_result = response.data['results'][0] if settings.REST_FRAMEWORK.get(
            'DEFAULT_PAGINATION_CLASS') or hasattr(view, 'pagination_class') else response.data
        expected_result = serializer.data
        self.assertDictEqual(actual_result, expected_result)

    def test_create_present_card_by_only_staff_users(self):
        """
        Checking create present card, which can create only by staff users
        """

        card_data = {
            'code': 'super_code',
            'valid_from': timezone.now(),
            'valid_to': timezone.now() + timezone.timedelta(days=10),
            'from_name': 'John Doe',
            'from_email': 'john_doe@example.com',
            'to_name': 'Admin User',
            'to_email': self.user.email,
            'amount': 250,
            'category': self.card.category.pk
        }

        # user is not staff and authorized
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.post(reverse('present_cards_api:present_card-list', kwargs={'version': 'v1'}),
                                    data=card_data,
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # user is staff
        self.user.is_staff = True
        self.user.save()
        response = self.client.post(reverse('present_cards_api:present_card-list', kwargs={'version': 'v1'}),
                                    data=card_data,
                                    format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created_card = PresentCard.objects.filter(code=card_data['code']).exists()
        self.assertTrue(created_card)

        for field, value in PresentCard.objects.get(code=card_data['code']).__dict__.items():
            if field in card_data:
                self.assertEqual(value, card_data[field])

    def test_retrieve_present_card_only_by_staff_users(self):
        """
        Checking retrieve present card by its id only by staff users
        """
        # user is not staff and authorized
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.get(reverse('present_cards_api:present_card-detail',
                                           kwargs={'pk': self.card.pk, 'version': 'v1'}),
                                   format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # user is staff
        self.user.is_staff = True
        self.user.save()
        response = self.client.get(reverse('present_cards_api:present_card-detail',
                                           kwargs={'pk': self.card.pk, 'version': 'v1'}),
                                   format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        serializer = PresentCardSerializer(instance=self.card)
        self.assertDictEqual(response.data, serializer.data)

    def test_partial_update_present_card_only_by_staff_users(self):
        """
        Checking update part of info of a present card only by staff users
        """
        card_data = {
            'valid_to': timezone.now() + timezone.timedelta(days=8),
            'amount': 300,
            'from_email': 'adam_smith@mail.org'
        }

        # user is not staff and authorized
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.patch(reverse('present_cards_api:present_card-detail',
                                             kwargs={'pk': self.card.pk, 'version': 'v1'}),
                                     data=card_data,
                                     format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # user is staff
        self.user.is_staff = True
        self.user.save()
        response = self.client.patch(reverse('present_cards_api:present_card-detail',
                                             kwargs={'pk': self.card.pk, 'version': 'v1'}),
                                     data=card_data,
                                     format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.card.refresh_from_db()
        self.assertEqual(self.card.amount, card_data['amount'])
        self.assertEqual(self.card.valid_to, card_data['valid_to'])
        self.assertEqual(self.card.from_email, card_data['from_email'])

    def test_full_update_present_card_only_by_staff_users(self):
        """
        Checking full update present card info only by staff users
        """
        card_data = {
            'valid_to': timezone.now() + timezone.timedelta(days=8),
            'valid_from': timezone.now(),
            'amount': 200,
            'category': self.card.category.pk,
            'code': self.card.code,
            'from_email': 'some_email@example.org',
            'from_name': 'Adam Smith',
            'to_name': 'Admin User',
            'to_email': self.user.email
        }

        # user is not staff and authorized
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.put(reverse('present_cards_api:present_card-detail',
                                           kwargs={'pk': self.card.pk, 'version': 'v1'}),
                                   data=card_data,
                                   format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # user is staff
        self.user.is_staff = True
        self.user.save()
        response = self.client.put(reverse('present_cards_api:present_card-detail',
                                           kwargs={'pk': self.card.pk, 'version': 'v1'}),
                                   data=card_data,
                                   format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.card.refresh_from_db()
        for field, value in self.card.__dict__.items():
            if field in card_data:
                self.assertEqual(value, card_data[field])

    def test_delete_present_card_only_by_staff_users(self):
        """
        Checking delete present card by its id only by staff users
        """
        # user is not staff and authorized
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.delete(reverse('present_cards_api:present_card-detail',
                                              kwargs={'pk': self.card.pk, 'version': 'v1'}))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # user is staff
        self.user.is_staff = True
        self.user.save()
        response = self.client.delete(reverse('present_cards_api:present_card-detail',
                                              kwargs={'pk': self.card.pk, 'version': 'v1'}))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        with self.assertRaises(ObjectDoesNotExist):
            self.card.refresh_from_db()

    def test_apply_or_cancel_present_card(self):
        """
        Checking apply or cancel present card, pass present card code.
        Do this actions can only if user is authenticated
        """
        # when cart is empty
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.post(reverse('present_cards_api:present_card-apply_or_cancel_present_card',
                                            kwargs={'act': 'apply', 'code': self.card.code, 'version': 'v1'}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {'detail': 'Cart is empty'})

        # when cart is not empty
        request = APIRequestFactory().post(reverse('present_cards_api:present_card-apply_or_cancel_present_card',
                                                   kwargs={'act': 'apply', 'code': self.card.code, 'version': 'v1'}))
        request.session = self.client.session
        request.user = self.user
        cart = Cart(request)
        cart.add(self.product)

        view_instance = PresentCardViewSet()
        # apply present card
        response = view_instance.apply_or_cancel_present_card(request, 'apply', self.card.code)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data,
                         {'success': f"Present card with code '{self.card.code}' has been successfully applied"})
        self.assertEqual(request.session['present_card_id'], self.card.pk)
        # cancel present card
        response = view_instance.apply_or_cancel_present_card(request, 'cancel', self.card.code)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data,
                         {'success': f"Present card with code '{self.card.code}' has been successfully canceled"})
        self.assertIsNone(request.session.get('present_card_id'))

        # when present card is invalid
        response = self.client.post(reverse('present_cards_api:present_card-apply_or_cancel_present_card',
                                            kwargs={'act': 'apply', 'code': 'invalid_code', 'version': 'v1'}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, {'error': "Present card with code 'invalid_code' was not found"})

    def test_get_all_present_cards_categories_only_for_staff_users(self):
        """
        Checking get all present cards categories.
        To the list of present cards categories have access only staff users.
        """
        # user is not staff and authorized
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.get(reverse('present_cards_api:category-list', kwargs={'version': 'v1'}))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # user is staff
        self.user.is_staff = True
        self.user.save()
        response = self.client.get(reverse('present_cards_api:category-list', kwargs={'version': 'v1'}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        serializer = PresentCardCategorySerializer()
        view = response.renderer_context['view']
        serializer.remove_fields(view.remove_fields_list_for_get_request)
        serializer = PresentCardCategorySerializer(instance=self.card.category)
        serializer.remove_fields(view.remove_fields_list_for_get_request)
        actual_result = response.data['results'][0] if settings.REST_FRAMEWORK.get(
            'DEFAULT_PAGINATION_CLASS') or hasattr(view, 'pagination_class') else response.data
        expected_result = serializer.data
        self.assertDictEqual(actual_result, expected_result)

    def test_create_present_card_category_by_only_staff_users(self):
        """
        Checking create present card category, which can create only by staff users.
        """

        category_data = {
            'translations': {
                'en': {
                    'name': 'new_card_category',
                    'slug': 'new-card-category',
                },
                'uk': {
                    'name': 'нова-категорія',
                    'slug': 'nova-categoria',
                }
            }
        }

        # user is not staff and authorized
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.post(reverse('present_cards_api:category-list', kwargs={'version': 'v1'}),
                                    data=category_data,
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # user is staff
        self.user.is_staff = True
        self.user.save()
        response = self.client.post(reverse('present_cards_api:category-list', kwargs={'version': 'v1'}),
                                    data=category_data,
                                    format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created_category = PresentCardCategory.objects.all()[1]
        self.assertTrue(created_category)

        for field, value in created_category.__dict__.items():
            if field in category_data:
                self.assertEqual(value, category_data[field])

    def test_retrieve_present_card_category_only_by_staff_users(self):
        """
        Checking retrieve present card category by its id only by staff users
        """
        # user is not staff and authorized
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.get(reverse('present_cards_api:category-detail',
                                           kwargs={'pk': self.card.category.pk, 'version': 'v1'}),
                                   format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # user is staff
        self.user.is_staff = True
        self.user.save()
        response = self.client.get(reverse('present_cards_api:category-detail',
                                           kwargs={'pk': self.card.category.pk, 'version': 'v1'}),
                                   format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        serializer = PresentCardCategorySerializer(instance=self.card.category)
        self.assertDictEqual(response.data, serializer.data)

    def test_full_update_present_card_category_only_by_staff_users(self):
        """
        Checking full update present card category info only by staff users.
        """
        category_data = {
            'translations': {
                'en': {
                    'name': 'Such a new name',
                    'slug': self.card.category.slug
                },
                'uk': {
                    'name': "Нове ім'я",
                    'slug': 'nove-imia'
                }
            }

        }

        # user is not staff and authorized
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.put(reverse('present_cards_api:category-detail',
                                           kwargs={'pk': self.card.category.pk, 'version': 'v1'}),
                                   data=category_data,
                                   format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # user is staff
        self.user.is_staff = True
        self.user.save()
        response = self.client.put(reverse('present_cards_api:category-detail',
                                           kwargs={'pk': self.card.category.pk, 'version': 'v1'}),
                                   data=category_data,
                                   format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.card.category.refresh_from_db()
        for field, value in self.card.category.__dict__.items():
            if field in category_data:
                self.assertEqual(value, category_data[field])

    def test_delete_present_card_category_only_by_staff_users(self):
        """
        Checking delete present card category by its id only by staff users
        """
        # user is not staff and authorized
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.delete(reverse('present_cards_api:category-detail',
                                              kwargs={'pk': self.card.category.pk, 'version': 'v1'}))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # user is staff
        self.user.is_staff = True
        self.user.save()
        response = self.client.delete(reverse('present_cards_api:category-detail',
                                              kwargs={'pk': self.card.category.pk, 'version': 'v1'}))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        with self.assertRaises(ObjectDoesNotExist):
            self.card.category.refresh_from_db()

    def tearDown(self):
        shutil.rmtree(os.path.join(settings.MEDIA_ROOT, f'products/product_{self.product.name}'))

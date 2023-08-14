import json
from random import randint

from django.contrib.auth.models import User
from django.http.response import JsonResponse
from django.test import TestCase, Client
from django.shortcuts import reverse
from django.utils import timezone

from account.models import Profile
from present_cards.models import PresentCard, Category


class TestPresentCardsViews(TestCase):
    """
    Testing present card views
    """

    user = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        random_number = randint(1, 50)
        cls.user = User.objects.create_user(username='testuser', password='password')
        cls.user.set_password('password')
        cls.profile = Profile.objects.create(user=cls.user)
        category_card = Category.objects.create(name=f'card_category_{random_number + 2}',
                                                slug=f'card-category-{random_number + 2}')

        cls.card = PresentCard.objects.create(code=f'card_code_{random_number + 5}',
                                              valid_from=timezone.now(),
                                              valid_to=timezone.now() + timezone.timedelta(days=10),
                                              amount=200,
                                              category=category_card)

    def test_apply_present_card_success(self):
        """
        Checking successfully applying present card and adding it to profile
        """
        client = Client()
        client.login(username=self.user.username, password='password')

        self.card.valid_to = timezone.now() + timezone.timedelta(days=10)  # make coupon as valid
        self.card.save()

        self.response = client.post(reverse('present_cards:apply_present_card'),
                                    {'code': self.card.code},
                                    **{'HTTP_X-REQUESTED-WITH': 'XMLHttpRequest'})
        self.assertIsInstance(self.response, JsonResponse)
        content_response = json.loads(self.response.content)  # convert Json to python dict

        self.assertIn('card_amount', content_response)
        self.assertEqual(content_response['card_amount'], self.card.amount)

        session = self.response.wsgi_request.session  # get session from request, got from response
        # check whether present card id is in session
        self.assertIn(('present_card_id', self.card.pk), session.items())
        # check whether present card is in profile present cards
        self.assertIn(self.card, self.profile.profile_cards.all())

    def test_apply_present_card_fail(self):
        """
        Checking applying present card, when present card is invalid
        """
        self.card.valid_to = timezone.now() - timezone.timedelta(days=5)  # make present card as invalid
        self.card.save()

        client = Client()
        client.login(username=self.user.username, password='password')

        self.response = client.post(reverse('present_cards:apply_present_card'),
                                    {'code': self.card.code},
                                    **{'HTTP_X-REQUESTED-WITH': 'XMLHttpRequest'})
        self.assertIsInstance(self.response, JsonResponse)
        content_response = json.loads(self.response.content)  # convert Json to python dict
        self.assertIn('form_errors', content_response)

        session = self.response.wsgi_request.session
        self.assertIsNone(session['present_card_id'])

    def test_cancel_present_card(self):
        """
        Checking successfully cancel present card applying
        """
        client = Client()
        client.login(username=self.user.username, password='password')
        session = client.session
        session.update({'present_card_id': self.card.pk})
        session.save()

        self.profile.profile_cards.add(self.card)  # add present card to profile
        client.login(username=self.user.username, password='password')

        self.response = client.post(reverse('present_cards:cancel_present_card'),
                                    {'code': self.card.code},
                                    **{'HTTP_X-REQUESTED-WITH': 'XMLHttpRequest'})

        self.assertIsInstance(self.response, JsonResponse)
        response_content = json.loads(self.response.content)

        self.assertIn('card_amount', response_content)
        self.assertEqual(response_content['card_amount'], self.card.amount)
        self.assertNotIn(self.card, self.profile.profile_cards.all())
        self.assertNotIn('present_card_id', self.response.wsgi_request.session)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

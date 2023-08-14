import json
from random import randint

from django.contrib.auth.models import User
from django.shortcuts import reverse
from django.test import TestCase, RequestFactory
from django.utils import timezone

from account.models import Profile
from present_cards.forms import PresentCardApplyForm
from present_cards.models import PresentCard, Category


class TestPresentCardForms(TestCase):
    """
    Testing forms in present_cards application
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

        cls.factory = RequestFactory()

    def test_receiving_error_when_present_card_invalid(self):
        """
        Checking appear error, when present card is invalid
        """
        self.card.valid_to = timezone.now() - timezone.timedelta(days=5)  # make present card invalid
        self.card.save()

        request = self.factory.post(reverse('present_cards:apply_present_card'), {'code': self.card.code})

        self.instance = PresentCardApplyForm(data=request.POST)
        self.instance.is_valid()

        self.assertTrue(self.instance.has_error('code'))  # must be an error
        error_info = self.instance.errors.as_json()
        self.assertEqual(json.loads(error_info)['code'][0]['message'], 'Invalid card code')  # error message

    def test_receiving_present_car_code_when_it_valid(self):
        """
        Checking returning present card code, when present card is valid.
        There are no errors have to be
        """
        self.card.valid_to = timezone.now() + timezone.timedelta(days=10)  # make present card valid
        self.card.save()

        request = self.factory.post(reverse('present_cards:apply_present_card'), {'code': self.card.code})

        self.instance = PresentCardApplyForm(data=request.POST)
        self.instance.is_valid()

        self.assertFalse(self.instance.has_error('code'))  # must not be error

    def test_receiving_error_when_present_card_was_already_used(self):
        """
        Checking appear error, when received present card code was already used
        """
        self.card.valid_to = timezone.now() + timezone.timedelta(days=10)  # make present card valid
        self.card.save()

        # simulate, that the present card already exists in another profile
        another_user = User.objects.create_user(username='user2', password='password')
        another_profile = Profile.objects.create(user=another_user)
        another_profile.profile_cards.add(self.card)

        request = self.factory.post(reverse('present_cards:apply_present_card'), {'code': self.card.code})
        self.instance = PresentCardApplyForm(data=request.POST)
        self.instance.is_valid()

        self.assertTrue(self.instance.has_error('code'))  # must be an error
        error_info = self.instance.errors.as_json()
        self.assertEqual(json.loads(error_info)['code'][0]['message'], 'The code was already used')

        self.card.profile = None  # necessary for other tests

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

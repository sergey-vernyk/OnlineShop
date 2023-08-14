from django.test import TestCase
from django.utils import timezone

from present_cards.models import PresentCard, Category
from random import randint


class TestPresentCardModels(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        random_number = randint(1, 50)
        category_card = Category.objects.create(name=f'card_category_{random_number + 2}',
                                                slug=f'card-category-{random_number + 2}')

        cls.card = PresentCard.objects.create(code=f'card_code_{random_number + 5}',
                                              valid_from=timezone.now(),
                                              valid_to=timezone.now() + timezone.timedelta(days=10),
                                              amount=200,
                                              category=category_card)

    def test_present_card_is_valid_property_if_coupon_valid(self):
        """
        Checking whether present card is valid
        """
        self.card.valid_to = timezone.now() + timezone.timedelta(days=10)  # make present card valid
        self.card.save()
        self.assertTrue(self.card.is_valid)

    def test_present_card_is_valid_property_if_coupon_invalid(self):
        """
        Checking whether present card is invalid
        """
        self.card.valid_to = timezone.now() - timezone.timedelta(days=5)  # make present card invalid
        self.card.save()
        self.assertFalse(self.card.is_valid)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

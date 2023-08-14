from random import randint

from django.contrib.admin.sites import AdminSite
from django.test import TestCase
from django.utils import timezone

from present_cards.admin import PresentCardAdmin
from present_cards.models import PresentCard, Category


class TestAdminPresentCards(TestCase):
    """
    Testing methods in admin site
    """

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

        cls.site = AdminSite()

    def test_correct_displaying_present_card_validity(self):
        """
        Checking displaying validity present card in present cards list
        """
        self.instance = PresentCardAdmin(model=PresentCard, admin_site=self.site)
        self.assertEqual(self.instance.is_valid(self.card), 'Valid')

        self.card.valid_to = timezone.now() - timezone.timedelta(days=5)  # make present card as invalid
        self.card.save()

        self.assertEqual(self.instance.is_valid(self.card), 'Invalid')

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

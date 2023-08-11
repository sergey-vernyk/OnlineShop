import os
import shutil
from decimal import Decimal
from random import randint

from django.conf import settings
from django.contrib.admin import AdminSite
from django.contrib.auth.models import User
from django.test import TestCase

from account.admin import CommentInline, ProfileAdmin
from account.models import Profile, get_profile_photo_path
from goods.models import Comment, Product, Category, Manufacturer


class TestAdminAccount(TestCase):
    """
    Testing methods in admin panel
    """

    def setUp(self) -> None:
        random_number = randint(1, 50)
        self.user = User.objects.create_user(username='testuser', first_name='Name', last_name='Surname')
        self.profile = Profile.objects.create(user=self.user)

        # save path profile's photo and assign this path as photo field attribute
        path = get_profile_photo_path(self.profile, 'profile_picture.jpg')
        self.profile.photo = path

        manufacturer = Manufacturer.objects.create(name=f'Manufacturer_{random_number}',
                                                   slug=f'manufacturer-{random_number}')

        category = Category.objects.create(name=f'Some_category_{random_number}',
                                           slug=f'some-category-{random_number}')

        self.product = Product.objects.create(name=f'product_{random_number}',
                                              slug=f'product-{random_number}',
                                              manufacturer_id=manufacturer.pk,
                                              description='Description',
                                              price=Decimal('120.50'),
                                              category_id=category.pk)

        self.comment_1 = Comment.objects.create(product=self.product,
                                                profile=self.profile,
                                                body='Body of comment_1')

        self.comment_2 = Comment.objects.create(product=self.product,
                                                profile=self.profile,
                                                body='Body of comment_2')
        self.site = AdminSite()

    def test_get_amount_profile_likes_for_comment(self):
        """
        Сhecking correct likes count under comments
        """
        self.profile.comments_liked.add(self.comment_1)  # make comment liked by profile
        instance = CommentInline(parent_model=Comment, admin_site=self.site)
        self.assertEqual(instance.get_amount_profile_likes(self.comment_1), 1)
        self.assertEqual(self.comment_1, self.profile.comments_liked.first())

    def test_get_amount_profile_unlikes_for_comment(self):
        """
        Checking correct dislikes count under comments
        """
        self.profile.comments_unliked.add(self.comment_2)  # make comment disliked by profile
        instance = CommentInline(parent_model=Comment, admin_site=self.site)
        self.assertEqual(instance.get_amount_profile_unlikes(self.comment_2), 1)
        self.assertEqual(self.comment_2, self.profile.comments_unliked.first())

    def test_profile_full_name_for_profile_admin(self):
        """
        Checking correct displaying full name of profile in change profile information menu
        """
        instance = ProfileAdmin(model=Profile, admin_site=self.site)
        self.assertEqual(instance.profile_full_name(self.profile),
                         f'{self.profile.user.first_name} {self.profile.user.last_name}')

    def test_profile_photo_tag_for_profile_admin(self):
        """
        Checking correct making profile's photo link in change profile infiormation menu
        """
        instance = ProfileAdmin(model=Profile, admin_site=self.site)
        link = f'<img src="{self.profile.photo.url}" width="100" height="100"/>'
        self.assertEqual(instance.profile_photo_tag(self.profile), link)

    def tearDown(self) -> None:
        if self.product:
            shutil.rmtree(os.path.join(settings.MEDIA_ROOT, f'products/product_{self.product.name}'))

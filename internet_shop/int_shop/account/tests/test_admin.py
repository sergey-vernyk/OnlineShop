from django.test import TestCase
from django.contrib.admin import AdminSite
from goods.models import Comment, Product, Category, Manufacturer
from account.models import Profile, get_profile_photo_path
from django.contrib.auth.models import User
from decimal import Decimal
from account.admin import CommentInline, ProfileAdmin


class TestAdminAccount(TestCase):
    """
    Тестирование функций админ панели приложения account
    """

    def setUp(self) -> None:
        self.user = User.objects.create_user(username='testuser', first_name='Name', last_name='Surname')
        self.profile = Profile.objects.create(user=self.user)

        # путь сохранения фото профиля и назначение этого пути атрибуту полю photo
        path = get_profile_photo_path(self.profile, 'profile_picture.jpg')
        self.profile.photo = path

        manufacturer = Manufacturer.objects.create(name='Manufacturer_1', slug='manufacturer-1')
        category = Category.objects.create(name='Some_category', slug='some-category')

        self.product = Product.objects.create(name='Some_product',
                                              slug='some-product',
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
        Проверка правильного кол-ва лайков под комментарием
        """
        self.profile.comments_liked.add(self.comment_1)  # добавление к профилю понравившегося комментария
        instance = CommentInline(parent_model=Comment, admin_site=self.site)
        self.assertEqual(instance.get_amount_profile_likes(self.comment_1), 1)
        self.assertEqual(self.comment_1, self.profile.comments_liked.first())

    def test_get_amount_profile_unlikes_for_comment(self):
        """
        Проверка правильного кол-ва дизлайков под комментарием
        """
        self.profile.comments_unliked.add(self.comment_2)  # добавление к профилю не понравившегося комментария
        instance = CommentInline(parent_model=Comment, admin_site=self.site)
        self.assertEqual(instance.get_amount_profile_unlikes(self.comment_2), 1)
        self.assertEqual(self.comment_2, self.profile.comments_unliked.first())

    def test_profile_full_name_for_profile_admin(self):
        """
        Проверка правильного отображения полного имени пользователя профиля
        в меню изменения информации о профиле
        """
        instance = ProfileAdmin(model=Profile, admin_site=self.site)
        self.assertEqual(instance.profile_full_name(self.profile),
                         f'{self.profile.user.first_name} {self.profile.user.last_name}')

    def test_profile_photo_tag_for_profile_admin(self):
        """
        Проверка правильности формирования ссылки на фото профиля
        в меню изменения информации о профиле
        """
        instance = ProfileAdmin(model=Profile, admin_site=self.site)
        link = f'<img src="{self.profile.photo.url}" width="100" height="100"/>'
        self.assertEqual(instance.profile_photo_tag(self.profile), link)

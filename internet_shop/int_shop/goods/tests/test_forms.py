from unittest.mock import patch

import redis
from django.conf import settings
from django.test import TestCase

from goods.forms import CommentProductForm


class TestGoodsForms(TestCase):
    """
    Testing forms in goods application
    """

    def setUp(self) -> None:
        redis_instance = redis.StrictRedis(host=settings.REDIS_HOST,
                                           port=settings.REDIS_PORT,
                                           db=settings.REDIS_DB_NUM,
                                           charset='utf-8',
                                           decode_responses=True,
                                           socket_timeout=30)

        redis_patcher = patch('common.moduls_init.redis', redis_instance)
        self.redis = redis_patcher.start()

    def test_comment_product_form_if_all_fields_filled_correctly(self):
        """
        Testing the form through which the user can submit a comment, when all fields filled correctly
        """
        captcha_text = 'AAA111'
        self.redis.hset(f'captcha:{captcha_text}', 'captcha_text', captcha_text)

        form_data = {
            'user_name': 'Test',
            'user_email': 'example@example.com',
            'body': 'Text of comment',
            'captcha': 'AAA111',
        }

        self.comment_form_instance = CommentProductForm(data=form_data)
        self.assertTrue(self.comment_form_instance.is_valid())

    def test_comment_product_form_if_all_fields_empty(self):
        """
        Testing the form through which the user can submit a comment, when all fields are empty
        """
        form_data = {
            'user_name': '',
            'user_email': '',
            'body': '',
            'captcha': '',
        }

        self.comment_form_instance = CommentProductForm(data=form_data)
        self.assertFalse(self.comment_form_instance.is_valid())
        self.assertFormError(self.comment_form_instance, 'user_name', ['This field must not be empty'])
        self.assertFormError(self.comment_form_instance, 'user_email', ['This field must not be empty'])
        self.assertFormError(self.comment_form_instance, 'body', ['This field must not be empty'])
        self.assertFormError(self.comment_form_instance, 'captcha', ['This field must not be empty'])

    def tearDown(self) -> None:
        self.redis.hdel('captcha:AAA111', 'captcha_text')

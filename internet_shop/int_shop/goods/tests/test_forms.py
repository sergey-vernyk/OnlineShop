from django.test import TestCase
from goods.forms import CommentProductForm


class TestGoodsForms(TestCase):
    """
    Testing forms in goods application
    """

    def test_comment_product_form_if_all_fields_filled_correctly(self):
        """
        Testing the form through which the user can submit a comment, when all fields filled correctly
        """
        form_data = {
            'user_name': 'Test',
            'user_email': 'example@example.com',
            'body': 'Text of comment'
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
            'body': ''
        }

        self.comment_form_instance = CommentProductForm(data=form_data)
        self.assertFalse(self.comment_form_instance.is_valid())
        self.assertFormError(self.comment_form_instance, 'user_name', ['This field must not be empty'])
        self.assertFormError(self.comment_form_instance, 'user_email', ['This field must not be empty'])
        self.assertFormError(self.comment_form_instance, 'body', ['This field must not be empty'])

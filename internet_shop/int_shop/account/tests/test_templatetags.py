from django.test import TestCase
from django.template import Template, Context


class TestTemplatetagsAccount(TestCase):
    """
    Testing templatetags in account application
    """

    def test_get_value_from_dict(self):
        """
        Checking the return correct value from dictionary in template
        """
        context_data = {'data': {'a': 1}}
        context = Context(context_data)
        template = Template("{% load get_value_from_dict %}Received data is: {{ data|get_dict_item:'a' }}")
        self.assertEqual(template.render(context=context), f'Received data is: {context_data["data"]["a"]}')

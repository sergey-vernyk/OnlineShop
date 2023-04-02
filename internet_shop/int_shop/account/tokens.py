from django.contrib.auth.tokens import PasswordResetTokenGenerator


class ActivationAccountTokenGenerator(PasswordResetTokenGenerator):
    """
    Генератор токенов для ссылки, которая используется для
    активации аккаунта и подтверждения email
    """

    def _make_hash_value(self, user, timestamp):
        return f'{user.pk}{timestamp}{user.is_active}{user.email}'


activation_account_token = ActivationAccountTokenGenerator()

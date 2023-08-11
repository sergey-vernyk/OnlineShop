from django.contrib.auth.tokens import PasswordResetTokenGenerator


class ActivationAccountTokenGenerator(PasswordResetTokenGenerator):
    """
    Token generator for confirmed link, which using for account activation and confirm email
    """

    def _make_hash_value(self, user, timestamp):
        return f'{user.pk}{timestamp}{user.is_active}{user.email}'


activation_account_token = ActivationAccountTokenGenerator()

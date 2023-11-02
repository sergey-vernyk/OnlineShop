from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from account.models import Profile
from parler.models import TranslatableModel, TranslatedFields


class PresentCard(models.Model):
    """
    Present card for purchases model.
    """
    code = models.CharField(max_length=50, unique=True, verbose_name=_('Code'))
    valid_from = models.DateTimeField(null=False, verbose_name=_('Valid from'))
    valid_to = models.DateTimeField(null=False, verbose_name=_('Valid to'))
    from_name = models.CharField(max_length=50, verbose_name=_('From name'))
    from_email = models.EmailField(verbose_name=_('From email'))
    to_name = models.CharField(max_length=50, verbose_name=_('To name'))
    to_email = models.EmailField(verbose_name=_('To email'))
    category = models.ForeignKey('Category',
                                 related_name='present_cards',
                                 on_delete=models.CASCADE,
                                 verbose_name=_('Category'))
    message = models.TextField(max_length=300, blank=True, verbose_name=_('Message'))
    amount = models.PositiveSmallIntegerField(blank=False, verbose_name=_('Amount'))
    profile = models.ForeignKey(Profile,
                                related_name='profile_cards',
                                on_delete=models.CASCADE,
                                null=True,
                                blank=True,
                                verbose_name=_('Profile'))

    def __str__(self):
        return f'Code: {self.code}'

    @property
    def is_valid(self) -> bool:
        """
        Returns state of present card
        """
        now = timezone.now()
        return self.valid_from <= now <= self.valid_to

    class Meta:
        ordering = ('id',)
        verbose_name = _('Present card')
        verbose_name_plural = _('Present cards')


class Category(TranslatableModel):
    """
    Present card category model
    """
    translations = TranslatedFields(
        name=models.CharField(max_length=50),
        slug=models.SlugField(max_length=50)
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Category')
        verbose_name_plural = _('Categories')
        ordering = ('id',)

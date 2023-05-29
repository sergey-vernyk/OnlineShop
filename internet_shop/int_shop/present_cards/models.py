from django.db import models
from django.utils import timezone
from account.models import Profile


class PresentCard(models.Model):
    """
    Модель подарочной карты для покупки
    """
    code = models.CharField(max_length=50, unique=True)
    valid_from = models.DateTimeField(null=False)
    valid_to = models.DateTimeField(null=False)
    from_name = models.CharField(max_length=50)
    from_email = models.EmailField()
    to_name = models.CharField(max_length=50)
    to_email = models.EmailField()
    category = models.ForeignKey('Category', related_name='present_cards', on_delete=models.CASCADE)
    message = models.TextField(max_length=300, blank=True)
    amount = models.DecimalField(max_digits=5, decimal_places=2)
    profile = models.ForeignKey(Profile, related_name='profile_cards', on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f'Code: {self.code}'

    @property
    def is_valid(self) -> bool:
        """
        Возврат состояния купона
        """
        now = timezone.now()
        return self.valid_from <= now <= self.valid_to


class Category(models.Model):
    """
    Модель категории подарочной карты
    """
    name = models.CharField(max_length=50)
    slug = models.SlugField(max_length=50)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'

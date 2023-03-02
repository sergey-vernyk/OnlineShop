from django.db import models


class PresentCard(models.Model):
    """
    Модель подарочной карты для покупки
    """
    code = models.CharField(max_length=50, unique=True)
    valid_from = models.DateTimeField(null=False)
    valid_to = models.DateTimeField(null=False)
    active = models.BooleanField(default=False)
    from_name = models.CharField(max_length=50)
    from_email = models.EmailField()
    to_name = models.CharField(max_length=50)
    to_email = models.EmailField()
    category = models.ForeignKey('Category', related_name='present_cards', on_delete=models.CASCADE)
    message = models.TextField(max_length=300, blank=True)
    amount = models.DecimalField(max_digits=5, decimal_places=2)

    def __str__(self):
        return f'Present card code {self.code}'

    class Meta:
        ordering = ('active',)


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

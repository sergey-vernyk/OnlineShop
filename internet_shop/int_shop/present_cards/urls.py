from django.urls import path
from . import views

app_name = 'present_cards'

urlpatterns = [
    path('apply/', views.apply_present_card, name='apply_present_card'),
    path('cancel/', views.cancel_present_card, name='cancel_present_card')
]

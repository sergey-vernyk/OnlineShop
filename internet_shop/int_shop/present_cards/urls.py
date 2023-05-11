from django.urls import path
from . import views

app_name = 'present_cards'

urlpatterns = [
    path('apply/ajax/', views.apply_present_card, name='apply_present_card'),
    path('cancel/ajax/', views.cancel_present_card, name='cancel_present_card')
]

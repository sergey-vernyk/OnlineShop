from django.urls import path
from . import views

urlpatterns = [
    path('make_payment/', views.MakePaymentView.as_view(), name='make_payment')
]

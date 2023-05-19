from django.urls import path, include
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('login/', views.LoginUserView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('password_reset/', views.ForgotPasswordView.as_view(), name='password_reset'),
    path('reset/<uidb64>/<token>/',
         views.SetNewPasswordView.as_view(),
         name='password_reset_confirm'),
    # path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('password_change/', views.UserPasswordChangeView.as_view(), name='password_change'),
    path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(), name='password_change_done'),
    path('register_user/', views.UserRegisterView.as_view(), name='register_user'),
    path('send_activate_email/<uidb64>/<token>', views.activate_user_account, name='activate_account'),
    path('<slug:customer>/<str:location>/', views.DetailUserView.as_view(), name='customer_detail'),
    path('social_auth/', include('social_django.urls', namespace='social')),

]

from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('signup/', views.signup, name='signup'),
    path('activate/<uidb64>/<token>/', views.activate, name='activate'),  # مسار جديد
    path('account_activation_sent/', views.account_activation_sent, name='account_activation_sent'),
    path('resend_activation/', views.resend_activation, name='resend_activation'), 
]
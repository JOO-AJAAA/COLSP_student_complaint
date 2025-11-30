from django.urls import path
from . import views

app_name = 'profiles'

urlpatterns = [
		# API endpoint for creating a guest account (called via AJAX)
		path('guest-login/', views.guest_login_api, name='guest_login_api'),
    path('request-otp/', views.request_otp_view, name='request-otp'),
    path('verify-otp/', views.verify_otp_view, name='verify-otp'),
    path('update-profile/', views.update_profile_api, name='update_profile_api'),
]
from django.urls import path
from . import views

app_name = 'kontol'

urlpatterns = [
	# API endpoint for creating a guest account (called via AJAX)
	path('guest-login/', views.guest_login_api, name='guest-login'),
]
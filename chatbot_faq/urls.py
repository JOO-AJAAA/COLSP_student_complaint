from django.urls import path
from . import views

urlpatterns = [
    # Halaman UI Chat (Diakses user lewat browser)
    path('', views.chat_page, name='chat_page'), 
    
    # API Endpoint (Diakses oleh JavaScript)
    path('api/chat/', views.chat_api, name='chat_api'),
]
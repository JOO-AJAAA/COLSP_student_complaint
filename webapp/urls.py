from django.contrib import admin
from django.urls import path, include
from . import views
from kontol import views as account_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('accounts/', include('allauth.urls')),
    # Reports pages and API
    path('reports/', include('reports.urls')),
    # Include kontol endpoints (guest, otp) under /api/kontol/
    path('api/kontol/', include('kontol.urls')),
    path('profile/', account_views.profile_view, name='profile'),
]

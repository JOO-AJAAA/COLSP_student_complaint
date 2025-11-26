from django.contrib import admin
from django.urls import path, include
from . import views
from profiles import views as account_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('accounts/', include('allauth.urls')),
    # Reports pages and API
    path('reports/', include('reports.urls')),
    path('api/profiles/', include('profiles.urls')),
    path('profile/', account_views.profile_view, name='profile'),
    path('profile/<str:username>/', account_views.public_profile_view, name='public_profile'),
]

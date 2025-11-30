from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views
from profiles import views as account_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('accounts/', include('allauth.urls')),
    # Reports pages and API
    path('reports/', include('reports.urls')),
    path('profile/', account_views.profile_view, name='profile'),
    path('profile/<str:username>/', account_views.public_profile_view, name='public_profile'),
    path('chatbot-faq/', include('chatbot_faq.urls')),
    path('api/auth/', include('profiles.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
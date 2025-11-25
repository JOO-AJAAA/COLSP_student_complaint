from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
  path('',views.reports,name="reports"),
  # API endpoint for AJAX submission
  path('submit/', views.submit_report_api, name='submit_report_api'),
  # Reaction toggle API
  path('toggle-reaction/', views.toggle_reaction, name='toggle_reaction'),
]
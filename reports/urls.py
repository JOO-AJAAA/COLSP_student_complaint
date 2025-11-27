from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
  path('',views.reports,name="reports"),
  # API endpoint for AJAX submission
  path('api/submit/', views.submit_report_api, name="submit_report_api"),
  path('preview/<uuid:report_id>/', views.preview_file, name='preview_file'),
  path('api/reaction/<uuid:report_id>/', views.toggle_reaction_api, name='toggle_reaction_api'),
]
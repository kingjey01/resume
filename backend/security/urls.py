from django.urls import path
from . import views

urlpatterns = [
    path('logs/', views.SecurityLogListCreateView.as_view(), name='security-log-list-create'),
    path('log-event/', views.log_security_event, name='log-security-event'),
    path('app-version/', views.app_version_view, name='app-version'),
    path('resume-pricing-config/', views.resume_pricing_config_view, name='resume-pricing-config'),
]

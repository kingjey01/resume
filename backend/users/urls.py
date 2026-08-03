from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('token/refresh/', views.refresh_token_view, name='token_refresh'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/update/', views.update_profile_view, name='update_profile'),
    path('user/', views.user_info_view, name='user_info'),
    
    # Récupération de mot de passe (Forgot Password)
    path('forgot-password/', views.forgot_password_view, name='forgot_password'),
    path('verify-reset-code/', views.verify_reset_code_view, name='verify_reset_code'),
    path('reset-password/', views.reset_password_view, name='reset_password'),
    
    # Modification de mot de passe (Settings)
    path('change-password/', views.change_password_view, name='change_password'),
    
    # Authentification OTP
    path('otp/request/', views.request_otp_view, name='request-otp'),
    path('otp/verify/', views.verify_otp_view, name='verify-otp'),
    path('profile/complete/', views.complete_profile_view, name='complete-profile'),

    # Suppression de compte
    path('delete-account/request-otp/', views.request_delete_otp_view, name='request-delete-otp'),
    path('delete-account/', views.delete_account_view, name='delete-account'),

    # Demande pour devenir CP
    path('cp-request/', views.create_cp_request_view, name='cp-request-create'),
    path('cp-request/status/', views.get_cp_request_view, name='cp-request-status'),
]

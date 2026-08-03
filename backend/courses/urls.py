from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Initialisation du routeur
router = DefaultRouter()
router.register(r'universites', views.UniversiteViewSet, basename='universite')
router.register(r'filieres', views.FiliereViewSet, basename='filiere')
router.register(r'promotions', views.PromotionViewSet, basename='promotion')

urlpatterns = [
    # Inclure les URLs du routeur
    path('', include(router.urls)),
    
    # Courses
   
    path('course-list/', views.CourseListCreateView.as_view(), name='course-list-create'),
    path('courses/<int:pk>/', views.CourseDetailView.as_view(), name='course-detail'),
    
    # Sessions
    path('sessions/', views.SessionListCreateView.as_view(), name='session-list-create'),
    path('sessions/<int:pk>/', views.SessionDetailView.as_view(), name='session-detail'),
    path('sessions/upload-audio/', views.upload_audio_session, name='upload-audio-session'),
    
    # 🔥 NOUVELLES ROUTES AUDIO AVANCÉES
    path('sessions/audio/', views.get_audio_sessions, name='get_audio_sessions'),
    path('sessions/audio/queue/', views.get_sessions_queue, name='get_sessions_queue'),
    path('sessions/<int:session_id>/process-audio/', views.process_audio_session, name='process_audio_session'),
    path('sessions/<int:session_id>/retry/', views.retry_failed_session, name='retry_failed_session'),
    path('sessions/<int:session_id>/audio-file/', views.get_audio_file, name='get_audio_file'),
    path('sessions/<int:session_id>/serve-audio/', views.serve_audio_file, name='serve_audio_file'),
    path('sessions/audio/stats/', views.get_audio_processing_stats, name='get_audio_processing_stats'),
    path('sessions/audio/batch-process/', views.batch_process_audio_sessions, name='batch_process_audio_sessions'),
    path('sessions/audio/auto-process/', views.auto_process_pending_sessions, name='auto_process_pending_sessions'),
    path('sessions/audio/cleanup/', views.cleanup_old_audio_files, name='cleanup_old_audio_files'),
    
    # Summaries
    path('summaries/', views.SummaryListCreateView.as_view(), name='summary-list-create'),
    path('summaries/<int:pk>/', views.SummaryDetailView.as_view(), name='summary-detail'),
    path('summaries/achetes/', views.SummaryAchetesView.as_view(), name='summary-achetes'),
    path('summaries/gratuits/', views.SummaryGratuitsView.as_view(), name='summary-gratuits'),
    
    # Professeurs
    path('professeurs/', views.ProfesseurListView.as_view(), name='professeur-list'),
    path('professeurs/create-simple/', views.create_professeur_simple_view, name='professeur-create-simple'),
    path('professeurs/<int:professeur_id>/delete/', views.delete_professeur_view, name='professeur-delete'),
    
    # Onboarding
    path('onboarding/status/', views.onboarding_status_view, name='onboarding-status'),
    
    # Dispenses
    path('dispenses/', views.list_dispenses_view, name='dispense-list'),
    path('dispenses/create/', views.create_dispense_view, name='dispense-create'),
    path('dispenses/<int:dispense_id>/delete/', views.delete_dispense_view, name='dispense-delete'),
    path('resolve-professor/', views.resolve_professor_view, name='resolve-professor'),
    
    # AI endpoint
    path('generate-summary/', views.generate_summary_from_audio, name='generate-summary'),
    
    # Validation des résumés (CP et Admin)
    path('summaries/<int:summary_id>/validate/', views.validate_summary_view, name='validate-summary'),
    path('summaries/<int:summary_id>/edit/', views.edit_summary_view, name='edit-summary'),
    path('summaries/validation/', views.get_summaries_for_validation_view, name='summaries-validation'),
    
    # Exercices QCM
    path('', include('courses.exercise_urls')),
    
    # Services and Abonnements moved to payments app
    # path('services/', views.ServiceListCreateView.as_view(), name='service-list-create'),
    # path('services/<int:pk>/', views.ServiceDetailView.as_view(), name='service-detail'),
    # path('abonnements/', views.AbonnementListCreateView.as_view(), name='abonnement-list-create'),
    # path('abonnements/<int:pk>/', views.AbonnementDetailView.as_view(), name='abonnement-detail'),
]

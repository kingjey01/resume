"""
Endpoint de vérification de santé pour le monitoring
"""
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db import connection
from django.conf import settings
import json

@csrf_exempt
@require_http_methods(["GET"])
def health_check(request):
    """
    Endpoint de vérification de santé de l'application
    """
    try:
        # Vérifier la connexion à la base de données
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    # Vérifier les services critiques
    status = {
        "status": "healthy" if db_status == "healthy" else "unhealthy",
        "timestamp": "2024-01-01T00:00:00Z",  # Vous pouvez utiliser datetime.now().isoformat()
        "version": "1.0.0",
        "services": {
            "database": db_status,
            "django": "healthy",
        },
        "debug": settings.DEBUG,
    }

    # Code de statut HTTP basé sur la santé
    status_code = 200 if status["status"] == "healthy" else 503

    return JsonResponse(status, status=status_code)
import logging
from datetime import datetime
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)

class JWTAuthenticationMiddleware(MiddlewareMixin):
    """
    Middleware personnalisé pour journaliser les requêtes JWT (sans bloquer l'authentification)
    """
    def process_request(self, request):
        # Ne traiter que les requêtes API (pas les options CORS)
        if not request.path.startswith('/api/') or request.method == 'OPTIONS':
            return None

        # Journalisation simple de la requête
        log_data = {
            'method': request.method,
            'path': request.path,
            'timestamp': datetime.now().isoformat()
        }

        # Vérifier la présence d'un token JWT (sans le valider ici)
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header:
            auth_parts = auth_header.split()
            if len(auth_parts) == 2 and auth_parts[0].lower() in ['bearer', 'jwt']:
                log_data['auth_header_present'] = True
                log_data['auth_type'] = auth_parts[0]
            else:
                log_data['auth_header_invalid'] = True
        else:
            log_data['auth_header_present'] = False

        # Journaliser sans bloquer
        logger.debug('API Request', extra=log_data)
        
        # Laisser Django REST Framework gérer l'authentification
        return None

    def process_response(self, request, response):
        # Journalisation simple de la réponse
        if request.path.startswith('/api/') and request.method != 'OPTIONS':
            logger.debug(f'API Response: {request.method} {request.path} -> {response.status_code}')
        
        return response

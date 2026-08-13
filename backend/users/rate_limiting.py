"""
Rate limiting OTP (TACHES.md) — protection anti force-brute et abus SMS.

L'autorité est le backend : ces protections s'appliquent AVANT la génération
d'un compte temporaire, l'envoi du SMS et la vérification du code.

Niveaux appliqués (send OTP) :
  - Niveau 1 : maximum d'envois par numéro de téléphone (3 / 10 min)
  - Niveau 2 : cooldown entre deux envois pour un même numéro (60 s)
  - Niveau 3 : maximum de requêtes par IP (100 / 10 min)
  - Niveau 4 : limite globale de l'endpoint (par seconde)

Vérification OTP :
  - 5 codes incorrects → blocage temporaire (10 min) par numéro.

Compteurs : cache Django (Redis en prod, fallback LocMem si Redis est
indisponible → le service ne casse jamais). Toutes les valeurs sont
lisibles dans settings (constantes OTP_*).
"""
import logging
import time

from django.conf import settings
from django.core.cache import caches
from rest_framework.response import Response

from .utils import get_client_ip

logger = logging.getLogger(__name__)


def _cache_get(key):
    """Lecture cache avec repli automatique sur LocMem si Redis est down."""
    try:
        return caches['default'].get(key)
    except Exception:
        return caches['fallback'].get(key)


def _cache_set(key, value, ttl):
    """Écriture cache avec repli automatique sur LocMem si Redis est down."""
    try:
        caches['default'].set(key, value, ttl)
    except Exception:
        caches['fallback'].set(key, value, ttl)


def _log_abuse(namespace, key, limit, count):
    logger.warning(
        '⚠️ [RateLimit] Abus détecté — namespace=%s key=%s count=%s/%s',
        namespace, key, count, limit,
    )


def _too_many(retry_after, message):
    """Réponse 429 standard avec header Retry-After."""
    resp = Response(
        {'error': message, 'retry_after': retry_after},
        status=429,
    )
    resp['Retry-After'] = str(retry_after)
    return resp


def check_rate_limit(namespace, key, limit, window_seconds, cost=1):
    """
    Incrémente le compteur `otp:{namespace}:{key}` (TTL = fenêtre) et
    retourne (allowed, retry_after_seconds, count).
    Avec cost=0 : lecture seule du compteur (utilisé pour la vérification
    OTP : on n'incrémente que sur un échec réel).
    """
    cache_key = f'otp:{namespace}:{key}'
    try:
        current = int(_cache_get(cache_key) or 0)
    except (TypeError, ValueError):
        current = 0

    if current >= limit:
        _log_abuse(namespace, key, limit, current)
        return False, window_seconds, current

    _cache_set(cache_key, current + cost, window_seconds)
    return True, 0, current + cost


def check_cooldown(namespace, key, cooldown_seconds):
    """
    Refuse un envoi tant que `cooldown_seconds` ne sont pas écoulés depuis le
    dernier envoi. Retourne (allowed, retry_after_seconds).
    """
    cache_key = f'otp:cooldown:{namespace}:{key}'
    last_sent = _cache_get(cache_key)
    if last_sent is not None:
        try:
            elapsed = time.time() - float(last_sent)
        except (TypeError, ValueError):
            elapsed = cooldown_seconds + 1
        if elapsed < cooldown_seconds:
            return False, int(cooldown_seconds - elapsed) + 1

    _cache_set(cache_key, str(time.time()), cooldown_seconds)
    return True, 0


def enforce_send_otp_limits(request, namespace, phone):
    """
    Niveaux 1-4 appliqués AVANT l'envoi du SMS (et avant la création d'un
    compte temporaire). Retourne une réponse 429 (avec Retry-After) si une
    limite est dépassée, sinon None.
    """
    # Niveau 2 — cooldown entre deux envois pour le même numéro
    allowed, retry_after = check_cooldown(
        namespace, f'phone:{phone}', settings.OTP_COOLDOWN_SECONDS)
    if not allowed:
        return _too_many(retry_after, 'Veuillez patienter avant de demander un nouveau code.')

    # Niveau 1 — maximum d'envois par numéro
    allowed, retry_after, _ = check_rate_limit(
        namespace, f'phone:{phone}',
        settings.OTP_MAX_SENDS_PER_PHONE, settings.OTP_PHONE_WINDOW_SECONDS)
    if not allowed:
        return _too_many(retry_after, 'Limite de codes envoyés atteinte. Réessayez plus tard.')

    # Niveau 3 — maximum de requêtes par IP
    allowed, retry_after, _ = check_rate_limit(
        namespace, f'ip:{get_client_ip(request)}',
        settings.OTP_MAX_REQUESTS_PER_IP, settings.OTP_IP_WINDOW_SECONDS)
    if not allowed:
        return _too_many(retry_after, 'Trop de demandes depuis votre réseau. Réessayez plus tard.')

    # Niveau 4 — limite globale de l'endpoint (par seconde)
    allowed, retry_after, _ = check_rate_limit(
        namespace, 'global', settings.OTP_GLOBAL_MAX_PER_SECOND, 1)
    if not allowed:
        return _too_many(retry_after, 'Trop de demandes. Réessayez dans un instant.')

    return None


def enforce_verify_otp_limits(request, namespace, phone):
    """
    Blocage temporaire AVANT vérification si le numéro a accumulé trop de
    codes incorrects (lecture seule, cost=0). Retourne une réponse 429
    (avec Retry-After) si bloqué, sinon None.
    """
    allowed, retry_after, _ = check_rate_limit(
        namespace, f'phone:{phone}',
        settings.OTP_MAX_VERIFY_ATTEMPTS, settings.OTP_VERIFY_BLOCK_SECONDS, cost=0)
    if not allowed:
        return _too_many(retry_after, 'Trop de tentatives. Réessayez plus tard.')
    return None


def record_verify_failure(namespace, phone):
    """
    Enregistre un code incorrect pour le blocage temporaire (appelé UNIQUEMENT
    sur un échec de vérification réel, jamais sur un succès).
    """
    cache_key = f'otp:{namespace}:phone:{phone}'
    try:
        current = int(_cache_get(cache_key) or 0)
    except (TypeError, ValueError):
        current = 0
    _cache_set(cache_key, current + 1, settings.OTP_VERIFY_BLOCK_SECONDS)

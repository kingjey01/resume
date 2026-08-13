"""
Utilitaires partagés du module users (normalisation téléphone, mode test OTP,
rate limiting, hash OTP).
"""
import hashlib

from django.conf import settings


def normalize_phone(phone):
    """
    Normalise un numéro de téléphone vers le format canonique 0XXXXXXXXX.

    Gère les formats : +243XXX, 243XXX, 0XXX, ou XXX (9 chiffres).
    Si le format n'est pas reconnu, retourne le numéro tel quel.
    """
    if not phone:
        return phone

    phone = str(phone).strip().replace(' ', '')
    digits_only = phone.lstrip('+')

    if digits_only.isdigit():
        if digits_only.startswith('243') and len(digits_only) == 12:
            # Format +243996816806 ou 243996816806 → 0996816806
            return '0' + digits_only[3:]
        elif len(digits_only) == 9:
            # Format 996816806 → 0996816806
            return '0' + digits_only
        elif digits_only.startswith('0') and len(digits_only) == 10:
            # Format déjà normalisé 0996816806
            return digits_only

    # Sinon garder tel quel
    return phone


def is_test_phone(phone):
    """
    Vérifie si un numéro fait partie du mode de test Google Play.

    Retourne True uniquement si :
      - OTP_TEST_MODE est activé dans la configuration, ET
      - le numéro (normalisé) figure dans OTP_TEST_PHONE_NUMBERS.

    Désactivable simplement via la configuration, sans impact sur
    les utilisateurs réels.
    """
    if not settings.OTP_TEST_MODE:
        return False

    normalized = normalize_phone(phone)
    test_numbers = [normalize_phone(p) for p in settings.OTP_TEST_PHONE_NUMBERS]
    return normalized in test_numbers


def get_client_ip(request):
    """
    IP réelle du client (gère le proxy via X-Forwarded-For).
    Utilisée par le rate limiting OTP.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def hash_otp(code):
    """
    Hash d'un code OTP — seul le hash est stocké en base, jamais le code
    en clair (TACHES.md). Le code clair n'existe qu'en mémoire le temps de
    l'envoi du SMS / de la réponse du mode test.
    """
    return hashlib.sha256(str(code).encode('utf-8')).hexdigest()

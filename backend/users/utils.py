"""
Utilitaires partagés du module users (normalisation téléphone, mode test OTP).
"""
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

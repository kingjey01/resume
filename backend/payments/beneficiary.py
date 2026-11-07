"""Résolution et validation du bénéficiaire d'un paiement.

Tâche 70 — « Payer pour un autre étudiant ».

Règles :
- un paiement sans `beneficiary_phone` est un paiement pour soi : le
  bénéficiaire est le payeur, comportement historique inchangé ;
- un paiement avec `beneficiary_phone` désigne un AUTRE compte étudiant actif,
  résolu exclusivement en base à partir du numéro normalisé ;
- le numéro fourni par l'application n'est jamais utilisé comme identifiant
  direct : il sert uniquement à retrouver un `UserProfile`.
"""

from users.models import UserProfile
from users.utils import normalize_phone


class BeneficiaryError(Exception):
    """Erreur métier de résolution du bénéficiaire (message affichable)."""

    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def normaliser_numero_paiement(value):
    """Normalise un numéro vers le format canonique `0XXXXXXXXX`.

    Retourne `None` si le numéro n'a pas un format exploitable. Un numéro
    Mobile Money congolais normalisé compte 10 chiffres et commence par 0.
    """
    raw = str(value or '').strip()
    if not raw:
        return None

    numero = normalize_phone(raw)
    if len(numero) == 10 and numero.startswith('0') and numero[1:].isdigit():
        return numero
    return None


def masquer_numero(numero):
    """Masque un numéro pour l'affichage (`09****456`)."""
    if not numero or len(numero) < 6:
        return '***'
    return f"{numero[:2]}****{numero[-3:]}"


def trouver_beneficiaire(numero_beneficiaire):
    """Retourne le `UserProfile` étudiant actif correspondant au numéro."""
    numero = normaliser_numero_paiement(numero_beneficiaire)
    if not numero:
        raise BeneficiaryError('Numéro du bénéficiaire invalide.')

    profils = list(
        UserProfile.objects.select_related('user', 'promotion', 'universite')
        .filter(phone=numero, user__is_active=True, groupe='ETUDIANT')[:2]
    )

    if not profils:
        raise BeneficiaryError(
            'Aucun compte étudiant actif ne correspond à ce numéro.',
            status_code=404,
        )

    if len(profils) > 1:
        # Le numéro n'est pas une contrainte d'unicité : refuser plutôt que
        # d'attribuer un achat au hasard.
        raise BeneficiaryError(
            'Plusieurs comptes utilisent ce numéro. Contactez le support.',
            status_code=409,
        )

    return profils[0]


def resoudre_beneficiaire(payeur, beneficiary_phone):
    """Résout le compte bénéficiaire.

    Retourne `(user_beneficiaire, profil_beneficiaire)`.

    - sans numéro de bénéficiaire → `(payeur, profil du payeur)` ;
    - avec numéro → compte étudiant actif distinct du payeur.

    Lève `BeneficiaryError` si la demande est invalide.
    """
    raw = str(beneficiary_phone or '').strip()
    if not raw:
        profil = getattr(payeur, 'profile', None)
        return payeur, profil

    profil = trouver_beneficiaire(raw)
    if profil.user_id == payeur.id:
        raise BeneficiaryError(
            'Le bénéficiaire doit être un autre étudiant. '
            'Utilisez « Payer pour moi » pour votre propre compte.'
        )

    return profil.user, profil


def est_cadeau(user_beneficiaire, user_payeur):
    """Vrai lorsque l'achat est offert à un autre compte."""
    return bool(user_beneficiaire and user_payeur and user_beneficiaire.id != user_payeur.id)

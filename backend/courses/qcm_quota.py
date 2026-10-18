"""
Quota mensuel (et plafond journalier) de générations QCM — tâche 57.

Règles :
- Une unité = UNE GÉNÉRATION COMPLÈTE de QCM pour un résumé : le pack des
  3 niveaux de difficulté (8 questions × 3 = 24 questions), jamais une
  question ni un niveau isolé.
- Le mois de consommation est une période glissante de 30 jours alignée sur
  `Abonnement.date_debut` — même logique que `Service.get_date_fin()`
  (`duree_mois * 30 jours`).
- Le compteur vit uniquement en base : l'application Flutter ne l'incrémente
  jamais, elle affiche seulement l'instantané renvoyé par le serveur.
- La consommation se fait sous `select_for_update()` pour qu'une rafale de
  requêtes concurrentes ne puisse pas dépasser le quota.
- Une génération qui échoue est remboursée (voir `rembourser_quota`).
"""
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

PERIODE_JOURS = 30


def _debut_periode(date_debut, now):
    """Début de la période de 30 jours contenant `now`."""
    if now <= date_debut:
        return date_debut
    jours_ecoules = (now - date_debut).days
    return date_debut + timedelta(days=(jours_ecoules // PERIODE_JOURS) * PERIODE_JOURS)


def periode_courante(abonnement, now=None):
    """Début de la période de consommation courante d'un abonnement.

    C'est la clé qui relie les 3 niveaux d'un même résumé à un seul pack :
    un exercice marqué avec cette date a déjà payé le pack pour la période.
    """
    now = now or timezone.now()
    return _debut_periode(abonnement.date_debut, now)


def get_active_subscription(user, now=None):
    """Retourne l'abonnement actif qui porte le quota QCM.

    Même hiérarchie que `has_exercise_subscription()` : service QCM/Exercices
    d'abord, puis n'importe quel abonnement actif (l'app ne vend qu'un type
    d'abonnement). Retourne `None` si l'utilisateur n'est pas abonné.
    """
    from payments.models import Service, Abonnement

    now = now or timezone.now()
    actifs = Abonnement.objects.filter(
        user=user,
        status='active',
        date_debut__lte=now,
        date_fin__gte=now,
    ).select_related('service')

    service_ids = list(
        Service.objects.filter(nom__icontains='qcm', is_active=True)
        .values_list('id', flat=True)
    )
    if service_ids:
        sub = actifs.filter(service_id__in=service_ids).order_by('-date_fin').first()
        if sub:
            return sub

    return actifs.order_by('-date_fin').first()


def plafond_journalier(sub):
    """Plafond journalier effectif.

    Un plafond explicite l'emporte. Sinon, un abonnement à quota mensuel reçoit
    automatiquement `quota / 30` (minimum 1) : impossible de vider un quota
    mensuel en une heure, comme demandé par la tâche.
    Avec l'unité « pack » (3 niveaux, 24 questions), 1/jour = un résumé
    complet par jour — et non un seul niveau.
    `0` signifie illimité.
    """
    if sub.plafond_qcm_journalier and sub.plafond_qcm_journalier > 0:
        return sub.plafond_qcm_journalier
    if sub.quota_qcm_mensuel and sub.quota_qcm_mensuel > 0:
        return max(1, sub.quota_qcm_mensuel // PERIODE_JOURS)
    return 0


def _normaliser_en_memoire(sub, now):
    """Applique les remises à zéro de période/jour sans écrire en base.

    Retourne (champs_modifies, periode_debut, conso_mensuelle, conso_jour).
    """
    champs = []

    periode_debut = sub.quota_qcm_periode_debut or _debut_periode(sub.date_debut, now)
    conso_mensuelle = sub.quota_qcm_consomme
    periode_attendue = _debut_periode(sub.date_debut, now)
    if periode_debut < periode_attendue:
        periode_debut = periode_attendue
        conso_mensuelle = 0
        sub.quota_qcm_periode_debut = periode_debut
        sub.quota_qcm_consomme = 0
        champs.extend(['quota_qcm_periode_debut', 'quota_qcm_consomme'])
    elif sub.quota_qcm_periode_debut is None:
        sub.quota_qcm_periode_debut = periode_debut
        champs.append('quota_qcm_periode_debut')

    if sub.quota_qcm_jour != now.date():
        conso_jour = 0
        sub.quota_qcm_jour = now.date()
        sub.quota_qcm_jour_consomme = 0
        champs.extend(['quota_qcm_jour', 'quota_qcm_jour_consomme'])
    else:
        conso_jour = sub.quota_qcm_jour_consomme

    return champs, periode_debut, conso_mensuelle, conso_jour


def quota_snapshot(sub, now=None):
    """Instantané JSON-ready du quota, tel que l'interface doit l'afficher."""
    now = now or timezone.now()

    if sub is None:
        return {
            'active': False,
            'status': 'none',
            'service': None,
            'date_debut': None,
            'date_fin': None,
            'quota_mensuel': 0,
            'quota_consomme': 0,
            'quota_restant': None,
            'plafond_journalier': 0,
            'jour_consomme': 0,
            'jour_restant': None,
            'prochaine_reinitialisation': None,
            'peut_generer': False,
            'raison_blocage': 'subscription_required',
            'message_blocage': "Abonnement exercices requis pour générer des QCM.",
        }

    _, periode_debut, conso_mensuelle, conso_jour = _normaliser_en_memoire(sub, now)

    quota = sub.quota_qcm_mensuel or 0
    plafond = plafond_journalier(sub)
    quota_restant = None if quota == 0 else max(0, quota - conso_mensuelle)
    jour_restant = None if plafond == 0 else max(0, plafond - conso_jour)

    actif = sub.status == 'active' and sub.date_debut <= now <= sub.date_fin
    raison = None
    message = None
    if not actif:
        raison = 'subscription_required'
        message = "Votre abonnement exercices n'est pas actif."
    elif quota > 0 and conso_mensuelle >= quota:
        raison = 'quota_exhausted'
        message = (
            "Quota mensuel de générations QCM épuisé. "
            "Renouvelez votre abonnement pour continuer."
        )
    elif plafond > 0 and conso_jour >= plafond:
        raison = 'daily_quota_exhausted'
        message = (
            "Plafond journalier de générations QCM atteint. "
            "Revenez demain pour générer de nouveaux QCM."
        )

    # La prochaine réinitialisation n'a de sens que si l'abonnement couvre
    # encore une période complète après le prochain cycle.
    prochaine = None
    if quota > 0:
        candidate = periode_debut + timedelta(days=PERIODE_JOURS)
        if candidate < sub.date_fin:
            prochaine = candidate

    return {
        'active': actif,
        'status': sub.status,
        'service': sub.service.nom,
        'date_debut': sub.date_debut.isoformat(),
        'date_fin': sub.date_fin.isoformat(),
        'quota_mensuel': quota,
        'quota_consomme': conso_mensuelle,
        'quota_restant': quota_restant,
        'plafond_journalier': plafond,
        'jour_consomme': conso_jour,
        'jour_restant': jour_restant,
        'prochaine_reinitialisation': prochaine.isoformat() if prochaine else None,
        'peut_generer': raison is None,
        'raison_blocage': raison,
        'message_blocage': message,
    }


def consommer_quota(user, now=None):
    """Réserve une génération QCM.

    Retourne `(ok, snapshot, abonnement_id)`. Quand `ok` est faux,
    `snapshot['raison_blocage']` vaut soit `subscription_required`, soit
    `quota_exhausted`, soit `daily_quota_exhausted`.
    """
    from payments.models import Abonnement

    now = now or timezone.now()
    sub = get_active_subscription(user, now)
    if sub is None:
        return False, quota_snapshot(None, now), None

    with transaction.atomic():
        verrou = Abonnement.objects.select_for_update().select_related('service').get(pk=sub.pk)
        champs, _, conso_mensuelle, conso_jour = _normaliser_en_memoire(verrou, now)

        quota = verrou.quota_qcm_mensuel or 0
        plafond = plafond_journalier(verrou)

        if quota > 0 and conso_mensuelle >= quota:
            if champs:
                verrou.save(update_fields=list(set(champs)))
            return False, quota_snapshot(verrou, now), verrou.id

        if plafond > 0 and conso_jour >= plafond:
            if champs:
                verrou.save(update_fields=list(set(champs)))
            return False, quota_snapshot(verrou, now), verrou.id

        verrou.quota_qcm_periode_debut = _debut_periode(verrou.date_debut, now)
        verrou.quota_qcm_consomme = conso_mensuelle + 1
        verrou.quota_qcm_jour = now.date()
        verrou.quota_qcm_jour_consomme = conso_jour + 1
        verrou.save(update_fields=[
            'quota_qcm_periode_debut',
            'quota_qcm_consomme',
            'quota_qcm_jour',
            'quota_qcm_jour_consomme',
        ])

    return True, quota_snapshot(verrou, now), verrou.id


def rembourser_quota(abonnement_id, consomme_le=None):
    """Rend une unité quand la génération n'a produit aucun résultat exploitable.

    Ne touche qu'aux compteurs de la période/jour où la consommation a eu lieu :
    si la période a changé entre-temps, l'ancien compteur a déjà été remis à
    zéro et il ne faut surtout pas amputer la nouvelle période.
    """
    from payments.models import Abonnement

    if not abonnement_id:
        return

    consomme_le = consomme_le or timezone.now()

    with transaction.atomic():
        sub = Abonnement.objects.select_for_update().filter(pk=abonnement_id).first()
        if sub is None:
            return

        champs = []
        if _debut_periode(sub.date_debut, consomme_le) == sub.quota_qcm_periode_debut:
            if sub.quota_qcm_consomme > 0:
                sub.quota_qcm_consomme -= 1
                champs.append('quota_qcm_consomme')
        if sub.quota_qcm_jour == consomme_le.date() and sub.quota_qcm_jour_consomme > 0:
            sub.quota_qcm_jour_consomme -= 1
            champs.append('quota_qcm_jour_consomme')

        if champs:
            sub.save(update_fields=champs)

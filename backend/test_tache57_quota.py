"""
Contrôles hors-Django de la logique de quota QCM (tâche 57).

Ce script ne touche ni à la base ni au serveur : il injecte deux stubs Django
(`django.db.transaction`, `django.utils.timezone`) puis vérifie les règles
pures de `courses/qcm_quota.py` (plafond journalier dérivé, remise à zéro des
périodes, blocage, prochaine réinitialisation).

Usage :
    python -I backend/test_tache57_quota.py        # depuis la racine du dépôt
    python -I test_tache57_quota.py                # depuis backend/
"""
import contextlib
import importlib.util
import sys
import types
from datetime import date, datetime, timedelta, timezone as dt_timezone
from pathlib import Path

NOW = datetime(2026, 10, 18, 12, 0, tzinfo=dt_timezone.utc)

# Stubs minimaux : qcm_quota importe django.db.transaction et django.utils.timezone.
django = types.ModuleType('django')
db = types.ModuleType('django.db')
db.transaction = types.SimpleNamespace(atomic=contextlib.nullcontext)
django.db = db
utils = types.ModuleType('django.utils')
utils.timezone = types.SimpleNamespace(now=lambda: NOW)
sys.modules['django'] = django
sys.modules['django.db'] = db
sys.modules['django.utils'] = utils

PATH = Path(__file__).resolve().parent / 'courses' / 'qcm_quota.py'
spec = importlib.util.spec_from_file_location('qcm_quota', PATH)
quota_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(quota_module)
q = quota_module


class Sub:
    """Abonnement factice, avec les seuls champs lus par qcm_quota."""

    def __init__(self, **overrides):
        self.id = 1
        self.status = 'active'
        self.service = types.SimpleNamespace(nom='Abonnement QCM')
        self.date_debut = NOW - timedelta(days=10)
        self.date_fin = NOW + timedelta(days=20)
        self.quota_qcm_mensuel = 30
        self.plafond_qcm_journalier = 0
        self.quota_qcm_consomme = 0
        self.quota_qcm_periode_debut = self.date_debut
        self.quota_qcm_jour = NOW.date()
        self.quota_qcm_jour_consomme = 0
        for key, value in overrides.items():
            setattr(self, key, value)


def check(label, condition, detail=''):
    print(('OK   ' if condition else 'ECHEC') + f' {label} {detail}')
    if not condition:
        raise SystemExit(1)


# 0) Grille Basic retenue : 15 packs (3 niveaux / 24 questions) par mois,
#    soit 1 pack par jour avec le plafond dérivé.
basic = Sub(quota_qcm_mensuel=15)
check('Basic : 15 packs / mois', q.quota_snapshot(basic, NOW)['quota_mensuel'] == 15)
check('Basic : 1 pack / jour', q.plafond_journalier(basic) == 1)

# 1) Plafond journalier : explicite, dérivé (quota / 30) ou illimité.
check('plafond dérivé 30/30 = 1', q.plafond_journalier(Sub()) == 1)
check('plafond explicite conservé',
      q.plafond_journalier(Sub(plafond_qcm_journalier=4)) == 4)
check('quota illimité => plafond illimité',
      q.plafond_journalier(Sub(quota_qcm_mensuel=0)) == 0)

# 2) Quota restant affiché par l'interface.
snap = q.quota_snapshot(Sub(quota_qcm_consomme=29), NOW)
check('quota restant = 1', snap['quota_restant'] == 1 and snap['peut_generer'])
check('jour restant = 1', snap['jour_restant'] == 1)

# 3) Blocage quand le quota mensuel est atteint, abonnement encore valide.
snap = q.quota_snapshot(Sub(quota_qcm_consomme=30), NOW)
check('quota mensuel épuisé',
      not snap['peut_generer'] and snap['raison_blocage'] == 'quota_exhausted')

# 4) Blocage quand le plafond journalier est atteint.
snap = q.quota_snapshot(Sub(quota_qcm_jour_consomme=1), NOW)
check('plafond journalier épuisé',
      not snap['peut_generer']
      and snap['raison_blocage'] == 'daily_quota_exhausted')

# 5) Nouvelle période de 30 jours : le compteur mensuel repart à zéro.
debut = NOW - timedelta(days=31)
snap = q.quota_snapshot(Sub(
    date_debut=debut,
    date_fin=NOW + timedelta(days=59),
    quota_qcm_consomme=30,
    quota_qcm_periode_debut=debut,
    quota_qcm_jour=NOW.date(),
    quota_qcm_jour_consomme=0,
), NOW)
check('période remise à zéro', snap['quota_consomme'] == 0 and snap['peut_generer'])
check('prochaine réinitialisation connue',
      snap['prochaine_reinitialisation'] is not None)

# 5bis) Changement de jour : le compteur journalier repart à zéro.
snap = q.quota_snapshot(Sub(
    quota_qcm_jour=date(2026, 10, 17),
    quota_qcm_jour_consomme=1,
), NOW)
check('jour remis à zéro', snap['jour_consomme'] == 0 and snap['peut_generer'])

# 6) Abonnement d'un seul mois : aucun reset avant l'expiration.
debut = NOW - timedelta(days=10)
snap = q.quota_snapshot(
    Sub(date_debut=debut, date_fin=debut + timedelta(days=30)), NOW)
check('pas de reset avant expiration',
      snap['prochaine_reinitialisation'] is None)

# 7) Aucun abonnement actif.
snap = q.quota_snapshot(None, NOW)
check('sans abonnement', snap['raison_blocage'] == 'subscription_required')

print('\nTous les contrôles du quota QCM sont passés.')

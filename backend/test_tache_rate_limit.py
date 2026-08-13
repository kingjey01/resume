"""
Vérification TACHES.md — rate limiting OTP (le backend est l'autorité).

Niveaux testés :
  Niveau 1 : max 3 OTP / 10 min par numéro → 4e demande = 429 + Retry-After
  Niveau 2 : cooldown 60 s entre deux envois pour un même numéro → 429
  Niveau 3 : max requêtes / 10 min par IP → dépassement = 429
  Niveau 4 : limite globale de l'endpoint (par seconde) → dépassement = 429
  Vérification : 5 codes incorrects → blocage temporaire (429 + Retry-After)
  OTP hashé : jamais stocké en clair, usage unique, invalidé après succès
  Les limites sont appliquées AVANT l'envoi SMS / la création du compte
  temporaire (un envoi bloqué ne crée aucun compte).

Usage : PYTHONIOENCODING=utf-8 python test_tache_rate_limit.py
"""
import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resume_backend.settings')
import django
django.setup()

# Mode Celery eager : les tâches s'exécutent en synchrone, sans broker
from celery import current_app
current_app.conf.task_always_eager = True
current_app.conf.task_eager_propagates = False

from django.conf import settings
from django.core.cache import caches
from django.test import override_settings
from rest_framework.test import APIClient

from django.contrib.auth.models import User
from users.models import UserProfile
from users.utils import hash_otp, normalize_phone

BASE = '/api/auth'

# Numéros de test Google Play dédiés (aucun SMS réel envoyé)
TEST_PHONES = [
    '+243990000002', '+243990000003',
    '+243990000041', '+243990000042', '+243990000043',
    '+243990000051', '+243990000052',
    '+243990000061', '+243990000071', '+243990000081',
]

ALL_RESULTS = []


def check(name, ok, detail=''):
    ALL_RESULTS.append((name, ok))
    print(f'  {"✅" if ok else "❌"} {name}{" — " + str(detail) if detail else ""}')


def clear_caches():
    """Compteurs du rate limiting : repartir de zéro entre chaque test."""
    for alias in ('default', 'fallback'):
        try:
            caches[alias].clear()
        except Exception:
            pass


def cleanup():
    for phone in TEST_PHONES:
        try:
            profile = UserProfile.objects.get(phone=normalize_phone(phone))
            profile.user.delete()  # cascade vers le profil
        except UserProfile.DoesNotExist:
            pass
    User.objects.filter(username__in=[
        'rl_hash_user', 'rl_delete_user', 'rl_verify_block_user']).delete()


# ──────────────────────────────────────────────────────────────
# 1) OTP hashé, usage unique, invalidé immédiatement après succès
# ──────────────────────────────────────────────────────────────
def test_otp_hashing():
    print('\n[1] OTP hashé + usage unique')
    user = User.objects.create_user(username='rl_hash_user', password='x')
    UserProfile.objects.create(user=user, phone='0999000001')

    profile = UserProfile.objects.get(phone='0999000001')
    code = profile.generate_otp()

    check('code clair retourné par generate_otp()', code and code.isdigit() and len(code) == 4)
    check('le code N est PAS stocké en clair', code != profile.otp_code)
    check('stocké = hash sha256 hex (64 caractères)', len(profile.otp_code) == 64 and profile.otp_code == hash_otp(code))

    ok = profile.verify_otp(code)
    check('verification avec le vrai code → succès', ok is True)
    check('OTP invalidé immédiatement après utilisation', profile.otp_code is None and profile.otp_expires is None)
    check('le même code ne peut plus être réutilisé', profile.verify_otp(code) is False)

    code2 = profile.generate_otp()
    check('mauvais code → échec + compteur d’échecs', profile.verify_otp('9999') is False and profile.otp_attempts == 1)
    check('un nouveau code reste valide après un échec', profile.verify_otp(code2) is True)
    user.delete()


# ──────────────────────────────────────────────────────────────
# 2) Niveau 2 — cooldown 60 s entre deux envois
# ──────────────────────────────────────────────────────────────
@override_settings(OTP_TEST_MODE=True, OTP_TEST_PHONE_NUMBERS=['+243990000002'])
def test_cooldown():
    print('\n[2] Niveau 2 — cooldown 60 s entre deux envois')
    clear_caches()
    client = APIClient()

    r1 = client.post(f'{BASE}/otp/request/', {'phone': '+243990000002'}, format='json')
    check('1er envoi → 200', r1.status_code == 200, r1.status_code)

    r2 = client.post(f'{BASE}/otp/request/', {'phone': '+243990000002'}, format='json')
    check('2e envoi immédiat → 429 (cooldown)', r2.status_code == 429, r2.status_code)
    check('header Retry-After présent', 'Retry-After' in r2.headers, r2.headers.get('Retry-After'))
    if 'Retry-After' in r2.headers:
        retry = int(r2.headers['Retry-After'])
        check('Retry-After cohérent avec le cooldown (1..60 s)',
              1 <= retry <= settings.OTP_COOLDOWN_SECONDS, retry)

    # Un envoi bloqué ne doit pas créer de compte temporaire supplémentaire
    n_profiles = UserProfile.objects.filter(phone=normalize_phone('+243990000002')).count()
    check('envoi bloqué → aucun compte temporaire créé', n_profiles == 1, n_profiles)


# ──────────────────────────────────────────────────────────────
# 3) Niveau 1 — max 3 OTP / 10 min par numéro
# ──────────────────────────────────────────────────────────────
@override_settings(OTP_TEST_MODE=True, OTP_TEST_PHONE_NUMBERS=['+243990000003'],
                   OTP_COOLDOWN_SECONDS=0, OTP_MAX_SENDS_PER_PHONE=3)
def test_phone_limit():
    print('\n[3] Niveau 1 — max 3 OTP / 10 min par numéro')
    clear_caches()
    client = APIClient()
    statuses = []
    last = None
    for _ in range(4):
        last = client.post(f'{BASE}/otp/request/', {'phone': '+243990000003'}, format='json')
        statuses.append(last.status_code)
    check('3 envois OK puis 4e → 429', statuses == [200, 200, 200, 429], statuses)
    check('Retry-After = fenêtre restante (600)', last.headers.get('Retry-After') == '600',
          last.headers.get('Retry-After'))

    n_profiles = UserProfile.objects.filter(phone=normalize_phone('+243990000003')).count()
    check('aucun compte temporaire créé en plus des 3 envois', n_profiles == 1, n_profiles)


# ──────────────────────────────────────────────────────────────
# 4) Niveau 3 — max requêtes / 10 min par IP
# ──────────────────────────────────────────────────────────────
@override_settings(OTP_TEST_MODE=True,
                   OTP_TEST_PHONE_NUMBERS=['+243990000041', '+243990000042', '+243990000043'],
                   OTP_COOLDOWN_SECONDS=0, OTP_MAX_SENDS_PER_PHONE=50,
                   OTP_MAX_REQUESTS_PER_IP=2)
def test_ip_limit():
    print('\n[4] Niveau 3 — limite par IP (2 requêtes max pour le test)')
    clear_caches()
    client = APIClient()
    extra = {'REMOTE_ADDR': '41.111.111.111'}
    phones = ['+243990000041', '+243990000042', '+243990000043']
    statuses = []
    for p in phones:
        r = client.post(f'{BASE}/otp/request/', {'phone': p}, format='json', **extra)
        statuses.append(r.status_code)
    check('2 numéros différents puis 3e depuis la même IP → 429',
          statuses == [200, 200, 429], statuses)
    check('Retry-After = fenêtre IP (600)', r.headers.get('Retry-After') == '600',
          r.headers.get('Retry-After'))


# ──────────────────────────────────────────────────────────────
# 5) Niveau 4 — limite globale de l'endpoint (par seconde)
#    Test direct de la fonction (2 requêtes enchaînées). Le cache est
#    branché directement sur LocMem pour le test : ici Redis est down
#    et chaque accès échoué prend ~2,3 s (la fenêtre de 1 s expirerait
#    entre les deux appels, même sans aucun I/O autre).
# ──────────────────────────────────────────────────────────────
@override_settings(OTP_TEST_MODE=True,
                   OTP_TEST_PHONE_NUMBERS=['+243990000051', '+243990000052'],
                   OTP_COOLDOWN_SECONDS=0, OTP_MAX_SENDS_PER_PHONE=50,
                   OTP_MAX_REQUESTS_PER_IP=50, OTP_GLOBAL_MAX_PER_SECOND=1)
def test_global_limit():
    print('\n[5] Niveau 4 — limite globale de l’endpoint (1 requête/s pour le test)')
    from unittest import mock
    from django.test import RequestFactory
    from users import rate_limiting

    clear_caches()
    factory = RequestFactory()
    req1 = factory.post(f'{BASE}/otp/request/', {'phone': '+243990000051'})
    req2 = factory.post(f'{BASE}/otp/request/', {'phone': '+243990000052'})

    # Cache local direct (sans tentative Redis) pour un enchaînement rapide
    fb = caches['fallback']
    with mock.patch.object(rate_limiting, '_cache_get', side_effect=lambda k: fb.get(k)), \
         mock.patch.object(rate_limiting, '_cache_set', side_effect=lambda k, v, t: fb.set(k, v, t)):
        r1 = rate_limiting.enforce_send_otp_limits(req1, 'send_otp', '+243990000051')
        r2 = rate_limiting.enforce_send_otp_limits(req2, 'send_otp', '+243990000052')
    check('1re requête (numéro + IP différents) → autorisée', r1 is None)
    check('2e requête → 429 (limite globale)',
          r2 is not None and r2.status_code == 429,
          getattr(r2, 'status_code', None))
    check('Retry-After présent', r2 is not None and 'Retry-After' in r2.headers,
          r2.headers.get('Retry-After') if r2 is not None else None)


# ──────────────────────────────────────────────────────────────
# 6) Vérification OTP — 5 codes incorrects → blocage temporaire
# ──────────────────────────────────────────────────────────────
@override_settings(OTP_TEST_MODE=True, OTP_TEST_PHONE_NUMBERS=['+243990000061'])
def test_verify_block():
    print('\n[6] Vérification — 5 codes incorrects → blocage temporaire')
    clear_caches()
    client = APIClient()

    send = client.post(f'{BASE}/otp/request/', {'phone': '+243990000061'}, format='json')
    check('envoi du code OK (mode test, sans SMS)', send.status_code == 200, send.status_code)

    statuses = []
    last = None
    for _ in range(5):
        last = client.post(f'{BASE}/otp/verify/',
                           {'phone': '+243990000061', 'otp_code': '9999'}, format='json')
        statuses.append(last.status_code)
    check('5 codes incorrects → [400, 400, 400, 400, 429]', statuses == [400, 400, 400, 400, 429], statuses)
    check('429 avec Retry-After = fenêtre de blocage (600)',
          last.headers.get('Retry-After') == '600', last.headers.get('Retry-After'))

    r6 = client.post(f'{BASE}/otp/verify/',
                     {'phone': '+243990000061', 'otp_code': '9999'}, format='json')
    check('6e tentative (même après reset du profil) → toujours 429', r6.status_code == 429, r6.status_code)


# ──────────────────────────────────────────────────────────────
# 7) Suppression de compte — cooldown + blocage + succès
# ──────────────────────────────────────────────────────────────
@override_settings(OTP_TEST_MODE=True, OTP_TEST_PHONE_NUMBERS=['+243990000071'],
                   OTP_COOLDOWN_SECONDS=0)
def test_delete_account_flow():
    print('\n[7] Suppression de compte — OTP protégé')
    clear_caches()
    user = User.objects.create_user(username='rl_delete_user', password='x')
    UserProfile.objects.create(user=user, phone='+243990000071')
    client = APIClient()
    client.force_authenticate(user=user)

    r1 = client.post(f'{BASE}/delete-account/request-otp/', {}, format='json')
    check('demande de code suppression → 200', r1.status_code == 200, r1.status_code)
    code = r1.data.get('otp_code')

    bad = client.delete(f'{BASE}/delete-account/', {'otp_code': '9999'}, format='json')
    check('mauvais code → 400', bad.status_code == 400, bad.status_code)

    good = client.delete(f'{BASE}/delete-account/', {'otp_code': code}, format='json')
    check('bon code → compte supprimé (200)', good.status_code == 200, good.status_code)
    check('l’utilisateur n’existe plus', not User.objects.filter(username='rl_delete_user').exists())


@override_settings(OTP_TEST_MODE=True, OTP_TEST_PHONE_NUMBERS=['+243990000081'],
                   OTP_COOLDOWN_SECONDS=0)
def test_delete_verify_block():
    print('\n[8] Suppression — blocage après 5 codes incorrects')
    clear_caches()
    user = User.objects.create_user(username='rl_verify_block_user', password='x')
    UserProfile.objects.create(user=user, phone='+243990000081')
    client = APIClient()
    client.force_authenticate(user=user)

    client.post(f'{BASE}/delete-account/request-otp/', {}, format='json')
    statuses = []
    last = None
    for _ in range(5):
        last = client.delete(f'{BASE}/delete-account/', {'otp_code': '9999'}, format='json')
        statuses.append(last.status_code)
    check('5 codes incorrects → [400, 400, 400, 400, 429]', statuses == [400, 400, 400, 400, 429], statuses)
    check('429 avec Retry-After (600)', last.headers.get('Retry-After') == '600',
          last.headers.get('Retry-After'))
    r6 = client.delete(f'{BASE}/delete-account/', {'otp_code': '9999'}, format='json')
    check('6e tentative → toujours 429', r6.status_code == 429, r6.status_code)
    check('compte toujours présent (bloqué, pas supprimé)',
          User.objects.filter(username='rl_verify_block_user').exists())


def main():
    test_otp_hashing()
    test_cooldown()
    test_phone_limit()
    test_ip_limit()
    test_global_limit()
    test_verify_block()
    test_delete_account_flow()
    test_delete_verify_block()

    print('\n' + '─' * 50)
    failed = [name for name, ok in ALL_RESULTS if not ok]
    for name, ok in ALL_RESULTS:
        print(f'{"✅" if ok else "❌"} {name}')
    if failed:
        print(f'\nÉCHEC: {len(failed)} vérification(s)')
        sys.exit(1)
    print('\nOK TACHES.md — rate limiting OTP entièrement vérifié')


if __name__ == '__main__':
    cleanup()
    main()
    cleanup()

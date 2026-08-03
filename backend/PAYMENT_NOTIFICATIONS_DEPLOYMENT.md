# Déploiement — Notifications de Paiement et Abonnement

## 📋 Fichiers à mettre à jour en production

### 1. **Backend Django**

#### Fichiers modifiés
- `notifications/tasks.py` — Ajout de 4 nouvelles tâches Celery
- `payments/apps.py` — Enregistrement des signaux
- `payments/signals.py` — **NOUVEAU** — Signaux pour déclencher les notifications

#### Fichiers créés
- `notifications/periodic_tasks.py` — **NOUVEAU** — Tâches périodiques Celery Beat
- `notifications/test_payment_notifications.py` — **NOUVEAU** — Tests unitaires

### 2. **Configuration Celery**

Ajouter à `resume_backend/celery.py` ou `settings.py` :

```python
# Celery Beat Schedule (pour les tâches périodiques)
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'check-subscriptions-expiring-soon': {
        'task': 'notifications.periodic_tasks.check_subscriptions_expiring_soon',
        'schedule': crontab(hour=9, minute=0),  # Chaque jour à 9h
    },
    'check-subscriptions-expired': {
        'task': 'notifications.periodic_tasks.check_subscriptions_expired',
        'schedule': crontab(hour=10, minute=0),  # Chaque jour à 10h
    },
}
```

---

## 🚀 Commandes de déploiement

### 1. **Appliquer les migrations** (si nécessaire)

```bash
python manage.py migrate
```

*Note: Aucune nouvelle migration requise — les modèles existants suffisent.*

### 2. **Collecte des fichiers statiques**

```bash
python manage.py collectstatic --noinput
```

### 3. **Redémarrer les services**

```bash
# Redémarrer Celery Worker
sudo systemctl restart celery

# Redémarrer Celery Beat (si utilisé)
sudo systemctl restart celery-beat

# Redémarrer Django (Gunicorn/uWSGI)
sudo systemctl restart gunicorn
# ou
sudo systemctl restart uwsgi
```

### 4. **Vérifier les logs**

```bash
# Logs Celery
sudo journalctl -u celery -f

# Logs Django
tail -f /var/log/django/error.log
```

---

## 🔧 Configuration Celery Beat (optionnel mais recommandé)

### Installation de Celery Beat

```bash
pip install django-celery-beat
```

### Configuration Django

Ajouter à `INSTALLED_APPS` dans `settings.py` :

```python
INSTALLED_APPS = [
    # ...
    'django_celery_beat',
]
```

### Créer la base de données pour Celery Beat

```bash
python manage.py migrate django_celery_beat
```

### Démarrer Celery Beat

```bash
celery -A resume_backend beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

---

## 📊 Flux de notification

### 1. **Abonnement payé** (Subscription Paid)

```
User paie abonnement
    ↓
Purchase.status = 'completed'
    ↓
Signal: post_save(Purchase)
    ↓
Celery: notify_subscription_paid()
    ↓
AppNotification créée
    ↓
UserNotification créée
    ↓
FCM envoyé
    ↓
User reçoit push: "✅ Abonnement activé"
```

### 2. **Abonnement expire bientôt** (Expiring Soon)

```
Celery Beat: check_subscriptions_expiring_soon() [quotidien à 9h]
    ↓
Trouve abonnements expirant dans 7 jours
    ↓
Pour chaque abonnement:
    Celery: notify_subscription_expiring_soon()
    ↓
    AppNotification créée
    ↓
    UserNotification créée
    ↓
    FCM envoyé
    ↓
    User reçoit push: "⏰ Abonnement expire bientôt"
```

### 3. **Abonnement expiré** (Expired)

```
Celery Beat: check_subscriptions_expired() [quotidien à 10h]
    ↓
Trouve abonnements expirés
    ↓
Pour chaque abonnement:
    Status = 'expired'
    ↓
    Celery: notify_subscription_expired()
    ↓
    AppNotification créée
    ↓
    UserNotification créée
    ↓
    FCM envoyé
    ↓
    User reçoit push: "❌ Abonnement expiré"
```

### 4. **Résumé acheté** (Summary Purchase)

```
User achète résumé
    ↓
Purchase.status = 'completed'
    ↓
Signal: post_save(Purchase)
    ↓
Celery: notify_summary_purchased()
    ↓
AppNotification créée
    ↓
UserNotification créée
    ↓
FCM envoyé
    ↓
User reçoit push: "📥 Résumé acheté"
```

---

## 🧪 Tests

### Exécuter les tests

```bash
# Tests de notifications de paiement
python manage.py test notifications.test_payment_notifications

# Tous les tests de notifications
python manage.py test notifications

# Tests avec couverture
coverage run --source='notifications' manage.py test notifications
coverage report
```

### Résultats attendus

```
test_subscription_paid_notification ... ok
test_subscription_expiring_soon_notification ... ok
test_subscription_expired_notification ... ok
test_multiple_subscriptions_notifications ... ok
test_summary_purchase_notification ... ok
test_multiple_purchases_notifications ... ok
test_purchase_without_summary ... ok

Ran 7 tests in 0.234s
OK
```

---

## 🔍 Vérification en production

### 1. **Vérifier que les signaux sont enregistrés**

```bash
python manage.py shell
>>> from django.db.models.signals import post_save
>>> from payments.models import Abonnement
>>> from django.dispatch import receiver
>>> # Les signaux doivent être enregistrés
>>> # Vérifier dans les logs
```

### 2. **Vérifier que Celery fonctionne**

```bash
# Envoyer une tâche de test
python manage.py shell
>>> from notifications.tasks import send_fcm_notification
>>> send_fcm_notification.apply_async(args=[[1]], countdown=1)
# Vérifier dans les logs Celery que la tâche est exécutée
```

### 3. **Vérifier que Celery Beat fonctionne**

```bash
# Vérifier les tâches planifiées
python manage.py shell
>>> from django_celery_beat.models import PeriodicTask
>>> PeriodicTask.objects.all()
# Doit afficher les 2 tâches périodiques
```

---

## 🚨 Dépannage

### Problème: Les notifications ne sont pas envoyées

**Cause possible**: Celery Worker n'est pas en cours d'exécution

```bash
# Vérifier l'état de Celery
sudo systemctl status celery

# Redémarrer Celery
sudo systemctl restart celery

# Vérifier les logs
sudo journalctl -u celery -f
```

### Problème: Les tâches périodiques ne s'exécutent pas

**Cause possible**: Celery Beat n'est pas en cours d'exécution

```bash
# Vérifier l'état de Celery Beat
sudo systemctl status celery-beat

# Redémarrer Celery Beat
sudo systemctl restart celery-beat

# Vérifier les logs
sudo journalctl -u celery-beat -f
```

### Problème: Les signaux ne sont pas déclenchés

**Cause possible**: Les signaux ne sont pas enregistrés

```bash
# Vérifier que payments.apps.PaymentsConfig.ready() est appelé
python manage.py shell
>>> from payments import signals  # Doit importer sans erreur
```

---

## 📝 Résumé des changements

| Fichier | Type | Description |
|---------|------|---|
| `notifications/tasks.py` | Modifié | +4 tâches (notify_subscription_paid, notify_subscription_expiring_soon, notify_subscription_expired, notify_summary_purchased) |
| `payments/apps.py` | Modifié | Ajout de `ready()` pour enregistrer les signaux |
| `payments/signals.py` | Créé | Signaux pour Abonnement et Purchase |
| `notifications/periodic_tasks.py` | Créé | Tâches Celery Beat pour vérifier les expirations |
| `notifications/test_payment_notifications.py` | Créé | Tests unitaires complets |

---

## ✅ Checklist de déploiement

- [ ] Fichiers modifiés copiés en production
- [ ] Fichiers créés copiés en production
- [ ] Migrations appliquées (`python manage.py migrate`)
- [ ] Celery Worker redémarré
- [ ] Celery Beat configuré et démarré (optionnel)
- [ ] Tests exécutés et passants
- [ ] Logs vérifiés (pas d'erreurs)
- [ ] Notification de test envoyée et reçue
- [ ] Abonnement de test créé et notification reçue
- [ ] Achat de test créé et notification reçue

---

## 🎯 Points clés

✅ **Aucune migration requise** — Les modèles existants suffisent
✅ **Signaux automatiques** — Les notifications sont déclenchées automatiquement
✅ **Tâches périodiques** — Vérification quotidienne des expirations
✅ **Tests complets** — 7 tests unitaires couvrent tous les cas
✅ **Logs détaillés** — Chaque notification est loggée
✅ **Pas de casse** — Aucun changement à la logique existante

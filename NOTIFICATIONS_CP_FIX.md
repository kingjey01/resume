# Correction — CP reçoit ses propres notifications

## 🔧 Problème identifié

Le CP (Chef de Promotion) était exclu des notifications de :
1. **Validation de résumé** — Notification "📚 Nouveau résumé disponible"
2. **Abonnement payé** — Notification "✅ Abonnement activé"
3. **Abonnement expire bientôt** — Notification "⏰ Abonnement expire bientôt"
4. **Abonnement expiré** — Notification "❌ Abonnement expiré"

### Cause
- `sender_id` était passé aux notifications de validation → exclusion du sender
- Les notifications d'abonnement créaient directement une notification pour l'utilisateur au lieu de passer par `create_and_send_notification()` qui respecte la logique de ciblage

---

## ✅ Corrections apportées

### 1. Validation de résumé (`courses/views.py:1336-1350`)

**Avant :**
```python
create_and_send_notification.apply_async(kwargs={
    ...
    'sender_id': request.user.id,  # ❌ Excluait le CP
}, countdown=3)
```

**Après :**
```python
create_and_send_notification.apply_async(kwargs={
    'title': '📚 Nouveau résumé disponible',
    'body': f'Le résumé « {summary.titre} » du cours {course.nom} est maintenant disponible.',
    'notification_type': 'summary_validated',
    'universite_id': course.universite_fk_id,
    'filiere_id': course.filiere_fk_id,
    'promotion_id': course.promotion_fk_id,
    'summary_id': summary.id,
    'course_id': course.id,
    # ✅ Pas de sender_id → CP inclus
}, countdown=3)
```

### 2. Notifications d'abonnement (`notifications/tasks.py`)

**Avant :**
```python
# Créait directement une notification pour l'utilisateur
notif = AppNotification.objects.create(...)
un, _ = UserNotification.objects.get_or_create(user=user, notification=notif)
send_fcm_notification.apply_async(args=[[un.id]], countdown=1)
```

**Après :**
```python
# Utilise create_and_send_notification pour respecter la logique de ciblage
profile = UserProfile.objects.get(user=user)
create_and_send_notification.apply_async(
    kwargs={
        'title': '✅ Abonnement activé',
        'body': f'Votre abonnement {service.nom} est maintenant actif...',
        'notification_type': 'payment',
        'universite_id': profile.universite_id,  # ✅ Ciblage par université
        'filiere_id': profile.filiere_id,        # ✅ Ciblage par filière
        'promotion_id': profile.promotion_id,    # ✅ Ciblage par promotion
    },
    countdown=1
)
```

**Tâches modifiées :**
- `notify_subscription_paid()` — Abonnement payé
- `notify_subscription_expiring_soon()` — Abonnement expire bientôt
- `notify_subscription_expired()` — Abonnement expiré

### 3. ALLOWED_HOSTS (`resume_backend/settings.py:20-29`)

**Ajout du domaine manquant :**
```python
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '0.0.0.0',
    'resumecours.gestionhospitaliare.site',
    'www.resumecours.gestionhospitaliare.site',
    'ftp.clavierplus.com',  # ✅ Domaine alternatif ajouté
    '180.149.197.29',
]
```

---

## 📋 Logique de ciblage

Avec `create_and_send_notification()`, les notifications sont envoyées à :

| Filtre | Destinataires |
|--------|---|
| `universite_id` uniquement | Tous les utilisateurs de l'université (y compris CP) |
| `universite_id` + `filiere_id` | Tous les utilisateurs de l'université + filière (y compris CP) |
| `universite_id` + `filiere_id` + `promotion_id` | Uniquement le groupe exact (y compris CP) |

**Point clé :** Aucun `sender_id` n'est passé → le CP reçoit ses propres notifications.

---

## 🚀 Déploiement

```bash
# 1. Redémarrer Celery Worker
sudo systemctl restart celery

# 2. Redémarrer Django
sudo systemctl restart gunicorn

# 3. Vérifier les logs
sudo journalctl -u celery -f
```

---

## ✅ Vérification

Après déploiement, vérifier que :
1. ✅ CP reçoit la notification "📚 Nouveau résumé disponible" lors de la validation
2. ✅ CP reçoit la notification "✅ Abonnement activé" lors d'un paiement réussi
3. ✅ CP reçoit la notification "⏰ Abonnement expire bientôt" 7 jours avant expiration
4. ✅ CP reçoit la notification "❌ Abonnement expiré" après expiration
5. ✅ Pas d'erreur `DisallowedHost` pour `ftp.clavierplus.com`

---

## 📁 Fichiers modifiés

- `backend/courses/views.py` — Suppression de `sender_id` ligne 1350
- `backend/notifications/tasks.py` — Refactorisation de 3 tâches (notify_subscription_paid, notify_subscription_expiring_soon, notify_subscription_expired)
- `backend/resume_backend/settings.py` — Ajout de `ftp.clavierplus.com` à ALLOWED_HOSTS

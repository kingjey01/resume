# Système de Notifications — Logique Métier

## Vue d'ensemble

Le système de notifications supporte deux sources :

1. **Notifications automatiques** : créées par les CP lors de la validation d'un résumé
2. **Notifications manuelles** : créées par les administrateurs

---

## Logique de Ciblage

Une notification est ciblée selon les filtres renseignés. La hiérarchie est stricte :

### Cas 1 : Aucun filtre (Global)

```
universite_id = null
filiere_id = null
promotion_id = null
```

→ **Envoyer à TOUS les utilisateurs actifs**

### Cas 2 : Université uniquement

```
universite_id = 123
filiere_id = null
promotion_id = null
```

→ **Envoyer à tous les utilisateurs de l'université 123**

### Cas 3 : Université + Filière

```
universite_id = 123
filiere_id = 45
promotion_id = null
```

→ **Envoyer à tous les utilisateurs de l'université 123 ET filière 45**

### Cas 4 : Université + Filière + Promotion (Exact)

```
universite_id = 123
filiere_id = 45
promotion_id = 6
```

→ **Envoyer UNIQUEMENT aux utilisateurs de l'université 123, filière 45, promotion 6**

---

## Logique CP (Automatique)

Quand un CP **valide un résumé** :

1. Le système détecte le changement `is_validated: False → True`
2. Une notification est créée automatiquement avec :
   - `target_universite` = université du cours
   - `target_filiere` = filière du cours
   - `target_promotion` = promotion du cours
   - `notification_type` = `'summary_validated'`
   - `sender_id` = ID du CP

3. **Destinataires** = tous les utilisateurs correspondant à cette université + filière + promotion
4. **Le CP REÇOIT sa propre notification** (pas d'exclusion)

### Exemple

```
CP valide un résumé du cours "Mathématiques L2 Informatique UNIKIN"
↓
Notification créée avec :
  - target_universite = UNIKIN
  - target_filiere = Informatique
  - target_promotion = L2
↓
Destinataires = tous les L2 Informatique UNIKIN (y compris le CP)
```

---

## Logique Admin (Manuelle)

L'administrateur peut créer une notification via l'endpoint `/notifications/admin/create/`.

### Endpoint

```
POST /api/notifications/admin/create/
```

### Payload

```json
{
  "title": "Maintenance prévue",
  "body": "Le serveur sera en maintenance ce soir.",
  "notification_type": "system",
  "universite_id": null,
  "filiere_id": null,
  "promotion_id": null,
  "image_url": "https://..."
}
```

### Validation

- `title` et `body` sont **obligatoires**
- Si `filiere_id` est renseigné → `universite_id` est **requis**
- Si `promotion_id` est renseigné → `universite_id` ET `filiere_id` sont **requis**

### Exemples d'utilisation

#### 1. Notification globale

```json
{
  "title": "Maintenance",
  "body": "Serveur en maintenance",
  "notification_type": "system",
  "universite_id": null,
  "filiere_id": null,
  "promotion_id": null
}
```

→ **Tous les utilisateurs** reçoivent la notification

#### 2. Notification par université

```json
{
  "title": "Annonce UNIKIN",
  "body": "Réunion obligatoire",
  "notification_type": "promo",
  "universite_id": 1,
  "filiere_id": null,
  "promotion_id": null
}
```

→ **Tous les utilisateurs UNIKIN** reçoivent la notification

#### 3. Notification par université + filière

```json
{
  "title": "Annonce Informatique",
  "body": "Changement d'horaire",
  "notification_type": "promo",
  "universite_id": 1,
  "filiere_id": 5,
  "promotion_id": null
}
```

→ **Tous les utilisateurs UNIKIN Informatique** reçoivent la notification

#### 4. Notification précise (groupe exact)

```json
{
  "title": "Annonce L2 Informatique",
  "body": "Examen reporté",
  "notification_type": "promo",
  "universite_id": 1,
  "filiere_id": 5,
  "promotion_id": 3
}
```

→ **UNIQUEMENT les L2 Informatique UNIKIN** reçoivent la notification

---

## Implémentation Technique

### Modèles

**AppNotification** (notification générale)
```python
- title: str
- body: str
- notification_type: str
- target_universite: ForeignKey (nullable)
- target_filiere: ForeignKey (nullable)
- target_promotion: ForeignKey (nullable)
- sender: ForeignKey (nullable)
- summary_id: int (nullable)
- course_id: int (nullable)
```

**UserNotification** (statut par utilisateur)
```python
- user: ForeignKey
- notification: ForeignKey
- is_read: bool
- read_at: datetime (nullable)
- delivered: bool
```

### Tâche Celery : `create_and_send_notification`

```python
create_and_send_notification.apply_async(kwargs={
    'title': str,
    'body': str,
    'notification_type': str,
    'universite_id': int | None,
    'filiere_id': int | None,
    'promotion_id': int | None,
    'summary_id': int | None,
    'course_id': int | None,
    'sender_id': int | None,
    'image_url': str | None,
})
```

**Logique interne** :

1. Crée `AppNotification` avec les filtres fournis
2. Détermine les utilisateurs ciblés selon la hiérarchie
3. Crée `UserNotification` pour chaque utilisateur ciblé
4. Envoie les push FCM en batches de 100

### Tâche Celery : `send_fcm_notification`

Envoie les push FCM via Firebase Cloud Messaging.

- Batch jusqu'à 500 tokens par appel FCM
- Détecte et supprime les tokens invalides automatiquement
- Retry jusqu'à 3 fois en cas d'erreur

---

## Points Clés

| Aspect | Détail |
|--------|--------|
| **CP reçoit sa propre notification** | ✅ Inclus (pas d'exclusion) |
| **Hiérarchie stricte** | ✅ filiere requiert universite, promotion requiert universite + filiere |
| **Envoi massif** | ✅ Pas de sélection individuelle requise |
| **Validation** | ✅ Erreurs claires si hiérarchie non respectée |
| **Nettoyage tokens** | ✅ Automatique lors de l'envoi FCM |
| **Admin uniquement** | ✅ Vérification `is_staff` ou `is_superuser` |

---

## Flux Complet : Validation d'un Résumé

```
1. CP valide un résumé
   ↓
2. Signal déclenche create_and_send_notification
   ↓
3. AppNotification créée avec target_universite, target_filiere, target_promotion
   ↓
4. Celery détermine les utilisateurs ciblés
   ↓
5. UserNotification créée pour chaque utilisateur
   ↓
6. send_fcm_notification envoyé en batches
   ↓
7. Firebase envoie les push
   ↓
8. Utilisateurs reçoivent la notification
```

---

## Flux Complet : Notification Admin

```
1. Admin appelle POST /notifications/admin/create/
   ↓
2. Validation des filtres (hiérarchie)
   ↓
3. create_and_send_notification planifiée
   ↓
4. AppNotification créée
   ↓
5. Utilisateurs ciblés déterminés
   ↓
6. UserNotification créée pour chaque utilisateur
   ↓
7. send_fcm_notification envoyé en batches
   ↓
8. Firebase envoie les push
   ↓
9. Utilisateurs reçoivent la notification
```

---

## Erreurs Courantes

### ❌ filiere_id sans universite_id

```json
{
  "universite_id": null,
  "filiere_id": 5
}
```

→ **Erreur 400** : `filiere_id requiert universite_id`

### ❌ promotion_id sans universite_id + filiere_id

```json
{
  "universite_id": 1,
  "filiere_id": null,
  "promotion_id": 3
}
```

→ **Erreur 400** : `promotion_id requiert universite_id et filiere_id`

### ✅ Correct

```json
{
  "universite_id": 1,
  "filiere_id": 5,
  "promotion_id": 3
}
```

→ **Succès** : Notification envoyée au groupe exact

---

## Permissions

- **CP** : Peut créer des notifications automatiques (via validation de résumé)
- **Admin/Superuser** : Peut créer des notifications manuelles via `/notifications/admin/create/`
- **Utilisateur normal** : Peut lire ses notifications et les marquer comme lues

---

## À Retenir

> **Logique simple, cohérente, prévisible**
>
> - CP → uniquement son audience académique
> - Admin sans filtre → tout le monde
> - Admin avec filtres → uniquement le segment correspondant
> - Aucune ambiguïté sur les destinataires

# Implémentation — Notifications d'Échec et Validation de Prix

## 📋 Résumé des changements

### 1. Notifications d'Échec (Backend)

**Fichier modifié:** `backend/notifications/tasks.py`

Deux nouvelles tâches Celery ajoutées :

#### `notify_subscription_payment_failed(abonnement_id, error_reason)`
- Déclenché quand un paiement d'abonnement échoue
- Notifie l'utilisateur : "❌ Paiement échoué"
- Message : "Votre paiement pour l'abonnement {service} a échoué. {error_reason} Veuillez réessayer."

#### `notify_summary_purchase_failed(purchase_id, error_reason)`
- Déclenché quand un achat de résumé échoue
- Notifie l'utilisateur : "❌ Achat échoué"
- Message : "Votre achat du résumé « {titre} » a échoué. {error_reason} Veuillez réessayer."

**Utilisation :**
```python
from notifications.tasks import notify_subscription_payment_failed, notify_summary_purchase_failed

# En cas d'échec de paiement
notify_subscription_payment_failed.apply_async(
    args=[abonnement.id, "Carte bancaire refusée"],
    countdown=2
)

# En cas d'échec d'achat
notify_summary_purchase_failed.apply_async(
    args=[purchase.id, "Solde insuffisant"],
    countdown=2
)
```

---

### 2. Validation Prix — Enregistrement Audio

#### Côté Flutter (`lib/features/upload/screens/record_audio_screen.dart`)

**Changements :**
- Champ prix rendu obligatoire
- Validation : prix minimum 3000 CDF
- Helper text : "Le prix minimum est 3000 CDF. Les résumés gratuits ne sont pas autorisés."
- Formulaire ne peut pas être envoyé si prix < 3000

**Code :**
```dart
TextFormField(
  controller: _priceController,
  decoration: InputDecoration(
    labelText: 'Prix du résumé (CDF) *',
    hintText: 'Minimum 3000 CDF',
    helperText: 'Le prix minimum est 3000 CDF. Les résumés gratuits ne sont pas autorisés.',
    helperMaxLines: 2,
  ),
  validator: (value) {
    final price = double.tryParse(value) ?? 0.0;
    if (price < 3000) {
      return 'Le prix minimum est 3000 CDF';
    }
    return null;
  },
)
```

#### Côté Backend (`backend/courses/views.py` - `create_session`)

**Changements :**
- Validation du prix minimum 3000 CDF
- Si prix < 3000 → remplacé automatiquement par 3000
- Log warning : "⚠️ Prix {price} inférieur à 3000 CDF — remplacé par 3000"

**Code :**
```python
# Valider le prix (minimum 3000 CDF)
price = float(summary_price)
if price < 3000:
    logger.warning(f'⚠️ Prix {price} inférieur à 3000 CDF — remplacé par 3000')
    price = 3000
```

---

### 3. Validation Prix — Modification Résumé

#### Côté Flutter (`lib/features/validation/screens/edit_summary_screen.dart`)

**Changements :**
- ✅ Suppression du switch "Gratuit" (is_free)
- ✅ Champ prix rendu obligatoire
- ✅ Validation : prix minimum 3000 CDF
- ✅ Helper text : "Le prix minimum est 3000 CDF. Aucun résumé ne peut être gratuit."
- ✅ Validation dans `_saveSummary()` : refuse si prix < 3000

**Code :**
```dart
// Validation avant sauvegarde
final price = double.tryParse(_prixController.text) ?? 0.0;
if (price < 3000) {
  ScaffoldMessenger.of(context).showSnackBar(
    const SnackBar(content: Text('Le prix minimum est 3000 CDF')),
  );
  return;
}

// Envoi avec is_free = false (jamais gratuit)
final data = {
  'titre': _titreController.text.trim(),
  'texte_resume': _texteController.text.trim(),
  'prix': price,
  'is_free': false,  // Toujours false
};
```

#### Côté Backend (`backend/courses/views.py` - `edit_summary`)

**Changements :**
- ✅ Validation du prix minimum 3000 CDF
- ✅ Si prix < 3000 → remplacé automatiquement par 3000
- ✅ Suppression de la possibilité de mettre `is_free = true`
- ✅ Force `is_free = false` toujours

**Code :**
```python
if 'prix' in request.data:
    price = float(request.data['prix'])
    if price < 3000:
        logger.warning(f'⚠️ Prix {price} inférieur à 3000 CDF — remplacé par 3000')
        price = 3000
    summary.prix = price

# Aucun résumé ne peut être gratuit
summary.is_free = False
```

---

## 📁 Fichiers modifiés

| Fichier | Type | Changements |
|---------|------|-------------|
| `backend/notifications/tasks.py` | Python | +2 tâches (notify_subscription_payment_failed, notify_summary_purchase_failed) |
| `lib/features/upload/screens/record_audio_screen.dart` | Dart | Validation prix min 3000 + helper text |
| `backend/courses/views.py` (create_session) | Python | Validation prix min 3000 + remplacement auto |
| `lib/features/validation/screens/edit_summary_screen.dart` | Dart | Suppression switch gratuit + validation prix |
| `backend/courses/views.py` (edit_summary) | Python | Validation prix min 3000 + force is_free=false |

---

## 🚀 Déploiement

### Commandes

```bash
# 1. Redémarrer Celery Worker
sudo systemctl restart celery

# 2. Redémarrer Django
sudo systemctl restart gunicorn

# 3. (Optionnel) Vérifier les logs
sudo journalctl -u celery -f
```

### Aucune migration requise
- Les modèles existants suffisent
- Pas de changement de structure de base de données

---

## ✅ Points clés

✅ **Notifications d'échec** — Utilisateurs notifiés en cas d'échec de paiement/achat
✅ **Prix minimum 3000 CDF** — Appliqué côté Flutter (validation) et backend (remplacement)
✅ **Pas de résumés gratuits** — Switch "Gratuit" supprimé, is_free toujours false
✅ **Helper text** — Utilisateurs informés du prix minimum
✅ **Logs détaillés** — Chaque remplacement de prix est loggé
✅ **Pas de casse** — Aucun changement à la logique existante

---

## 🧪 Tests

### Tests manuels recommandés

1. **Enregistrement audio**
   - Essayer prix < 3000 → formulaire refuse
   - Essayer prix >= 3000 → formulaire accepte
   - Vérifier helper text visible

2. **Modification résumé**
   - Vérifier que switch "Gratuit" est supprimé
   - Essayer prix < 3000 → erreur snackbar
   - Essayer prix >= 3000 → sauvegarde réussit

3. **Backend**
   - Envoyer prix < 3000 via API → remplacé par 3000 (vérifier logs)
   - Envoyer is_free=true → forcé à false

4. **Notifications d'échec**
   - Déclencher manuellement une notification d'échec
   - Vérifier que l'utilisateur reçoit la notification push

---

## 📝 Notes

- Le prix minimum 3000 CDF est appliqué **deux fois** : côté Flutter (validation) et backend (remplacement)
- Cela garantit que même si quelqu'un contourne la validation Flutter, le backend corrigera le prix
- Les logs warning permettent de tracker les tentatives de contournement

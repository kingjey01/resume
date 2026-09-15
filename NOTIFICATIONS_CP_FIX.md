 Transcription réussie: 725 caractères
[2026-08-29 15:33:47,962: WARNING/ForkPoolWorker-4] ✅ Transcription Deepgram réussie (confiance: 96.78%)
[2026-08-29 15:33:47,962: INFO/ForkPoolWorker-4] ✅ Transcription Deepgram réussie (confiance: 96.78%)
[2026-08-29 15:33:47,967: INFO/ForkPoolWorker-4] ✅ [Celery] Étape 1/2 terminée: Transcription #40
[2026-08-29 15:33:47,967: INFO/ForkPoolWorker-4] 📝 [Celery] Étape 2/2 : Résumé session 42...
[2026-08-29 15:33:47,967: INFO/ForkPoolWorker-4] 🔍 DIAGNOSTIC - Début étape 2 génération résumé
[2026-08-29 15:33:47,967: INFO/ForkPoolWorker-4] 🔍 Transcription ID: 40
[2026-08-29 15:33:47,967: INFO/ForkPoolWorker-4] 🔍 Transcription created_at: 2026-08-29 15:33:46.660429
[2026-08-29 15:33:47,968: INFO/ForkPoolWorker-4] 🔍 Session ID: 42
[2026-08-29 15:33:47,968: INFO/ForkPoolWorker-4] 🔍 Session date: 2026-08-29 15:33:46.553794
[2026-08-29 15:33:47,968: INFO/ForkPoolWorker-4] 🔍 Author user: YETA6
[2026-08-29 15:33:47,974: INFO/ForkPoolWorker-4] 🤖 Génération du résumé via DeepSeek API...
[2026-08-29 15:34:13,034: INFO/ForkPoolWorker-4] Tokens: 5521
[2026-08-29 15:34:13,039: INFO/ForkPoolWorker-4] ✅ Résumé DeepSeek généré avec succès
[2026-08-29 15:34:13,039: INFO/ForkPoolWorker-4] 🔍 Création Summary avec:
[2026-08-29 15:34:13,039: INFO/ForkPoolWorker-4] 🔍   - titre: variables
[2026-08-29 15:34:13,044: INFO/ForkPoolWorker-4] 🔍   - course: Python - INFORMATIQUE (UCC)
[2026-08-29 15:34:13,045: INFO/ForkPoolWorker-4] 🔍   - session: Python - 29/08/2026
[2026-08-29 15:34:13,045: INFO/ForkPoolWorker-4] 🔍   - transcription: Transcription - Python - 29/08/2026 (completed)
[2026-08-29 15:34:13,045: INFO/ForkPoolWorker-4] 🔍   - author_user: YETA6
[2026-08-29 15:34:13,053: INFO/ForkPoolWorker-4] 🔍 Summary créé: ID=45, created_at=2026-08-29 15:34:13.049171
[2026-08-29 15:34:13,056: INFO/ForkPoolWorker-4] ✅ [Celery] Session 42 terminée — Transcription #40, Résumé #45
[2026-08-29 15:34:13,057: INFO/ForkPoolWorker-4] Task courses.tasks.process_audio_session_task[c86f2081-535d-4ac0-b196-1dcf72bb8c89] succeeded in 26.45073343720287s: {'success': True, 'session_id': 42, 'summary_id': 45, 'transcription_id': 40}
## PROBLÈME 1 — La file d'attente audio ne détecte pas les changements de statut en temps réel

Dans l'onglet **File d'attente audio** (icône microphone), l'état affiché ne se met pas automatiquement à jour lorsque le traitement d'une session évolue.

Exemple :

**Transcription en cours → Transcrit → Résumé disponible**

Le backend change correctement le statut, mais la file d'attente Flutter conserve l'ancien état jusqu'à ce que l'utilisateur fasse manuellement un rafraîchissement de la page.

### Travail demandé

Analyser comment la file d'attente récupère actuellement les sessions et comment le state est mis à jour.

Identifier pourquoi les changements de statut provenant du backend ne sont pas propagés automatiquement à l'interface.

Corriger uniquement la gestion du state/rafraîchissement afin que la file d'attente reflète automatiquement le nouveau statut.

Lorsqu'un statut change :

* la progression doit se mettre à jour automatiquement ;
* la barre de progression doit évoluer jusqu'à son état final ;
* lorsque le traitement est terminé, afficher immédiatement l'état correspondant (par exemple terminé/vert) ;
* l'utilisateur ne doit pas avoir besoin de quitter l'écran ou de faire un refresh manuel.

Utiliser le mécanisme de mise à jour déjà présent dans l'application lorsqu'il existe, plutôt que de dupliquer la logique.

Ne pas modifier le workflow backend de transcription/génération si celui-ci fonctionne correctement.

---

## PROBLÈME 2 — Notification « Résumé créé » absente et badge de notification non incrémenté

Lorsqu'un résumé est créé avec succès, le **badge de validation** s'incrémente correctement : le système détecte donc bien qu'un nouveau résumé doit être validé.

Cependant, la notification correspondante n'est pas envoyée au CP.

Conséquence :

* le badge **Validation** s'incrémente ;
* aucune notification « Résumé créé » n'est reçue ;
* le badge de l'icône **Notifications** ne s'incrémente pas.

### Travail demandé

Analyser le workflow exact lorsqu'un résumé est créé :

**Résumé généré → Résumé enregistré → statut Résumé créé → déclenchement notification → réception → incrément du badge Notifications**

Comparer ce workflow avec celui utilisé pour les validations, puisque le badge Validation fonctionne correctement.

Vérifier notamment :

* si la tâche Celery/worker de notification existe ;
* si elle est réellement appelée après la création du résumé ;
* si elle reçoit le bon utilisateur/CP destinataire ;
* si la notification est correctement enregistrée ;
* si le système de badge Notifications écoute correctement ce type de notification.

Corriger le workflow afin que, dès qu'un résumé est créé :

1. une notification soit créée et envoyée au CP concerné ;
2. cette notification apparaisse dans l'onglet Notifications ;
3. le compteur/badge Notifications soit immédiatement incrémenté ;
4. le badge Validation continue également de fonctionner comme actuellement.

Ne pas modifier le mécanisme de validation qui fonctionne déjà. Utiliser son fonctionnement comme référence pour identifier pourquoi le workflow de notification « Résumé créé » ne fonctionne pas.

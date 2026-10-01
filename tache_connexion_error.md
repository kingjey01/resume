## UPLOAD AUDIO — ERREUR « CONNEXION EXPIRÉE »

Analyser le problème d'upload audio depuis un fichier présent sur le téléphone, **sans modifier ni casser la logique actuelle d'enregistrement audio qui fonctionne déjà en production**.

### Problème constaté

* Enregistrement audio directement depuis l'application → fonctionne correctement.
* Soumission de l'enregistrement → upload vers le backend et sauvegarde en base → fonctionne.
* Upload d'un fichier audio existant depuis le téléphone → le fichier semble être sélectionné/uploadé correctement.
* Lors de la soumission → erreur **« Erreur d'upload / delai de Connexion expirée / Vérifiez votre connexion »**, alors que la connexion Internet fonctionne.

Le problème apparaît notamment avec un fichier d'environ **1 heure**, donc vérifier la gestion des fichiers longs, jusqu'à la limite métier actuelle de **3 heures**.

### Vérifications demandées

Analyser toute la chaîne :

**Flutter → sélection du fichier → préparation du fichier → requête HTTP → upload → Django/backend → stockage → création de la Session → traitement Celery**

Comparer cette chaîne avec celle utilisée par l'enregistrement audio natif qui fonctionne actuellement afin d'identifier précisément la différence.

Vérifier notamment :

* timeout Flutter/HTTP ;
* timeout côté serveur ;
* limite de taille des requêtes ;
* `multipart/form-data` ;
* configuration Django ;
* configuration Apache/Nginx/proxy si présente ;
* limite d'upload du serveur ;
* gestion des fichiers volumineux ;
* durée maximale d'une requête ;
* traitement et stockage du fichier ;
* différence entre fichier enregistré localement par l'application et fichier sélectionné depuis le téléphone.

### Limite métier

Un audio pouvant atteindre **3 heures** doit être correctement supporté.

Ne pas simplement augmenter arbitrairement les timeouts ou les limites sans identifier la cause réelle.

Vérifier que **l'enregistrement natif et l'upload d'un fichier existant utilisent des paramètres et une logique compatibles** avec cette limite.

### Correction attendue

Corriger uniquement la chaîne d'upload des fichiers existants afin qu'un fichier audio valide puisse être soumis correctement, y compris pour des fichiers longs.

Après correction :

* le fichier doit être envoyé correctement au backend ;
* la `Session` doit être créée comme actuellement ;
* le fichier doit être conservé ;
* le traitement/transcription Celery doit continuer à fonctionner avec la logique existante ;
* aucune régression ne doit être introduite sur l'enregistrement audio natif.

**Avant toute modification, analyser le code existant et identifier précisément pourquoi l'enregistrement natif fonctionne alors que l'upload d'un fichier existant échoue.**

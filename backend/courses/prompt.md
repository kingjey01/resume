 1) TÂCHE PRINCIPALE : SÉPARATION ENREGISTREMENT SESSIONS ET TRANSCRIPTION POUR LA GENERATION DU RESUME INTELLIGRNTE.

- ### 1.1 Modification de la soumission de session
- Supprimer TOUT appel à l'API de transcription ou de résumé dans la fonction  d'enregistrement audio/session.
- La fonction doit UNIQUEMENT :
  a. Uploader le fichier audio vers le stockage.
  b. Insérer l'entrée dans la table sessions avec le champ statut = "EN_ATTENTE".
  c. Rafraîchir la liste des sessions apres sa soumission ou l'envoi(upload) effectuée en base de donnée.
  d. envoyer le message de succès à l'utilisatur si oui le stokage de la sessions a réussie et enregistrer en base des données 
- Aucun appel à  deepgram ou deepseek

- #### 1.2 Création du service de transcription manuelle si pas existant
- Logique interne de cette méthode :
  a. Appeler le backend  avec l'ID de la session.
  b. Le backend récupère l'URL audio, pour éffectuer l'opération de la transcription et du résumé intélligent.
  c. Le backend met à jour la DB : transcription, resume, statut de la session...
  d. Retourner une confirmation simple : { "success": true }.

 

- ### 1.3 Sénario UI
Enregistrement : Audio -> Upload -> DB (statut = EN_ATTENTE) -> réinitialisation de l'interface d'eregistrement(refresh).
Transcription manuelle dans ecrant session: Clic bouton transcription -> Barre de progression apparaît -> Appel backend.
Backend : Récupère audio -> deepgram(transcription) -> deepseek( création résumé intélligent) DB mise à jour.
Realtime : L'app écoute les changements DB -> Met à jour les 4 écrans des session automatiquement.
Terminé : L'élément quitte "En cours" -> Apparaît dans "Terminé" -> Barre disparaît si plus rien en cours.
Échec : L'élément quitte "En cours" -> Apparaît dans "Échec" -> Bouton Réessayer disponible.

- ### 1.4 contrainte obligatoire à suivre
- met à jours sans cassé la logique actuelle 
- ne lit pas tout le projet mais uniquement les interfaces et le endpoin concerné
- endpoin référence: @urls.py#L22-48 


2) TACHE PRINCIPALLE: AMELIORATION DE LA LOGIQUE ET EXPERIENCE UI DANS LES PAGES SESSIONS
- ### 1.1 Corrections du dernière mise à jour
- dans session, le bouton "voir resumé"  doit  apparaitre uniquement: 
  a) si la session a été transcrit(terminé).
- dans session le boutton "voir resumé" (meme celui qui apparait dans le modal apres trascription réussie) doit plutot diriger vers la page de validation résumé et non au contenue détaillé du résumé.
- supprime l'onglet "en cours" dans sessions ,puis que le traitement se fais déjà meme dans la apage en attente
- la durée des enregistrement audio ou fichier audio uploadé n'est pas toujours souvegardé ni pris en compte (durée est toujours 00:00)
ref:@urls.py#L22-48 

3) TACHE PRINCIPALLE: VISIBILITE ET ACCESSIBILITE DES RESUMES PAR LE CP
### 1.1 page validation
- erreur sementique(logique), aucun résumé n'apparait dans l'onglet validation (à ameliorer)
ref:@urls.py#L50-54 

4) TACHE PRINCIPALLE: PAGE ENREGISTREMENT AUDIO
- ### message non claire et precis apres sauvegarde de l'enregistrement ou audio uploadé
- le message doit dire exactement au CP que son opération de sauvegarde a reussie(si opération reussie) puis le dire d'aller dans l'onglet de session en attente pour la transcription de cet audio en résumé intélligent
- le champs Professeur est toujours obligatoir , change le en facultatif.
ref:@urls.py#L22-25 

5) TACHE PRINCIPALE: AMELIORATION VISIBILITE TEXT
- #### interface Politique de confidentialité et  Conditions d'utilisation 
- en theme sombre le texte détail sont en noir au lieu de blanc pas moyen de les lire 

- dans session le titre du résumé dans le card n'est pas visible (doit etre visible en blanc)

6) TACHE PRINCIPALE : AMELIORATION DE L'EXPERIENCE UI  
- ### Session interface et redirection
- lorqu'on se diriger à la page de la validation à partir du bouton "voir résumé" la barre de navigation avec ses onglet s'affiche pas.

7) TACHE PRINCIPALE: AMELIORATION LOGIQUE ET AJOUT DE LA BIBLIOTHEQUE CELERY
- ### enregistrement session audio, transcription et génération résumé intélligente: 

- Le CP termine l’enregistrement audio.
- L’audio est sauvegardé en base de données (comme actuellement).
- Le message de succès(Session enregistrée avec succès.) s’affiche immédiatement et en expliquant à utilisateur d'aller dans le session s'il veut voir le procesus de transcription déclanché automatiquement en arrière plan
- La session passe en statut attente (comme actuellement)
- Quelques secondes après (en arrière-plan), Celery lance automatiquement :
  * transcription audio
  * résumé intelligent
- Une fois terminé :
  * bouton Écouter la session reste disponible
   * bouton Voir résumé apparaît automatiquement si résumé prêt pour rédiriger vers la page de validation(comme actuelement)

- Architecture recommandée
  Save Session
    ↓
  Message succès
    ↓
  Celery delay()
    ↓
  Transcription async
    ↓
  Résumé IA
    ↓
  Bouton Voir résumé activé


NB: Ne pas casser le code actuel

Donc :

✅ conserver sauvegarde actuelle
✅ conserver lecture audio actuelle
✅ conserver bouton résumé existant
✅ juste automatiser le déclenchement

7) TACHE PRINCIPALE: RETABLISSEMENT DE L'INTERFACE EN COURS DANS SESSION
- retablis l'onglet "en cours" pour  afficher toutes les sessions qui passe en status "processing" 
- garde la Barre de progression (comme actuellement) lorsque la session passe en cours "processing" 

8) TACHE PRINCIPALE :  SUPPRESSION ONGLET EN COURS ET MODIFICATION DANS L4INTERFACE VALIDATION
- supprime l'onglet "en cours" dans sessions 
- lorsque le CP click sur "modifier" un résumé dans validation, cela doit prendre l'ID du résumé est chargé/affiché/remplir  le données de ces résumé dans le formulaire de modification 


Je veux modifier la logique de connexion de mon application de résumés.

Situation actuelle

Aujourd’hui, le système fonctionne ainsi :

L’utilisateur saisit son numéro de téléphone
Il reçoit un code OTP
Il valide le code OTP
Si c’est la première connexion sur cet appareil, il voit la page Compléter le profil
Ensuite il accède à son espace personnel

Le problème est que cette logique dépend actuellement du device / appareil utilisé.

Donc si l’utilisateur change de téléphone ou se connecte sur un nouvel appareil, la page Compléter le profil peut réapparaître, ce qui est incorrect.

Nouvelle logique demandée

Je veux que la page Compléter le profil soit liée au compte utilisateur en base de données, et non à l’appareil.

Règles à appliquer
Cas 1 : Le numéro n’existe pas en base de données

Après validation OTP :

créer le compte utilisateur
créer son profil initial
rediriger vers Compléter le profil

✅ La page de complétion doit apparaître uniquement dans ce cas.

Cas 2 : Le numéro existe déjà en base de données

Après validation OTP :

connecter l’utilisateur
rediriger directement vers Espace personnel / Dashboard

 Ne jamais afficher la page Compléter le profil, même sur :

un nouveau téléphone
une tablette
un navigateur différent
un autre appareil
Important : Supprimer la logique liée au device

Ne plus utiliser :

first login on device
appareil reconnu / non reconnu
local storage de première connexion
device id pour décider du onboarding

Le device peut être stocké pour sécurité ou analytics, mais jamais pour afficher le profil setup.
Résultat attendu
Un utilisateur déjà inscrit entre son numéro + OTP sur n’importe quel appareil et entre directement dans son espace personnel.

NB: Onboarding → dépend de l’appareil
Complétion du profil → dépend du compte utilisateur
Logique demandée
Onboarding = lié au device/appareil
Le onboarding (slides d’introduction, découverte de l’app, tutoriel) doit rester basé sur l’appareil utilisé.
#######------modification-------#######
Modifie verify_otp_view dans mon backend Django REST Framework. Supprime totalement la logique is_new_user basée sur profile.created_at et tout test avec timedelta. Cette approche ne doit plus être utilisée. Après validation OTP, la seule vérification métier doit être si le profil utilisateur est complet ou non. Considère le profil complet uniquement si user.first_name, profile.universite, profile.promotion et profile.filiere sont remplis. Si tous les champs existent : retourner profile_complete=true et requires_profile_completion=false. Sinon : retourner profile_complete=false et requires_profile_completion=true. Supprime is_new_user de la réponse API. Garde intactes la génération OTP, la validation OTP, JWT tokens et le reste du flux. Objectif final : le frontend redirige vers dashboard si profil complet, sinon vers page compléter profil.


Prompt 1 — Correction du calcul de durée audio (Session Audio / File d’attente)

Corrige le système de validation de durée des fichiers audio côté Flutter + Django.

Problème actuel :

Les audios inférieurs à 3 heures sont parfois rejetés avec le message :
« Durée audio > 3 heures (max autorisé : 180 minutes) »
Exemple observé : audio de 02:10:57 rejeté alors qu’il est inférieur à 180 minutes.
Après un deuxième essai manuel, la transcription fonctionne correctement.

Corrections demandées :

Vérifier et corriger le calcul exact de la durée audio côté backend Django et frontend Flutter.
S’assurer que la conversion heures/minutes/secondes vers minutes est correcte.
Utiliser une comparaison précise basée sur les secondes réelles et non un arrondi incorrect.
Ajouter des logs de debug pour afficher :
durée brute,
durée en secondes,
durée convertie en minutes,
limite maximale autorisée.
La validation doit accepter automatiquement tout audio inférieur ou égal à 180 minutes.
Éviter qu’un deuxième essai manuel soit nécessaire.
Vérifier toute incohérence entre :
métadonnées audio,
calcul Flutter,
calcul Django.

Prompt 2 — Correction erreur chargement des professeurs
Corrige l’erreur de chargement des professeurs dans l’écran d’enregistrement.
Erreur actuelle :
DioException [bad response]: status code 500
Objectifs :
Identifier précisément la cause du code 500 côté Django.
Vérifier :
endpoint API,
serializer,
queryset,
permissions,
données nulles,
relations cassées.
Ajouter une gestion d’erreur propre côté Flutter avec :
message utilisateur clair,
retry automatique,
logs détaillés.
Empêcher l’affichage brut des erreurs techniques DioException à l’utilisateur.
Si aucun professeur n’existe, afficher :
« Aucun professeur disponible »
Sécuriser la requête API pour éviter les crashs serveur.

Prompt 3 — Barre de recherche et filtres (Validation des résumés)

Améliore l’interface de validation des résumés.

Fonctionnalités à ajouter :

Ajouter une barre de recherche dynamique.
Permettre la recherche par :
titre,
professeur,
matière.

Ajouter une mise à jour en temps réel sans recharger toute la page.

Prompt 4 — Blocage automatique après expiration d’abonnement

Corrige la logique des abonnements côté Django + Flutter.

Problème actuel :

Les utilisateurs continuent d’accéder aux services même après expiration de leur abonnement.

Corrections demandées :

Vérifier automatiquement la date d’expiration de l’abonnement à chaque requête sensible.
Bloquer immédiatement l’accès si :
abonnement expiré,
abonnement inactif,
paiement non validé.
Empêcher l’accès :
- à la génération des QCM/exercices pour un résumé
Ajouter des middlewares/permissions Django pour sécuriser toutes les routes.
Afficher côté Flutter :
« Votre abonnement a expiré. Veuillez renouveler votre abonnement. »
Ajouter une redirection automatique vers la page d’abonnement.
Vérifier les fuseaux horaires et éviter les erreurs de date.
Ajouter des tests backend pour valider les expirations correctement.

Prompt 5 — Amélioration du rendu des résumés IA et résumés intelligents
Améliore complètement le formatage des résumés générés par l’IA afin qu’ils soient plus professionnels, lisibles et agréables pour les étudiants.
Problèmes actuels :


Présence excessive de :


hashtags (#),


astérisques (*),


symboles inutiles,


listes désordonnées,


points mal structurés.




Le rendu paraît trop “brut IA” et peu professionnel.


Objectifs :


Générer des résumés propres, fluides et naturellement rédigés.


Supprimer automatiquement :


hashtags,


doubles astérisques,


symboles markdown inutiles,


caractères parasites.




Produire un texte clair avec :


titres élégants en gras,


paragraphes bien espacés,


sections organisées,


transitions naturelles.

liste avec des point




Améliorer la lisibilité pour rendre le résumé :


attractif,


moderne,


facile à lire,


adapté aux étudiants.




Structurer automatiquement les résumés avec :


Introduction,


Points clés,


Explications importantes,


Conclusion synthétique.




Éviter les listes trop robotiques.


Utiliser un style pédagogique et humain.


Optimiser également :


la traduction,


le résumé intelligent,


la reformulation,


la résolution/simplification des résumés.




Ajouter un post-traitement automatique côté backend pour nettoyer le texte avant affichage.


Garantir une cohérence visuelle dans toute l’application Flutter.


Exemple attendu :


Texte fluide


Mise en page propre


Aucun symbole inutile


Résumé agréable à lire comme un véritable document pédagogique professionnel.

- [Mon May 18 12:05:14.299033 2026] [wsgi:error] [pid 292391:tid 140270828357376] [remote 102.206.242.29:24771]     return self.related_manager_cls(instance)
[Mon May 18 12:05:14.299037 2026] [wsgi:error] [pid 292391:tid 140270828357376] [remote 102.206.242.29:24771]   File "/home/jey/resumecours.gestionhospitaliare.site/env39/lib64/python3.9/site-packages/django/db/models/fields/related_descriptors.py", line 1010, in __init__
[Mon May 18 12:05:14.299041 2026] [wsgi:error] [pid 292391:tid 140270828357376] [remote 102.206.242.29:24771]     self.source_field = self.through._meta.get_field(self.source_field_name)
[Mon May 18 12:05:14.299045 2026] [wsgi:error] [pid 292391:tid 140270828357376] [remote 102.206.242.29:24771]   File "/home/jey/resumecours.gestionhospitaliare.site/env39/lib64/python3.9/site-packages/django/db/models/options.py", line 683, in get_field
[Mon May 18 12:05:14.299049 2026] [wsgi:error] [pid 292391:tid 140270828357376] [remote 102.206.242.29:24771]     raise FieldDoesNotExist(
[Mon May 18 12:05:14.299053 2026] [wsgi:error] [pid 292391:tid 140270828357376] [remote 102.206.242.29:24771] django.core.exceptions.FieldDoesNotExist: Professeur_filieres has no field named 'None' et pourtant j'ai  appliquer les modification et migragions .

- le filtrage par recherche ne fonctionne pas dans validation malgré que :
  *lorsqu'on tape la recherge et que la page se rafraichie aucune recherche se fait
- le design du input de la recherche dans validation n'est pas bon cela doit etre pareil que dans les autres pages à l'occurent "Résumé"
- les ecris sont invisible dans le champs input de recherche dans l'interface "validation"
- meme si l'utilisateur sont abonnement est épuisé , il a toujours la possibilité de générer les QCM ce qui devrait déjà etre bloquer tant pour le CP et pour tout autre utilisateur
- les professeurs doit se charger en foctions de leur appartenance à une université/filiere/promotion au quelles ils dispensent la matière, actuellement il charge tous les professeurs or il devrait charger seulement les professeurs de l'utilisateur connecté en fonction de université/filiere/promotion

- Ajouter une gestion d’erreur propre côté Flutter avec :
message utilisateur clair,
retry automatique,
logs détaillés.
Empêcher l’affichage brut des erreurs techniques DioException à l’utilisateur sur toute les interface.

UI/UX UPDATE — Résumé Plus

1. TYPOGRAPHIE
- Remplacer la police actuelle utilisée dans l’affichage des résumés par une police proche de celle de WhatsApp(monstera,poppin...).
- Utiliser une police moderne, propre, très lisible et professionnelle identique ou très similaire à WhatsApp iOS/Android.


2. PAGINATION DU CONTENU DES RÉSUMÉS
Dans l’écran des détails du résumé :
- Ajouter un système de pagination uniquement pour le contenu du résumé lorsque le texte est trop long.
- La pagination doit être fluide et orientée UX mobile.
- Le contenu doit être découpé automatiquement en plusieurs pages/blocs lisibles.
- Ajouter navigation simple :
  - précédent
  - suivant
  - indicateur de page actuelle

3. CONTRAINTES IMPORTANTES
- Ne rien casser dans la logique actuelle.
- Ne modifier aucune logique backend.
- Tous les IDs, routes, états, contrôleurs et appels existants restent inchangés.
- Le footer actuel reste totalement intact :
  - logique d’abonnement
  - génération des QCM
  - vérification premium
  - boutons existants
- Aucune régression UI/UX.
- La pagination concerne uniquement le contenu texte du résumé.

4. OBJECTIF
Améliorer la lisibilité, le rendu professionnel et l’expérience de lecture des résumés longs sans impacter l’architecture actuelle.


Voici les étapes pour générer un .aab (Android App Bundle) :

1. Créer le Keystore (une seule fois)
bash
cd android/app
keytool -genkey -v -keystore keystore.jks -keyalg RSA -keysize 2048 -validity 10000 -alias resumeplus
Mot de passe + infos requises. Conservez le fichier keystore.jks et les mots de passe.

2. Créer le fichier de configuration
android/key.properties (ne PAS commit sur git) :

properties
storePassword=<votre_mdp>
keyPassword=<votre_mdp>
keyAlias=resumeplus
storeFile=app/keystore.jks
3. Configurer android/app/build.gradle
Ajoutez avant android {} :

gradle
def keystoreProperties = new Properties()
def keystorePropertiesFile = rootProject.file('key.properties')
if (keystorePropertiesFile.exists()) {
    keystoreProperties.load(new FileInputStream(keystorePropertiesFile))
}
Dans le bloc android {}, remplacez buildTypes par :

gradle
signingConfigs {
    release {
        keyAlias keystoreProperties['keyAlias']
        keyPassword keystoreProperties['keyPassword']
        storeFile keystoreProperties['storeFile'] ? file(keystoreProperties['storeFile']) : null
        storePassword keystoreProperties['storePassword']
    }
}
buildTypes {
    release {
        signingConfig signingConfigs.release
        minifyEnabled true
        shrinkResources true
        proguardFiles getDefaultProguardFile('proguard-android.txt'), 'proguard-rules.pro'
    }
}
4. Vérifier pubspec.yaml
Assurez-vous que la version est correcte (ex: version: 1.2.3+4).

5. Build
bash
flutter clean
flutter pub get
flutter build appbundle
Le fichier .aab sera généré dans : build/app/outputs/bundle/release/app-release.aab

6. Tester localement (optionnel)
bash
bundletool build-apks --bundle=build/app/outputs/bundle/release/app-release.aab --output=app.apks --ks=android/app/keystore.jks --ks-key-alias=resumeplus
Commande unique pour générer l'APK de test depuis l'AAB :

bash
bundletool build-apks --bundle=build/app/outputs/bundle/release/app-release.aab --output=app.apks --mode=universal --ks=android/app/keystore.jks --ks-key-alias=resumeplus && bundletool install-apks --apks=app.apks
Points clés :

Le .aab est requis par Google Play pour les nouvelles applications
ProGuard est activé pour réduire la taille
Ne jamais versionner key.properties ni keystore.jks sur git

- 122] ERROR 2026-05-20 10:40:15,836 log Internal Server Error: /api/courses/sessions/72/
[Wed May 20 10:40:15.836923 2026] [wsgi:error] [pid 460319:tid 140479820125952] [remote 102.206.242.29:24122] Traceback (most recent call last):
[Wed May 20 10:40:15.836929 2026] [wsgi:error] [pid 460319:tid 140479820125952] [remote 102.206.242.29:24122]   File "/home/jey/resumecours.gestionhospitaliare.site/env39/lib64/python3.9/site-packages/django/core/handlers/exception.py", line 55, in inner
[Wed May 20 10:40:15.836934 2026] [wsgi:error] [pid 460319:tid 140479820125952] [remote 102.206.242.29:24122]     response = get_response(request)
[Wed May 20 10:40:15.836938 2026] [wsgi:error] [pid 460319:tid 140479820125952] [remote 102.206.242.29:24122]   File "/home/jey/resumecours.gestionhospitaliare.site/env39/lib64/python3.9/site-packages/django/core/handlers/base.py", line 197, in _get_response
[Wed May 20 10:40:15.836943 2026] [wsgi:error] [pid 460319:tid 140479820125952] [remote 102.206.242.29:24122]     response = wrapped_callback(request, *callback_args, **callback_kwargs)
[Wed May 20 10:40:15.836948 2026] [wsgi:error] [pid 460319:tid 140479820125952] [remote 102.206.242.29:24122]   File "/home/jey/resumecours.gestionhospitaliare.site/env39/lib64/python3.9/site-packages/django/views/decorators/csrf.py", line 56, in wrapper_view
[Wed May 20 10:40:15.836953 2026] [wsgi:error] [pid 460319:tid 140479820125952] [remote 102.206.242.29:24122]     return view_func(*args, **kwargs)
[Wed May 20 10:40:15.836957 2026] [wsgi:error] [pid 460319:tid 140479820125952] [remote 102.206.242.29:24122]   File "/home/jey/resumecours.gestionhospitaliare.site/env39/lib64/python3.9/site-packages/django/views/generic/base.py", line 104, in view
[Wed May 20 10:40:15.836962 2026] [wsgi:error] [pid 460319:tid 140479820125952] [remote 102.206.242.29:24122]     return self.dispatch(request, *args, **kwargs)
[Wed May 20 10:40:15.836966 2026] [wsgi:error] [pid 460319:tid 140479820125952] [remote 102.206.242.29:24122]   File "/home/jey/resumecours.gestionhospitaliare.site/env39/lib64/python3.9/site-packages/rest_framework/views.py", line 509, in dispatch
[Wed May 20 10:40:15.836970 2026] [wsgi:error] [pid 460319:tid 140479820125952] [remote 102.206.242.29:24122]     response = self.handle_exception(exc)
[Wed May 20 10:40:15.836975 2026] [wsgi:error] [pid 460319:tid 140479820125952] [remote 102.206.242.29:24122]   File "/home/jey/resumecours.gestionhospitaliare.site/env39/lib64/python3.9/site-packages/rest_framework/views.py", line 469, in handle_exception
[Wed May 20 10:40:15.836979 2026] [wsgi:error] [pid 460319:tid 140479820125952] [remote 102.206.242.29:24122]     self.raise_uncaught_exception(exc)
[Wed May 20 10:40:15.836984 2026] [wsgi:error] [pid 460319:tid 140479820125952] [remote 102.206.242.29:24122]   File "/home/jey/resumecours.gestionhospitaliare.site/env39/lib64/python3.9/site-packages/rest_framework/views.py", line 480, in raise_uncaught_exception
[Wed May 20 10:40:15.836997 2026] [wsgi:error] [pid 460319:tid 140479820125952] [remote 102.206.242.29:24122]     raise exc
[Wed May 20 10:40:15.837001 2026] [wsgi:error] [pid 460319:tid 140479820125952] [remote 102.206.242.29:24122]   File "/home/jey/resumecours.gestionhospitaliare.site/env39/lib64/python3.9/site-packages/rest_framework/views.py", line 506, in dispatch
[Wed May 20 10:40:15.837005 2026] [wsgi:error] [pid 460319:tid 140479820125952] [remote 102.206.242.29:24122]     response = handler(request, *args, **kwargs)
[Wed May 20 10:40:15.837009 2026] [wsgi:error] [pid 460319:tid 140479820125952] [remote 102.206.242.29:24122]   File "/home/jey/resumecours.gestionhospitaliare.site/env39/lib64/python3.9/site-packages/rest_framework/generics.py", line 286, in get
[Wed May 20 10:40:15.837013 2026] [wsgi:error] [pid 460319:tid 140479820125952] [remote 102.206.242.29:24122]     return self.retrieve(request, *args, **kwargs)
[Wed May 20 10:40:15.837017 2026] [wsgi:error] [pid 460319:tid 140479820125952] [remote 102.206.242.29:24122]   File "/home/jey/resumecours.gestionhospitaliare.site/env39/lib64/python3.9/site-packages/rest_framework/mixins.py", line 54, in retrieve
[Wed May 20 10:40:15.837021 2026] [wsgi:error] [pid 460319:tid 140479820125952] [remote 102.206.242.29:24122]     instance = self.get_object()
[Wed May 20 10:40:15.837024 2026] [wsgi:error] [pid 460319:tid 140479820125952] [remote 102.206.242.29:24122]   File "/home/jey/resumecours.gestionhospitaliare.site/env39/lib64/python3.9/site-packages/rest_framework/generics.py", line 103, in get_object
[Wed May 20 10:40:15.837028 2026] [wsgi:error] [pid 460319:tid 140479820125952] [remote 102.206.242.29:24122]     self.check_object_permissions(self.request, obj)
[Wed May 20 10:40:15.837032 2026] [wsgi:error] [pid 460319:tid 140479820125952] [remote 102.206.242.29:24122]   File "/home/jey/resumecours.gestionhospitaliare.site/env39/lib64/python3.9/site-packages/rest_framework/views.py", line 345, in check_object_permissions
[Wed May 20 10:40:15.837037 2026] [wsgi:error] [pid 460319:tid 140479820125952] [remote 102.206.242.29:24122]     if not permission.has_object_permission(request, self, obj):
[Wed May 20 10:40:15.837041 2026] [wsgi:error] [pid 460319:tid 140479820125952] [remote 102.206.242.29:24122]   File "/home/jey/resumecours.gestionhospitaliare.site/backend/courses/permissions.py", line 165, in has_object_permission
[Wed May 20 10:40:15.837045 2026] [wsgi:error] [pid 460319:tid 140479820125952] [remote 102.206.242.29:24122]     course.universite_id == profile.universite_id and
[Wed May 20 10:40:15.837049 2026] [wsgi:error] [pid 460319:tid 140479820125952] [remote 102.206.242.29:24122] AttributeError: 'Course' object has no attribute 'universite_id'



# 1. Sauvegarder l'ancien fichier
sudo cp /etc/systemd/system/celery.service /etc/systemd/system/celery.service.backup

# 2. Créer le nouveau fichier corrigé
sudo tee /etc/systemd/system/celery.service > /dev/null << 'EOF'
[Unit]
Description=Celery Worker ResumeCours
After=network.target redis.service

[Service]
Type=simple
User=root
WorkingDirectory=/home/jey/resumecours.gestionhospitaliare.site/backend

ExecStart=/home/jey/resumecours.gestionhospitaliare.site/env39/bin/python -m celery -A backend worker -l info --concurrency=2

Restart=always
RestartSec=5

Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

# 3. Recharger systemd
sudo systemctl daemon-reload

# 4. Redémarrer le service
sudo systemctl restart celery

# 5. Vérifier qu'il utilise le bon Python
systemctl status celery | head -15

tous ces mise ajours dans les ligne suivante ne sont pas effective, je fais le build mais toujours le meme probleme qu'avant :

 - Badge rouge sur "Résumés" quand un résumé est validé
- Badge orange sur "Validation" quand un résumé est créé
-Badges se réinitialisent quand on clique sur les onglets
- Badge rouge sur "Résumés" quand un résumé est validé

NB: pour "mes achat" meme apres consultation ou lecture(click  sur l'onglé en question  mes achat ) apres rafraichissment de la page le badje compteur apparait encore comme si la page n'etait pas consulté 
Diagnostique entièrement mon système Flutter + Django + Firebase Cloud Messaging (FCM) concernant l’association des tokens aux utilisateurs.

Stack technique :

Backend :

* Django
* Celery
* Redis
* Firebase Admin SDK
* Production VPS Linux/CentOS.

Frontend :

* Flutter
* Firebase Messaging.

Modèle principal :

```python
class UserDevice(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='devices')
    fcm_token = models.TextField(unique=True)
    device_type = models.CharField(max_length=10, default='android')
    is_active = models.BooleanField(default=True)
```

IMPORTANT : utiliser les résultats déjà obtenus du diagnostic production ci-dessous.

────────────────────────────
DIAGNOSTIC DÉJÀ EFFECTUÉ CÔTÉ SERVEUR / PRODUCTION
────────────────────────────

Backend / Infra :

✓ Celery fonctionne.
✓ Redis fonctionne.
✓ Worker Celery actif.
✓ firebase-admin installé.
✓ Firebase Admin SDK initialise correctement l’application.
✓ _get_fcm_app() retourne bien un objet Firebase App.
✓ credentials JSON chargées.
✓ Firebase connecté côté serveur.

Logs Celery obtenus :

Avant :

* "firebase-admin non installé"
* "Firebase non configuré"

Ces problèmes sont maintenant corrigés.

Test shell Django :

```python
from notifications.tasks import _get_fcm_app
app = _get_fcm_app()
print(app)
```

Résultat :

```text
<firebase_admin.App object ...>
```

Donc Firebase SDK fonctionne côté serveur.

Diagnostic FCM obtenu :

Erreur initiale :

```text
PermissionDeniedError:
cloudmessaging.messages.create denied
```

Cause :
permissions IAM / API Firebase.

Cette erreur a été corrigée.

Nouvelle erreur actuelle :

```text
UnregisteredError
Requested entity was not found
```

Conclusion actuelle :

le backend arrive bien à contacter Firebase Cloud Messaging.

Le problème restant concerne principalement les tokens utilisateurs.

Inspection DB :

des tokens existent déjà dans UserDevice.

Exemple réel :

```python
<QuerySet [
 {'fcm_token': 'token_1'},
 {'fcm_token': 'token_2'}
]>
```

Mais certains tests montrent :

* token expiré
* token invalide
* token non enregistré
* mauvais utilisateur associé.

Donc l’infrastructure serveur n’est plus la cause principale.

────────────────────────────
PROBLÈME MÉTIER ACTUEL
────────────────────────────

Quand je me connecte avec plusieurs utilisateurs ou plusieurs téléphones, les tokens semblent mal associés.

Exemples :

Téléphone A :

* login User1
* token enregistré.

Puis :

* logout User1
* login User2.

Ou :

Téléphone B :

* autre utilisateur
* autre compte.

Comportement observé :

* un seul utilisateur semble conserver le token
* certains utilisateurs n’ont aucun token enregistré
* mauvais user lié au token
* notifications envoyées au mauvais utilisateur
* DB incohérente user ↔ token ↔ device.

Je soupçonne maintenant un problème de logique Flutter/API/DB.

────────────────────────────
ANALYSE DEMANDÉE
────────────────────────────

1. FLUTTER

Vérifie :

* permission notifications
* FirebaseMessaging.instance.getToken()
* moment exact récupération token
* moment exact envoi backend
* FirebaseMessaging.instance.onTokenRefresh
* login flow
* logout flow
* changement de compte
* multi device.

Cherche bugs possibles :

* token envoyé avant authentification
* getToken jamais rappelé après login
* token jamais rafraîchi
* logout non géré
* stale token
* mauvais ordre d’exécution.

2. DJANGO API

Vérifie :

* endpoint d’enregistrement token
* request.user
* auth API
* create/update/delete.

Cherche bugs possibles :

* mauvais request.user
* update_or_create incorrect
* token écrasé
* token lié au mauvais user
* ancien token conservé
* bug filtre queryset.

3. BASE DE DONNÉES

Vérifie :

* contenu UserDevice
* cohérence user/token/device
* doublons
* tokens inactifs
* relation multi-device.

4. LOGIQUE ATTENDUE

LOGIN :

→ récupérer token actif
→ envoyer backend
→ associer au request.user.

LOGOUT :

→ supprimer ou désactiver token.

TOKEN REFRESH :

→ mise à jour automatique.

CHANGEMENT DE COMPTE :

→ transférer correctement le token vers le nouvel utilisateur.

MULTI DEVICE :

→ un utilisateur peut posséder plusieurs devices.

5. DEBUG LOGS

Ajouter logs complets.

Flutter :

* permission
* getToken
* onTokenRefresh
* user connecté
* token envoyé.

Django :

* request.user
* token reçu
* create/update/delete UserDevice.

Exemple :

```text
[Flutter]
user=42
token=abc123

[API]
request.user=42
token reçu=abc123

[DB]
UserDevice updated user=42 token=abc123
```

Je veux :

* diagnostic détaillé
* causes probables classées par probabilité
* corrections exactes Flutter + Django
* architecture production-grade FCM.

# CORRECTIONS UI / BADGES / FEEDBACK UTILISATEUR

Appliquer les corrections suivantes.

### Badges — Résumés

Le badge rouge sur l’icône Résumés ne fonctionne pas correctement.

Corriger la logique :

- nouveau résumé disponible → badge + compteur.
- consultation réelle → réinitialisation.
NB: le compteur et le badge s'affiche mais pas la reinitialisationni l'incrémentation du compteur, et meme apres click/consultation sur l'onglet. donc cad meme si on a déjà clické sur le compteur ça reste toujours intancte au lieu d'enleve le badge apres consultation
---

### Badges — Validation

Le badge orange de Validation ne fonctionne pas.

Corriger la logique :

- nouveau résumé (généré) à valider → badge + compteur.
- ouverture/consultation → réinitialisation.

Le CP doit immédiatement voir qu’une validation est en attente.

---
Nouveau contenu → badge actif.

Consultation → suppression du badge.

---

### Cohérence globale

Uniformiser le comportement entre :

- Notifications
- Résumés
- Validation

### Feedback importation fichier audio

Dans :

Enregistrement → Création résumé → Audio.

Lorsqu’un utilisateur importe un fichier audio :

afficher immédiatement un Snackbar / indicateur de chargement.

Message exemple :

"Importation du fichier..."

Objectif :

indiquer clairement qu’un traitement est en cours lorsque l’importation prend du temps.

À la fin :

- succès → message de confirmation.
- erreur → message clair d’échec.

# AMÉLIORATIONS NOTIFICATIONS

Appliquer les améliorations suivantes.

### Logo dans les notifications

Ajouter le branding de l’application dans les notifications push.

Si supporté par le système de notification :

- afficher le logo / icône officielle de l’application,
- rendre les notifications immédiatement reconnaissables.

L’objectif est d’avoir un rendu plus professionnel et identifiable par l’utilisateur.

---

### Notifications background

Les notifications doivent fonctionner également :

- application ouverte,
- application en arrière-plan,
- téléphone en veille.

L’utilisateur doit recevoir les notifications même hors navigation active.

---

### Notification fin de création résumé — CP

Ajouter une notification dédiée pour le créateur du résumé.

Lorsqu’un CP lance une création de résumé :

pendant le traitement/session de génération, le processus continue normalement.

À la fin de la génération :

envoyer automatiquement une notification au CP créateur.

Titre exemple :

"Résumé créé"

Message exemple :

"Votre résumé a été généré avec succès."

Cette notification est destinée uniquement au CP ayant lancé la création.

---

### Nouveau résumé disponible

Lorsqu’un résumé devient disponible après validation/publication :

envoyer la notification prévue aux utilisateurs concernés.

Exemple :

"Nouveau résumé disponible"

La logique de ciblage existante doit rester inchangée.

# AMÉLIORATIONS NOTIFICATIONS

Appliquer les améliorations suivantes.

### Logo dans les notifications

Ajouter le branding de l’application dans les notifications push.

Si supporté par le système de notification :

- afficher le logo / icône officielle de l’application,
- rendre les notifications immédiatement reconnaissables.

L’objectif est d’avoir un rendu plus professionnel et identifiable par l’utilisateur.

---

### Notifications background

Les notifications doivent fonctionner également :

- application ouverte,
- application en arrière-plan,
- téléphone en veille.

L’utilisateur doit recevoir les notifications même hors navigation active.

---

### Notification fin de création résumé — CP

Ajouter une notification dédiée pour le créateur du résumé.

Lorsqu’un CP lance une création de résumé :

pendant le traitement/session de génération, le processus continue normalement.

À la fin de la génération :

envoyer automatiquement une notification au CP créateur.

Titre exemple :

"Résumé créé"

Message exemple :

"Votre résumé a été généré avec succès."

Cette notification est destinée uniquement au CP ayant lancé la création.

---

### Nouveau résumé disponible

Lorsqu’un résumé devient disponible après validation/publication :

envoyer la notification prévue aux utilisateurs concernés.

Exemple :

"Nouveau résumé disponible"

La logique de ciblage existante doit rester inchangée.

OBJECTIF :

Générer une build Android App Bundle (.aab) Flutter prête pour déploiement Google Play Store.

ETAPE 1 — Nettoyer le projet

Exécuter :

flutter clean
flutter pub get

Vérifier que le projet compile sans erreur.

--------------------------------------------------

ETAPE 2 — Mettre à jour la version de l’application

Ouvrir :

pubspec.yaml

Vérifier ou modifier :

version: 1.0.0+1

Règles :

1.0.0 = versionName visible sur Play Store.

+1 = versionCode Android.

Augmenter versionCode à chaque nouvelle release.

--------------------------------------------------

ETAPE 3 — Générer le keystore Android Release

Depuis la racine du projet, exécuter :

keytool -genkey -v -keystore upload-keystore.jks -keyalg RSA -keysize 2048 -validity 10000 -alias upload

Lors des questions :

Choisir un mot de passe pour le keystore.

Choisir un mot de passe pour la clé.

Entrer nom, organisation, pays.

Conserver soigneusement :

- fichier upload-keystore.jks
- storePassword
- keyPassword
- alias

Déplacer ensuite le fichier vers :

android/app/upload-keystore.jks

--------------------------------------------------

ETAPE 4 — Créer key.properties

Créer :

android/key.properties

Ajouter :

storePassword=VOTRE_STORE_PASSWORD
keyPassword=VOTRE_KEY_PASSWORD
keyAlias=upload
storeFile=upload-keystore.jks

Remplacer les valeurs par celles utilisées lors de la création du keystore.

--------------------------------------------------

ETAPE 5 — Configurer android/app/build.gradle

Ouvrir :

android/app/build.gradle

Ajouter en haut du fichier :

def keystoreProperties = new Properties()
def keystorePropertiesFile = rootProject.file("key.properties")

if (keystorePropertiesFile.exists()) {
    keystoreProperties.load(new FileInputStream(keystorePropertiesFile))
}

Dans android { }, ajouter :

signingConfigs {
    release {
        keyAlias keystoreProperties['keyAlias']
        keyPassword keystoreProperties['keyPassword']
        storeFile file(keystoreProperties['storeFile'])
        storePassword keystoreProperties['storePassword']
    }
}

Dans buildTypes { }, vérifier :

buildTypes {
    release {
        signingConfig signingConfigs.release
        minifyEnabled false
        shrinkResources false
    }
}

Sauvegarder.

--------------------------------------------------

ETAPE 6 — Générer le Android App Bundle (.aab)

Exécuter :

flutter build appbundle --release

Attendre la fin du build.

--------------------------------------------------

ETAPE 7 — Vérifier le fichier généré

Le résultat attendu doit exister ici :

build/app/outputs/bundle/release/app-release.aab

Vérifier que le fichier existe.

--------------------------------------------------

ETAPE 8 — Générer aussi un APK de test (optionnel mais recommandé)

Exécuter :

flutter build apk --release

APK attendu :

build/app/outputs/flutter-apk/app-release.apk

Tester l’installation.

--------------------------------------------------

ETAPE 9 — Sécurité

Ne jamais commiter :

android/key.properties
android/app/upload-keystore.jks

Ajouter dans .gitignore :

android/key.properties
android/app/upload-keystore.jks

--------------------------------------------------

ETAPE 10 — Résultat attendu

Produire :

- app-release.aab
- rapport des commandes exécutées
- confirmation de réussite ou erreurs rencontrées

Chemin final attendu :

build/app/outputs/bundle/release/app-release.aab

PROBLÈME 1 : Lecture incomplète des résumés

Symptôme :

Les résumés longs sont découpés en plusieurs pages via un système de pagination.
Lorsqu'on lance la lecture vocales l'intégralité du résumé n'est pas lue juste une tres petite parite,ou paragraphe qui est lue.

Analyse attendue :

Vérifier si le moteur TTS lit uniquement le contenu de la page courante.
Vérifier si la source envoyée au TTS provient du widget affiché au lieu du résumé complet.
Vérifier si la pagination coupe le texte avant son envoi au moteur TTS.
Vérifier si le texte complet existe déjà dans le modèle de données mais n'est pas transmis au TTS.

Correction attendue :

Le TTS doit toujours lire le résumé complet, indépendamment de la pagination visuelle.
La pagination doit rester uniquement un mécanisme d'affichage.
Le moteur TTS doit recevoir la totalité du texte du résumé.
Si nécessaire, concaténer automatiquement toutes les pages avant la lecture.

PROBLÈME 2 : Vitesse anormale après Pause/Reprise

Symptôme :

Au démarrage, la vitesse de lecture est correcte.
Lorsque l'utilisateur met en pause puis reprend la lecture, la voix devient beaucoup trop rapide.
Le débit devient difficilement compréhensible.

Analyse attendue :

Vérifier la gestion des états Play, Pause, Resume et Stop.
Vérifier si la vitesse (speechRate) est réinitialisée après Resume().
Vérifier si plusieurs instances du moteur TTS sont créées.
Vérifier si Resume() relance une nouvelle lecture avec une vitesse différente.
Vérifier les éventuels conflits entre les callbacks du TTS.

Correction attendue :

La vitesse doit rester strictement identique avant et après Pause/Reprise.
Les paramètres suivants doivent être conservés :
speechRate
pitch
volume
voice
language
Empêcher toute accélération involontaire après Resume().
Garantir une expérience utilisateur fluide et constante.

TRAVAIL DEMANDÉ

Analyser tout le code lié au TTS.
Identifier précisément la cause des deux bugs.
Corriger les bugs.
Refactoriser le code si nécessaire.
Vérifier que :
les résumés longs sont lus entièrement ;
la pagination n'affecte pas le TTS ;
Pause/Reprise conserve exactement la même vitesse ;
aucun doublon de lecture n'est créé ;
aucune fuite mémoire n'est présente.
Fournir le code corrigé complet avec explication des modifications effectuées.

IMPORTANT :
Avant toute modification, explique la cause exacte des bugs détectés. Ensuite applique la correction la plus robuste possible.

- lorsque qu'un utilisateur s'abonne la notification est envoyer à tout le monde, probleme grave: * les notifiation sur un abonnement ou un achat resumé doit etre fermement individuel, uniquement l'utilisateur effectuant l'opération qui doit etre informer

=========
OBJECTIF

<<<<<<< HEAD
Analyser les modèles existants et modifier uniquement les relations qui imposent actuellement des affectations une par une, afin de permettre des affectations en masse tout en conservant la cohérence du système, les permissions, les validations et la logique métier existante.
NB: les tables concernées sont les suivantes:
- filiere
- promotion
- universite
- notification
- cours
=======
Analyser les modèles existants et modifier uniquement les relations qui imposent actuellement des affectations une par une, afin de permettre des affectations en masse côté administration, tout en conservant la cohérence du système, les permissions, les validations et la logique métier existante.

>>>>>>> feature-refactoModel

RÈGLES IMPORTANTES

* Ne rien casser dans le système actuel.
* Conserver les contrôles d'accès et permissions.

* Conserver les validations existantes.
* Adapter les formulaires, API, serializers, vues et interfaces concernées.
* Mettre à jour les tests si nécessaire.
* Vérifier les impacts avant toute modification.
* Utiliser les relations ManyToMany lorsque cela est nécessaire.

---

1. RELATION PROFESSEUR ↔ FILIÈRE

---

Situation actuelle :

* Un professeur peut être lié à une ou plusieurs filières.
* Cette partie fonctionne correctement.

Aucune modification majeure requise sauf vérification de cohérence avec les autres modules.

---

2. RELATION FILIÈRE ↔ PROMOTION

---

Problème actuel :

Une table intermédiaire impose d'affecter chaque filière à chaque promotion manuellement.

Exemple :

* 100 filières
* 100 promotions

Cela oblige à créer énormément d'associations une par une.

Modification souhaitée :

Une filière peut contenir  une ou plusieurs promotions.

<<<<<<< HEAD
Une promotion peut appartenir à une ou plusieurs filières.
=======
Une promotion peut a partenir à une ou plusieurs filières.
>>>>>>> feature-refactoModel

Relation souhaitée :

ManyToMany

Exemple :

Filière Informatique
→ Licence 1
→ Licence 2
→ Licence 3

En une seule opération.

---

3. RELATION UNIVERSITÉ ↔ FILIÈRE

---

Problème actuel :

Une université doit être reliée aux filières une par une via une table intermédiaire.

Modification souhaitée :

Une université peut contenir une ou plusieurs filières.

<<<<<<< HEAD
=======

>>>>>>> feature-refactoModel
Relation souhaitée :

ManyToMany

Objectif :

Permettre la sélection multiple de filières lors de la création ou modification d'une université dans l'administration.

---

4. NOTIFICATION ↔ UNIVERSITÉ

---

Problème actuel :

Une notification ne peut cibler qu'une seule université.

Modification souhaitée :

Une notification peut cibler :

* une université
* plusieurs universités

Relation :

ManyToMany

---

5. NOTIFICATION ↔ FILIÈRE

---

Problème actuel :

Une notification ne peut cibler qu'une seule filière.

Modification souhaitée :

Une notification peut cibler :

* une filière
* plusieurs filières

Relation :

ManyToMany

---

6. NOTIFICATION ↔ PROMOTION

---

Problème actuel :

Une notification ne peut cibler qu'une seule promotion.

Modification souhaitée :

Une notification peut cibler :

* une promotion
* plusieurs promotions

Relation :

ManyToMany

---

7. NOTIFICATION ↔ UTILISATEUR

---

Problème actuel :

Une notification est destinée à un seul utilisateur coté  administration.

Modification souhaitée :

Une notification peut être envoyée à :

* un utilisateur
* plusieurs utilisateurs

Relation :

ManyToMany

Objectif :
Permettre l'envoi de notifications groupées

<<<<<<< HEAD

9. COURS - PROMOTION/FILIERE/UNIVERSITE
* un cours peut appartenir à une ou plusieurs promotions
* un cours peut appartenir à une ou plusieurs filières
* un cours peut appartenir à une ou plusieurs universités
=======
Permettre l'envoi de notifications groupées a partir de l'administration.

---



---


---

10. MIGRATIONS

---

Créer les migrations nécessaires.

Migrer les données existantes vers les nouvelles relations.

Conserver les données déjà enregistrées.

Ne supprimer aucune donnée existante.

---

11. CONTRÔLES À EFFECTUER

---
>>>>>>> feature-refactoModel

objectif permetre le chiox multiple de promotion, filière et université pour un cours
10. CONTRÔLES À EFFECTUER
Vérifier :

* Cohérence des données
* Permissions
* API
* Serializers
* Vues
* Formulaires
* Tests unitaires
* Performance des requêtes

---
COURS - PROMOTION/FILIRER/UNIVERSITE
permetre qu'un cours puis appartenir à une ou plusieur université,filiere,promotion 
objectif : permetre la selection et l'appartenance multiple coté administrateur en fin de facilité la création de cours et évité les repétions inutilise pouvant surcharger la base de données
sans casser la logique metier actuel

## RÉSULTAT ATTENDU

Le système doit fonctionner exactement comme aujourd'hui mais avec la possibilité de sélectionner :

* une ou plusieurs universités
* une ou plusieurs filières
* une ou plusieurs promotions
* un ou plusieurs utilisateurs

<<<<<<< HEAD
afin de faciliter les affectations et les notifications en masse dans l'administration.

========historique de paiement
=======
afin de faciliter les affectations et les notifications en masse.

>>>>>>> feature-refactoModel
- dans résumé achaté et historique de paement:
* le resumé chargé dans ces onglet doit venir de la base de donéé , et affcihé les donnée de l'utilisateur connecté et non d'afficher tout du cache sans vérifié l'utilisateur connecté 





# Objectif 1 : Parcours de première utilisation

Lorsqu'un CP se connecte pour la première fois et qu'il ne possède :

* aucun professeur
* aucun cours
* aucune séance
* aucun résumé

Afficher un écran d'accueil de type Empty State.

Titre :

Bienvenue sur Résumé Plus

Description :

Commencez par créer votre premier professeur et votre premier cours afin d'enregistrer vos premières séances.

Actions :
- continuer 

1. Créer mon premier professeur(écrant 1)
2. Créer mon premier cours(écrant 2)
3. Félicitation (si les opérations précedente on reussie, ecrant 3 avec le bouton créer ma premiere séance/enregistrement et aller à l'acceuil)

Le système doit guider l'utilisateur étape par étape.

---

# Objectif 2 : Création simplifiée d'un professeur

Lors de la création d'un professeur, l'utilisateur renseigne uniquement :

* Nom complet
* Téléphone
* Spécialité

Le backend doit automatiquement :

1. Créer un utilisateur Django associé au professeur.
2. Créer l'objet Professeur.
3. Associer automatiquement l'université de l'utilisateur connecté.

Exemple :

```python
prof_user = User.objects.create(
    username=...
)

professeur = Professeur.objects.create(
    user=prof_user,
    universite=current_user.universite
)
```

Ne jamais demander à l'utilisateur :

* Université
* Filière
* Promotion

Ces informations doivent être récupérées automatiquement depuis le profil de l'utilisateur connecté.

---

# Objectif 3 : Création simplifiée d'un cours

Le formulaire de création d'un cours ne doit afficher que :

* Nom du cours
* Description

Masquer complètement :

* Université
* Filière
* Promotion

Le backend doit remplir automatiquement ces informations à partir du profil de l'utilisateur connecté.

Exemple :

```python
cours.universite = current_user.universite
cours.filiere = current_user.filiere
cours.promotion = current_user.promotion
```

Conserver toutes les relations existantes.

Ne supprimer aucun champ existant.

---

# Objectif 4 : Création d'une table métier Dispense

Ne pas modifier les modèles Course et Professeur existants.

Ajouter une nouvelle table métier :

```python
class Dispense(models.Model):

    professeur = models.ForeignKey(
        Professeur,
        on_delete=models.CASCADE,
        related_name='dispenses'
    )

    cours = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='dispenses'
    )

    universite = models.ForeignKey(
        Universite,
        on_delete=models.CASCADE
    )

    filiere = models.ForeignKey(
        Filiere,
        on_delete=models.CASCADE
    )

    promotion = models.ForeignKey(
        Promotion,
        on_delete=models.CASCADE
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (
            'cours',
            'professeur',
            'promotion'
        )
```

Cette table devient la source officielle de liaison entre :

* Professeur
* Cours
* Université
* Filière
* Promotion

---

# Objectif 5 : Création automatique de Dispense

Après la création du premier cours et du premier professeur :

Créer automatiquement une ligne dans la table Dispense.

Exemple :

```python
Dispense.objects.create(
    professeur=professeur,
    cours=cours,
    universite=current_user.universite,
    filiere=current_user.filiere,
    promotion=current_user.promotion
)
```

Cette opération peut être réalisée :

* dans la vue
* dans un service métier

Éviter les signaux si possible.

---

Avant toute modification, analyser les modèles existants et vérifier que toutes les fonctionnalités actuelles continuent de fonctionner.
NB: commence d'abord le backend puis le frontend, avant de commencé coté création de ces interface(3) previent moin car je doit t'envoyer les image(maquette) comment je veux que mes interface soit 


# Objectif 6 : Création simplifiée d'une séance

Le modèle Session existe déjà :

```python
class Session(models.Model):
    course = models.ForeignKey(...)
    professeur_fk = models.ForeignKey(..., null=True, blank=True)
    professeur = models.CharField(...)
```

Ne modifier aucun champ existant.


---

# Objectif 7 : Récupération automatique du professeur

Lorsque l'utilisateur sélectionne un cours :

Rechercher automatiquement dans la table Dispense :

```python
dispense = Dispense.objects.filter(
    cours=course,
    universite=current_user.universite,
    filiere=current_user.filiere,
    promotion=current_user.promotion
).first()
```

---

## Cas 1 : Une liaison existe

Si une ligne Dispense est trouvée :

```python
session.professeur_fk = dispense.professeur

session.professeur = (
    dispense.professeur.user.get_full_name()
    or dispense.professeur.user.username
)
```

Le nom du professeur doit être affiché automatiquement dans l'interface.

L'utilisateur ne doit pas sélectionner le professeur.

---

## Cas 2 : Aucune liaison trouvée

Si aucune ligne Dispense n'existe :

```python
session.professeur_fk = None
```

Afficher un champ libre :

Nom du professeur

L'utilisateur peut saisir manuellement :

```text
Mme Judith
```

Puis enregistrer :

```python
session.professeur = "Mme Judith"
session.professeur_fk = None
```

---

# Objectif 8 : Compatibilité totale avec les anciennes données

Tous les anciens enregistrements doivent continuer à fonctionner.

Même lorsque :

```python
professeur_fk = None
```

La valeur :

```python
professeur
```

doit continuer à être utilisée comme valeur affichée.

Ne jamais casser :

* les anciennes séances
* les anciens résumés
* les API existantes
* les migrations existantes


L'utilisateur ne doit voir que les données appartenant à son contexte académique.

---

# Contraintes importantes

NE PAS :

* supprimer de colonnes
* modifier les clés primaires
* casser les relations existantes
* renommer les modèles existants
* supprimer les FK existantes
* casser les API
* casser les migrations existantes

FAIRE UNIQUEMENT :

* ajouter la table Dispense
* simplifier les formulaires
* automatiser les relations
* pré-remplir les données à partir de l'utilisateur connecté
* récupérer automatiquement le professeur associé à un cours
* conserver une compatibilité totale avec l'existant

Avant toute modification, analyser les modèles existants et vérifier que toutes les fonctionnalités actuelles continuent de fonctionner.
NB: commence d'abord le backend puis le frontend, avant de commencé coté frontend previent moin car je doit t'envoyer les image comment je veux que mes interface soit 

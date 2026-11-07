# MISSION : INVESTIGATION, DÉVELOPPEMENT ET DÉPLOIEMENT DE MUHTASARI+ EN PWA

## CONTEXTE

Le projet Muhtasari+ est une application Flutter connectée à un backend Django existant.

Nous voulons disposer d'une version Web installable sous forme de Progressive Web Application (PWA), principalement pour les utilisateurs iOS (iPhone et iPad), afin qu'ils puissent installer Muhtasari+ directement depuis notre site Web, sans passer par l'App Store.

## RÈGLE ABSOLUE : PROTÉGER LA VERSION ANDROID

La version Android actuelle est déjà en production. Elle fonctionne parfaitement.

**Il est strictement interdit de modifier, dégrader ou perturber son fonctionnement.**

- Ne modifier aucune fonctionnalité Android existante.
- Ne modifier aucun écran Android.
- Ne modifier aucun parcours utilisateur Android.
- Ne modifier aucun mécanisme de paiement Android.
- Ne modifier aucune configuration Android de production.
- Ne modifier ni le package ID, ni les paramètres de signature, ni les versions Android.
- Ne supprimer aucun package ou dépendance actuellement utilisé par Android sans justification et validation préalable.

Toutes les adaptations doivent être réalisées exclusivement pour la cible Web/PWA.

Privilégier les implémentations conditionnelles selon la plateforme et les fichiers spécifiques au Web lorsque cela est possible.

## PHASE 1 : INVESTIGATION

Analyser intégralement le projet Flutter :

1. Vérifier la possibilité de compiler le projet avec `flutter build web`.
2. Examiner les dépendances et leur compatibilité Web.
3. Identifier les fonctionnalités incompatibles avec les navigateurs.
4. Examiner particulièrement l'authentification OTP, les paiements FlexPay, les fichiers audio, l'enregistrement audio, les téléchargements, les notifications et le stockage local.
5. Vérifier la compatibilité avec Safari iOS et Chrome Android.
6. Identifier les adaptations nécessaires pour transformer le projet en PWA.

Produire un rapport technique avant toute modification importante.

## PHASE 2 : ADAPTATION WEB/PWA

Après validation de la faisabilité :

- Configurer Flutter Web.
- Créer le manifeste PWA.
- Configurer le Service Worker.
- Définir le nom Muhtasari+.
- Configurer les icônes et l'écran de lancement.
- Configurer le mode standalone.
- Prévoir le cache et la stratégie de mise à jour.
- Garantir le fonctionnement en HTTPS.
- Adapter uniquement les fonctionnalités incompatibles avec le Web.

Conserver l'identité visuelle et l'expérience utilisateur de l'application mobile.

## PHASE 3 : FONCTIONNALITÉS

La version Web doit utiliser le backend Django et les API existantes.

Elle doit permettre :

- Connexion avec le compte existant.
- Consultation des cours et résumés.
- Accès aux achats existants.
- Paiements FlexPay.
- Accès aux abonnements et QCM.
- Lecture et enregistrement audio lorsque compatible.
- Téléchargement des documents.
- Consultation de l'historique.

Ne pas créer une nouvelle base de données ni un système de comptes indépendant.

## PHASE 4 : DÉPLOIEMENT

Préparer et déployer la version PWA sur l'infrastructure existante.
Ne pas remplacer les fichiers de production Android.

## PHASE 5 : TESTS DE NON-RÉGRESSION

Effectuer des tests spécifiques :

**Android :**
- Vérifier que le projet Android conserve son fonctionnement.
- Vérifier que les paiements, la connexion, les résumés et les QCM restent opérationnels.
- Vérifier que les configurations et signatures Android sont inchangées.
- Ne publier aucune nouvelle version Android dans le cadre de cette mission.

**Web/PWA :**
- Tester la compilation.
- Tester Safari sur iPhone.
- Tester Chrome sur Android.
- Tester l'installation PWA.
- Tester la connexion et les fonctionnalités métier.
- Tester les paiements et les achats.
- Tester les mises à jour et le fonctionnement hors connexion lorsque prévu.

## LIVRABLES

1. Rapport de faisabilité.
2. Liste des adaptations effectuées.
3. Version Flutter Web compilée.
4. PWA fonctionnelle.
5. Déploiement Web opérationnel.
6. Rapport des tests de non-régression Android.
7. Documentation technique de déploiement.

**CONSIGNE FINALE :** travailler exclusivement sur la version Web/PWA. La version Android actuellement en production doit rester strictement intacte. Toute modification susceptible de l'affecter doit être isolée, justifiée et soumise à validation avant exécution.
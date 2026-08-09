PROMPT 1 — BACKEND : STATISTIQUES MÉTIER ET FINANCIÈRES
Implémente dans le backend Django de Résumé Plus un système de statistiques métier et financières.

IMPORTANT :
- Analyse d'abord les modèles existants avant toute modification.
- Réutilise les données existantes.
- Ne crée pas de doublons.
- Ne modifie pas la logique actuelle des achats, paiements ou abonnements.
- Ne stocke aucune donnée personnelle supplémentaire uniquement pour les statistiques.
- Les statistiques doivent être agrégées et anonymisées.
- Les revenus doivent provenir des transactions réellement enregistrées et validées.
- Ne pas utiliser Firebase Analytics comme source de vérité financière.
- Ne pas ajouter de statistiques sur les images, fichiers ou contenus personnels.
- Ne pas ajouter de suivi des heures d'utilisation, durée des sessions ou parcours utilisateur.

STATISTIQUES À IMPLÉMENTER :

1. UTILISATEURS
Conserver uniquement :
- nombre total d'utilisateurs
- nouveaux utilisateurs
- évolution du nombre d'utilisateurs par jour
- évolution par semaine
- évolution par mois

Ne pas implémenter :
- utilisateurs actifs
- temps d'utilisation
- durée des sessions
- comportement individuel
- suivi détaillé des utilisateurs.

2. RÉSUMÉS
Conserver :
- nombre total de résumés générés
- résumés générés par jour
- résumés générés par semaine
- résumés générés par mois

Ne pas ajouter :
- résumés consultés
- temps de consultation
- comportement individuel
- contenu des résumés dans les statistiques.

3. QCM
Conserver uniquement :
- nombre total de QCM générés
- QCM générés par jour
- QCM générés par semaine
- QCM générés par mois

Ne pas ajouter :
- QCM commencés
- QCM terminés
- taux de complétion
- temps passé sur les QCM.

4. TRANSACTIONS
Implémenter :
- transactions lancées
- transactions réussies
- transactions échouées
- transactions annulées
- nombre total de transactions
- évolution par jour/semaine/mois.

5. ACHATS DE RÉSUMÉS
Implémenter :
- nombre total de résumés achetés
- résumés achetés aujourd'hui
- cette semaine
- ce mois
- évolution quotidienne
- évolution hebdomadaire
- évolution mensuelle
- montant total généré par les achats de résumés
- montant quotidien
- montant hebdomadaire
- montant mensuel
- panier moyen si calculable.

6. ABONNEMENTS
Implémenter :
- abonnements actifs
- nouveaux abonnements
- abonnements renouvelés
- abonnements expirés
- abonnements annulés
- nombre total d'abonnements
- revenus des abonnements
- revenus par jour
- revenus par semaine
- revenus par mois.

7. REVENUS
Séparer clairement :
- revenus provenant des achats de résumés
- revenus provenant des abonnements
- revenu total
- revenu quotidien
- revenu hebdomadaire
- revenu mensuel
- évolution du revenu par période.

Ne compter comme revenu que les transactions réellement payées/réussies selon les statuts existants dans le projet.

8. FILTRES DE PÉRIODE
Toutes les statistiques doivent permettre :
- aujourd'hui
- 7 derniers jours
- 30 derniers jours
- cette semaine
- ce mois
- mois précédent
- période personnalisée

Utiliser le timezone déjà configuré dans Django.

9. API
Créer des endpoints administrateur protégés :

/api/admin/statistics/overview/
/api/admin/statistics/users/
/api/admin/statistics/summaries/
/api/admin/statistics/qcm/
/api/admin/statistics/transactions/
/api/admin/statistics/purchases/
/api/admin/statistics/subscriptions/
/api/admin/statistics/revenue/

/api/admin/statistics/export/excel/
/api/admin/statistics/export/csv/

Les réponses doivent être agrégées et directement exploitables par le dashboard.

10. RECHERCHE ET FILTRES
Ajouter les filtres/recherches réellement utiles aux statistiques :
- période
- type de transaction
- type d'achat
- type d'abonnement
- statut de transaction
- autres filtres uniquement s'ils existent déjà dans les modèles.

Ne pas créer de recherche permettant d'exposer les données personnelles des utilisateurs.

11. PERFORMANCE
Utiliser les agrégations Django ORM :
Count, Sum, Avg, TruncDay, TruncWeek, TruncMonth, etc.

Éviter les requêtes N+1.
Ajouter des index uniquement lorsque nécessaire après analyse des modèles.

12. SÉCURITÉ
- Endpoints accessibles uniquement aux administrateurs autorisés.
- Ne jamais retourner email, téléphone, nom, mot de passe, token ou autre donnée personnelle dans les statistiques.
- Ne pas enregistrer de données personnelles supplémentaires uniquement pour construire les statistiques.

13. EXPORT
Créer des exports Excel et CSV contenant uniquement les statistiques agrégées.

L'export doit respecter la période et les filtres sélectionnés.

À la fin :
- liste des fichiers modifiés/créés ;
- liste des endpoints ;
- source de chaque statistique ;
- migrations éventuelles ;
- tests effectués ;
- statistiques impossibles à calculer avec les données actuelles.

Ne pas intégrer Firebase dans cette tâche.
PROMPT 2 — DASHBOARD ADMIN
Implémente dans le dashboard administrateur de Résumé Plus une page "Statistiques" basée sur les endpoints statistiques du backend.

IMPORTANT :
- Analyse d'abord le dashboard existant et respecte son design.
- Ne modifie pas les fonctionnalités existantes.
- Ne crée aucune donnée fictive.
- Ne calcule pas les revenus côté frontend.
- Ne jamais afficher de données personnelles.
- Ne pas afficher les statistiques d'heures d'utilisation, sessions ou comportement utilisateur.

STRUCTURE DU DASHBOARD :

1. FILTRE GLOBAL

Ajouter :
- Aujourd'hui
- 7 derniers jours
- 30 derniers jours
- Cette semaine
- Ce mois
- Mois précédent
- Période personnalisée

2. CARTES PRINCIPALES

Afficher uniquement :
- Total utilisateurs
- Nouveaux utilisateurs
- Total résumés générés
- Total QCM générés
- Total transactions
- Transactions réussies
- Résumés achetés
- Abonnements actifs
- Revenu total

3. ONGLET UTILISATEURS

Afficher uniquement :
- nombre total d'utilisateurs
- nouveaux utilisateurs
- évolution quotidienne
- évolution hebdomadaire
- évolution mensuelle

Ne pas afficher :
- utilisateurs actifs
- temps d'utilisation
- durée des sessions
- parcours utilisateur
- données personnelles.

4. ONGLET RÉSUMÉS

Afficher :
- total résumés générés
- résumés générés aujourd'hui
- cette semaine
- ce mois
- évolution quotidienne
- évolution hebdomadaire
- évolution mensuelle

Ne pas afficher les contenus des résumés ni les informations personnelles.

5. ONGLET QCM

Afficher uniquement :
- total QCM générés
- QCM générés aujourd'hui
- cette semaine
- ce mois
- évolution quotidienne
- évolution hebdomadaire
- évolution mensuelle

Ne pas afficher QCM commencés, terminés ou temps d'utilisation.

6. ONGLET TRANSACTIONS

Afficher :
- transactions lancées
- transactions réussies
- transactions échouées
- transactions annulées
- taux de réussite
- évolution par jour/semaine/mois

Ajouter les filtres :
- période
- statut
- type de transaction.

7. ONGLET ACHATS

Afficher :
- nombre de résumés achetés
- achats aujourd'hui
- achats cette semaine
- achats ce mois
- montant total des achats
- montant quotidien
- montant hebdomadaire
- montant mensuel
- panier moyen.

8. ONGLET ABONNEMENTS

Afficher :
- abonnements actifs
- nouveaux abonnements
- renouvellements
- abonnements expirés
- abonnements annulés
- revenus abonnements
- évolution quotidienne/hebdomadaire/mensuelle.

9. ONGLET REVENUS

Créer une vue financière claire avec :

ACHATS DE RÉSUMÉS
- quantité
- revenu quotidien
- revenu hebdomadaire
- revenu mensuel

ABONNEMENTS
- quantité
- revenu quotidien
- revenu hebdomadaire
- revenu mensuel

TOTAL
- revenu total
- évolution du revenu
- comparaison avec la période précédente.

10. EXPORT

Ajouter :
[Exporter Excel]
[Exporter CSV]

L'export doit respecter les filtres actuellement sélectionnés.

11. RECHERCHE

Ajouter uniquement les recherches/filtres utiles aux statistiques :
- période
- statut
- type de transaction
- type d'achat
- type d'abonnement.

Ne pas permettre de rechercher ou afficher les données personnelles des utilisateurs.

12. UX

Prévoir :
- loading
- empty state
- error state
- graphiques lisibles
- responsive
- pagination si nécessaire
- aucune donnée hardcodée.

IMPORTANT :
Avant de coder, vérifie les endpoints réellement disponibles dans le backend.

Si une statistique demandée n'est pas calculable avec les modèles actuels, ne l'invente pas. Signale précisément la donnée manquante.

À la fin :
- liste des fichiers modifiés/créés ;
- endpoints utilisés ;
- statistiques disponibles ;
- statistiques impossibles à calculer ;
- tests effectués.
Résultat final recherché

Ton dashboard sera donc beaucoup plus simple :

Vue générale
→ utilisateurs + résumés + QCM + transactions + achats + abonnements + revenus.

Utilisateurs
→ combien d'utilisateurs, nouveaux utilisateurs et évolution.

Résumé
→ combien générés.

QCM
→ combien générés.

Transactions
→ lancées/réussies/échouées/annulées.

Achats
→ combien achetés + montant.

Abonnements
→ actifs/nouveaux/renouvelés/expirés/annulés + revenus.

Revenus
→ achats + abonnements + total.

Export
→ Excel + CSV.

NB: a chaque fin d'une tache lance le test et l'analyse pour s'assurer que tout marche
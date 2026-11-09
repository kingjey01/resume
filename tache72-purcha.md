Nous validons le démarrage de l'implémentation backend Apple In-App Purchase.

Travaille maintenant sur la PHASE BACKEND uniquement.

1. Implémente les modèles AppleTransaction et AppleNotification.
2. Ajoute les champs nécessaires dans Purchase et Abonnement sans casser les données existantes.
3. Implémente la vérification cryptographique des transactions Apple avec app-store-server-library.
4. Crée les endpoints :
   - GET /api/apple/products/
   - POST /api/apple/verify/
   - POST /api/apple/notifications/
5. Implémente l'idempotence des transactions et notifications.
6. Prépare les migrations Django.
7. Ajoute les tests unitaires avec des mocks.
8. Vérifie la compatibilité avec les achats FlexPay existants.
9. Vérifie que les remboursements Apple ne suppriment pas les droits provenant d'autres achats valides.

IMPORTANT :

- Ne déploie rien sur le VPS.
- Ne modifie aucune configuration de production.
- Ne lance aucune migration sur la base de production.
- Ne touche pas aux fichiers Android.
- Ne publie aucune clé, aucun token ni aucune information personnelle.
- Ne mets aucune valeur secrète dans le code ou les rapports.

Prépare également une configuration distincte pour les tests Sandbox et la production.

POINT IMPORTANT SUR LES PRIX :

Le premier produit Apple est configuré à 0,99 USD alors que le résumé correspondant coûte actuellement 300 CDF dans Django.

Il faut éviter toute incohérence entre le prix réellement facturé par Apple, le prix affiché dans l'application et le droit attribué par Django.

Ne considère pas automatiquement 300 CDF comme équivalent à 0,99 USD.

À la fin, fournis :
- les fichiers complets créés et modifiés ;
- les migrations ;
- les résultats des tests ;
- les variables d'environnement nécessaires, sans leurs valeurs ;
- les éventuelles opérations restantes à effectuer manuellement.

Attends mon autorisation avant tout déploiement.
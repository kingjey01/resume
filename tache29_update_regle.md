Prompt à donner à ton agent

Analyse et corrige uniquement les deux points suivants, sans modifier la logique existante qui fonctionne :

1. Suppression d’un résumé en attente — Validation

Dans Validation > Résumés en attente, ajouter la possibilité de supprimer un résumé qui est encore en attente de validation.

Ajouter une icône/bouton de suppression sur les résumés concernés.
La suppression doit demander une confirmation avant exécution.
Supprimer correctement le résumé côté backend et actualiser la liste côté Flutter.
Vérifier les éventuelles données liées afin d’éviter les références orphelines.
Ne pas modifier le fonctionnement actuel des résumés déjà validés/publiés.
2. Résumés IA générés par DeepSeek tronqués

Mes résumés intelligents générés par DeepSeek semblent parfois être incomplets ou coupés.

Faire une investigation complète pour déterminer précisément où intervient la coupure :

Vérifier d’abord la réponse brute retournée par DeepSeek : est-elle déjà tronquée ?
Vérifier ensuite le traitement dans DeepSeek_service.py et les éventuels traitements intermédiaires.
Vérifier la taille maximale des champs utilisés en base de données pour stocker le résumé.
Vérifier les serializers/API et Flutter afin de déterminer si le contenu complet est bien transmis et affiché.
Tester avec un contenu volontairement très long.
Si nécessaire, utiliser l’audio de test que je placerai(nom du fichier "IPP") dans le backend et comparer :
audio → transcription → génération DeepSeek → réponse brute → traitement backend → base de données → API → Flutter.
Identifier précisément l’étape où le contenu est tronqué avant de corriger.

Important : ne pas augmenter ou modifier arbitrairement les limites sans identifier la cause. Ne change rien d’autre dans l’application. Conserver les modèles de réponse, endpoints et structures existantes autant que possible.
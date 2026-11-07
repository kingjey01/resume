// Bootstrap Flutter personnalisé — cible Web/PWA de Muhtasari+.
//
// Pourquoi ce fichier existe : à partir des versions récentes de Flutter, le
// service worker intégré est déprécié et le fichier généré s'auto-désinscrit.
// En fournissant notre propre bootstrap SANS `serviceWorkerSettings`, on empêche
// Flutter d'enregistrer ce worker. C'est `sw.js` (enregistré par index.html)
// qui fournit le cache PWA, la stratégie de mise à jour et le mode hors ligne.
//
// Les deux variables ci-dessous sont remplacées par l'outil Flutter au build.
{{flutter_js}}
{{flutter_build_config}}

_flutter.loader.load();

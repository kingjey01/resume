/*
 * Service worker FCM (Web Push) de Muhtasari+.
 *
 * Firebase enregistre ce fichier dans un scope dédié
 * (`/firebase-cloud-messaging-push-scope`) : il ne remplace pas le service
 * worker PWA (`sw.js`, scope racine) qui gère le cache et le hors ligne.
 *
 * Il affiche les notifications reçues en arrière-plan et gère le clic.
 */
importScripts('firebase-config.js');

(function () {
  var config = self.MUHTASARI_FIREBASE_CONFIG || {};
  var configured =
    config.apiKey &&
    config.appId &&
    config.apiKey.indexOf('REMPLACER') === -1 &&
    config.appId.indexOf('REMPLACER') === -1;

  if (!configured) {
    // Pas de configuration : on n'enregistre pas Firebase, mais le fichier
    // reste servi sans erreur d'installation.
    console.warn('[FCM SW] Configuration Firebase Web absente — push désactivé.');
    return;
  }

  importScripts('https://www.gstatic.com/firebasejs/10.14.1/firebase-app-compat.js');
  importScripts('https://www.gstatic.com/firebasejs/10.14.1/firebase-messaging-compat.js');

  firebase.initializeApp(config);
  var messaging = firebase.messaging();

  messaging.onBackgroundMessage(function (payload) {
    var notification = payload.notification || {};
    var data = payload.data || {};
    var title = notification.title || 'Muhtasari+';
    var options = {
      body: notification.body || '',
      icon: 'icons/Icon-192.png',
      badge: 'icons/Icon-192.png',
      data: {
        // L'application n'expose pas encore de route Web profonde : on ouvre
        // l'accueil (qui rafraîchit la liste et le badge).
        url: '/',
        user_notification_id: data.user_notification_id || '',
        notification_type: data.notification_type || ''
      }
    };
    return self.registration.showNotification(title, options);
  });

  self.addEventListener('notificationclick', function (event) {
    event.notification.close();
    var target = (event.notification.data && event.notification.data.url) || '/';
    event.waitUntil(
      self.clients
        .matchAll({ type: 'window', includeUncontrolled: true })
        .then(function (windows) {
          for (var i = 0; i < windows.length; i++) {
            var client = windows[i];
            if (client.url.indexOf(self.location.origin) === 0 && 'focus' in client) {
              return client.focus();
            }
          }
          if (self.clients.openWindow) return self.clients.openWindow(target);
        })
    );
  });
})();

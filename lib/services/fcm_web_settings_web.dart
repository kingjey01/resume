import 'dart:js_interop';
import 'dart:js_interop_unsafe';

import 'package:firebase_core/firebase_core.dart';

/// Lit `web/firebase-config.js` (chargé par index.html) :
/// `MUHTASARI_FIREBASE_CONFIG` et `MUHTASARI_VAPID_KEY`.
@JS('MUHTASARI_FIREBASE_CONFIG')
external JSObject? get _configJs;

@JS('MUHTASARI_VAPID_KEY')
external JSString? get _vapidJs;

String _string(JSObject obj, String key) {
  final value = obj.getProperty(key.toJS);
  if (value == null || value.isUndefinedOrNull) return '';
  return (value as JSString).toDart;
}

class FirebaseWebSettings {
  final FirebaseOptions? options;
  final String? vapidKey;

  const FirebaseWebSettings({this.options, this.vapidKey});

  bool get configured => options != null && vapidKey != null;

  static FirebaseWebSettings read() {
    final config = _configJs;
    if (config == null || config.isUndefinedOrNull) {
      return const FirebaseWebSettings();
    }

    final apiKey = _string(config, 'apiKey');
    final appId = _string(config, 'appId');
    final senderId = _string(config, 'messagingSenderId');
    final projectId = _string(config, 'projectId');

    // Valeurs encore à remplacer : on désactive proprement le push Web.
    if (apiKey.isEmpty ||
        appId.isEmpty ||
        senderId.isEmpty ||
        projectId.isEmpty ||
        apiKey.contains('REMPLACER') ||
        appId.contains('REMPLACER')) {
      return const FirebaseWebSettings();
    }

    final vapid = _vapidJs?.toDart ?? '';
    final authDomain = _string(config, 'authDomain');
    final storageBucket = _string(config, 'storageBucket');

    return FirebaseWebSettings(
      options: FirebaseOptions(
        apiKey: apiKey,
        appId: appId,
        messagingSenderId: senderId,
        projectId: projectId,
        authDomain: authDomain.isEmpty ? null : authDomain,
        storageBucket: storageBucket.isEmpty ? null : storageBucket,
      ),
      vapidKey: (vapid.isEmpty || vapid.contains('REMPLACER')) ? null : vapid,
    );
  }
}

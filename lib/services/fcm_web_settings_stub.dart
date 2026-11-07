import 'package:firebase_core/firebase_core.dart';

/// Version non-Web : aucune configuration Firebase Web n'est lue.
///
/// L'implémentation réellement utilisée sur Flutter Web est
/// `fcm_web_settings_web.dart` (import conditionnel dans `fcm_service.dart`).
class FirebaseWebSettings {
  final FirebaseOptions? options;
  final String? vapidKey;

  const FirebaseWebSettings({this.options, this.vapidKey});

  bool get configured => false;

  static FirebaseWebSettings read() => const FirebaseWebSettings();
}

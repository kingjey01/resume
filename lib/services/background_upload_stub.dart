import 'dart:typed_data';

/// Envoi d'arrière-plan — VERSION DE REPLI (web et plateformes sans support).
///
/// Le paquet `background_downloader` ne prend en charge qu'Android et iOS :
/// l'importer dans du code partagé casserait la compilation web de
/// l'application. D'où cet import conditionnel : cette version renvoie `null`,
/// et l'appelant retombe alors sur l'envoi Dio habituel.
Future<Map<String, dynamic>?> uploadEnArrierePlan({
  required String url,
  required String? filePath,
  required Uint8List? bytes,
  required String fileName,
  required String mimeType,
  required Map<String, String> fields,
  required Map<String, String> headers,
  void Function(int sent, int total)? onProgress,
}) async =>
    null;

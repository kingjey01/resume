import 'dart:typed_data';

/// Version non-Web : aucun blob à lire.
///
/// L'implémentation réellement utilisée sur Flutter Web est
/// `web_blob_reader_web.dart` (import conditionnel dans
/// `mobile_audio_recorder.dart`).
Future<Uint8List?> readBlobBytes(String url) async => null;

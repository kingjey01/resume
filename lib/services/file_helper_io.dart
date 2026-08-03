import 'dart:io';
import 'dart:typed_data';

/// Implémentation IO pour mobile - lit les fichiers
Future<Uint8List?> readFileBytes(String path) async {
  try {
    final file = File(path);
    if (await file.exists()) {
      return await file.readAsBytes();
    }
  } catch (e) {
    print('Erreur lecture fichier: $e');
  }
  return null;
}

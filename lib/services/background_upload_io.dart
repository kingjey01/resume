import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

import 'package:background_downloader/background_downloader.dart';
import 'package:flutter/foundation.dart';
import 'package:resume_plus_clean/exceptions/api_exception.dart';

/// Envoi d'arrière-plan — iOS uniquement.
///
/// POURQUOI iOS SEULEMENT : sur iOS, une application mise en arrière-plan est
/// suspendue au bout de ~30 s — verrouiller le téléphone suffit à figer un envoi
/// de plusieurs minutes. Le seul mécanisme qui poursuit réellement le transfert
/// est le `URLSession` d'arrière-plan : le SYSTÈME prend le relais, l'application
/// suspendue (ou même terminée) n'y change rien.
///
/// Android n'en a pas besoin : le service de premier plan (étape B) garde le
/// processus vivant, et Dio poursuit l'envoi. On renvoie donc `null` pour laisser
/// l'appelant utiliser son chemin habituel — un seul chemin par plateforme,
/// plutôt qu'une refonte commune.
///
/// Le paquet ne déclare que les plateformes Android et iOS ; ce fichier n'est
/// compilé que là où `dart:io` existe, et n'agit qu'ici sur iOS.

bool _initialise = false;

Future<Map<String, dynamic>?> uploadEnArrierePlan({
  required String url,
  required String? filePath,
  required Uint8List? bytes,
  required String fileName,
  required String mimeType,
  required Map<String, String> fields,
  required Map<String, String> headers,
  void Function(int sent, int total)? onProgress,
}) async {
  if (!Platform.isIOS) {
    return null; // Android : chemin Dio + service de premier plan.
  }

  // LE PAQUET N'ENVOIE QUE DES FICHIERS D'UN RÉPERTOIRE DE BASE CONNU. On
  // dépose donc une copie dans le dossier temporaire de l'application : le
  // fichier d'origine peut venir de n'importe où (sélecteur de fichiers,
  // brouillon, enregistrement), et il doit rester lisible pendant que le
  // système effectue le transfert — y compris application suspendue.
  final nom = 'envoi_${DateTime.now().millisecondsSinceEpoch}_$fileName';
  final cible = File('${Directory.systemTemp.path}/$nom');

  if (filePath != null && filePath.isNotEmpty && File(filePath).existsSync()) {
    await File(filePath).copy(cible.path);
  } else if (bytes != null && bytes.isNotEmpty) {
    await cible.writeAsBytes(bytes, flush: true);
  } else {
    return null; // rien à envoyer : l'appelant signalera l'absence de fichier
  }
  final taille = await cible.length();

  if (!_initialise) {
    // Initialise la base de suivi des transferts du paquet.
    await FileDownloader().start(autoCleanDatabase: true);
    _initialise = true;
  }

  final tache = UploadTask(
    url: url,
    filename: nom,
    baseDirectory: BaseDirectory.temporary,
    httpRequestMethod: 'POST',
    fileField: 'audio_file',
    mimeType: mimeType,
    fields: fields,
    headers: headers,
    updates: Updates.statusAndProgress,
    // Le paquet rejoue lui-même un transfert interrompu par le système. La clé
    // d'idempotence, transmise dans `fields`, garantit qu'une reprise ne crée
    // pas de doublon côté serveur (étape C).
    retries: 2,
    displayName: 'Envoi de ${fields['summary_title'] ?? 'votre cours'}',
  );

  final transfert = await FileDownloader().transfers.start(tache);

  // La progression du paquet est un ratio 0..1 ; l'écran, lui, attend des
  // OCTETS (il en déduit la vitesse et le temps restant). On la convertit, avec
  // la taille du fichier comme total.
  if (onProgress != null) {
    transfert.progressNotifier.addListener(() {
      final ratio = transfert.progressNotifier.value;
      if (ratio != null) {
        onProgress((ratio * taille).round(), taille);
      }
    });
  }

  final resultat = await transfert.result;
  if (resultat.status != TaskStatus.complete) {
    throw ApiException(
      resultat.exception?.description ?? "L'envoi a été interrompu.",
      type: ApiExceptionType.network,
    );
  }

  final corps = resultat.responseBody;
  if (corps == null || corps.trim().isEmpty) {
    return <String, dynamic>{};
  }
  final decode = jsonDecode(corps);
  if (decode is Map<String, dynamic>) return decode;
  return <String, dynamic>{'data': decode};
}

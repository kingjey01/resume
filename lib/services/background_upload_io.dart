import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

import 'package:background_downloader/background_downloader.dart';
import 'package:flutter/foundation.dart';

/// Envoi d'arrière-plan — Android et iOS (tâche 58).
///
/// POURQUOI LE MÉCANISME NATIF SUR LES DEUX PLATEFORMES :
///  • iOS suspend l'application ~30 s après son passage en arrière-plan ; seul
///    le `URLSession` d'arrière-plan poursuit réellement un transfert long,
///    même écran verrouillé et même application terminée.
///  • Android peut geler le processus malgré le service de premier plan, et
///    WorkManager limite une tâche standard à ~9 minutes. Le plugin utilise
///    `WorkManager` / `DownloadWorker` avec `TransferHint.largeFile`, qui
///    relance automatiquement le transfert par cycles au lieu de le perdre.
///
/// Le service de premier plan reste utile pour l'ENREGISTREMENT et la
/// notification de progression ; l'envoi, lui, ne dépend plus de sa survie.
///
/// Ce fichier n'est compilé que là où `dart:io` existe (import conditionnel).

bool _initialise = false;

/// Initialise la base de suivi et reprend les transferts interrompus pendant
/// que l'application était suspendue ou fermée. À appeler au démarrage.
Future<void> initialiserEnvoiArrierePlan() async {
  if (_initialise) return;
  try {
    await FileDownloader().start(autoCleanDatabase: true);
    _initialise = true;
  } catch (e) {
    debugPrint("↻ Envoi d'arrière-plan indisponible ($e) : repli classique.");
  }
}

/// Statut natif d'un transfert d'arrière-plan, ou `null` s'il n'est pas suivi
/// (envoi classique Dio, tâche purgée, ou plugin indisponible).
///
/// Permet de distinguer « transfert toujours en cours » d'une vraie erreur
/// réseau lorsque l'utilisateur revient dans l'application.
Future<String?> statutTacheArrierePlan(String taskId) async {
  try {
    await initialiserEnvoiArrierePlan();
    final record = await FileDownloader().database.recordForId(taskId);
    return record?.status.name;
  } catch (_) {
    return null;
  }
}

Future<Map<String, dynamic>?> uploadEnArrierePlan({
  required String url,
  required String? filePath,
  required Uint8List? bytes,
  required String fileName,
  required String mimeType,
  required Map<String, String> fields,
  required Map<String, String> headers,
  required String taskId,
  void Function(int sent, int total)? onProgress,
}) async {

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

  await initialiserEnvoiArrierePlan();
  if (!_initialise) return null;

  final tache = UploadTask(
    // La clé d'idempotence sert AUSSI d'identifiant natif : après un
    // redémarrage, on peut retrouver l'état exact du transfert dans la base
    // persistante du plugin.
    taskId: taskId,
    url: url,
    filename: nom,
    baseDirectory: BaseDirectory.temporary,
    httpRequestMethod: 'POST',
    fileField: 'audio_file',
    mimeType: mimeType,
    fields: fields,
    headers: headers,
    updates: Updates.statusAndProgress,
    // `largeFile` active la reprise par cycles de 9 minutes côté Android ;
    // `retries` couvre les coupures réseau transitoires. La clé d'idempotence
    // garantit qu'une reprise ne crée pas de doublon côté serveur.
    transferHints: const {TransferHint.largeFile},
    retries: 3,
    displayName: 'Envoi de ${fields['summary_title'] ?? 'votre cours'}',
  );

  late final Transfer transfert;
  try {
    // `getOrStart` (et non `start`) : si un transfert portant la même clé est
    // déjà en cours — cas d'une reprise après redémarrage — on s'y rattache
    // au lieu d'en lancer un second. Un transfert terminé est réutilisé, un
    // transfert échoué est ré-enfilé par le plugin.
    transfert = await FileDownloader().transfers.getOrStart(tache);
  } catch (e) {
    debugPrint("↻ Envoi d'arrière-plan refusé ($e) : repli classique.");
    return null;
  }

  // LA PROGRESSION DU PAQUET EST UN RATIO 0..1 ; l'écran attend des OCTETS (il
  // en déduit la vitesse et le temps restant). On la convertit, avec la taille
  // du fichier comme total.
  transfert.progressNotifier.addListener(() {
    final ratio = transfert.progressNotifier.value;
    if (ratio != null) {
      onProgress?.call((ratio * taille).round(), taille);
    }
  });

  // On attend le résultat natif. Si l'application est suspendue, cette attente
  // est suspendue avec elle et reprend au retour ; si elle est tuée, le
  // transfert continue côté système et la base persistante du plugin permet
  // la réconciliation au prochain lancement (voir statutTacheArrierePlan).
  late final TaskStatusUpdate resultat;
  try {
    resultat = await transfert.result;
  } catch (e) {
    debugPrint("↻ Envoi d'arrière-plan interrompu ($e) : repli classique.");
    return null;
  }

  // Réponse reçue : on la rend telle quelle, y compris une erreur métier (400),
  // que l'appelant doit afficher. Un échec SANS réponse (réseau) rend la main
  // pour que l'envoi classique reprenne — la clé d'idempotence évite le doublon.
  final corps = resultat.responseBody;
  if (corps == null || corps.trim().isEmpty) {
    if (resultat.status != TaskStatus.complete) {
      debugPrint('↻ Envoi d\'arrière-plan échoué sans réponse : repli sur '
          'l\'envoi classique (${resultat.exception?.description}).');
      return null;
    }
    return <String, dynamic>{};
  }
  final decode = jsonDecode(corps);
  if (decode is Map<String, dynamic>) return decode;
  return <String, dynamic>{'data': decode};
}

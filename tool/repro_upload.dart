// Verification LOCALE de l'envoi, sans telephone ni serveur.
//
//     dart run tool/repro_upload.dart
//
// Compare les DEUX façons d'envoyer le corps — en mémoire (`fromBytes`) et
// depuis le disque (`fromFile`) — pour s'assurer que le passage au fichier
// (build 49) ne change RIEN à la requête : ni Content-Length, ni boundary, ni
// encodage chunked. Un changement sur ces trois points casserait le serveur,
// qui voit aujourd'hui une requête parfaitement formée.
//
// Ce que ce test ne peut PAS montrer : la finesse de la progression. Sur
// loopback le transfert est instantané, donc les deux variantes atteignent le
// total. C'est précisément ce qui a rendu ce test aveugle au vrai problème.

import 'dart:io';
import 'dart:typed_data';

import 'package:dio/dio.dart';

const int _tailleMo = 60;
const int _port = 8099;

Future<void> main() async {
  final fichierTemporaire = File('${Directory.systemTemp.path}/repro_upload.bin');
  await fichierTemporaire.writeAsBytes(
    Uint8List(_tailleMo * 1024 * 1024),
    flush: true,
  );

  await _cas('fromBytes (mémoire)', () async {
    final formData = FormData();
    formData.files.add(MapEntry(
      'audio_file',
      MultipartFile.fromBytes(
        Uint8List(_tailleMo * 1024 * 1024),
        filename: 'repro.m4a',
      ),
    ));
    formData.fields.add(MapEntry('course_id', '1'));
    return formData;
  });

  await _cas('fromFile (disque, build 49)', () async {
    final formData = FormData();
    formData.files.add(MapEntry(
      'audio_file',
      await MultipartFile.fromFile(fichierTemporaire.path,
          filename: 'repro.m4a'),
    ));
    formData.fields.add(MapEntry('course_id', '1'));
    return formData;
  });

  await fichierTemporaire.delete();
}

/// Envoie un corps vers un serveur local qui compte les octets reçus.
Future<void> _cas(String nom, Future<FormData> Function() construire) async {
  final serveur = await HttpServer.bind(InternetAddress.loopbackIPv4, _port);

  final coteServeur = serveur.first.then((requete) async {
    var recus = 0;
    await for (final bloc in requete) {
      recus += bloc.length;
    }
    final annonce = requete.contentLength;
    final type = requete.headers.value('content-type') ?? '';
    final transfert = requete.headers.value('transfer-encoding');
    requete.response.statusCode = 201;
    requete.response.write('{"ok":true}');
    await requete.response.close();

    stdout.writeln('--- $nom ---');
    stdout.writeln('  Content-Length annoncé : $annonce');
    stdout.writeln('  octets reçus           : $recus  (écart ${annonce - recus})');
    stdout.writeln('  boundary présent       : ${type.contains('boundary=')}');
    stdout.writeln('  transfer-encoding      : ${transfert ?? 'null (donc pas de chunked)'}');
  });

  final formData = await construire();
  final dio = Dio(BaseOptions(baseUrl: 'http://127.0.0.1:$_port'));
  var dernier = 0, total = 0;

  try {
    final reponse = await dio.post(
      '/api/courses/sessions/upload-audio/',
      data: formData,
      options: Options(
        headers: {'Content-Type': 'multipart/form-data'},
        sendTimeout: Duration.zero,
        receiveTimeout: const Duration(minutes: 10),
      ),
      onSendProgress: (envoyes, t) {
        dernier = envoyes;
        total = t;
      },
    );
    stdout.writeln('  progrès client         : $dernier / $total'
        '  (écart ${total - dernier})  → statut ${reponse.statusCode}');
  } catch (e) {
    stdout.writeln('  ÉCHEC client : $e');
  }

  await coteServeur;
  await serveur.close(force: true);
  stdout.writeln('');
}

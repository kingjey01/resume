// Reproduction LOCALE de l'échec d'upload, sans téléphone ni serveur.
//
//     dart run tool/repro_upload.dart
//
// POURQUOI (2026-10-16) : les envois de plus de ~50 Mo échouent depuis
// l'application, toujours à une poignée d'octets de la fin, et le serveur
// journalise « Request data read error » sans jamais voir Django. Deux
// questions restent ouvertes, et ce script y répond sans dépendre du réseau :
//
//   1. le client envoie-t-il EXACTEMENT ce qu'il annonce dans Content-Length ?
//      (un écart d'une trentaine d'octets produirait un blocage parfait : le
//      serveur attend la fin du corps, le client attend la réponse)
//   2. le Content-Type posé à la main dans les Options — sans « boundary » —
//      est-il bien remplacé par Dio, ou part-il tel quel ?
//
// Le serveur local compte les octets reçus et affiche les en-têtes réellement
// transmis. Aucun réseau, aucun token, aucune base : le résultat est net.

import 'dart:io';
import 'dart:typed_data';

import 'package:dio/dio.dart';

const int _tailleMo = 60;
const int _port = 8099;

Future<void> main() async {
  final serveur = await HttpServer.bind(InternetAddress.loopbackIPv4, _port);
  stdout.writeln('Serveur local sur 127.0.0.1:$_port');

  // Un seul échange, puis on ferme.
  final fini = serveur.first.then((requete) async {
    var recus = 0;
    await for (final bloc in requete) {
      recus += bloc.length;
    }
    final annonce = requete.contentLength;
    stdout.writeln('');
    stdout.writeln('--- CE QUE LE SERVEUR A REÇU ---');
    stdout.writeln('  octets annoncés (Content-Length) : $annonce');
    stdout.writeln('  octets réellement reçus          : $recus');
    stdout.writeln('  écart                            : ${annonce - recus}');
    stdout.writeln('  content-type reçu                : '
        '${requete.headers.value('content-type')}');
    stdout.writeln('  transfer-encoding reçu           : '
        '${requete.headers.value('transfer-encoding')}');
    stdout.writeln('  boundary présent ?               : '
        '${(requete.headers.value('content-type') ?? '').contains('boundary=')}');
    requete.response.statusCode = 201;
    requete.response.write('{"ok":true}');
    await requete.response.close();
    return recus;
  });

  // Envoi avec EXACTEMENT les options de l'application (api_service.dart).
  final octets = Uint8List(_tailleMo * 1024 * 1024);
  final formData = FormData();
  formData.files.add(MapEntry(
    'audio_file',
    MultipartFile.fromBytes(octets, filename: 'repro.m4a'),
  ));
  formData.fields.add(MapEntry('course_id', '1'));
  formData.fields.add(MapEntry('summary_title', 'repro'));

  final dio = Dio(BaseOptions(baseUrl: 'http://127.0.0.1:$_port'));
  var dernierProgres = 0;
  var totalAnnonce = 0;

  stdout.writeln('Envoi de $_tailleMo Mo (longueur FormData calculée par Dio : '
      '${formData.length} octets)');

  try {
    final reponse = await dio.post(
      '/api/courses/sessions/upload-audio/',
      data: formData,
      options: Options(
        headers: {'Content-Type': 'multipart/form-data'}, // <- le point n°2
        sendTimeout: Duration.zero,
        receiveTimeout: const Duration(minutes: 10),
      ),
      onSendProgress: (envoyes, total) {
        dernierProgres = envoyes;
        totalAnnonce = total;
      },
    );
    stdout.writeln('');
    stdout.writeln('--- CE QUE LE CLIENT A ENVOYÉ ---');
    stdout.writeln('  dernier progrès rapporté : $dernierProgres');
    stdout.writeln('  total annoncé par Dio    : $totalAnnonce');
    stdout.writeln('  écart                    : ${totalAnnonce - dernierProgres}');
    stdout.writeln('  statut de la réponse     : ${reponse.statusCode}');
  } catch (e) {
    stdout.writeln('');
    stdout.writeln('--- ÉCHEC CÔTÉ CLIENT ---');
    stdout.writeln('  dernier progrès : $dernierProgres / $totalAnnonce');
    stdout.writeln('  erreur          : $e');
  }

  await fini;
  await serveur.close(force: true);
}

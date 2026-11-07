// Génère `web/firebase-config.js` à partir de l'environnement ou de `.env.pwa`.
//
// Tâche 60 — les clés Firebase Web ne doivent JAMAIS être commitées.
//
// Usage :
//   dart run tool/generate_firebase_config.dart
//
// Priorité des sources :
//   1. variables d'environnement du processus ;
//   2. fichier `.env.pwa` à la racine du projet (ignoré par Git).
//
// Le fichier produit est ignoré par Git et utilisé par :
//   - index.html (page Flutter) ;
//   - firebase-messaging-sw.js (service worker de push).
//
// Les clés Web Firebase (apiKey, appId, vapidKey) sont des identifiants
// publics côté client, mais elles ne sont pas versionnées ici : chaque
// environnement fournit les siennes.

import 'dart:io';

const Map<String, String> _mapping = {
  'apiKey': 'FIREBASE_API_KEY',
  'authDomain': 'FIREBASE_AUTH_DOMAIN',
  'projectId': 'FIREBASE_PROJECT_ID',
  'storageBucket': 'FIREBASE_STORAGE_BUCKET',
  'messagingSenderId': 'FIREBASE_MESSAGING_SENDER_ID',
  'appId': 'FIREBASE_APP_ID',
  'measurementId': 'FIREBASE_MEASUREMENT_ID',
};

const List<String> _requis = [
  'FIREBASE_API_KEY',
  'FIREBASE_PROJECT_ID',
  'FIREBASE_MESSAGING_SENDER_ID',
  'FIREBASE_APP_ID',
  'FIREBASE_VAPID_KEY',
];

Map<String, String> _lireDotEnv(String chemin) {
  final fichier = File(chemin);
  if (!fichier.existsSync()) return {};

  final valeurs = <String, String>{};
  for (final ligne in fichier.readAsLinesSync()) {
    final texte = ligne.trim();
    if (texte.isEmpty || texte.startsWith('#')) continue;
    final separateur = texte.indexOf('=');
    if (separateur <= 0) continue;
    final cle = texte.substring(0, separateur).trim();
    var valeur = texte.substring(separateur + 1).trim();
    if (valeur.length >= 2 &&
        ((valeur.startsWith('"') && valeur.endsWith('"')) ||
            (valeur.startsWith("'") && valeur.endsWith("'")))) {
      valeur = valeur.substring(1, valeur.length - 1);
    }
    valeurs[cle] = valeur;
  }
  return valeurs;
}

String _echapper(String valeur) =>
    valeur.replaceAll(r'\', r'\\').replaceAll("'", r"\'");

void main() {
  final dotenv = _lireDotEnv('.env.pwa');

  String lire(String cle) {
    final depuisEnv = Platform.environment[cle];
    if (depuisEnv != null && depuisEnv.isNotEmpty) return depuisEnv;
    return dotenv[cle] ?? '';
  }

  final valeurs = <String, String>{
    for (final entree in _mapping.entries) entree.key: lire(entree.value),
  };
  final vapid = lire('FIREBASE_VAPID_KEY');

  final manquantes = _requis.where((cle) => lire(cle).isEmpty).toList(growable: false);

  final sortie = StringBuffer()
    ..writeln('/*')
    ..writeln(' * Fichier GÉNÉRÉ par tool/generate_firebase_config.dart.')
    ..writeln(' * Ne pas commiter : il est ignoré par Git et reconstruit depuis')
    ..writeln(' * les variables d\'environnement ou `.env.pwa`.')
    ..writeln(' */')
    ..writeln('(function (scope) {')
    ..writeln('  scope.MUHTASARI_FIREBASE_CONFIG = {');
  for (final entree in valeurs.entries) {
    sortie.writeln("    ${entree.key}: '${_echapper(entree.value)}',");
  }
  sortie
    ..writeln('  };')
    ..writeln()
    ..writeln("  scope.MUHTASARI_VAPID_KEY = '${_echapper(vapid)}';")
    ..writeln("})(typeof self !== 'undefined' ? self : this);");

  final destination = File('web/firebase-config.js');
  destination.parent.createSync(recursive: true);
  destination.writeAsStringSync(sortie.toString());

  if (manquantes.isNotEmpty) {
    stderr.writeln(
      '⚠️  Variables absentes : ${manquantes.join(', ')}. '
      'Le push Web sera désactivé jusqu\'à ce qu\'elles soient fournies.',
    );
    exitCode = 1;
    return;
  }

  stdout.writeln(
    '✅ web/firebase-config.js généré (${destination.path}) — aucune clé affichée.',
  );
}

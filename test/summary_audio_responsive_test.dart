import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:resume_plus_clean/services/audio_service.dart';
import 'package:resume_plus_clean/theme/app_theme.dart';
import 'package:resume_plus_clean/widgets/audio_player_widget.dart';

/// Tache34, point 4 — la zone des boutons audio ne doit jamais déborder, et
/// doit s'empiler verticalement quand la largeur manque.
///
/// Le cas qui cassait réellement l'écran est celui des DEUX boutons
/// (« Écouter » + « Arrêter ») : c'est donc lui qu'on reproduit. Le bouton
/// « Arrêter » n'apparaît que pendant/après une lecture, qui dépend du moteur
/// TTS du téléphone : on simule donc les rappels du canal `flutter_tts`
/// (démarrage de la synthèse) pour atteindre cet état sans appareil réel.

const MethodChannel _canalTts = MethodChannel('flutter_tts');

/// Simule un moteur TTS présent : toute commande sortante réussit.
void _installerMoteurTts() {
  final messenger = TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger;
  messenger.setMockMethodCallHandler(_canalTts, (call) async {
    if (call.method == 'getLanguages') return <String>['fr-FR'];
    return 1;
  });
  addTearDown(() => messenger.setMockMethodCallHandler(_canalTts, null));
}

/// Monte le lecteur à une largeur donnée et laisse l'initialisation du service
/// audio (puis l'enregistrement de ses callbacks) se terminer.
Future<void> _pomperLecteur(
  WidgetTester tester, {
  required double largeur,
}) async {
  await tester.pumpWidget(
    MaterialApp(
      theme: AppTheme.lightTheme,
      home: Scaffold(
        body: Center(
          child: SizedBox(
            width: largeur,
            child: const AudioPlayerWidget(
              text: 'Contenu à lire.',
              title: 'Écouter le résumé',
              rate: 0.5,
            ),
          ),
        ),
      ),
    ),
  );
  // Initialisation du service audio (canal simulé) puis enregistrement des
  // callbacks : quelques pompages bornés, le faux temps de `testWidgets`
  // n'avançant que sur `pump()`.
  for (var i = 0; i < 4; i++) {
    await tester.pump(const Duration(milliseconds: 20));
  }
}

/// Fait croire au plugin que la synthèse a démarré : le bouton principal passe
/// en « Pause » et « Arrêter » apparaît.
Future<void> _declencherDemarrageLecture(WidgetTester tester) async {
  // Non attendu volontairement : un appel de plateforme qui ne renvoie pas de
  // réponse peut ne jamais compléter sa Future, ce qui bloquerait le test.
  unawaited(
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .handlePlatformMessage(
      'flutter_tts',
      const StandardMethodCodec()
          .encodeMethodCall(const MethodCall('speak.onStart')),
      (_) {},
    ),
  );
  await tester.pump();
  await tester.pump();
}

/// Boîte englobant les deux boutons, telle qu'elle est réellement peinte.
Rect _boiteDesBoutons(WidgetTester tester) {
  final boutons = find.byType(ElevatedButton);
  return tester.getRect(boutons.at(0)).expandToInclude(tester.getRect(boutons.at(1)));
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() {
    AudioService().dispose(); // repart d'un service non initialisé
    _installerMoteurTts();
  });

  testWidgets('les deux boutons sont affichés pendant la lecture',
      (tester) async {
    await _pomperLecteur(tester, largeur: 600);
    await _declencherDemarrageLecture(tester);

    expect(find.text('Pause'), findsOneWidget);
    expect(find.text('Arrêter'), findsOneWidget);
  });

  testWidgets('écran large : les boutons restent côte à côte', (tester) async {
    await _pomperLecteur(tester, largeur: 600);
    await _declencherDemarrageLecture(tester);

    final pause = tester.getRect(find.text('Pause'));
    final arreter = tester.getRect(find.text('Arrêter'));

    // Même ligne : les deux libellés sont au même niveau.
    expect((arreter.top - pause.top).abs(), lessThan(1));
    expect(tester.takeException(), isNull);
  });

  testWidgets('écran étroit : les boutons s\'empilent au lieu de déborder',
      (tester) async {
    await _pomperLecteur(tester, largeur: 200);
    await _declencherDemarrageLecture(tester);

    final pause = tester.getRect(find.text('Pause'));
    final arreter = tester.getRect(find.text('Arrêter'));

    // L'un est AU-DESSUS de l'autre : plus aucun chevauchement horizontal.
    expect(arreter.top, greaterThanOrEqualTo(pause.bottom));
    expect(tester.takeException(), isNull);
  });

  // Tache37, point 2 : une fois empilés, les boutons doivent être centrés
  // horizontalement dans leur conteneur — et non plus collés au bord gauche.
  testWidgets('écran étroit : les boutons empilés sont centrés horizontalement',
      (tester) async {
    await _pomperLecteur(tester, largeur: 200);
    await _declencherDemarrageLecture(tester);

    final centreConteneur = tester.getCenter(find.byType(Card)).dx;

    expect(
      (_boiteDesBoutons(tester).center.dx - centreConteneur).abs(),
      lessThan(1),
      reason: 'les boutons empilés doivent être centrés, pas alignés à gauche',
    );
  });

  testWidgets('écran large : les boutons côte à côte restent centrés',
      (tester) async {
    await _pomperLecteur(tester, largeur: 600);
    await _declencherDemarrageLecture(tester);

    final pause = tester.getRect(find.widgetWithText(ElevatedButton, 'Pause'));
    final arreter = tester.getRect(find.widgetWithText(ElevatedButton, 'Arrêter'));

    // Disposition en ligne conservée…
    expect((arreter.top - pause.top).abs(), lessThan(1));
    // …et couple de boutons centré sur l'axe horizontal du conteneur.
    expect(
      (_boiteDesBoutons(tester).center.dx - tester.getCenter(find.byType(Card)).dx).abs(),
      lessThan(1),
    );
  });

  testWidgets('aucun débordement, lecture arrêtée comme en cours, de 200 à 900 px',
      (tester) async {
    for (final largeur in <double>[200, 240, 280, 320, 360, 480, 900]) {
      await _pomperLecteur(tester, largeur: largeur);
      // `takeException` remonte tout RenderFlex overflow : c'est exactement le
      // symptôme constaté (boutons sortant de leur conteneur).
      expect(tester.takeException(), isNull,
          reason: 'lecture arrêtée @${largeur}px');

      await _declencherDemarrageLecture(tester);
      expect(tester.takeException(), isNull,
          reason: 'lecture en cours @${largeur}px');
    }
  });
}

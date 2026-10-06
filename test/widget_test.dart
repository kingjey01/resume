import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:resume_plus_clean/main.dart';

/// Test de fumée du démarrage.
///
/// Remplace le test-compteur hérité de `flutter create`, qui montait `MyApp`
/// sans `ProviderScope` et cherchait un compteur inexistant : il échouait donc
/// depuis toujours, sans rien couvrir.
///
/// Ce qu'on vérifie ici : l'application se monte, peint son premier frame sans
/// exception, et affiche bien son nom commercial — ce qui en fait aussi un
/// garde-fou du renommage en « Muhtasari+ ».
void main() {
  testWidgets('l\'application démarre sur le splash et affiche « Muhtasari+ »',
      (WidgetTester tester) async {
    await tester.pumpWidget(const ProviderScope(child: MyApp()));
    await tester.pump();

    // Premier frame peint sans erreur.
    expect(tester.takeException(), isNull);

    // Le splash porte le nom commercial et son accroche.
    expect(find.text('Muhtasari+'), findsOneWidget);
    expect(find.text('Vos cours, simplifiés'), findsOneWidget);

    // Le splash programme une navigation différée (~2,5 s), à laquelle
    // s'enchaînent la vérification de version puis l'auto-login — chacun avec
    // ses propres délais. On laisse le temps s'écouler par paliers : sans
    // cela le test se terminerait sur un timer encore en attente, ce que
    // `flutter_test` signale comme un échec.
    for (var i = 0; i < 20; i++) {
      await tester.pump(const Duration(seconds: 1));
    }
  });
}

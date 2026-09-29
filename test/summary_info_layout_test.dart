// Vérification ciblée de la zone « auteur / date / prix » du détail d'un résumé.
// Objectif : aucun débordement, quelle que soit la longueur du nom d'utilisateur
// et quelle que soit la largeur de l'écran.

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:resume_plus_clean/features/summaries/providers/seen_summaries_provider.dart';
import 'package:resume_plus_clean/features/summary_details/screens/summary_details_screen.dart';
import 'package:resume_plus_clean/models/summary.dart';
import 'package:resume_plus_clean/theme/app_theme.dart';

const _court = 'Jean';
const _moyen = 'Jean-Pierre Mbala Nkosi';
const _tresLong =
    'Jean-Pierre-Mbala-Nkosi-Kalala-Mukendi-Tshibangu-Wa-Mulumba-Ilunga-Kabongo';
const _sansEspace = 'JeanPierreMbalaNkosiKalalaMukendiTshibanguWaMulumbailunga';

Summary _summary(String auteur) => Summary(
      id: 1,
      title: 'Résumé de test',
      subject: 'Mathématiques',
      filiereName: 'Informatique',
      imageUrl: '',
      content: 'Contenu de test ' * 60,
      price: 2500,
      isFree: false,
      authorName: auteur,
      createdAt: DateTime(2025, 3, 14),
      authorType: 'cp',
      isValidated: false,
    );

/// Badge prix de la carte info (le montant apparaît aussi dans le bloc
/// « contenu verrouillé », d'où le ciblage par style).
Finder _badgePrix() => find.byWidgetPredicate(
      (w) => w is Text && w.data == '2500 FC' && w.style?.fontSize == 13,
    );

Future<void> _pumpAt(WidgetTester tester, String auteur, Size size) async {
  tester.view.physicalSize = size;
  tester.view.devicePixelRatio = 1.0;
  addTearDown(tester.view.reset);

  await tester.pumpWidget(
    ProviderScope(
      // L'écran est un ConsumerStatefulWidget : il marque le résumé comme
      // « vu ». On l'isole ici du statut utilisateur (le `ProviderContainer`
      // réel construirait l'état d'authentification, qui dépend du stockage
      // sécurisé — un canal natif qui ne répond pas sous le faux temps de
      // `testWidgets`).
      overrides: [
        seenSummariesProvider.overrideWith(
          (ref) => SeenSummariesNotifier(userId: null),
        ),
      ],
      child: MaterialApp(
        theme: AppTheme.lightTheme,
        home: SummaryDetailsScreen(summary: _summary(auteur)),
      ),
    ),
  );
  await tester.pump(const Duration(milliseconds: 100));
}

void main() {
  final ecrans = <String, Size>{
    'petit mobile (320px)': const Size(320, 640),
    'mobile (360px)': const Size(360, 800),
    'large (800px)': const Size(800, 1000),
  };

  for (final ecran in ecrans.entries) {
    for (final nom in <String, String>{
      'nom court': _court,
      'nom moyen': _moyen,
      'nom très long': _tresLong,
      'nom sans espace': _sansEspace,
    }.entries) {
      testWidgets('${ecran.key} / ${nom.key} : aucun débordement',
          (WidgetTester tester) async {
        await _pumpAt(tester, nom.value, ecran.value);

        // Un RenderFlex overflow ferait échouer le test ici.
        expect(tester.takeException(), isNull);

        // Le prix et la date restent visibles et dans la carte.
        expect(_badgePrix(), findsOneWidget);
        expect(find.text('14/03/2025'), findsOneWidget);
      });
    }
  }

  testWidgets('nom très long sur mobile : le nom passe sur plusieurs lignes',
      (WidgetTester tester) async {
    await _pumpAt(tester, _tresLong, const Size(320, 640));

    final text = tester.widget<Text>(find.text(_tresLong));
    expect(text.maxLines, isNull); // plusieurs lignes autorisées

    final taille = tester.getSize(find.text(_tresLong));
    final hauteurLigne = tester.getSize(find.text('14/03/2025')).height;
    expect(taille.height, greaterThan(hauteurLigne * 1.5)); // a bien wrappé

    // Le prix reste dans la carte : son bord droit ne dépasse pas le contenu.
    final prix = tester.getRect(_badgePrix());
    expect(prix.right, lessThanOrEqualTo(320.0));
  });

  testWidgets('nom court sur grand écran : le prix reste aligné à droite',
      (WidgetTester tester) async {
    await _pumpAt(tester, _court, const Size(800, 1000));

    final prix = tester.getRect(_badgePrix());
    final date = tester.getRect(find.text('14/03/2025'));
    // Disposition horizontale conservée : date puis prix plus à droite,
    // et prix proche du bord droit (20 de padding + 16 de padding carte).
    expect(prix.left, greaterThan(date.right));
    expect(prix.right, greaterThan(800 - 100));
  });
}

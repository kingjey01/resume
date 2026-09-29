import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:resume_plus_clean/features/summaries/providers/seen_summaries_provider.dart';
import 'package:resume_plus_clean/features/summary_details/screens/summary_details_screen.dart';
import 'package:resume_plus_clean/models/summary.dart';
import 'package:resume_plus_clean/theme/app_theme.dart';
import 'package:resume_plus_clean/widgets/ai_content_view.dart';
import 'package:resume_plus_clean/widgets/audio_player_widget.dart';

/// Tache34, point 2 — la lecture audio démarre à la page affichée et va
/// jusqu'à la fin du résumé, sans repartir du début.
///
/// Test mené sur l'écran RÉEL : c'est la valeur de `text` reçue par
/// [AudioPlayerWidget] qui est vérifiée, pas une copie de la logique.

/// Trois sections `##` d'environ 400 caractères : le découpage de
/// [AiContentView] en fait trois pages (les sections de moins de 300
/// caractères seraient fusionnées avec la précédente).
String _contenu() {
  final buffer = StringBuffer();
  for (var section = 1; section <= 3; section++) {
    buffer.write('## Section $section\n\n');
    buffer.write('Phrase de la section $section. ' * 20);
    buffer.write('\n\n');
  }
  return buffer.toString();
}

Summary _summary() => Summary(
      id: 1,
      title: 'Résumé paginé',
      subject: 'Mathématiques',
      imageUrl: '',
      content: _contenu(),
      price: 0,
      isFree: true,
      authorName: 'Auteur',
      createdAt: DateTime(2025, 3, 14),
    );

Finder _flecheSuivante() => find.descendant(
      of: find.byType(AiContentView),
      matching: find.byIcon(Icons.arrow_forward_ios_rounded),
    );

Finder _flechePrecedente() => find.descendant(
      of: find.byType(AiContentView),
      matching: find.byIcon(Icons.arrow_back_ios_new_rounded),
    );

String _texteLu(WidgetTester tester) =>
    tester.widget<AudioPlayerWidget>(find.byType(AudioPlayerWidget)).text;

Future<ProviderContainer> _pomperEcran(WidgetTester tester) async {
  final container = ProviderContainer(
    // Statut « vu » isolé : le conteneur réel construirait l'état
    // d'authentification, qui dépend du stockage sécurisé — un canal natif
    // qui ne répond pas sous le faux temps de `testWidgets`.
    overrides: [
      seenSummariesProvider.overrideWith(
        (ref) => SeenSummariesNotifier(userId: null),
      ),
    ],
  );
  addTearDown(container.dispose);

  await tester.pumpWidget(
    UncontrolledProviderScope(
      container: container,
      child: MaterialApp(
        theme: AppTheme.lightTheme,
        home: SummaryDetailsScreen(summary: _summary()),
      ),
    ),
  );
  await tester.pump(const Duration(milliseconds: 100));
  return container;
}

Future<void> _allerPageSuivante(WidgetTester tester) async {
  await tester.ensureVisible(_flecheSuivante());
  await tester.pump();
  await tester.tap(_flecheSuivante());
  await tester.pump();
}

void main() {
  testWidgets('ouvrir le résumé le marque comme consulté', (tester) async {
    final container = await _pomperEcran(tester);
    // `markSeen` est différé après la première frame (Riverpod interdit de
    // modifier un provider pendant `initState`) : c'est ici qu'on vérifie que
    // le marquage a bien lieu à l'ouverture.
    expect(container.read(seenSummariesProvider), contains(1));
  });

  testWidgets('page 1 : le texte lu est le résumé complet', (tester) async {
    await _pomperEcran(tester);

    final texte = _texteLu(tester);
    expect(texte, contains('## Section 1'));
    expect(texte, contains('## Section 2'));
    expect(texte, contains('## Section 3'));
  });

  testWidgets(
      'page 2 : la lecture commence à la page affichée et continue jusqu\'à la fin',
      (tester) async {
    await _pomperEcran(tester);
    await _allerPageSuivante(tester);

    final texte = _texteLu(tester);
    // Plus de retour au début…
    expect(texte, isNot(contains('## Section 1')));
    // …démarrage sur la page affichée…
    expect(texte, contains('## Section 2'));
    // …et poursuite normale jusqu'à la fin du résumé.
    expect(texte, contains('## Section 3'));
  });

  testWidgets('page 3 : la lecture ne contient que la dernière page',
      (tester) async {
    await _pomperEcran(tester);
    await _allerPageSuivante(tester);
    await _allerPageSuivante(tester);

    final texte = _texteLu(tester);
    expect(texte, isNot(contains('## Section 1')));
    expect(texte, isNot(contains('## Section 2')));
    expect(texte, contains('## Section 3'));
  });

  testWidgets('revenir en arrière élargit de nouveau la lecture',
      (tester) async {
    await _pomperEcran(tester);
    await _allerPageSuivante(tester);
    await _allerPageSuivante(tester);
    expect(_texteLu(tester), isNot(contains('## Section 1')));

    await tester.tap(_flechePrecedente());
    await tester.pump();

    final texte = _texteLu(tester);
    expect(texte, contains('## Section 2'));
    expect(texte, contains('## Section 3'));
    expect(texte, isNot(contains('## Section 1')));
  });
}

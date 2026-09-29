import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:resume_plus_clean/features/auth/providers/auth_provider.dart';
import 'package:resume_plus_clean/features/home/widgets/summary_card.dart';
import 'package:resume_plus_clean/features/summaries/providers/seen_summaries_provider.dart';
import 'package:resume_plus_clean/models/summary.dart';
import 'package:resume_plus_clean/models/user.dart';
import 'package:resume_plus_clean/theme/app_theme.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Tache34, point 1 — pastille « résumé non consulté » et statut « vu ».
///
/// Vérifie :
///  - la pastille bleue est présente sur un résumé jamais ouvert ;
///  - elle disparaît dès que le résumé est marqué comme consulté ;
///  - le statut est PERSISTÉ et PROPRE À L'UTILISATEUR connecté.

User _user(int id) => User(
      id: id,
      username: 'user$id',
      email: 'user$id@exemple.test',
      groupe: 'ETUDIANT',
    );

Summary _summary(int id) => Summary(
      id: id,
      title: 'Résumé $id',
      subject: 'Mathématiques',
      imageUrl: '',
      content: 'Contenu du résumé $id',
      price: 0,
      isFree: true,
      authorName: 'Auteur',
      createdAt: DateTime(2025, 3, 14),
    );

/// La pastille : un petit rond bleu, même définition que les notifications
/// non lues (`AppTheme.primaryBlue`, `BoxShape.circle`).
Finder _pastille() => find.byWidgetPredicate((widget) {
      if (widget is! Container) return false;
      final decoration = widget.decoration;
      return decoration is BoxDecoration &&
          decoration.shape == BoxShape.circle &&
          decoration.color == AppTheme.primaryBlue;
    });

/// Monte une carte de résumé pour l'utilisateur [userId], et attend que le
/// stockage ait été relu.
Future<ProviderContainer> _pomperCarte(
  WidgetTester tester, {
  required int userId,
}) async {
  final container = ProviderContainer(
    overrides: [currentUserProvider.overrideWithValue(_user(userId))],
  );
  addTearDown(container.dispose);

  await tester.pumpWidget(
    UncontrolledProviderScope(
      container: container,
      child: MaterialApp(
        theme: AppTheme.lightTheme,
        home: Scaffold(body: SummaryCard(summary: _summary(42))),
      ),
    ),
  );

  // Le stockage passe par un canal natif : on attend sa réponse hors du faux
  // temps de `testWidgets`.
  await tester.runAsync(
    () => container.read(seenSummariesProvider.notifier).initialLoad,
  );
  await tester.pump();
  return container;
}

/// Crée un notifier comme le ferait l'application, en attendant sa lecture
/// initiale du stockage.
Future<SeenSummariesNotifier> _notifier(WidgetTester tester, int userId) async {
  late SeenSummariesNotifier notifier;
  await tester.runAsync(() async {
    notifier = SeenSummariesNotifier(userId: userId);
    await notifier.initialLoad;
  });
  return notifier;
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() {
    SharedPreferences.setMockInitialValues({});
  });

  testWidgets('résumé jamais ouvert : la pastille bleue est affichée',
      (tester) async {
    await _pomperCarte(tester, userId: 7);

    expect(_pastille(), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets(
      'ouvrir le résumé fait disparaître la pastille (sans rechargement de la liste)',
      (tester) async {
    final container = await _pomperCarte(tester, userId: 7);
    expect(_pastille(), findsOneWidget);

    // Ce que fait SummaryDetailsScreen à l'ouverture.
    await tester.runAsync(
      () => container.read(seenSummariesProvider.notifier).markSeen(42),
    );
    await tester.pump();

    expect(_pastille(), findsNothing);
  });

  testWidgets('la pastille des autres résumés n\'est pas affectée',
      (tester) async {
    final container = await _pomperCarte(tester, userId: 7);

    await tester.runAsync(
      () => container.read(seenSummariesProvider.notifier).markSeen(99),
    );
    await tester.pump();

    // Le résumé 42 (affiché) n'a pas été ouvert : sa pastille reste.
    expect(_pastille(), findsOneWidget);
  });

  testWidgets('le statut « vu » est persisté et relu au redémarrage',
      (tester) async {
    final premier = await _notifier(tester, 7);
    await tester.runAsync(() => premier.markSeen(42));

    // Nouvelle instance = redémarrage de l'application.
    final second = await _notifier(tester, 7);

    expect(second.state, contains(42));
  });

  testWidgets('le statut « vu » est propre à l\'utilisateur connecté',
      (tester) async {
    final userA = await _notifier(tester, 7);
    await tester.runAsync(() => userA.markSeen(42));

    // Un autre compte sur le même téléphone ne doit rien hériter.
    final userB = await _notifier(tester, 8);

    expect(userA.state, contains(42));
    expect(userB.state, isNot(contains(42)));
    expect(userB.state, isEmpty);
  });
}

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:resume_plus_clean/widgets/ai_content_view.dart';
import 'package:resume_plus_clean/widgets/math_formula_view.dart';
import 'package:resume_plus_clean/widgets/tech_block_widget.dart';

Widget _wrap(Widget child) => MaterialApp(
      home: Scaffold(body: SingleChildScrollView(child: child)),
    );

void main() {
  group('normalizeMathBlocks', () {
    test('convertit \$...\$ en bloc ```formula', () {
      final out = AiContentView.normalizeMathBlocks(
        'Avant\n\n\$\$f(x) = ax^2 + bx + c\$\$\n\nAprès',
      );
      expect(out, contains('```formula'));
      expect(out, contains('f(x) = ax^2 + bx + c'));
      expect(out, isNot(contains(r'$$')));
    });

    test('laisse le \$ inline intact', () {
      expect(
        AiContentView.normalizeMathBlocks('une somme de \$5 et \$10'),
        'une somme de \$5 et \$10',
      );
    });

    test('laisse un bloc de code intact', () {
      const code = '```python\nx = 5\n```';
      expect(AiContentView.normalizeMathBlocks(code), code);
    });
  });

  group('isFormulaLanguage', () {
    test('reconnait les langages de formule', () {
      for (final lang in ['latex', 'formula', 'math', 'equation', 'LATEX']) {
        expect(TechBlockWidget.isFormulaLanguage(lang), isTrue, reason: lang);
      }
    });

    test('ne confond pas code et formule', () {
      for (final lang in ['python', 'sql', 'text', '', null]) {
        expect(TechBlockWidget.isFormulaLanguage(lang), isFalse, reason: '$lang');
      }
    });
  });

  group('rendu intégré AiContentView', () {
    testWidgets('une formule \$\$...\$\$ obtient sa zone dédiée', (tester) async {
      await tester.pumpWidget(_wrap(const AiContentView(
        content: 'Intro\n\n\$\$E = mc^2\$\$\n\nFin',
      )));
      await tester.pump();

      expect(find.text('FORMULE'), findsOneWidget);
      // Tâche 30 : la formule n'est plus affichée en texte brut mais
      // typographiée par MathFormulaView (KaTeX). L'assertion d'origine
      // (`find.text('E = mc^2')`) vérifiait donc l'ancien comportement :
      // c'est exactement le LaTeX brut qu'on cherche à ne plus afficher.
      expect(find.byType(MathFormulaView), findsOneWidget);
      expect(find.text('E = mc^2'), findsNothing);
      // Les délimiteurs bruts ne doivent JAMAIS rester visibles.
      expect(find.textContaining(r'$$'), findsNothing);
    });

    testWidgets('un bloc de code garde son rendu habituel', (tester) async {
      await tester.pumpWidget(_wrap(const AiContentView(
        content: 'Intro\n\n```python\nx = 5\n```\n\nFin',
      )));
      await tester.pump();

      // Le code reste rendu comme avant : pas de zone « FORMULE ».
      expect(find.text('FORMULE'), findsNothing);
      expect(find.textContaining('x = 5'), findsOneWidget);
    });

    testWidgets('un bloc ```latex est aussi traité comme formule',
        (tester) async {
      await tester.pumpWidget(_wrap(const AiContentView(
        content: '```latex\n\\frac{a}{b}\n```',
      )));
      await tester.pump();

      expect(find.text('FORMULE'), findsOneWidget);
    });
  });
}

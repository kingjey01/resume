// Tâche 30 — Rendu des formules mathématiques, physiques et chimiques.
//
// Vérifie trois choses :
//   1. les formules RÉELLEMENT produites par DeepSeek sont rendues par le moteur
//      (donc plus affichées en LaTeX brut) ;
//   2. le rendu INLINE (`$...$`, `\(...\)`) fonctionne dans le fil du texte ;
//   3. aucune régression : texte normal, montants en `$` et blocs de code.
//
// `TexParser` n'est pas exporté par le package : on teste donc le comportement
// observable — une formule non analysable déclenche le repli `onErrorFallback`.
// C'est exactement ce que l'utilisateur voit.

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:resume_plus_clean/widgets/ai_content_view.dart';
import 'package:resume_plus_clean/widgets/math_formula_view.dart';

Widget _wrap(Widget child) => MaterialApp(
      home: Scaffold(body: SingleChildScrollView(child: child)),
    );

/// Le moteur de rendu sait-il typographier cette formule ?
///
/// Critère : quand le rendu réussit, la formule n'existe plus en tant que texte
/// (c'est un dessin typographique). Quand il échoue, le repli affiche le LaTeX
/// BRUT — donc la chaîne reste trouvable comme `Text`.
Future<bool> _formuleRendue(WidgetTester tester, String tex) async {
  await tester.pumpWidget(_wrap(
    MathFormulaView(tex: tex, display: true),
  ));
  await tester.pump();
  final brut = MathFormulaView.stripDelimiters(tex);
  return find.text(brut).evaluate().isEmpty;
}

void main() {
  // ─────────────────────────────────────────────────────────────
  // 1. Formules réelles (produites par DeepSeek)
  // ─────────────────────────────────────────────────────────────
  group('formules réelles analysables par le moteur de rendu', () {
    // Échantillon représentatif de ce que DeepSeek écrit dans les résumés.
    const cas = <String, String>{
      'vecteur (physique)': r'\vec{F} = m \vec{a}',
      'fraction': r'\frac{\pi}{2}',
      'fraction imbriquée': r'\frac{a+b}{c-d}',
      'puissance': r'E = mc^{2}',
      'indice (chimie)': r'H_{2}O',
      'formule chimique composée': r'2H_{2} + O_{2} \rightarrow 2H_{2}O',
      'intégrale': r'\int_{0}^{1} x \, dx',
      'somme': r'\sum_{i=1}^{n} i = \frac{n(n+1)}{2}',
      'racine': r'\sqrt{16} = 4',
      'racine cubique': r'\sqrt[3]{27} = 3',
      'lettres grecques': r'\alpha + \beta = \gamma',
      'opérateurs de comparaison': r'a \leq b \times c \geq d \neq e',
      'valeur absolue': r'|x| = \begin{cases} x & x \geq 0 \\ -x & x < 0 \end{cases}',
      'trigonométrie': r'\cos^{2}\theta + \sin^{2}\theta = 1',
      'limite': r'\lim_{x \to \infty} \frac{1}{x} = 0',
      'dérivée': r'\frac{d}{dx}\left(x^{2}\right) = 2x',
      'matrice': r'\begin{pmatrix} a & b \\ c & d \end{pmatrix}',
      'unité et texte': r'v = \frac{d}{t} \quad \text{en m/s}',
    };

    cas.forEach((nom, tex) {
      testWidgets('$nom : $tex', (tester) async {
        expect(await _formuleRendue(tester, tex), isTrue,
            reason: 'LaTeX non analysable, donc affiché brut : $tex');
      });
    });
  });

  // ─────────────────────────────────────────────────────────────
  // 2. Nettoyage des délimiteurs
  // ─────────────────────────────────────────────────────────────
  group('stripDelimiters', () {
    test('retire les délimiteurs de bloc', () {
      expect(MathFormulaView.stripDelimiters(r'$$E = mc^2$$'), r'E = mc^2');
      expect(MathFormulaView.stripDelimiters(r'\[E = mc^2\]'), r'E = mc^2');
    });

    test('retire les délimiteurs inline', () {
      expect(MathFormulaView.stripDelimiters(r'$x^2$'), r'x^2');
      expect(MathFormulaView.stripDelimiters(r'\(x^2\)'), r'x^2');
    });

    test('laisse une formule nue intacte', () {
      expect(MathFormulaView.stripDelimiters(r'\frac{a}{b}'), r'\frac{a}{b}');
    });
  });

  // ─────────────────────────────────────────────────────────────
  // 3. Rendu inline dans le fil du texte
  // ─────────────────────────────────────────────────────────────
  group('formules inline dans un résumé', () {
    testWidgets('un \$...\$ inline est rendu, pas affiché brut',
        (tester) async {
      await tester.pumpWidget(_wrap(const AiContentView(
        content: r'La force est $\vec{F} = m\vec{a}$ selon Newton.',
      )));
      await tester.pump();

      expect(find.byType(MathFormulaView), findsOneWidget);
      // Le texte autour reste du texte normal.
      expect(find.textContaining('La force est'), findsOneWidget);
      expect(find.textContaining('selon Newton'), findsOneWidget);
      // Plus aucune commande LaTeX brute à l'écran.
      expect(find.textContaining(r'\vec'), findsNothing);
      expect(find.textContaining(r'$'), findsNothing);
    });

    testWidgets('plusieurs formules inline sur une même ligne', (tester) async {
      await tester.pumpWidget(_wrap(const AiContentView(
        content: r'On a $\frac{\pi}{2}$ puis $\sqrt{16}$ et enfin $\alpha$.',
      )));
      await tester.pump();

      expect(find.byType(MathFormulaView), findsNWidgets(3));
      expect(find.textContaining(r'\frac'), findsNothing);
      expect(find.textContaining(r'\sqrt'), findsNothing);
    });

    testWidgets(r'la syntaxe \(...\) est aussi prise en charge', (tester) async {
      await tester.pumpWidget(_wrap(const AiContentView(
        content: r'Ici \(x^{2}\) en ligne.',
      )));
      await tester.pump();

      expect(find.byType(MathFormulaView), findsOneWidget);
      expect(find.textContaining(r'\('), findsNothing);
    });
  });

  // ─────────────────────────────────────────────────────────────
  // 4. Non-régression
  // ─────────────────────────────────────────────────────────────
  group('aucune régression', () {
    testWidgets('un résumé sans formule reste du texte normal', (tester) async {
      await tester.pumpWidget(_wrap(const AiContentView(
        content: '## Introduction\n\n'
            'Ce cours explique les bases simplement.\n\n'
            '- Premier point\n- Deuxième point\n',
      )));
      await tester.pump();

      expect(find.byType(MathFormulaView), findsNothing);
      expect(find.textContaining('Ce cours explique les bases'), findsOneWidget);
    });

    testWidgets('des montants en \$ ne sont PAS pris pour des formules',
        (tester) async {
      // Cas piège classique : une paire de prix ressemble à `$...$`.
      await tester.pumpWidget(_wrap(const AiContentView(
        content: 'Le résumé coûte \$5 et la version complète \$10.',
      )));
      await tester.pump();

      expect(find.byType(MathFormulaView), findsNothing);
      expect(find.textContaining('Le résumé coûte'), findsOneWidget);
    });

    testWidgets('un bloc de code Python garde son rendu', (tester) async {
      await tester.pumpWidget(_wrap(const AiContentView(
        content: 'Exemple :\n\n```python\nx = 5\nprint(x)\n```\n',
      )));
      await tester.pump();

      expect(find.text('FORMULE'), findsNothing);
      expect(find.textContaining('x = 5'), findsOneWidget);
      expect(find.byType(MathFormulaView), findsNothing);
    });

    testWidgets('un bloc de code contenant des \$ reste du code', (tester) async {
      await tester.pumpWidget(_wrap(const AiContentView(
        content: 'Bash :\n\n```bash\necho \$HOME\n```\n',
      )));
      await tester.pump();

      expect(find.text('FORMULE'), findsNothing);
      expect(find.byType(MathFormulaView), findsNothing);
    });

    testWidgets('une formule invalide reste lisible (repli)', (tester) async {
      // LaTeX volontairement cassé : ne doit pas faire échouer le rendu.
      await tester.pumpWidget(_wrap(const AiContentView(
        content: r'Formule cassée : $\frac{a}{$',
      )));
      await tester.pump();

      expect(tester.takeException(), isNull);
    });
  });
}

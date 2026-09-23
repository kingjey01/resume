import 'package:flutter/material.dart';
import 'package:flutter_math_fork/flutter_math.dart';
import 'package:google_fonts/google_fonts.dart';

/// Rendu d'une formule LaTeX (maths, physique, chimie) produite par DeepSeek.
///
/// Le LaTeX est typographié par `flutter_math_fork` (port Dart de KaTeX) :
/// vecteurs, fractions, puissances, indices, racines, intégrales, sommes,
/// lettres grecques, opérateurs… au lieu d'afficher les commandes brutes
/// (`$`, `\vec{}`, `\frac{}{}`, `\,`) comme le faisait l'application.
///
/// Utilisé à deux endroits :
///   - [TechBlockWidget] pour les formules de BLOC (bandeau « FORMULE ») ;
///   - [AiContentView] pour les formules INLINE (`$...$`, `\(...\)`) dans le fil
///     du texte.
///
/// ⚠️ Sécurité : si le LaTeX n'est pas analysable, [Math.tex] appelle
/// [onErrorFallback] et on réaffiche alors la formule BRUTE — c'est-à-dire
/// exactement ce que montrait l'application avant cette tâche. Une formule
/// exotique reste donc lisible au lieu de faire échouer le rendu.
class MathFormulaView extends StatelessWidget {
  /// Formule LaTeX, délimiteurs éventuels inclus (`$…$`, `$$…$$`, `\[…\]`).
  final String tex;

  /// `true` pour une formule de bloc (mise en avant, style « display »),
  /// `false` pour une formule insérée dans une phrase (style « text »).
  final bool display;

  final double fontSize;

  const MathFormulaView({
    super.key,
    required this.tex,
    this.display = true,
    this.fontSize = 15,
  });

  /// Retire les délimiteurs LaTeX (`$`, `$$`, `\[`, `\]`, `\(`, `\)`) restés
  /// autour de la formule. Le backend transmet un contenu brut, mais on reste
  /// tolérant : les formules anciennes en base peuvent en contenir.
  static String stripDelimiters(String raw) {
    var formule = raw.trim();

    // Délimiteurs de bloc et inline, ouvrants puis fermants.
    // Les `$$` / `\[` sont testés AVANT les `$` / `\(` simples, sinon un
    // délimiteur double serait retiré en deux fois.
    final ouvrants = <RegExp>[
      RegExp(r'^\\\['), RegExp(r'^\\\('), RegExp(r'^\$\$'), RegExp(r'^\$'),
    ];
    final fermants = <RegExp>[
      RegExp(r'\\\]$'), RegExp(r'\\\)$'), RegExp(r'\$\$$'), RegExp(r'\$$'),
    ];

    for (final re in ouvrants) {
      formule = formule.replaceFirst(re, '');
    }
    for (final re in fermants) {
      formule = formule.replaceFirst(re, '');
    }
    return formule.trim();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final formule = stripDelimiters(tex);

    if (formule.isEmpty) return const SizedBox.shrink();

    final style = GoogleFonts.poppins(
      fontSize: fontSize,
      height: 1.6,
      color: theme.colorScheme.onSurface,
    );

    final rendu = Math.tex(
      formule,
      mathStyle: display ? MathStyle.display : MathStyle.text,
      textStyle: style,
      // LaTeX non analysable → on retombe sur le texte brut (rendu d'avant).
      onErrorFallback: (erreur) => Text(
        formule,
        textAlign: display ? TextAlign.center : TextAlign.start,
        style: style.copyWith(height: 1.5),
      ),
    );

    // En bloc, la formule est centrée et aérée, comme un objet à part.
    if (display) {
      return SizedBox(
        width: double.infinity,
        child: Padding(
          padding: const EdgeInsets.symmetric(vertical: 4),
          child: Center(
            child: SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: rendu,
            ),
          ),
        ),
      );
    }

    return rendu;
  }
}

import 'package:flutter/material.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:markdown/markdown.dart' as md;
import 'ai_content_view.dart';
import 'math_formula_view.dart';

/// Widget réutilisable pour afficher du contenu technique (code, formule,
/// algorithme, commande, pseudo-code) dans les QCM et leurs résultats.
///
/// Utilise [MarkdownBody] avec le MÊME style que [AiContentView] pour garantir
/// un rendu visuel identique à celui des détails de résumé.
///
/// S'affiche automatiquement si [codeBlock] est non nul et non vide.
class TechBlockWidget extends StatelessWidget {
  final String? codeLanguage;
  final String? codeBlock;

  /// Dessiner le cadre (bordure + coins arrondis + marge) autour du bloc.
  ///
  /// À laisser à `false` quand l'appelant encadre DÉJÀ le bloc — c'est le cas
  /// des résumés : flutter_markdown enveloppe tout bloc de code dans
  /// `codeblockDecoration`. Sans ce drapeau on obtiendrait un cadre dans le
  /// cadre.
  final bool withFrame;

  const TechBlockWidget({
    super.key,
    this.codeLanguage,
    this.codeBlock,
    this.withFrame = true,
  });

  bool get hasContent => codeBlock != null && codeBlock!.trim().isNotEmpty;

  /// Le langage désigne-t-il une FORMULE (maths, physique, chimie, calcul,
  /// équation…) plutôt que du code ?
  ///
  /// Ces blocs sont rendus dans une zone dédiée, en typographie de lecture —
  /// pas en police monospace. Le jeu de langages est celui que produit le
  /// backend (`code_language: "latex" | "formula" | "math"`) et celui des
  /// clôtures Markdown ` ```latex `.
  static bool isFormulaLanguage(String? language) {
    const formulaLanguages = <String>{
      'latex',
      'formula',
      'formule',
      'math',
      'maths',
      'mathematics',
      'equation',
    };
    return formulaLanguages.contains(language?.trim().toLowerCase() ?? '');
  }

  @override
  Widget build(BuildContext context) {
    if (!hasContent) return const SizedBox.shrink();

    final lang = codeLanguage?.trim().toLowerCase() ?? '';
    final label = _languageLabel(lang);
    final icon = _languageIcon(lang);

    final content = Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisSize: MainAxisSize.min,
      children: [
        _buildHeader(context, icon, label),
        if (isFormulaLanguage(lang))
          _buildFormulaBody(context)
        else
          _buildCodeBody(context, lang),
      ],
    );

    if (!withFrame) return content;

    return Container(
      width: double.infinity,
      margin: const EdgeInsets.symmetric(vertical: 8),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(10),
        border: Border.all(
          color: Theme.of(context).brightness == Brightness.dark
              ? const Color(0xFF3A3A4E)
              : const Color(0xFFE0E0E8),
          width: 1,
        ),
      ),
      child: content,
    );
  }

  /// Bandeau supérieur : icône + libellé du langage.
  Widget _buildHeader(BuildContext context, IconData icon, String label) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.fromLTRB(12, 8, 12, 8),
      decoration: BoxDecoration(
        color: Theme.of(context).brightness == Brightness.dark
            ? const Color(0xFF252540)
            : const Color(0xFFE8E8F0),
        borderRadius: const BorderRadius.only(
          topLeft: Radius.circular(9),
          topRight: Radius.circular(9),
        ),
      ),
      child: Row(
        children: [
          Icon(icon, size: 16, color: Theme.of(context).colorScheme.primary),
          const SizedBox(width: 6),
          Text(
            label,
            style: GoogleFonts.poppins(
              fontSize: 11,
              fontWeight: FontWeight.w600,
              color: Theme.of(context).colorScheme.primary,
              letterSpacing: 0.5,
            ),
          ),
        ],
      ),
    );
  }

  /// Corps « code » : rendu via flutter_markdown (MÊME style que AiContentView).
  Widget _buildCodeBody(BuildContext context, String lang) {
    // Envelopper le code dans un bloc de code Markdown
    // pour que MarkdownBody le rende comme dans AiContentView
    final markdownContent = '```$lang\n${codeBlock!.trim()}\n```';

    return MarkdownBody(
      data: markdownContent,
      selectable: true,
      styleSheet: AiContentView.sharedStyleSheet(context),
      extensionSet: md.ExtensionSet.gitHubFlavored,
      softLineBreak: true,
    );
  }

  /// Corps « formule » : même fond que les blocs de code pour rester dans la
  /// même famille visuelle, mais avec un VRAI rendu mathématique (KaTeX) au lieu
  /// des commandes LaTeX brutes — une formule n'est pas du code.
  Widget _buildFormulaBody(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.fromLTRB(16, 14, 16, 14),
      decoration: BoxDecoration(
        color: isDark ? const Color(0xFF1E1E2E) : const Color(0xFFF5F5FA),
        // Coins bas arrondis : sans cadre, le corps dépasserait sinon du cadre
        // arrondi du parent (le Container englobant n'a pas de `clipBehavior`).
        borderRadius: const BorderRadius.only(
          bottomLeft: Radius.circular(9),
          bottomRight: Radius.circular(9),
        ),
      ),
      child: MathFormulaView(
        tex: codeBlock!,
        display: true,
        fontSize: 15,
      ),
    );
  }

  IconData _languageIcon(String lang) {
    switch (lang) {
      case 'latex':
      case 'formula':
      case 'math':
      case 'equation':
      case 'mathematics':
      case 'maths':
      case 'formule':
        return Icons.functions_rounded;
      case 'command':
      case 'bash':
      case 'shell':
      case 'terminal':
        return Icons.terminal_rounded;
      case 'algorithm':
      case 'pseudocode':
        return Icons.account_tree_rounded;
      default:
        return Icons.code_rounded;
    }
  }

  String _languageLabel(String lang) {
    switch (lang) {
      case 'python':
        return 'PYTHON';
      case 'javascript':
        return 'JAVASCRIPT';
      case 'typescript':
        return 'TYPESCRIPT';
      case 'dart':
        return 'DART';
      case 'java':
        return 'JAVA';
      case 'kotlin':
        return 'KOTLIN';
      case 'swift':
        return 'SWIFT';
      case 'c':
      case 'cpp':
      case 'c++':
        return 'C / C++';
      case 'csharp':
        return 'C#';
      case 'go':
        return 'GO';
      case 'rust':
        return 'RUST';
      case 'sql':
        return 'SQL';
      case 'html':
        return 'HTML';
      case 'css':
        return 'CSS';
      case 'bash':
      case 'shell':
      case 'command':
      case 'terminal':
        return 'COMMANDE';
      case 'latex':
      case 'formula':
      case 'math':
      case 'equation':
      case 'mathematics':
      case 'maths':
      case 'formule':
        return 'FORMULE';
      case 'algorithm':
        return 'ALGORITHME';
      case 'pseudocode':
        return 'PSEUDO-CODE';
      case 'json':
        return 'JSON';
      case 'yaml':
        return 'YAML';
      case 'xml':
        return 'XML';
      case 'text':
        return 'TEXTE';
      default:
        return lang.toUpperCase();
    }
  }
}

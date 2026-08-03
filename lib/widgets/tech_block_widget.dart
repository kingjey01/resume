import 'package:flutter/material.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:markdown/markdown.dart' as md;
import 'ai_content_view.dart';

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

  const TechBlockWidget({
    super.key,
    this.codeLanguage,
    this.codeBlock,
  });

  bool get hasContent => codeBlock != null && codeBlock!.trim().isNotEmpty;

  @override
  Widget build(BuildContext context) {
    if (!hasContent) return const SizedBox.shrink();

    final lang = codeLanguage?.trim().toLowerCase() ?? '';
    final label = _languageLabel(lang);
    final icon = _languageIcon(lang);

    // Envelopper le code dans un bloc de code Markdown
    // pour que MarkdownBody le rende comme dans AiContentView
    final markdownContent = '```$lang\n${codeBlock!.trim()}\n```';

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
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          // Header avec icône et langage
          Container(
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
          ),
          // Contenu technique rendu via flutter_markdown (MÊME style que AiContentView)
          MarkdownBody(
            data: markdownContent,
            selectable: true,
            styleSheet: AiContentView.sharedStyleSheet(context),
            extensionSet: md.ExtensionSet.gitHubFlavored,
            softLineBreak: true,
          ),
        ],
      ),
    );
  }

  IconData _languageIcon(String lang) {
    switch (lang) {
      case 'latex':
      case 'formula':
      case 'math':
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

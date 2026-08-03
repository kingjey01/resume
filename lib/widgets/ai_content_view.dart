import 'package:flutter/material.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:resume_plus_clean/theme/app_theme.dart';
import 'package:markdown/markdown.dart' as md;

/// Widget d'affichage de contenu IA avec rendu Markdown complet.
///
/// Utilise [flutter_markdown] pour interpréter le Markdown produit par DeepSeek.
/// Supporte :
///   - Blocs de code (```lang) avec fond gris + police monospace
///   - Tableaux Markdown
///   - Citations (>)
///   - Listes ordonnées et non ordonnées
///   - Titres ##, ###
///   - Gras et italique
///   - Sélection de texte
///   - Pagination intelligente par sections
class AiContentView extends StatefulWidget {
  final String content;
  final bool isSelectable;

  const AiContentView({
    super.key,
    required this.content,
    this.isSelectable = true,
  });

  /// Style sheet Markdown complet (clair/sombre) utilisable par
  /// AiContentView ET TechBlockWidget pour un rendu identique.
  static MarkdownStyleSheet sharedStyleSheet(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    return MarkdownStyleSheet(
      p: GoogleFonts.poppins(
        fontSize: 15, height: 1.7,
        color: theme.colorScheme.onSurface, fontWeight: FontWeight.w400,
      ),
      pPadding: const EdgeInsets.symmetric(vertical: 2),
      h2: GoogleFonts.poppins(
        fontSize: 18, fontWeight: FontWeight.w700,
        color: theme.colorScheme.primary, height: 1.3,
      ),
      h2Padding: const EdgeInsets.only(top: 20, bottom: 8),
      h3: GoogleFonts.poppins(
        fontSize: 16, fontWeight: FontWeight.w600,
        color: theme.colorScheme.onSurface, height: 1.3,
      ),
      h3Padding: const EdgeInsets.only(top: 16, bottom: 6),
      listBullet: GoogleFonts.poppins(
        fontSize: 15, color: theme.colorScheme.primary, fontWeight: FontWeight.w700,
      ),
      listBulletPadding: const EdgeInsets.only(right: 8),
      listIndent: 24,
      strong: GoogleFonts.poppins(
        fontWeight: FontWeight.w700, color: theme.colorScheme.onSurface,
      ),
      em: GoogleFonts.poppins(
        fontStyle: FontStyle.italic, color: theme.colorScheme.onSurface,
      ),
      blockquoteDecoration: BoxDecoration(
        color: theme.colorScheme.primary.withOpacity(0.06),
        border: Border(left: BorderSide(color: theme.colorScheme.primary.withOpacity(0.4), width: 3)),
        borderRadius: BorderRadius.circular(4),
      ),
      blockquotePadding: const EdgeInsets.fromLTRB(14, 8, 14, 8),
      code: GoogleFonts.jetBrainsMono(
        fontSize: 13,
        color: isDark ? const Color(0xFFE8E8E8) : const Color(0xFF1A1A2E),
        backgroundColor: isDark ? const Color(0xFF2A2A3E) : const Color(0xFFF0F0F5),
      ),
      codeblockDecoration: BoxDecoration(
        color: isDark ? const Color(0xFF1E1E2E) : const Color(0xFFF5F5FA),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: isDark ? const Color(0xFF3A3A4E) : const Color(0xFFE0E0E8), width: 1),
      ),
      codeblockPadding: const EdgeInsets.fromLTRB(16, 12, 16, 12),
      tableHead: GoogleFonts.poppins(fontWeight: FontWeight.w600, fontSize: 13, color: theme.colorScheme.onSurface),
      tableBody: GoogleFonts.poppins(fontSize: 13, color: theme.colorScheme.onSurface.withOpacity(0.85)),
      tableBorder: TableBorder.all(color: theme.dividerTheme.color ?? (isDark ? Colors.grey.shade700 : Colors.grey.shade300), width: 1),
      tableColumnWidth: const FlexColumnWidth(),
      tableCellsPadding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
      horizontalRuleDecoration: BoxDecoration(
        border: Border(top: BorderSide(color: theme.dividerTheme.color ?? Colors.grey.shade300, width: 1)),
      ),
      a: GoogleFonts.poppins(color: theme.colorScheme.primary, decoration: TextDecoration.underline),
    );
  }

  @override
  State<AiContentView> createState() => _AiContentViewState();
}

class _AiContentViewState extends State<AiContentView> {
  int _currentPage = 0;
  final List<String> _pages = [];

  @override
  void initState() {
    super.initState();
    _splitContent();
  }

  @override
  void didUpdateWidget(AiContentView oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.content != widget.content) {
      _splitContent();
    }
  }

  /// Découpe le contenu en pages.
  ///
  /// Méthode 1 (propre) : par sections `##` quand elles existent.
  /// Méthode 2 (fallback) : par blocs de ~1800 caractères, en respectant
  /// les sauts de paragraphe pour ne pas couper en milieu de phrase.
  ///
  /// Tant qu'il y a plus de 2000 caractères, il y a AU MOINS 2 pages.
  static const int _charsPerPage = 1800;

  void _splitContent() {
    _pages.clear();
    final content = widget.content.trim();
    if (content.isEmpty) return;

    // ── Méthode 1 : découpage par sections ## ───────────────────
    final sectionPattern = RegExp(r'^##\s+(.*)$', multiLine: true);
    final matches = sectionPattern.allMatches(content).toList();

    if (matches.length >= 2) {
      // Assez de sections → page par section
      for (int i = 0; i < matches.length; i++) {
        final start = matches[i].start;
        final end = (i + 1 < matches.length) ? matches[i + 1].start : content.length;
        final section = content.substring(start, end).trim();

        if (section.length < 300 && _pages.isNotEmpty) {
          // Trop petite → fusionner avec la page précédente
          _pages.last += '\n\n$section';
        } else {
          _pages.add(section);
        }
      }
    }

    // ── Méthode 2 : découpage par caractères (fallback) ─────────
    if (_pages.length < 2 && content.length > _charsPerPage) {
      _pages.clear();
      final paragraphs = content.split('\n\n');
      String buffer = '';

      for (final para in paragraphs) {
        if (buffer.length + para.length > _charsPerPage && buffer.isNotEmpty) {
          _pages.add(buffer.trim());
          buffer = '$para\n\n';
        } else {
          buffer += '$para\n\n';
        }
      }
      if (buffer.trim().isNotEmpty) _pages.add(buffer.trim());
    }

    // ── Fallback final : tout en une seule page ─────────────────
    if (_pages.isEmpty) _pages.add(content);

    if (_currentPage >= _pages.length) _currentPage = 0;
  }

  @override
  Widget build(BuildContext context) {
    if (widget.content.isEmpty) return const SizedBox.shrink();
    if (_pages.isEmpty) return const SizedBox.shrink();

    final pageContent = _pages[_currentPage];

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Rendu Markdown de la page courante
        Theme(
          data: Theme.of(context).copyWith(
            textTheme: Theme.of(context).textTheme.apply(fontFamily: 'Poppins'),
          ),
          child: MarkdownBody(
            data: pageContent,
            selectable: widget.isSelectable,
            styleSheet: AiContentView.sharedStyleSheet(context),
            extensionSet: md.ExtensionSet.gitHubFlavored,
            builders: {
              // Personnalisation supplémentaire si nécessaire
            },
          ),
        ),

        // Pagination (si plus d'une page)
        if (_pages.length > 1) ...[
          const SizedBox(height: 24),
          const Divider(height: 1),
          const SizedBox(height: 12),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              _buildNavButton(
                icon: Icons.arrow_back_ios_new_rounded,
                onPressed: _currentPage > 0
                    ? () => setState(() => _currentPage--)
                    : null,
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
                decoration: BoxDecoration(
                  color: Theme.of(context).colorScheme.primary.withOpacity(0.05),
                  borderRadius: BorderRadius.circular(20),
                ),
                child: Text(
                  '${_currentPage + 1} / ${_pages.length}',
                  style: GoogleFonts.poppins(
                    fontSize: 13,
                    fontWeight: FontWeight.w700,
                    color: Theme.of(context).colorScheme.primary,
                  ),
                ),
              ),
              _buildNavButton(
                icon: Icons.arrow_forward_ios_rounded,
                onPressed: _currentPage < _pages.length - 1
                    ? () => setState(() => _currentPage++)
                    : null,
              ),
            ],
          ),
        ],
      ],
    );
  }

  Widget _buildNavButton({
    required IconData icon,
    VoidCallback? onPressed,
  }) {
    final theme = Theme.of(context);
    final bool isDisabled = onPressed == null;
    final color = isDisabled
        ? theme.colorScheme.onSurface.withOpacity(0.3)
        : theme.colorScheme.primary;

    return InkWell(
      onTap: onPressed,
      borderRadius: BorderRadius.circular(12),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
        decoration: BoxDecoration(
          border: Border.all(
            color: color.withOpacity(0.2),
            width: 1,
          ),
          borderRadius: BorderRadius.circular(12),
        ),
        child: Icon(icon, size: 16, color: color),
      ),
    );
  }
}

import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:resume_plus_clean/models/summary.dart';
import 'package:resume_plus_clean/features/summary_details/screens/summary_details_screen.dart';
import 'package:resume_plus_clean/theme/app_theme.dart';

class SummaryCard extends StatelessWidget {
  final Summary summary;
  final bool showAuthorBadge;

  const SummaryCard({super.key, required this.summary, this.showAuthorBadge = false});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return LayoutBuilder(
      builder: (context, constraints) {
        final isNarrow = constraints.maxWidth < 200;
        return _buildCardContent(context, theme, isNarrow);
      },
    );
  }

  Widget _buildCardContent(BuildContext context, ThemeData theme, bool isNarrow) {
    return Container(
      decoration: BoxDecoration(
        color: theme.colorScheme.surface,
        borderRadius: BorderRadius.circular(16),
        boxShadow: AppTheme.softShadow,
      ),
      clipBehavior: Clip.antiAlias,
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          borderRadius: BorderRadius.circular(16),
          onTap: () {
            Navigator.of(context).push(MaterialPageRoute(
              builder: (context) => SummaryDetailsScreen(summary: summary),
            ));
          },
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              // Image / placeholder avec gradient
              Container(
                height: 80,
                width: double.infinity,
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                    colors: [
                      AppTheme.primaryBlue.withValues(alpha:0.08),
                      AppTheme.accentBlue.withValues(alpha:0.12),
                    ],
                  ),
                ),
                child: Stack(
                  children: [
                    Positioned.fill(
                      child: summary.imageUrl.isNotEmpty
                          ? Image.network(
                              summary.imageUrl,
                              fit: BoxFit.cover,
                              errorBuilder: (context, error, stackTrace) => _buildPlaceholder(),
                            )
                          : _buildPlaceholder(),
                    ),
                    if (showAuthorBadge)
                      Positioned(
                        top: 6,
                        right: 6,
                        child: Container(
                          padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 3),
                          decoration: BoxDecoration(
                            color: summary.isAiGenerated
                                ? const Color(0xFF7C3AED).withValues(alpha:0.9)
                                : AppTheme.primaryBlue.withValues(alpha:0.9),
                            borderRadius: BorderRadius.circular(6),
                          ),
                          child: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Icon(
                                summary.isAiGenerated ? Icons.smart_toy_rounded : Icons.person_rounded,
                                size: 10,
                                color: Colors.white,
                              ),
                              const SizedBox(width: 3),
                              Text(
                                summary.isAiGenerated ? 'IA' : 'CP',
                                style: const TextStyle(color: Colors.white, fontSize: 9, fontWeight: FontWeight.w700),
                              ),
                            ],
                          ),
                        ),
                      ),
                  ],
                ),
              ),

              // Contenu
              Padding(
                padding: const EdgeInsets.fromLTRB(12, 10, 12, 12),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    // Titre
                    Text(
                      summary.title,
                      style: theme.textTheme.titleSmall?.copyWith(
                        fontWeight: FontWeight.w600,
                        color: theme.colorScheme.onSurface,
                        fontSize: 13,
                      ),
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                    ),
                    const SizedBox(height: 4),
                    // Matière
                    Text(
                      summary.subject,
                      style: theme.textTheme.bodySmall?.copyWith(
                        color: theme.colorScheme.onSurface.withValues(alpha:0.6),
                        fontSize: 11,
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                    const SizedBox(height: 8),
                    // Meta: professeur + prix + date + auteur (responsive)
                    isNarrow
                        ? _buildCompactMetaRow(theme)
                        : _buildWideMetaRow(theme),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildCompactMetaRow(ThemeData theme) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisSize: MainAxisSize.min,
      children: [
        if (summary.professorName.isNotEmpty)
          Text(
            summary.professorName,
            style: TextStyle(
              color: const Color(0xFF9C27B0).withValues(alpha: 0.8),
              fontSize: 9,
              fontWeight: FontWeight.w500,
            ),
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
        const SizedBox(height: 4),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
          decoration: BoxDecoration(
            color: summary.isFree
                ? AppTheme.success.withValues(alpha: 0.1)
                : AppTheme.primaryBlue.withValues(alpha: 0.1),
            borderRadius: BorderRadius.circular(20),
          ),
          child: Text(
            summary.isFree ? 'Gratuit' : '${summary.price.toStringAsFixed(0)} FC',
            style: TextStyle(
              color: summary.isFree ? AppTheme.success : AppTheme.primaryBlue,
              fontSize: 10,
              fontWeight: FontWeight.w600,
            ),
          ),
        ),
        const SizedBox(height: 2),
        Text(
          DateFormat('dd/MM/yyyy').format(summary.createdAt),
          style: TextStyle(
            color: theme.colorScheme.onSurface.withValues(alpha: 0.5),
            fontSize: 9,
            fontWeight: FontWeight.w500,
          ),
        ),
        const SizedBox(height: 2),
        Text(
          summary.authorName,
          style: TextStyle(
            color: theme.colorScheme.onSurface.withValues(alpha: 0.5),
            fontSize: 9,
            fontWeight: FontWeight.w500,
          ),
          maxLines: 1,
          overflow: TextOverflow.ellipsis,
        ),
      ],
    );
  }

  Widget _buildWideMetaRow(ThemeData theme) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        if (summary.professorName.isNotEmpty) ...[
          Row(
            children: [
              Icon(Icons.school_rounded, size: 12, color: const Color(0xFF9C27B0).withValues(alpha: 0.8)),
              const SizedBox(width: 4),
              Flexible(
                child: Text(
                  summary.professorName,
                  style: TextStyle(
                    color: const Color(0xFF9C27B0).withValues(alpha: 0.8),
                    fontSize: 10,
                    fontWeight: FontWeight.w500,
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
            ],
          ),
          const SizedBox(height: 4),
        ],
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
              decoration: BoxDecoration(
                color: summary.isFree
                    ? AppTheme.success.withValues(alpha: 0.1)
                    : AppTheme.primaryBlue.withValues(alpha: 0.1),
                borderRadius: BorderRadius.circular(20),
              ),
              child: Text(
                summary.isFree ? 'Gratuit' : '${summary.price.toStringAsFixed(0)} FC',
                style: TextStyle(
                  color: summary.isFree ? AppTheme.success : AppTheme.primaryBlue,
                  fontSize: 11,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
            Row(
              children: [
                Icon(Icons.calendar_today_rounded, size: 11, color: theme.colorScheme.onSurface.withValues(alpha: 0.45)),
                const SizedBox(width: 3),
                Text(
                  DateFormat('dd/MM/yyyy').format(summary.createdAt),
                  style: TextStyle(
                    color: theme.colorScheme.onSurface.withValues(alpha: 0.5),
                    fontSize: 10,
                    fontWeight: FontWeight.w500,
                  ),
                ),
              ],
            ),
          ],
        ),
        const SizedBox(height: 4),
        Row(
          children: [
            Icon(Icons.person_outline_rounded, size: 12, color: theme.colorScheme.onSurface.withValues(alpha: 0.45)),
            const SizedBox(width: 3),
            Flexible(
              child: Text(
                summary.authorName,
                style: TextStyle(
                  color: theme.colorScheme.onSurface.withValues(alpha: 0.5),
                  fontSize: 10,
                  fontWeight: FontWeight.w500,
                ),
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildPlaceholder() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.menu_book_rounded, size: 32, color: AppTheme.primaryBlue.withValues(alpha:0.4)),
          const SizedBox(height: 4),
          Text(
            'Résumé',
            style: TextStyle(
              color: AppTheme.primaryBlue.withValues(alpha:0.4),
              fontSize: 11,
              fontWeight: FontWeight.w500,
            ),
          ),
        ],
      ),
    );
  }
}

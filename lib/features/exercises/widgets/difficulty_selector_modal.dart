import 'package:flutter/material.dart';
import 'package:resume_plus_clean/theme/app_theme.dart';

/// Bottom sheet de sélection de la difficulté pour la génération d'exercices.
/// S'affiche depuis le bas de l'écran, limité au centre de l'interface.
class DifficultySelectorModal extends StatelessWidget {
  final VoidCallback onEasySelected;
  final VoidCallback onMediumSelected;
  final VoidCallback onHardSelected;
  final VoidCallback onCancel;
  final bool isLoading;

  const DifficultySelectorModal({
    super.key,
    required this.onEasySelected,
    required this.onMediumSelected,
    required this.onHardSelected,
    required this.onCancel,
    this.isLoading = false,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final bottomPadding = MediaQuery.of(context).padding.bottom;

    return SafeArea(
      top: false,
      child: Container(
        padding: EdgeInsets.fromLTRB(24, 12, 24, bottomPadding + 20),
        decoration: BoxDecoration(
          color: theme.colorScheme.surface,
          borderRadius: const BorderRadius.vertical(top: Radius.circular(24)),
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            // Poignée de glissement
            Container(
              width: 40,
              height: 4,
              decoration: BoxDecoration(
                color: theme.colorScheme.onSurface.withOpacity(0.2),
                borderRadius: BorderRadius.circular(2),
              ),
            ),
            const SizedBox(height: 20),

            // Header
            Container(
              width: 60,
              height: 60,
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: [AppTheme.primaryBlue, AppTheme.primaryBlueLight],
                ),
                shape: BoxShape.circle,
                boxShadow: [
                  BoxShadow(
                    color: AppTheme.primaryBlue.withOpacity(0.3),
                    blurRadius: 12,
                    offset: const Offset(0, 4),
                  ),
                ],
              ),
              child: const Icon(
                Icons.quiz_rounded,
                color: Colors.white,
                size: 32,
              ),
            ),
            const SizedBox(height: 16),

            Text(
              'Choisir la difficulté',
              style: theme.textTheme.titleLarge?.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 8),

            Text(
              'Sélectionnez le niveau de difficulté pour votre exercice.\nDes questions adaptées seront générées.',
              textAlign: TextAlign.center,
              style: theme.textTheme.bodyMedium?.copyWith(
                color: theme.colorScheme.onSurface.withOpacity(0.6),
              ),
            ),
            const SizedBox(height: 24),

            // Options de difficulté
            _DifficultyOption(
              icon: Icons.sentiment_very_satisfied_rounded,
              title: 'Facile',
              subtitle: 'Questions factuelles et mémorisation',
              color: const Color(0xFF10B981), // Vert
              gradientColors: const [Color(0xFF10B981), Color(0xFF34D399)],
              onTap: isLoading ? null : onEasySelected,
              isLoading: isLoading,
            ),
            const SizedBox(height: 12),

            _DifficultyOption(
              icon: Icons.sentiment_satisfied_rounded,
              title: 'Moyen',
              subtitle: 'Compréhension et application des concepts',
              color: const Color(0xFFF59E0B), // Orange
              gradientColors: const [Color(0xFFF59E0B), Color(0xFFFBBF24)],
              onTap: isLoading ? null : onMediumSelected,
              isLoading: isLoading,
              isRecommended: true,
            ),
            const SizedBox(height: 12),

            _DifficultyOption(
              icon: Icons.sentiment_very_dissatisfied_rounded,
              title: 'Difficile',
              subtitle: 'Analyse critique et raisonnement avancé',
              color: const Color(0xFFEF4444), // Rouge
              gradientColors: const [Color(0xFFEF4444), Color(0xFFF87171)],
              onTap: isLoading ? null : onHardSelected,
              isLoading: isLoading,
            ),
            const SizedBox(height: 20),

            // Bouton annuler
            SizedBox(
              width: double.infinity,
              child: TextButton(
                onPressed: isLoading ? null : onCancel,
                style: TextButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 12),
                ),
                child: Text(
                  'Annuler',
                  style: theme.textTheme.bodyLarge?.copyWith(
                    color: theme.colorScheme.onSurface.withOpacity(0.6),
                    fontWeight: FontWeight.w500,
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _DifficultyOption extends StatelessWidget {
  final IconData icon;
  final String title;
  final String subtitle;
  final Color color;
  final List<Color> gradientColors;
  final VoidCallback? onTap;
  final bool isLoading;
  final bool isRecommended;

  const _DifficultyOption({
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.color,
    required this.gradientColors,
    this.onTap,
    this.isLoading = false,
    this.isRecommended = false,
  });

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(16),
        child: Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            gradient: LinearGradient(
              colors: onTap != null
                  ? [gradientColors[0].withOpacity(0.1), gradientColors[1].withOpacity(0.05)]
                  : [Colors.grey[100]!, Colors.grey[50]!],
            ),
            borderRadius: BorderRadius.circular(16),
            border: Border.all(
              color: onTap != null ? gradientColors[0].withOpacity(0.3) : Colors.grey[300]!,
              width: 2,
            ),
          ),
          child: Row(
            children: [
              // Icon
              Container(
                width: 50,
                height: 50,
                decoration: BoxDecoration(
                  gradient: LinearGradient(colors: gradientColors),
                  shape: BoxShape.circle,
                ),
                child: isLoading
                    ? const Center(
                        child: SizedBox(
                          width: 24,
                          height: 24,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                          ),
                        ),
                      )
                    : Icon(icon, color: Colors.white, size: 28),
              ),
              const SizedBox(width: 16),

              // Text
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Text(
                          title,
                          style: Theme.of(context).textTheme.titleMedium?.copyWith(
                            fontWeight: FontWeight.bold,
                            color: onTap != null ? gradientColors[0] : Colors.grey,
                          ),
                        ),
                        if (isRecommended) ...[
                          const SizedBox(width: 8),
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                            decoration: BoxDecoration(
                              color: gradientColors[0],
                              borderRadius: BorderRadius.circular(12),
                            ),
                            child: Text(
                              'Recommandé',
                              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                                color: Colors.white,
                                fontWeight: FontWeight.w500,
                                fontSize: 10,
                              ),
                            ),
                          ),
                        ],
                      ],
                    ),
                    const SizedBox(height: 4),
                    Text(
                      subtitle,
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: Theme.of(context).colorScheme.onSurface.withOpacity(0.6),
                      ),
                    ),
                  ],
                ),
              ),

              // Arrow
              Icon(
                Icons.arrow_forward_ios_rounded,
                color: onTap != null ? gradientColors[0] : Colors.grey,
                size: 20,
              ),
            ],
          ),
        ),
      ),
    );
  }
}

/// Extension pour afficher facilement le bottom sheet de difficulté
extension DifficultySelectorModalExtension on BuildContext {
  Future<String?> showDifficultySelector({
    bool isLoading = false,
  }) async {
    String? selectedDifficulty;

    await showModalBottomSheet<String>(
      context: this,
      isScrollControlled: true,
      barrierColor: Colors.black54,
      backgroundColor: Colors.transparent,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      builder: (context) => DifficultySelectorModal(
        onEasySelected: () {
          selectedDifficulty = 'easy';
          Navigator.pop(context);
        },
        onMediumSelected: () {
          selectedDifficulty = 'medium';
          Navigator.pop(context);
        },
        onHardSelected: () {
          selectedDifficulty = 'hard';
          Navigator.pop(context);
        },
        onCancel: () => Navigator.pop(context),
        isLoading: isLoading,
      ),
    );

    return selectedDifficulty;
  }
}

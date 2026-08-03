import 'package:flutter/material.dart';
import 'package:resume_plus_clean/theme/app_theme.dart';

/// Widget affichant la progression de génération d'un exercice
/// Inspiré de la génération de résumés avec animation fluide
class ExerciseGenerationProgress extends StatelessWidget {
  final double progress; // 0.0 à 1.0
  final String status;
  final String? errorMessage;
  final VoidCallback? onRetry;
  final VoidCallback? onCancel;

  const ExerciseGenerationProgress({
    super.key,
    this.progress = 0.0,
    required this.status,
    this.errorMessage,
    this.onRetry,
    this.onCancel,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Container(
      margin: const EdgeInsets.all(16),
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            AppTheme.primaryBlue.withOpacity(0.1),
            AppTheme.primaryBlueLight.withOpacity(0.05),
          ],
        ),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(
          color: AppTheme.primaryBlue.withOpacity(0.2),
          width: 1,
        ),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // Animation ou icône
          _buildIcon(),
          const SizedBox(height: 16),

          // Titre
          Text(
            _getTitle(),
            style: theme.textTheme.titleMedium?.copyWith(
              fontWeight: FontWeight.bold,
              color: errorMessage != null ? AppTheme.error : AppTheme.primaryBlueDark,
            ),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 8),

          // Sous-titre / status
          Text(
            errorMessage ?? status,
            style: theme.textTheme.bodyMedium?.copyWith(
              color: errorMessage != null ? AppTheme.error : Colors.grey[600],
            ),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 20),

          // Barre de progression (sauf en cas d'erreur)
          if (errorMessage == null) ...[
            _buildProgressBar(),
            const SizedBox(height: 12),

            // Pourcentage
            Text(
              '${(progress * 100).toInt()}%',
              style: theme.textTheme.bodyMedium?.copyWith(
                fontWeight: FontWeight.w600,
                color: AppTheme.primaryBlue,
              ),
            ),
          ],

          // Boutons d'action (si erreur ou annulation possible)
          if (errorMessage != null || onCancel != null) ...[
            const SizedBox(height: 16),
            _buildActionButtons(),
          ],
        ],
      ),
    );
  }

  Widget _buildIcon() {
    if (errorMessage != null) {
      return Container(
        width: 60,
        height: 60,
        decoration: BoxDecoration(
          color: AppTheme.error.withOpacity(0.1),
          shape: BoxShape.circle,
        ),
        child: const Icon(
          Icons.error_outline_rounded,
          color: AppTheme.error,
          size: 32,
        ),
      );
    }

    return Container(
      width: 60,
      height: 60,
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [AppTheme.primaryBlue, AppTheme.primaryBlueLight],
        ),
        shape: BoxShape.circle,
      ),
      child: const _AnimatedGenerationIcon(),
    );
  }

  Widget _buildProgressBar() {
    return ClipRRect(
      borderRadius: BorderRadius.circular(10),
      child: LinearProgressIndicator(
        value: progress,
        minHeight: 8,
        backgroundColor: Colors.grey[200],
        valueColor: AlwaysStoppedAnimation<Color>(
          AppTheme.primaryBlue,
        ),
      ),
    );
  }

  Widget _buildActionButtons() {
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        if (errorMessage != null && onRetry != null)
          ElevatedButton.icon(
            onPressed: onRetry,
            icon: const Icon(Icons.refresh_rounded),
            label: const Text('Réessayer'),
            style: ElevatedButton.styleFrom(
              backgroundColor: AppTheme.primaryBlue,
              foregroundColor: Colors.white,
            ),
          ),
        if (errorMessage != null && onRetry != null && onCancel != null)
          const SizedBox(width: 12),
        if (onCancel != null)
          TextButton(
            onPressed: onCancel,
            child: Text(
              'Annuler',
              style: TextStyle(color: Colors.grey[600]),
            ),
          ),
      ],
    );
  }

  String _getTitle() {
    if (errorMessage != null) return 'Échec de la génération';
    if (progress >= 0.9) return 'Finalisation...';
    if (progress >= 0.6) return 'Génération des questions...';
    if (progress >= 0.3) return 'Analyse du contenu...';
    return 'Préparation...';
  }
}

/// Icône animée pour la génération
class _AnimatedGenerationIcon extends StatefulWidget {
  const _AnimatedGenerationIcon();

  @override
  State<_AnimatedGenerationIcon> createState() => _AnimatedGenerationIconState();
}

class _AnimatedGenerationIconState extends State<_AnimatedGenerationIcon>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _pulseAnimation;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: const Duration(milliseconds: 1500),
      vsync: this,
    )..repeat(reverse: true);

    _pulseAnimation = Tween<double>(begin: 0.8, end: 1.2).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeInOut),
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _pulseAnimation,
      builder: (context, child) {
        return Transform.scale(
          scale: _pulseAnimation.value,
          child: child,
        );
      },
      child: const Icon(
        Icons.auto_fix_high_rounded,
        color: Colors.white,
        size: 28,
      ),
    );
  }
}

/// Card compacte pour afficher dans la liste des résumés
class ExerciseGenerationCard extends StatelessWidget {
  final double progress;
  final String status;
  final bool isCompact;

  const ExerciseGenerationCard({
    super.key,
    required this.progress,
    required this.status,
    this.isCompact = false,
  });

  @override
  Widget build(BuildContext context) {
    if (isCompact) {
      return _buildCompactVersion();
    }
    return ExerciseGenerationProgress(
      progress: progress,
      status: status,
    );
  }

  Widget _buildCompactVersion() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            AppTheme.primaryBlue.withOpacity(0.1),
            AppTheme.primaryBlueLight.withOpacity(0.05),
          ],
        ),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        children: [
          SizedBox(
            width: 24,
            height: 24,
            child: CircularProgressIndicator(
              value: progress,
              strokeWidth: 3,
              valueColor: const AlwaysStoppedAnimation<Color>(AppTheme.primaryBlue),
              backgroundColor: Colors.grey[200],
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Génération de l\'exercice...',
                  style: TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w600,
                    color: AppTheme.primaryBlueDark,
                  ),
                ),
                Text(
                  status,
                  style: TextStyle(
                    fontSize: 12,
                    color: Colors.grey[600],
                  ),
                ),
              ],
            ),
          ),
          Text(
            '${(progress * 100).toInt()}%',
            style: const TextStyle(
              fontSize: 14,
              fontWeight: FontWeight.bold,
              color: AppTheme.primaryBlue,
            ),
          ),
        ],
      ),
    );
  }
}

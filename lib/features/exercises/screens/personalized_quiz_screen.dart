import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:resume_plus_clean/features/exercises/providers/personalized_exercise_provider.dart';
import 'package:resume_plus_clean/features/exercises/screens/quiz_result_screen.dart';
import 'package:resume_plus_clean/theme/app_theme.dart';

/// Écran principal du quiz QCM personnalisé
class PersonalizedQuizScreen extends ConsumerStatefulWidget {
  final int summaryId;
  final String summaryTitle;

  const PersonalizedQuizScreen({
    super.key,
    required this.summaryId,
    required this.summaryTitle,
  });

  @override
  ConsumerState<PersonalizedQuizScreen> createState() => _PersonalizedQuizScreenState();
}

class _PersonalizedQuizScreenState extends ConsumerState<PersonalizedQuizScreen> {
  bool _resultNavigated = false;

  @override
  void initState() {
    super.initState();
    // Charger l'exercice existant ou vérifier
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.read(personalizedExerciseProvider.notifier).checkExistingExercise(widget.summaryId);
    });
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(personalizedExerciseProvider);
    final theme = Theme.of(context);

    return WillPopScope(
      onWillPop: () async {
        // Si quiz en cours, demander confirmation
        if (state.isQuizInProgress && !state.isQuizComplete) {
          final shouldPop = await _showExitConfirmation();
          return shouldPop ?? false;
        }
        return true;
      },
      child: Scaffold(
        backgroundColor: theme.scaffoldBackgroundColor,
        appBar: AppBar(
          backgroundColor: AppTheme.primaryBlue,
          foregroundColor: Colors.white,
          elevation: 0,
          title: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Exercice QCM',
                style: theme.textTheme.titleMedium?.copyWith(
                  color: Colors.white,
                  fontWeight: FontWeight.bold,
                ),
              ),
              Text(
                widget.summaryTitle,
                style: theme.textTheme.bodySmall?.copyWith(
                  color: Colors.white.withValues(alpha: 0.8),
                ),
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
            ],
          ),
          actions: [
            if (state.isQuizInProgress)
              Center(
                child: Padding(
                  padding: const EdgeInsets.only(right: 16),
                  child: Text(
                    '${state.currentQuestionIndex + 1}/${state.questions?.length ?? 0}',
                    style: theme.textTheme.bodyMedium?.copyWith(
                      color: Colors.white,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
              ),
          ],
        ),
        body: _buildBody(state),
      ),
    );
  }

  Widget _buildBody(PersonalizedExerciseState state) {
    if (state.isLoading && state.status == ExerciseGenerationStatus.checking) {
      return const Center(
        child: CircularProgressIndicator(color: AppTheme.primaryBlue),
      );
    }

    if (state.showDifficultySelector) {
      return _buildDifficultySelector();
    }

    if (state.isGenerating) {
      return _buildGeneratingView();
    }

    if (state.isReady && state.questions != null) {
      return _buildQuizView(state);
    }

    if (state.hasResult) {
      return _buildResultView(state);
    }

    if (state.status == ExerciseGenerationStatus.error) {
      return _buildErrorView(state);
    }

    return const Center(
      child: CircularProgressIndicator(color: AppTheme.primaryBlue),
    );
  }

  Widget _buildDifficultySelector() {
    return Center(
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Column(
          children: [
            Icon(
              Icons.quiz_outlined,
              size: 64,
              color: AppTheme.primaryBlue.withValues(alpha: 0.5),
            ),
            const SizedBox(height: 24),
            Text(
              'Prêt à générer votre exercice ?',
              style: Theme.of(context).textTheme.titleLarge?.copyWith(
                fontWeight: FontWeight.bold,
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 8),
            Text(
              'Choisissez le niveau de difficulté adapté à votre préparation.',
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                color: Colors.grey[600],
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 32),
            _DifficultyButton(
              difficulty: 'Facile',
              icon: Icons.sentiment_very_satisfied_rounded,
              color: const Color(0xFF10B981),
              onTap: () => _generateExercise('easy'),
            ),
            const SizedBox(height: 12),
            _DifficultyButton(
              difficulty: 'Moyen',
              icon: Icons.sentiment_satisfied_rounded,
              color: const Color(0xFFF59E0B),
              isRecommended: true,
              onTap: () => _generateExercise('medium'),
            ),
            const SizedBox(height: 12),
            _DifficultyButton(
              difficulty: 'Difficile',
              icon: Icons.sentiment_very_dissatisfied_rounded,
              color: const Color(0xFFEF4444),
              onTap: () => _generateExercise('hard'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildGeneratingView() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          SizedBox(
            width: 80,
            height: 80,
            child: CircularProgressIndicator(
              strokeWidth: 6,
              valueColor: const AlwaysStoppedAnimation<Color>(AppTheme.primaryBlue),
              backgroundColor: Colors.grey[200],
            ),
          ),
          const SizedBox(height: 24),
          Text(
            'Génération de votre exercice...',
            style: Theme.of(context).textTheme.titleMedium?.copyWith(
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            'Création de questions uniques adaptées à votre niveau',
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
              color: Colors.grey[600],
            ),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 32),
          TextButton.icon(
            onPressed: () {
              ref.read(personalizedExerciseProvider.notifier).reset();
              Navigator.pop(context);
            },
            icon: const Icon(Icons.close),
            label: const Text('Annuler'),
          ),
        ],
      ),
    );
  }

  Widget _buildQuizView(PersonalizedExerciseState state) {
    final questions = state.questions!;
    final currentIndex = state.currentQuestionIndex;
    final currentQuestion = questions[currentIndex];

    return Column(
      children: [
        // Barre de progression
        _buildQuestionProgressBar(state),

        // Question
        Expanded(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Numéro de question
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                  decoration: BoxDecoration(
                    color: AppTheme.primaryBlue.withValues(alpha: 0.1),
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: Text(
                    'Question ${currentIndex + 1}',
                    style: TextStyle(
                      color: AppTheme.primaryBlue,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
                const SizedBox(height: 20),

                // Texte de la question
                Text(
                  currentQuestion.questionText,
                  style: Theme.of(context).textTheme.titleLarge?.copyWith(
                    fontWeight: FontWeight.w600,
                    height: 1.4,
                  ),
                ),
                const SizedBox(height: 32),

                // Options
                ...currentQuestion.optionsList.map((option) {
                  final isSelected = state.currentAnswers[currentIndex] == option.key;
                  return _buildOptionCard(
                    option: option,
                    isSelected: isSelected,
                    onTap: () => _selectAnswer(option.key),
                  );
                }),
              ],
            ),
          ),
        ),

        // Navigation
        _buildNavigationBar(state),
      ],
    );
  }

  Widget _buildQuestionProgressBar(PersonalizedExerciseState state) {
    final answeredCount = state.currentAnswers.length;
    final total = state.questions?.length ?? 0;
    final progress = total > 0 ? answeredCount / total : 0.0;

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
      decoration: BoxDecoration(
        color: Colors.white,
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.05),
            blurRadius: 10,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                '$answeredCount/$total répondues',
                style: TextStyle(
                  color: Colors.grey[600],
                  fontSize: 14,
                ),
              ),
              if (state.isQuizComplete)
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                  decoration: BoxDecoration(
                    color: const Color(0xFF10B981).withValues(alpha: 0.1),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: const Text(
                    'Terminé !',
                    style: TextStyle(
                      color: Color(0xFF10B981),
                      fontWeight: FontWeight.w600,
                      fontSize: 12,
                    ),
                  ),
                ),
            ],
          ),
          const SizedBox(height: 8),
          ClipRRect(
            borderRadius: BorderRadius.circular(8),
            child: LinearProgressIndicator(
              value: progress,
              minHeight: 8,
              backgroundColor: Colors.grey[200],
              valueColor: AlwaysStoppedAnimation<Color>(
                state.isQuizComplete ? const Color(0xFF10B981) : AppTheme.primaryBlue,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildOptionCard({
    required MapEntry<String, String> option,
    required bool isSelected,
    required VoidCallback onTap,
  }) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(16),
          child: Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: isSelected
                  ? AppTheme.primaryBlue.withValues(alpha: 0.1)
                  : Colors.grey[50],
              borderRadius: BorderRadius.circular(16),
              border: Border.all(
                color: isSelected ? AppTheme.primaryBlue : Colors.grey[300]!,
                width: isSelected ? 2 : 1,
              ),
            ),
            child: Row(
              children: [
                Container(
                  width: 40,
                  height: 40,
                  decoration: BoxDecoration(
                    color: isSelected ? AppTheme.primaryBlue : Colors.white,
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(
                      color: isSelected ? AppTheme.primaryBlue : Colors.grey[300]!,
                    ),
                  ),
                  child: Center(
                    child: Text(
                      option.key,
                      style: TextStyle(
                        fontWeight: FontWeight.bold,
                        color: isSelected ? Colors.white : Colors.grey[600],
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: Text(
                    option.value,
                    style: TextStyle(
                      fontSize: 16,
                      color: isSelected ? AppTheme.primaryBlueDark : Colors.grey[800],
                      fontWeight: isSelected ? FontWeight.w500 : FontWeight.normal,
                    ),
                  ),
                ),
                if (isSelected)
                  const Icon(
                    Icons.check_circle_rounded,
                    color: AppTheme.primaryBlue,
                  ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildNavigationBar(PersonalizedExerciseState state) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.05),
            blurRadius: 10,
            offset: const Offset(0, -2),
          ),
        ],
      ),
      child: SafeArea(
        child: Row(
          children: [
            // Bouton précédent
            if (state.currentQuestionIndex > 0)
              TextButton.icon(
                onPressed: () {
                  ref.read(personalizedExerciseProvider.notifier).previousQuestion();
                },
                icon: const Icon(Icons.arrow_back_ios_rounded),
                label: const Text('Précédent'),
              )
            else
              const SizedBox(width: 100),

            const Spacer(),

            // Bouton suivant / terminer
            if (state.currentQuestionIndex < (state.questions?.length ?? 1) - 1)
              ElevatedButton.icon(
                onPressed: state.currentAnswers.containsKey(state.currentQuestionIndex)
                    ? () {
                        ref.read(personalizedExerciseProvider.notifier).nextQuestion();
                      }
                    : null,
                icon: const Icon(Icons.arrow_forward_ios_rounded),
                label: const Text('Suivant'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppTheme.primaryBlue,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
                ),
              )
            else
              ElevatedButton.icon(
                onPressed: state.isQuizComplete
                    ? () => _submitQuiz()
                    : null,
                icon: const Icon(Icons.check_rounded),
                label: const Text('Terminer'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF10B981),
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
                ),
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildResultView(PersonalizedExerciseState state) {
    // Éviter de relancer la navigation à chaque rebuild
    if (_resultNavigated) {
      return const Center(child: CircularProgressIndicator());
    }
    _resultNavigated = true;

    final result = state.attemptResult!;
    final exercise = state.exercise!;

    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      // push (et non pushReplacement) pour conserver l'écran quiz qui écoute le provider
      Navigator.of(context).push(
        MaterialPageRoute(
          builder: (_) => QuizResultScreen(
            result: result,
            exercise: exercise,
            onRetry: () {
              _resultNavigated = false;
              Navigator.of(context).pop(); // ferme l'écran de résultat
              ref.read(personalizedExerciseProvider.notifier).prepareRegeneration();
            },
            onBack: () {
              _resultNavigated = false;
              Navigator.of(context).pop(); // ferme l'écran de résultat
              ref.read(personalizedExerciseProvider.notifier).reset();
              Navigator.of(context).pop(); // ferme l'écran quiz → retour au résumé
            },
          ),
        ),
      );
    });

    return const Center(
      child: CircularProgressIndicator(),
    );
  }

  Widget _buildErrorView(PersonalizedExerciseState state) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(
              Icons.error_outline_rounded,
              size: 64,
              color: AppTheme.error,
            ),
            const SizedBox(height: 16),
            Text(
              'Une erreur est survenue',
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              state.errorMessage ?? 'Erreur inconnue',
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                color: Colors.grey[600],
              ),
            ),
            const SizedBox(height: 24),
            ElevatedButton.icon(
              onPressed: () {
                ref.read(personalizedExerciseProvider.notifier).checkExistingExercise(widget.summaryId);
              },
              icon: const Icon(Icons.refresh_rounded),
              label: const Text('Réessayer'),
            ),
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Retour'),
            ),
          ],
        ),
      ),
    );
  }

  void _generateExercise(String difficulty) {
    ref.read(personalizedExerciseProvider.notifier).generateExercise(
      summaryId: widget.summaryId,
      difficulty: difficulty,
    );
  }

  void _selectAnswer(String option) {
    ref.read(personalizedExerciseProvider.notifier).selectAnswer(option);
  }

  Future<void> _submitQuiz() async {
    await ref.read(personalizedExerciseProvider.notifier).submitQuiz();
  }

  Future<bool?> _showExitConfirmation() async {
    return showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Quitter le quiz ?'),
        content: const Text(
          'Vos réponses actuelles ne seront pas sauvegardées. Voulez-vous vraiment quitter ?',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Continuer'),
          ),
          ElevatedButton(
            onPressed: () => Navigator.pop(context, true),
            style: ElevatedButton.styleFrom(
              backgroundColor: AppTheme.error,
            ),
            child: const Text('Quitter'),
          ),
        ],
      ),
    );
  }
}

/// Bouton de difficulté
class _DifficultyButton extends StatelessWidget {
  final String difficulty;
  final IconData icon;
  final Color color;
  final VoidCallback onTap;
  final bool isRecommended;

  const _DifficultyButton({
    required this.difficulty,
    required this.icon,
    required this.color,
    required this.onTap,
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
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            gradient: LinearGradient(
              colors: [color.withValues(alpha: 0.1), color.withValues(alpha: 0.05)],
            ),
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: color.withValues(alpha: 0.3), width: 2),
          ),
          child: Row(
            children: [
              Container(
                width: 50,
                height: 50,
                decoration: BoxDecoration(
                  gradient: LinearGradient(colors: [color, color.withValues(alpha: 0.8)]),
                  shape: BoxShape.circle,
                ),
                child: Icon(icon, color: Colors.white, size: 28),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Text(
                          difficulty,
                          style: Theme.of(context).textTheme.titleMedium?.copyWith(
                            fontWeight: FontWeight.bold,
                            color: color,
                          ),
                        ),
                        if (isRecommended) ...[
                          const SizedBox(width: 8),
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                            decoration: BoxDecoration(
                              color: color,
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
                  ],
                ),
              ),
              Icon(Icons.arrow_forward_ios, color: color, size: 20),
            ],
          ),
        ),
      ),
    );
  }
}

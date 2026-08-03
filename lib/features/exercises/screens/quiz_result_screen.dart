import 'package:flutter/material.dart';
import 'package:resume_plus_clean/models/personalized_exercise.dart';
import 'package:resume_plus_clean/theme/app_theme.dart';

/// Écran affichant les résultats détaillés d'un quiz
class QuizResultScreen extends StatelessWidget {
  final AttemptResult result;
  final PersonalizedExercise exercise;
  final VoidCallback onRetry;
  final VoidCallback onBack;

  const QuizResultScreen({
    super.key,
    required this.result,
    required this.exercise,
    required this.onRetry,
    required this.onBack,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final score = result.score;
    final isSuccess = score >= 60;

    return Scaffold(
      backgroundColor: theme.scaffoldBackgroundColor,
      body: SafeArea(
        child: CustomScrollView(
          slivers: [
            // Header avec score
            SliverToBoxAdapter(
              child: _buildScoreHeader(isSuccess, score),
            ),

            // Message et stats
            SliverToBoxAdapter(
              child: Padding(
                padding: const EdgeInsets.all(20),
                child: Column(
                  children: [
                    Text(
                      result.message,
                      style: theme.textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.w600,
                      ),
                      textAlign: TextAlign.center,
                    ),
                    const SizedBox(height: 20),
                    _buildStatsCard(),
                  ],
                ),
              ),
            ),

            // Réponses détaillées
            SliverToBoxAdapter(
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 20),
                child: Text(
                  'Détail des réponses',
                  style: theme.textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            ),
            const SliverToBoxAdapter(child: SizedBox(height: 12)),

            // Liste des questions avec corrections
            SliverList(
              delegate: SliverChildBuilderDelegate(
                (context, index) {
                  final questionResult = result.results[index];
                  return _buildQuestionResultCard(questionResult);
                },
                childCount: result.results.length,
              ),
            ),

            // Boutons d'action
            SliverToBoxAdapter(
              child: Padding(
                padding: const EdgeInsets.all(20),
                child: _buildActionButtons(),
              ),
            ),

            // Espace en bas
            const SliverToBoxAdapter(child: SizedBox(height: 40)),
          ],
        ),
      ),
    );
  }

  Widget _buildScoreHeader(bool isSuccess, double score) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 40, horizontal: 20),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
          colors: isSuccess
              ? [const Color(0xFF10B981), const Color(0xFF059669)]
              : [const Color(0xFFF59E0B), const Color(0xFFD97706)],
        ),
        borderRadius: const BorderRadius.only(
          bottomLeft: Radius.circular(30),
          bottomRight: Radius.circular(30),
        ),
      ),
      child: Column(
        children: [
          // Icône
          Container(
            width: 100,
            height: 100,
            decoration: BoxDecoration(
              color: Colors.white.withOpacity(0.2),
              shape: BoxShape.circle,
            ),
            child: Icon(
              isSuccess ? Icons.emoji_events_rounded : Icons.school_rounded,
              color: Colors.white,
              size: 50,
            ),
          ),
          const SizedBox(height: 20),

          // Score
          Text(
            '${score.toStringAsFixed(0)}%',
            style: const TextStyle(
              fontSize: 64,
              fontWeight: FontWeight.bold,
              color: Colors.white,
            ),
          ),
          const SizedBox(height: 8),

          // Label
          Text(
            isSuccess ? 'Félicitations !' : 'Continue tes efforts !',
            style: const TextStyle(
              fontSize: 24,
              fontWeight: FontWeight.w600,
              color: Colors.white,
            ),
          ),
          const SizedBox(height: 8),

          // Sous-texte
          Text(
            '${result.correctAnswers}/${result.totalQuestions} bonnes réponses',
            style: TextStyle(
              fontSize: 16,
              color: Colors.white.withOpacity(0.9),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildStatsCard() {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 10,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceAround,
        children: [
          _buildStatItem(
            icon: Icons.check_circle_rounded,
            value: '${result.correctAnswers}',
            label: 'Correctes',
            color: const Color(0xFF10B981),
          ),
          _buildStatItem(
            icon: Icons.cancel_rounded,
            value: '${result.totalQuestions - result.correctAnswers}',
            label: 'Incorrectes',
            color: const Color(0xFFEF4444),
          ),
          _buildStatItem(
            icon: Icons.timer_rounded,
            value: result.formattedTime,
            label: 'Temps',
            color: AppTheme.primaryBlue,
          ),
          _buildStatItem(
            icon: Icons.trending_up_rounded,
            value: exercise.difficultyLabel,
            label: 'Difficulté',
            color: const Color(0xFFF59E0B),
          ),
        ],
      ),
    );
  }

  Widget _buildStatItem({
    required IconData icon,
    required String value,
    required String label,
    required Color color,
  }) {
    return Column(
      children: [
        Container(
          width: 48,
          height: 48,
          decoration: BoxDecoration(
            color: color.withOpacity(0.1),
            shape: BoxShape.circle,
          ),
          child: Icon(icon, color: color, size: 24),
        ),
        const SizedBox(height: 8),
        Text(
          value,
          style: const TextStyle(
            fontSize: 18,
            fontWeight: FontWeight.bold,
          ),
        ),
        Text(
          label,
          style: TextStyle(
            fontSize: 12,
            color: Colors.grey[600],
          ),
        ),
      ],
    );
  }

  Widget _buildQuestionResultCard(QuestionResult result) {
    final isCorrect = result.isCorrect;

    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
      decoration: BoxDecoration(
        color: isCorrect
            ? const Color(0xFF10B981).withOpacity(0.05)
            : const Color(0xFFEF4444).withOpacity(0.05),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: isCorrect
              ? const Color(0xFF10B981).withOpacity(0.3)
              : const Color(0xFFEF4444).withOpacity(0.3),
        ),
      ),
      child: ExpansionTile(
        leading: Container(
          width: 32,
          height: 32,
          decoration: BoxDecoration(
            color: isCorrect ? const Color(0xFF10B981) : const Color(0xFFEF4444),
            shape: BoxShape.circle,
          ),
          child: Icon(
            isCorrect ? Icons.check_rounded : Icons.close_rounded,
            color: Colors.white,
            size: 20,
          ),
        ),
        title: Text(
          'Question ${result.questionIndex + 1}',
          style: const TextStyle(fontWeight: FontWeight.w600),
        ),
        subtitle: Text(
          isCorrect ? 'Bonne réponse' : 'Mauvaise réponse',
          style: TextStyle(
            color: isCorrect ? const Color(0xFF10B981) : const Color(0xFFEF4444),
            fontSize: 13,
          ),
        ),
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Question
                Text(
                  result.questionText,
                  style: const TextStyle(
                    fontSize: 15,
                    fontWeight: FontWeight.w500,
                  ),
                ),
                const SizedBox(height: 16),

                // Options avec mise en évidence
                ...result.options.entries.map((entry) {
                  final isSelected = entry.key == result.userAnswer;
                  final isCorrectOption = entry.key == result.correctAnswer;

                  return Container(
                    margin: const EdgeInsets.only(bottom: 8),
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: isCorrectOption
                          ? const Color(0xFF10B981).withOpacity(0.1)
                          : isSelected && !isCorrectOption
                              ? const Color(0xFFEF4444).withOpacity(0.1)
                              : Colors.grey[50],
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(
                        color: isCorrectOption
                            ? const Color(0xFF10B981)
                            : isSelected && !isCorrectOption
                                ? const Color(0xFFEF4444)
                                : Colors.grey[300]!,
                      ),
                    ),
                    child: Row(
                      children: [
                        Container(
                          width: 28,
                          height: 28,
                          decoration: BoxDecoration(
                            color: isCorrectOption
                                ? const Color(0xFF10B981)
                                : isSelected && !isCorrectOption
                                    ? const Color(0xFFEF4444)
                                    : Colors.grey[300],
                            shape: BoxShape.circle,
                          ),
                          child: Center(
                            child: Text(
                              entry.key,
                              style: TextStyle(
                                color: isCorrectOption || (isSelected && !isCorrectOption)
                                    ? Colors.white
                                    : Colors.grey[600],
                                fontWeight: FontWeight.bold,
                                fontSize: 13,
                              ),
                            ),
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Text(
                            entry.value,
                            style: TextStyle(
                              fontSize: 14,
                              color: isCorrectOption
                                  ? const Color(0xFF10B981)
                                  : isSelected && !isCorrectOption
                                      ? const Color(0xFFEF4444)
                                      : Colors.grey[800],
                              fontWeight: isCorrectOption || isSelected
                                  ? FontWeight.w600
                                  : FontWeight.normal,
                            ),
                          ),
                        ),
                        if (isCorrectOption)
                          const Icon(
                            Icons.check_circle_rounded,
                            color: Color(0xFF10B981),
                            size: 20,
                          ),
                        if (isSelected && !isCorrectOption)
                          const Icon(
                            Icons.cancel_rounded,
                            color: Color(0xFFEF4444),
                            size: 20,
                          ),
                      ],
                    ),
                  );
                }),

                // Explication
                if (result.explanation.isNotEmpty) ...[
                  const SizedBox(height: 16),
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: Colors.blue.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Icon(
                          Icons.lightbulb_rounded,
                          color: Colors.blue,
                          size: 20,
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            result.explanation,
                            style: const TextStyle(
                              fontSize: 13,
                              color: Colors.blue,
                              fontStyle: FontStyle.italic,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildActionButtons() {
    return Column(
      children: [
        // Bouton réessayer (régénérer avec nouvelles questions)
        ElevatedButton.icon(
          onPressed: onRetry,
          icon: const Icon(Icons.refresh_rounded),
          label: const Text('Nouvel exercice'),
          style: ElevatedButton.styleFrom(
            backgroundColor: AppTheme.primaryBlue,
            foregroundColor: Colors.white,
            minimumSize: const Size(double.infinity, 50),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(12),
            ),
          ),
        ),
        const SizedBox(height: 12),

        // Bouton retour
        OutlinedButton.icon(
          onPressed: onBack,
          icon: const Icon(Icons.arrow_back_rounded),
          label: const Text('Retour au résumé'),
          style: OutlinedButton.styleFrom(
            foregroundColor: Colors.grey[700],
            minimumSize: const Size(double.infinity, 50),
            side: BorderSide(color: Colors.grey[300]!),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(12),
            ),
          ),
        ),
      ],
    );
  }
}

import 'package:flutter/material.dart';
import 'package:resume_plus_clean/models/exercise.dart';
import 'package:resume_plus_clean/services/api_service.dart';
import 'package:resume_plus_clean/features/exercises/screens/exercise_quiz_screen.dart';
import 'package:resume_plus_clean/theme/app_theme.dart';
import 'package:resume_plus_clean/widgets/secure_screen_wrapper.dart';
import 'package:resume_plus_clean/widgets/tech_block_widget.dart';

class ExerciseResultScreen extends StatefulWidget {
  final ExerciseResult result;
  final int? summaryId;
  final String? difficulty;

  const ExerciseResultScreen({
    super.key,
    required this.result,
    this.summaryId,
    this.difficulty,
  });

  @override
  State<ExerciseResultScreen> createState() => _ExerciseResultScreenState();
}

class _ExerciseResultScreenState extends State<ExerciseResultScreen> {
  final ApiService _apiService = ApiService();
  bool _isRegenerating = false;

  Future<void> _regenerateExercise() async {
    setState(() => _isRegenerating = true);
    try {
      final data = await _apiService.generateExercise(
        widget.summaryId!,
        difficulty: widget.difficulty,
        forceRegenerate: true,
      );

      if (data.containsKey('subscription_required')) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('Abonnement requis pour régénérer un exercice'),
              backgroundColor: Colors.red,
            ),
          );
        }
        return;
      }

      final exerciseId = data['exercise_id'] ?? data['id'];
      if (exerciseId == null) {
        throw Exception('Aucun exercice retourné');
      }

      // Poll jusqu'à completion puis naviguer
      if (mounted) {
        await _pollExerciseStatus(exerciseId);
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Erreur: $e'), backgroundColor: Colors.red),
        );
      }
    } finally {
      if (mounted) setState(() => _isRegenerating = false);
    }
  }

  Future<void> _pollExerciseStatus(int exerciseId) async {
    for (int i = 0; i < 30; i++) {
      await Future.delayed(const Duration(seconds: 3));
      if (!mounted) return;
      try {
        final exercise = await _apiService.getExercise(exerciseId);
        final s = exercise['status'] ?? '';
        if (s == 'completed') {
          if (mounted) {
            Navigator.of(context).pushReplacement(
              MaterialPageRoute(
                builder: (_) => ExerciseQuizScreen(
                  exerciseId: exerciseId,
                  exerciseTitle: 'QCM - ${widget.difficulty!.toUpperCase()}',
                  summaryId: widget.summaryId!,
                  difficulty: widget.difficulty!,
                ),
              ),
            );
          }
          return;
        } else if (s == 'failed') {
          throw Exception('La génération a échoué. Veuillez réessayer.');
        }
      } catch (e) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('Erreur: $e'), backgroundColor: Colors.red),
          );
        }
        return;
      }
    }
    throw Exception('Délai dépassé.');
  }

  @override
  Widget build(BuildContext context) {
    final topPadding = MediaQuery.of(context).padding.top;
    final isPassed = widget.result.score >= 50;

    return SecureScreenWrapper(
      screenName: 'Résultats QCM',
      enableSecurity: true,
      child: Scaffold(
        backgroundColor: Theme.of(context).scaffoldBackgroundColor,
        body: Column(
        children: [
          // Header avec score
          Container(
            padding: EdgeInsets.only(top: topPadding + 8, left: 20, right: 20, bottom: 30),
            decoration: BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
                colors: isPassed
                    ? [const Color(0xFF16A34A), const Color(0xFF22C55E), const Color(0xFF4ADE80)]
                    : [const Color(0xFFDC2626), const Color(0xFFEF4444), const Color(0xFFF87171)],
              ),
              borderRadius: const BorderRadius.only(
                bottomLeft: Radius.circular(32),
                bottomRight: Radius.circular(32),
              ),
            ),
            child: Column(
              children: [
                Row(
                  children: [
                    GestureDetector(
                      onTap: () => Navigator.of(context).pop(),
                      child: Container(
                        width: 40, height: 40,
                        decoration: BoxDecoration(
                          color: Colors.white.withOpacity(0.2),
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: const Icon(Icons.close_rounded, color: Colors.white, size: 22),
                      ),
                    ),
                    const Spacer(),
                    Text(
                      isPassed ? 'Bravo !' : 'Résultat',
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        color: Colors.white, fontWeight: FontWeight.w700,
                      ),
                    ),
                    const Spacer(),
                    const SizedBox(width: 40),
                  ],
                ),
                const SizedBox(height: 24),
                // Score circle
                Container(
                  width: 120, height: 120,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: Colors.white.withOpacity(0.2),
                    border: Border.all(color: Colors.white.withOpacity(0.5), width: 3),
                  ),
                  child: Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Text(
                          '${widget.result.score.toStringAsFixed(0)}%',
                          style: const TextStyle(
                            color: Colors.white, fontSize: 36, fontWeight: FontWeight.w800,
                          ),
                        ),
                        Text(
                          '${widget.result.correctAnswers}/${widget.result.totalQuestions}',
                          style: TextStyle(
                            color: Colors.white.withOpacity(0.8), fontSize: 14, fontWeight: FontWeight.w500,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 16),
                Text(
                  isPassed
                      ? 'Excellent travail ! Vous maîtrisez ce sujet.'
                      : 'Continuez à réviser, vous pouvez vous améliorer !',
                  style: TextStyle(
                    color: Colors.white.withOpacity(0.9), fontSize: 14, fontWeight: FontWeight.w500,
                  ),
                  textAlign: TextAlign.center,
                ),
              ],
            ),
          ),
          // Détails des réponses
          Expanded(
            child: ListView.builder(
              padding: const EdgeInsets.all(20),
              itemCount: widget.result.results.length,
              itemBuilder: (context, index) {
                final qr = widget.result.results[index];
                return _buildQuestionResultCard(context, qr, index);
              },
            ),
          ),
          // Boutons d'action
          Container(
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              color: Colors.white,
              boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.06), blurRadius: 10, offset: const Offset(0, -4))],
            ),
            child: SafeArea(
              child: Column(
                children: [
                  // Bouton Régénérer (seulement si summaryId et difficulty sont disponibles)
                  // if (widget.summaryId != null && widget.difficulty != null)
                  //   SizedBox(
                  //     width: double.infinity,
                  //     child: ElevatedButton.icon(
                  //       onPressed: _isRegenerating ? null : _regenerateExercise,
                  //       icon: _isRegenerating
                  //           ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                  //           : const Icon(Icons.refresh_rounded, size: 20),
                  //       label: Text(_isRegenerating ? 'Génération en cours...' : 'Régénérer un nouvel exercice'),
                  //       style: ElevatedButton.styleFrom(
                  //         backgroundColor: AppTheme.primaryBlue,
                  //         foregroundColor: Colors.white,
                  //         padding: const EdgeInsets.symmetric(vertical: 16),
                  //         shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                  //       ),
                  //     ),
                  //   ),
                  if (widget.summaryId != null && widget.difficulty != null)
                    const SizedBox(height: 10),
                  // Bouton Retour
                  SizedBox(
                    width: double.infinity,
                    child: OutlinedButton.icon(
                      onPressed: () => Navigator.of(context).pop(),
                      icon: const Icon(Icons.arrow_back_rounded, size: 20),
                      label: const Text('Retour au résumé'),
                      style: OutlinedButton.styleFrom(
                        foregroundColor: AppTheme.primaryBlue,
                        side: const BorderSide(color: AppTheme.primaryBlue),
                        padding: const EdgeInsets.symmetric(vertical: 16),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
      ),
    );
  }

  Widget _buildQuestionResultCard(BuildContext context, QuestionResult qr, int index) {
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: qr.isCorrect ? AppTheme.success.withOpacity(0.3) : AppTheme.error.withOpacity(0.3),
          width: 1.5,
        ),
        boxShadow: AppTheme.softShadow,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 30, height: 30,
                decoration: BoxDecoration(
                  color: qr.isCorrect ? AppTheme.success.withOpacity(0.1) : AppTheme.error.withOpacity(0.1),
                  shape: BoxShape.circle,
                ),
                child: Icon(
                  qr.isCorrect ? Icons.check_rounded : Icons.close_rounded,
                  color: qr.isCorrect ? AppTheme.success : AppTheme.error,
                  size: 18,
                ),
              ),
              const SizedBox(width: 10),
              Text(
                'Question ${index + 1}',
                style: TextStyle(
                  color: qr.isCorrect ? AppTheme.success : AppTheme.error,
                  fontWeight: FontWeight.w700, fontSize: 13,
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Text(
            qr.questionText,
            style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600, height: 1.4),
          ),
          // Bloc technique (code, formule, algorithme)
          TechBlockWidget(
            codeLanguage: qr.codeLanguage,
            codeBlock: qr.codeBlock,
          ),
          const SizedBox(height: 12),
          // Votre réponse
          if (qr.userAnswer != null) ...[
            _buildAnswerRow(
              label: 'Votre réponse',
              answer: qr.userAnswer!,
              color: qr.isCorrect ? AppTheme.success : AppTheme.error,
              icon: qr.isCorrect ? Icons.check_circle_rounded : Icons.cancel_rounded,
            ),
            const SizedBox(height: 6),
          ],
          // Bonne réponse (si incorrecte)
          if (!qr.isCorrect)
            _buildAnswerRow(
              label: 'Bonne réponse',
              answer: qr.correctAnswer,
              color: AppTheme.success,
              icon: Icons.check_circle_rounded,
            ),
          // Explication
          if (qr.explanation != null && qr.explanation!.isNotEmpty) ...[
            const SizedBox(height: 12),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: AppTheme.primaryBlue.withOpacity(0.05),
                borderRadius: BorderRadius.circular(10),
              ),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Icon(Icons.lightbulb_outline_rounded, size: 18, color: AppTheme.primaryBlue.withOpacity(0.7)),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      qr.explanation!,
                      style: TextStyle(fontSize: 12, color: AppTheme.textSecondary, height: 1.4),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildAnswerRow({
    required String label,
    required String answer,
    required Color color,
    required IconData icon,
  }) {
    return Row(
      children: [
        Icon(icon, size: 16, color: color),
        const SizedBox(width: 6),
        Text('$label: ', style: TextStyle(fontSize: 12, color: color, fontWeight: FontWeight.w600)),
        Expanded(
          child: Text(answer, style: TextStyle(fontSize: 12, color: color)),
        ),
      ],
    );
  }
}

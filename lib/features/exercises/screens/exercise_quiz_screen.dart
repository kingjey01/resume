import 'package:flutter/material.dart';
import 'package:resume_plus_clean/models/exercise.dart';
import 'package:resume_plus_clean/services/api_service.dart';
import 'package:resume_plus_clean/features/exercises/screens/exercise_result_screen.dart';
import 'package:resume_plus_clean/theme/app_theme.dart';
import 'package:resume_plus_clean/widgets/secure_screen_wrapper.dart';
import 'package:resume_plus_clean/widgets/tech_block_widget.dart';

class ExerciseQuizScreen extends StatefulWidget {
  final int exerciseId;
  final String exerciseTitle;
  final int summaryId;
  final String difficulty;

  const ExerciseQuizScreen({
    super.key,
    required this.exerciseId,
    required this.exerciseTitle,
    required this.summaryId,
    required this.difficulty,
  });

  @override
  State<ExerciseQuizScreen> createState() => _ExerciseQuizScreenState();
}

class _ExerciseQuizScreenState extends State<ExerciseQuizScreen> {
  final ApiService _apiService = ApiService();
  List<ExerciseQuestion> _questions = [];
  Map<String, String> _selectedAnswers = {};
  bool _isLoading = true;
  bool _isSubmitting = false;
  String? _error;
  int _currentQuestionIndex = 0;
  final PageController _pageController = PageController();

  @override
  void initState() {
    super.initState();
    _loadExercise();
  }

  Future<void> _loadExercise() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final data = await _apiService.getExercise(widget.exerciseId);

      if (data.containsKey('subscription_required')) {
        setState(() {
          _error = 'Abonnement au service d\'exercices requis';
          _isLoading = false;
        });
        return;
      }

      final questionsRaw = data['questions'] as List<dynamic>? ?? [];
      final questions = questionsRaw
          .map((q) => ExerciseQuestion.fromJson(q as Map<String, dynamic>))
          .toList();

      setState(() {
        _questions = questions;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _error = 'Erreur lors du chargement: $e';
        _isLoading = false;
      });
    }
  }

  void _selectAnswer(int questionId, String answer) {
    setState(() {
      _selectedAnswers[questionId.toString()] = answer;
    });
  }

  Future<void> _submitAnswers() async {
    if (_selectedAnswers.length < _questions.length) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            'Veuillez répondre à toutes les questions (${_selectedAnswers.length}/${_questions.length})',
          ),
          backgroundColor: Colors.orange,
        ),
      );
      return;
    }

    setState(() => _isSubmitting = true);

    try {
      final result = await _apiService.submitExercise(widget.exerciseId, _selectedAnswers);

      if (result.containsKey('subscription_required')) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Abonnement au service d\'exercices requis'),
            backgroundColor: Colors.red,
          ),
        );
        setState(() => _isSubmitting = false);
        return;
      }

      if (mounted) {
        final exerciseResult = ExerciseResult.fromJson(result);
        Navigator.of(context).pushReplacement(
          MaterialPageRoute(
            builder: (_) => ExerciseResultScreen(
              result: exerciseResult,
              summaryId: widget.summaryId,
              difficulty: widget.difficulty,
            ),
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Erreur: $e'), backgroundColor: Colors.red),
        );
      }
      setState(() => _isSubmitting = false);
    }
  }

  void _goToQuestion(int index) {
    _pageController.animateToPage(
      index,
      duration: const Duration(milliseconds: 300),
      curve: Curves.easeInOut,
    );
  }

  @override
  void dispose() {
    _pageController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final topPadding = MediaQuery.of(context).padding.top;

    return SecureScreenWrapper(
      screenName: 'QCM: ${widget.exerciseTitle}',
      enableSecurity: true,
      child: Scaffold(
        backgroundColor: Theme.of(context).scaffoldBackgroundColor,
        body: Column(
        children: [
          // Header
          Container(
            padding: EdgeInsets.only(top: topPadding + 8, left: 20, right: 20, bottom: 16),
            decoration: const BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
                colors: [AppTheme.primaryBlueDark, AppTheme.primaryBlue, AppTheme.primaryBlueLight],
              ),
              borderRadius: BorderRadius.only(
                bottomLeft: Radius.circular(24),
                bottomRight: Radius.circular(24),
              ),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    GestureDetector(
                      onTap: () => _showExitDialog(),
                      child: Container(
                        width: 40, height: 40,
                        decoration: BoxDecoration(
                          color: Colors.white.withOpacity(0.2),
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: const Icon(Icons.close_rounded, color: Colors.white, size: 22),
                      ),
                    ),
                    const SizedBox(width: 14),
                    Expanded(
                      child: Text(
                        widget.exerciseTitle,
                        style: Theme.of(context).textTheme.titleMedium?.copyWith(
                          color: Colors.white, fontWeight: FontWeight.w700,
                        ),
                        maxLines: 1, overflow: TextOverflow.ellipsis,
                      ),
                    ),
                    if (!_isLoading && _questions.isNotEmpty)
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                        decoration: BoxDecoration(
                          color: Colors.white.withOpacity(0.2),
                          borderRadius: BorderRadius.circular(20),
                        ),
                        child: Text(
                          '${_selectedAnswers.length}/${_questions.length}',
                          style: const TextStyle(color: Colors.white, fontSize: 13, fontWeight: FontWeight.w600),
                        ),
                      ),
                  ],
                ),
                if (!_isLoading && _questions.isNotEmpty) ...[
                  const SizedBox(height: 14),
                  // Progress dots
                  Row(
                    children: List.generate(_questions.length, (i) {
                      final isAnswered = _selectedAnswers.containsKey(_questions[i].id.toString());
                      final isCurrent = i == _currentQuestionIndex;
                      return Expanded(
                        child: GestureDetector(
                          onTap: () => _goToQuestion(i),
                          child: Container(
                            height: 4,
                            margin: const EdgeInsets.symmetric(horizontal: 2),
                            decoration: BoxDecoration(
                              color: isCurrent
                                  ? Colors.white
                                  : isAnswered
                                      ? Colors.white.withOpacity(0.6)
                                      : Colors.white.withOpacity(0.2),
                              borderRadius: BorderRadius.circular(2),
                            ),
                          ),
                        ),
                      );
                    }),
                  ),
                ],
              ],
            ),
          ),
          // Content
          Expanded(
            child: _isLoading
                ? const Center(child: CircularProgressIndicator(color: AppTheme.primaryBlue))
                : _error != null
                    ? _buildError()
                    : _questions.isEmpty
                        ? const Center(child: Text('Aucune question disponible'))
                        : PageView.builder(
                            controller: _pageController,
                            itemCount: _questions.length,
                            onPageChanged: (index) {
                              setState(() => _currentQuestionIndex = index);
                            },
                            itemBuilder: (context, index) {
                              return _buildQuestionCard(_questions[index], index);
                            },
                          ),
          ),
          // Bottom bar
          if (!_isLoading && _error == null && _questions.isNotEmpty)
            _buildBottomBar(),
        ],
      ),
      ),
    );
  }

  Widget _buildQuestionCard(ExerciseQuestion question, int index) {
    final theme = Theme.of(context);
    final cs = theme.colorScheme;
    final selectedAnswer = _selectedAnswers[question.id.toString()];

    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Question number
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
            decoration: BoxDecoration(
              color: AppTheme.primaryBlue.withOpacity(0.1),
              borderRadius: BorderRadius.circular(20),
            ),
            child: Text(
              'Question ${index + 1}/${_questions.length}',
              style: const TextStyle(
                color: AppTheme.primaryBlue, fontSize: 13, fontWeight: FontWeight.w600,
              ),
            ),
          ),
          const SizedBox(height: 16),
          // Question text
          Text(
            question.questionText,
            style: Theme.of(context).textTheme.titleMedium?.copyWith(
              color: cs.onSurface,
              fontWeight: FontWeight.w700,
              fontSize: 17,
              height: 1.5,
            ),
          ),
          // Bloc technique (code, formule, algorithme)
          TechBlockWidget(
            codeLanguage: question.codeLanguage,
            codeBlock: question.codeBlock,
          ),
          const SizedBox(height: 24),
          // Options
          ...question.options.entries.map((entry) {
            final isSelected = selectedAnswer == entry.key;
            return Padding(
              padding: const EdgeInsets.only(bottom: 12),
              child: GestureDetector(
                onTap: () => _selectAnswer(question.id, entry.key),
                child: AnimatedContainer(
                  duration: const Duration(milliseconds: 200),
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: isSelected
                        ? AppTheme.primaryBlue.withOpacity(0.1)
                        : cs.surface,
                    borderRadius: BorderRadius.circular(14),
                    border: Border.all(
                      color: isSelected ? AppTheme.primaryBlue : theme.dividerTheme.color ?? Colors.grey.shade300,
                      width: isSelected ? 2 : 1,
                    ),
                    boxShadow: isSelected
                        ? [BoxShadow(color: AppTheme.primaryBlue.withOpacity(0.1), blurRadius: 8, offset: const Offset(0, 2))]
                        : AppTheme.softShadow,
                  ),
                  child: Row(
                    children: [
                      Container(
                        width: 36, height: 36,
                        decoration: BoxDecoration(
                          color: isSelected ? AppTheme.primaryBlue : cs.surface.withOpacity(0.6),
                          shape: BoxShape.circle,
                        ),
                        child: Center(
                          child: Text(
                            entry.key,
                            style: TextStyle(
                              color: isSelected ? Colors.white : cs.onSurfaceVariant,
                              fontWeight: FontWeight.w700, fontSize: 15,
                            ),
                          ),
                        ),
                      ),
                      const SizedBox(width: 14),
                      Expanded(
                        child: Text(
                          entry.value,
                          style: TextStyle(
                            color: isSelected ? AppTheme.primaryBlue : cs.onSurface,
                            fontSize: 15, fontWeight: isSelected ? FontWeight.w600 : FontWeight.w500,
                          ),
                        ),
                      ),
                      if (isSelected)
                        const Icon(Icons.check_circle_rounded, color: AppTheme.primaryBlue, size: 22),
                    ],
                  ),
                ),
              ),
            );
          }),
        ],
      ),
    );
  }

  Widget _buildBottomBar() {
    final surface = Theme.of(context).colorScheme.surface;
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: surface,
        boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.06), blurRadius: 10, offset: const Offset(0, -4))],
      ),
      child: SafeArea(
        child: Row(
          children: [
            if (_currentQuestionIndex > 0)
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: () => _goToQuestion(_currentQuestionIndex - 1),
                  icon: const Icon(Icons.arrow_back_rounded, size: 18),
                  label: const Text('Précédent'),
                  style: OutlinedButton.styleFrom(
                    foregroundColor: AppTheme.primaryBlue,
                    side: const BorderSide(color: AppTheme.primaryBlue),
                    padding: const EdgeInsets.symmetric(vertical: 14),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                  ),
                ),
              ),
            if (_currentQuestionIndex > 0) const SizedBox(width: 12),
            Expanded(
              flex: 2,
              child: _currentQuestionIndex < _questions.length - 1
                  ? ElevatedButton.icon(
                      onPressed: () => _goToQuestion(_currentQuestionIndex + 1),
                      icon: const Text('Suivant'),
                      label: const Icon(Icons.arrow_forward_rounded, size: 18),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: AppTheme.primaryBlue,
                        foregroundColor: Colors.white,
                        padding: const EdgeInsets.symmetric(vertical: 14),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                      ),
                    )
                  : ElevatedButton.icon(
                      onPressed: _isSubmitting ? null : _submitAnswers,
                      icon: _isSubmitting
                          ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                          : const Icon(Icons.check_rounded, size: 20),
                      label: Text(_isSubmitting ? 'Envoi...' : 'Terminer'),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: AppTheme.success,
                        foregroundColor: Colors.white,
                        padding: const EdgeInsets.symmetric(vertical: 14),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                      ),
                    ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildError() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              width: 80, height: 80,
              decoration: BoxDecoration(
                color: AppTheme.error.withOpacity(0.1), shape: BoxShape.circle,
              ),
              child: const Icon(Icons.error_outline_rounded, size: 36, color: AppTheme.error),
            ),
            const SizedBox(height: 20),
            Text(_error!, textAlign: TextAlign.center, style: const TextStyle(color: AppTheme.textLight, fontSize: 14)),
            const SizedBox(height: 20),
            ElevatedButton(onPressed: _loadExercise, child: const Text('Réessayer')),
          ],
        ),
      ),
    );
  }

  void _showExitDialog() {
    if (_selectedAnswers.isEmpty) {
      Navigator.of(context).pop();
      return;
    }
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Quitter l\'exercice ?'),
        content: const Text('Vos réponses ne seront pas sauvegardées.'),
        actions: [
          TextButton(onPressed: () => Navigator.of(ctx).pop(), child: const Text('Annuler')),
          TextButton(
            onPressed: () {
              Navigator.of(ctx).pop();
              Navigator.of(context).pop();
            },
            child: const Text('Quitter', style: TextStyle(color: AppTheme.error)),
          ),
        ],
      ),
    );
  }
}

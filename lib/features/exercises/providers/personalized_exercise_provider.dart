import 'dart:async';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:resume_plus_clean/models/personalized_exercise.dart';
import 'package:resume_plus_clean/services/api_service.dart';

/// ═══════════════════════════════════════════════════════════════════════════════
///  STATE POUR LES EXERCICES PERSONNALISÉS
/// ═══════════════════════════════════════════════════════════════════════════════

enum ExerciseGenerationStatus {
  idle,
  checking,      // Vérification existence
  selectingDifficulty, // Modal ouvert
  generating,    // En cours de génération (avec progress)
  ready,         // Questions prêtes
  submitting,    // Soumission en cours
  completed,     // Résultats affichés
  error,
}

class PersonalizedExerciseState {
  final ExerciseGenerationStatus status;
  final PersonalizedExercise? exercise;
  final List<ExerciseQuestion>? questions;
  final AttemptResult? attemptResult;
  final String? errorMessage;
  final bool isLoading;

  // Pour le quiz en cours
  final Map<int, String> currentAnswers; // index_question -> 'A/B/C/D'
  final int currentQuestionIndex;

  const PersonalizedExerciseState({
    this.status = ExerciseGenerationStatus.idle,
    this.exercise,
    this.questions,
    this.attemptResult,
    this.errorMessage,
    this.isLoading = false,
    this.currentAnswers = const {},
    this.currentQuestionIndex = 0,
  });

  PersonalizedExerciseState copyWith({
    ExerciseGenerationStatus? status,
    PersonalizedExercise? exercise,
    List<ExerciseQuestion>? questions,
    AttemptResult? attemptResult,
    String? errorMessage,
    bool? isLoading,
    Map<int, String>? currentAnswers,
    int? currentQuestionIndex,
    bool clearError = false,
    bool clearExercise = false,
    bool clearQuestions = false,
    bool clearResult = false,
  }) {
    return PersonalizedExerciseState(
      status: status ?? this.status,
      exercise: clearExercise ? null : (exercise ?? this.exercise),
      questions: clearQuestions ? null : (questions ?? this.questions),
      attemptResult: clearResult ? null : (attemptResult ?? this.attemptResult),
      errorMessage: clearError ? null : (errorMessage ?? this.errorMessage),
      isLoading: isLoading ?? this.isLoading,
      currentAnswers: currentAnswers ?? this.currentAnswers,
      currentQuestionIndex: currentQuestionIndex ?? this.currentQuestionIndex,
    );
  }

  bool get canStartGeneration => status == ExerciseGenerationStatus.idle || status == ExerciseGenerationStatus.error;
  bool get isGenerating => status == ExerciseGenerationStatus.generating;
  bool get isReady => status == ExerciseGenerationStatus.ready;
  bool get showDifficultySelector => status == ExerciseGenerationStatus.selectingDifficulty;
  bool get isQuizInProgress => status == ExerciseGenerationStatus.ready && questions != null;
  bool get hasResult => status == ExerciseGenerationStatus.completed && attemptResult != null;

  double get progressPercentage {
    if (!isQuizInProgress || questions == null || questions!.isEmpty) return 0.0;
    return currentAnswers.length / questions!.length;
  }

  bool get isQuizComplete {
    if (questions == null) return false;
    return currentAnswers.length == questions!.length;
  }
}

/// ═══════════════════════════════════════════════════════════════════════════════
///  NOTIFIER
/// ═══════════════════════════════════════════════════════════════════════════════

class PersonalizedExerciseNotifier extends StateNotifier<PersonalizedExerciseState> {
  PersonalizedExerciseNotifier() : super(const PersonalizedExerciseState());

  final ApiService _api = ApiService();
  Timer? _pollingTimer;

  // ═══════════════════════════════════════════════════════════════════════════════
  //  1. VÉRIFICATION INITIALE
  // ═══════════════════════════════════════════════════════════════════════════════

  /// Vérifie si un exercice existe déjà pour ce résumé
  Future<void> checkExistingExercise(int summaryId) async {
    state = state.copyWith(status: ExerciseGenerationStatus.checking, isLoading: true);

    try {
      final data = await _api.checkPersonalizedExercise(summaryId);
      final exists = data['exists'] as bool? ?? false;

      if (exists) {
        final exerciseData = data;
        final status = exerciseData['status'] as String? ?? 'pending';

        if (status == 'completed') {
          // Exercice déjà prêt, le charger
          final exerciseId = exerciseData['exercise_id'] as int;
          await _loadExercise(exerciseId);
        } else if (status == 'generating') {
          // En cours, commencer le polling
          state = state.copyWith(
            status: ExerciseGenerationStatus.generating,
            isLoading: true,
          );
          final exerciseId = exerciseData['exercise_id'] as int;
          _startPolling(exerciseId);
        } else {
          // Failed ou autre, montrer le sélecteur de difficulté
          state = state.copyWith(
            status: ExerciseGenerationStatus.selectingDifficulty,
            isLoading: false,
          );
        }
      } else {
        // Pas d'exercice, montrer le sélecteur de difficulté
        state = state.copyWith(
          status: ExerciseGenerationStatus.selectingDifficulty,
          isLoading: false,
        );
      }
    } catch (e) {
      state = state.copyWith(
        status: ExerciseGenerationStatus.error,
        errorMessage: 'Erreur lors de la vérification: $e',
        isLoading: false,
      );
    }
  }

  // ═══════════════════════════════════════════════════════════════════════════════
  //  2. SÉLECTION DIFFICULTÉ
  // ═══════════════════════════════════════════════════════════════════════════════

  /// Affiche le modal de sélection de difficulté
  void showDifficultySelector() {
    state = state.copyWith(status: ExerciseGenerationStatus.selectingDifficulty);
  }

  /// Masque le sélecteur
  void hideDifficultySelector() {
    if (state.exercise == null) {
      state = state.copyWith(status: ExerciseGenerationStatus.idle);
    }
  }

  // ═══════════════════════════════════════════════════════════════════════════════
  //  3. GÉNÉRATION
  // ═══════════════════════════════════════════════════════════════════════════════

  /// Lance la génération avec la difficulté choisie
  Future<void> generateExercise({
    required int summaryId,
    required String difficulty,
    bool regenerate = false,
  }) async {
    state = state.copyWith(
      status: ExerciseGenerationStatus.generating,
      isLoading: true,
      clearExercise: true,
      clearQuestions: true,
      clearResult: true,
    );

    try {
      final data = await _api.generatePersonalizedExercise(
        summaryId: summaryId,
        difficulty: difficulty,
        regenerate: regenerate,
      );

      final exerciseId = data['exercise_id'] as int;
      final status = data['status'] as String? ?? 'generating';

      if (status == 'completed') {
        // Déjà complété (exercice existant)
        await _loadExercise(exerciseId);
      } else {
        // En cours de génération, commencer le polling
        _startPolling(exerciseId);
      }
    } catch (e) {
      state = state.copyWith(
        status: ExerciseGenerationStatus.error,
        errorMessage: 'Erreur lors de la génération: $e',
        isLoading: false,
      );
    }
  }

  // ═══════════════════════════════════════════════════════════════════════════════
  //  4. POLLING DE GÉNÉRATION (comme pour les résumés)
  // ═══════════════════════════════════════════════════════════════════════════════

  void _startPolling(int exerciseId) {
    _pollingTimer?.cancel();

    _pollingTimer = Timer.periodic(const Duration(seconds: 2), (timer) async {
      try {
        final data = await _api.getPersonalizedExercise(exerciseId);
        final status = data['status'] as String? ?? 'generating';

        if (status == 'completed') {
          timer.cancel();
          await _loadExercise(exerciseId);
        } else if (status == 'failed') {
          timer.cancel();
          state = state.copyWith(
            status: ExerciseGenerationStatus.error,
            errorMessage: 'La génération a échoué. Vous pouvez réessayer.',
            isLoading: false,
          );
        }
        // Sinon continue polling
      } catch (e) {
        timer.cancel();
        state = state.copyWith(
          status: ExerciseGenerationStatus.error,
          errorMessage: 'Erreur de connexion pendant la génération',
          isLoading: false,
        );
      }
    });
  }

  // ═══════════════════════════════════════════════════════════════════════════════
  //  5. CHARGEMENT EXERCICE
  // ═══════════════════════════════════════════════════════════════════════════════

  Future<void> _loadExercise(int exerciseId) async {
    try {
      final data = await _api.getPersonalizedExercise(exerciseId);

      final exerciseData = data['exercise'] as Map<String, dynamic>;
      final questionsList = data['questions'] as List<dynamic>? ?? [];

      final exercise = PersonalizedExercise.fromJson(exerciseData);
      final questions = questionsList
          .map((q) => ExerciseQuestion.fromJson(q as Map<String, dynamic>))
          .toList();

      state = state.copyWith(
        status: ExerciseGenerationStatus.ready,
        exercise: exercise,
        questions: questions,
        isLoading: false,
        currentAnswers: {},
        currentQuestionIndex: 0,
      );
    } catch (e) {
      state = state.copyWith(
        status: ExerciseGenerationStatus.error,
        errorMessage: 'Erreur lors du chargement: $e',
        isLoading: false,
      );
    }
  }

  // ═══════════════════════════════════════════════════════════════════════════════
  //  6. QUIZ - NAVIGATION ET RÉPONSES
  // ═══════════════════════════════════════════════════════════════════════════════

  /// Sélectionne une réponse pour la question courante
  void selectAnswer(String option) {
    if (!state.isQuizInProgress) return;

    final newAnswers = Map<int, String>.from(state.currentAnswers);
    newAnswers[state.currentQuestionIndex] = option;

    state = state.copyWith(currentAnswers: newAnswers);
  }

  /// Passe à la question suivante
  void nextQuestion() {
    if (state.questions == null) return;
    if (state.currentQuestionIndex < state.questions!.length - 1) {
      state = state.copyWith(currentQuestionIndex: state.currentQuestionIndex + 1);
    }
  }

  /// Revient à la question précédente
  void previousQuestion() {
    if (state.currentQuestionIndex > 0) {
      state = state.copyWith(currentQuestionIndex: state.currentQuestionIndex - 1);
    }
  }

  /// Va directement à une question spécifique
  void goToQuestion(int index) {
    if (state.questions != null && index >= 0 && index < state.questions!.length) {
      state = state.copyWith(currentQuestionIndex: index);
    }
  }

  // ═══════════════════════════════════════════════════════════════════════════════
  //  7. SOUMISSION
  // ═══════════════════════════════════════════════════════════════════════════════

  /// Soumet toutes les réponses et récupère le score
  Future<void> submitQuiz() async {
    if (!state.isQuizComplete || state.exercise == null) return;

    state = state.copyWith(status: ExerciseGenerationStatus.submitting, isLoading: true);

    try {
      // Convertir les réponses au format API
      final answers = state.currentAnswers.map(
        (key, value) => MapEntry(key.toString(), value),
      );

      final data = await _api.submitPersonalizedExercise(
        exerciseId: state.exercise!.id,
        answers: answers,
      );

      final result = AttemptResult.fromJson(data);

      state = state.copyWith(
        status: ExerciseGenerationStatus.completed,
        attemptResult: result,
        isLoading: false,
      );
    } catch (e) {
      state = state.copyWith(
        status: ExerciseGenerationStatus.error,
        errorMessage: 'Erreur lors de la soumission: $e',
        isLoading: false,
      );
    }
  }

  // ═══════════════════════════════════════════════════════════════════════════════
  //  8. RÉINITIALISATION
  // ═══════════════════════════════════════════════════════════════════════════════

  /// Réinitialise tout pour recommencer
  void reset() {
    _pollingTimer?.cancel();
    state = const PersonalizedExerciseState();
  }

  /// Prépare une régénération (garde le résumé mais reset le reste)
  void prepareRegeneration() {
    _pollingTimer?.cancel();
    state = state.copyWith(
      status: ExerciseGenerationStatus.selectingDifficulty,
      clearExercise: true,
      clearQuestions: true,
      clearResult: true,
      currentAnswers: {},
      currentQuestionIndex: 0,
    );
  }

  @override
  void dispose() {
    _pollingTimer?.cancel();
    super.dispose();
  }
}

/// ═══════════════════════════════════════════════════════════════════════════════
///  PROVIDERS
/// ═══════════════════════════════════════════════════════════════════════════════

final personalizedExerciseProvider =
    StateNotifierProvider<PersonalizedExerciseNotifier, PersonalizedExerciseState>(
  (ref) => PersonalizedExerciseNotifier(),
);

/// Provider pour l'historique des tentatives
final personalizedExerciseAttemptsProvider =
    FutureProvider.autoDispose<List<ExerciseAttempt>>((ref) async {
  final api = ApiService();
  final data = await api.getPersonalizedExerciseAttempts();
  final attemptsList = data['attempts'] as List<dynamic>? ?? [];
  return attemptsList
      .map((a) => ExerciseAttempt.fromJson(a as Map<String, dynamic>))
      .toList();
});

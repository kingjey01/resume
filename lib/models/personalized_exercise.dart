import 'package:flutter/foundation.dart';

/// ═══════════════════════════════════════════════════════════════════════════════
///  MODÈLES POUR LES EXERCICES QCM PERSONNALISÉS
/// ═══════════════════════════════════════════════════════════════════════════════

/// Exercice personnalisé d'un utilisateur
class PersonalizedExercise {
  final int id;
  final int summaryId;
  final String summaryTitle;
  final String difficulty; // 'easy', 'medium', 'hard'
  final String difficultyLabel;
  final int questionsCount;
  final bool generatedByAi;
  final int regeneratedCount;
  final DateTime createdAt;
  final String status; // 'pending', 'generating', 'completed', 'failed'

  const PersonalizedExercise({
    required this.id,
    required this.summaryId,
    required this.summaryTitle,
    required this.difficulty,
    required this.difficultyLabel,
    required this.questionsCount,
    required this.generatedByAi,
    required this.regeneratedCount,
    required this.createdAt,
    required this.status,
  });

  factory PersonalizedExercise.fromJson(Map<String, dynamic> json) {
    return PersonalizedExercise(
      id: json['exercise_id'] as int? ?? json['id'] as int? ?? 0,
      summaryId: json['summary_id'] as int? ?? 0,
      summaryTitle: json['summary_title'] as String? ?? '',
      difficulty: json['difficulty'] as String? ?? 'medium',
      difficultyLabel: json['difficulty_label'] as String? ?? 'Moyen',
      questionsCount: json['questions_count'] as int? ?? 0,
      generatedByAi: json['generated_by_ai'] as bool? ?? false,
      regeneratedCount: json['regenerated_count'] as int? ?? 0,
      createdAt: DateTime.tryParse(json['created_at'] as String? ?? '') ?? DateTime.now(),
      status: json['status'] as String? ?? 'pending',
    );
  }

  PersonalizedExercise copyWith({
    int? id,
    int? summaryId,
    String? summaryTitle,
    String? difficulty,
    String? difficultyLabel,
    int? questionsCount,
    bool? generatedByAi,
    int? regeneratedCount,
    DateTime? createdAt,
    String? status,
  }) {
    return PersonalizedExercise(
      id: id ?? this.id,
      summaryId: summaryId ?? this.summaryId,
      summaryTitle: summaryTitle ?? this.summaryTitle,
      difficulty: difficulty ?? this.difficulty,
      difficultyLabel: difficultyLabel ?? this.difficultyLabel,
      questionsCount: questionsCount ?? this.questionsCount,
      generatedByAi: generatedByAi ?? this.generatedByAi,
      regeneratedCount: regeneratedCount ?? this.regeneratedCount,
      createdAt: createdAt ?? this.createdAt,
      status: status ?? this.status,
    );
  }

  bool get isGenerating => status == 'generating';
  bool get isCompleted => status == 'completed';
  bool get isFailed => status == 'failed';

  @override
  String toString() {
    return 'PersonalizedExercise(id: $id, difficulty: $difficulty, status: $status)';
  }
}

/// Question QCM
class ExerciseQuestion {
  final int index;
  final String questionText;
  final Map<String, String> options; // {'A': 'Option A', 'B': 'Option B', ...}

  const ExerciseQuestion({
    required this.index,
    required this.questionText,
    required this.options,
  });

  factory ExerciseQuestion.fromJson(Map<String, dynamic> json) {
    final optionsMap = json['options'] as Map<String, dynamic>? ?? {};
    return ExerciseQuestion(
      index: json['index'] as int? ?? 0,
      questionText: json['question_text'] as String? ?? '',
      options: optionsMap.map((k, v) => MapEntry(k, v.toString())),
    );
  }

  List<MapEntry<String, String>> get optionsList => options.entries.toList();
}

/// Exercice complet avec questions
class PersonalizedExerciseWithQuestions {
  final PersonalizedExercise exercise;
  final List<ExerciseQuestion> questions;

  const PersonalizedExerciseWithQuestions({
    required this.exercise,
    required this.questions,
  });

  factory PersonalizedExerciseWithQuestions.fromJson(Map<String, dynamic> json) {
    final exercise = PersonalizedExercise.fromJson(json['exercise'] as Map<String, dynamic>);
    final questionsList = (json['questions'] as List<dynamic>? ?? [])
        .map((q) => ExerciseQuestion.fromJson(q as Map<String, dynamic>))
        .toList();

    return PersonalizedExerciseWithQuestions(
      exercise: exercise,
      questions: questionsList,
    );
  }
}

/// Réponse soumise par l'utilisateur
class ExerciseAnswer {
  final int questionIndex;
  final String selectedOption; // 'A', 'B', 'C', 'D'

  const ExerciseAnswer({
    required this.questionIndex,
    required this.selectedOption,
  });

  Map<String, dynamic> toJson() => {
    questionIndex.toString(): selectedOption,
  };
}

/// Résultat d'une tentative
class AttemptResult {
  final int attemptId;
  final double score;
  final int correctAnswers;
  final int totalQuestions;
  final int timeSpentSeconds;
  final String message;
  final List<QuestionResult> results;

  const AttemptResult({
    required this.attemptId,
    required this.score,
    required this.correctAnswers,
    required this.totalQuestions,
    required this.timeSpentSeconds,
    required this.message,
    required this.results,
  });

  factory AttemptResult.fromJson(Map<String, dynamic> json) {
    final resultsList = (json['results'] as List<dynamic>? ?? [])
        .map((r) => QuestionResult.fromJson(r as Map<String, dynamic>))
        .toList();

    return AttemptResult(
      attemptId: json['attempt_id'] as int? ?? 0,
      score: (json['score'] as num?)?.toDouble() ?? 0.0,
      correctAnswers: json['correct_answers'] as int? ?? 0,
      totalQuestions: json['total_questions'] as int? ?? 0,
      timeSpentSeconds: json['time_spent_seconds'] as int? ?? 0,
      message: json['message'] as String? ?? '',
      results: resultsList,
    );
  }

  String get formattedScore => '${score.toStringAsFixed(0)}%';
  String get formattedTime {
    final minutes = timeSpentSeconds ~/ 60;
    final seconds = timeSpentSeconds % 60;
    if (minutes > 0) {
      return '${minutes}min ${seconds}s';
    }
    return '${seconds}s';
  }
}

/// Résultat d'une question spécifique
class QuestionResult {
  final int questionIndex;
  final String questionText;
  final String userAnswer;
  final String correctAnswer;
  final bool isCorrect;
  final String explanation;
  final Map<String, String> options;

  const QuestionResult({
    required this.questionIndex,
    required this.questionText,
    required this.userAnswer,
    required this.correctAnswer,
    required this.isCorrect,
    required this.explanation,
    required this.options,
  });

  factory QuestionResult.fromJson(Map<String, dynamic> json) {
    final optionsMap = json['options'] as Map<String, dynamic>? ?? {};
    return QuestionResult(
      questionIndex: json['question_index'] as int? ?? 0,
      questionText: json['question_text'] as String? ?? '',
      userAnswer: json['user_answer'] as String? ?? '',
      correctAnswer: json['correct_answer'] as String? ?? '',
      isCorrect: json['is_correct'] as bool? ?? false,
      explanation: json['explanation'] as String? ?? '',
      options: optionsMap.map((k, v) => MapEntry(k, v.toString())),
    );
  }
}

/// Tentative dans l'historique
class ExerciseAttempt {
  final int id;
  final int exerciseId;
  final int summaryId;
  final String summaryTitle;
  final String difficulty;
  final String difficultyLabel;
  final double score;
  final int correctAnswers;
  final int totalQuestions;
  final int timeSpentSeconds;
  final DateTime startedAt;
  final DateTime? completedAt;

  const ExerciseAttempt({
    required this.id,
    required this.exerciseId,
    required this.summaryId,
    required this.summaryTitle,
    required this.difficulty,
    required this.difficultyLabel,
    required this.score,
    required this.correctAnswers,
    required this.totalQuestions,
    required this.timeSpentSeconds,
    required this.startedAt,
    this.completedAt,
  });

  factory ExerciseAttempt.fromJson(Map<String, dynamic> json) {
    return ExerciseAttempt(
      id: json['id'] as int? ?? 0,
      exerciseId: json['exercise_id'] as int? ?? 0,
      summaryId: json['summary_id'] as int? ?? 0,
      summaryTitle: json['summary_title'] as String? ?? '',
      difficulty: json['difficulty'] as String? ?? 'medium',
      difficultyLabel: json['difficulty_label'] as String? ?? 'Moyen',
      score: (json['score'] as num?)?.toDouble() ?? 0.0,
      correctAnswers: json['correct_answers'] as int? ?? 0,
      totalQuestions: json['total_questions'] as int? ?? 0,
      timeSpentSeconds: json['time_spent_seconds'] as int? ?? 0,
      startedAt: DateTime.tryParse(json['started_at'] as String? ?? '') ?? DateTime.now(),
      completedAt: json['completed_at'] != null
          ? DateTime.tryParse(json['completed_at'] as String)
          : null,
    );
  }

  String get formattedScore => '${score.toStringAsFixed(0)}%';
  String get formattedTime {
    final minutes = timeSpentSeconds ~/ 60;
    final seconds = timeSpentSeconds % 60;
    if (minutes > 0) {
      return '${minutes}min ${seconds}s';
    }
    return '${seconds}s';
  }
}

/// Vérification existence exercice
class ExerciseExistsCheck {
  final bool exists;
  final int? exerciseId;
  final String? status;
  final String? difficulty;
  final String? difficultyLabel;
  final int? questionsCount;
  final int? regeneratedCount;
  final DateTime? createdAt;
  final bool canRegenerate;
  final int? attemptsCount;

  const ExerciseExistsCheck({
    required this.exists,
    this.exerciseId,
    this.status,
    this.difficulty,
    this.difficultyLabel,
    this.questionsCount,
    this.regeneratedCount,
    this.createdAt,
    this.canRegenerate = false,
    this.attemptsCount,
  });

  factory ExerciseExistsCheck.fromJson(Map<String, dynamic> json) {
    return ExerciseExistsCheck(
      exists: json['exists'] as bool? ?? false,
      exerciseId: json['exercise_id'] as int?,
      status: json['status'] as String?,
      difficulty: json['difficulty'] as String?,
      difficultyLabel: json['difficulty_label'] as String?,
      questionsCount: json['questions_count'] as int?,
      regeneratedCount: json['regenerated_count'] as int?,
      createdAt: json['created_at'] != null
          ? DateTime.tryParse(json['created_at'] as String)
          : null,
      canRegenerate: json['can_regenerate'] as bool? ?? false,
      attemptsCount: json['attempts_count'] as int?,
    );
  }

  bool get hasCompletedExercise => exists && status == 'completed';
  bool get isGenerating => exists && status == 'generating';
}

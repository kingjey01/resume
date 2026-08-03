class Exercise {
  final int id;
  final String titre;
  final String? description;
  final String status;
  final bool generatedByAi;
  final int summaryId;
  final String? summaryTitle;
  final int questionsCount;
  final DateTime createdAt;

  const Exercise({
    required this.id,
    required this.titre,
    this.description,
    required this.status,
    this.generatedByAi = true,
    required this.summaryId,
    this.summaryTitle,
    this.questionsCount = 0,
    required this.createdAt,
  });

  factory Exercise.fromJson(Map<String, dynamic> json) {
    return Exercise(
      id: json['id'] ?? 0,
      titre: json['titre'] ?? '',
      description: json['description'],
      status: json['status'] ?? 'pending',
      generatedByAi: json['generated_by_ai'] ?? true,
      summaryId: json['summary'] ?? json['summary_id'] ?? 0,
      summaryTitle: json['summary_title'],
      questionsCount: json['questions_count'] ?? 0,
      createdAt: json['created_at'] != null
          ? DateTime.parse(json['created_at'])
          : DateTime.now(),
    );
  }

  bool get isCompleted => status == 'completed';
  bool get isGenerating => status == 'generating';
  bool get isFailed => status == 'failed';
}

class ExerciseQuestion {
  final int id;
  final String questionText;
  final Map<String, String> options;
  final int order;
  // Only available after submission
  final String? correctAnswer;
  final String? explanation;
  final String? codeLanguage;
  final String? codeBlock;

  const ExerciseQuestion({
    required this.id,
    required this.questionText,
    required this.options,
    required this.order,
    this.correctAnswer,
    this.explanation,
    this.codeLanguage,
    this.codeBlock,
  });

  factory ExerciseQuestion.fromJson(Map<String, dynamic> json) {
    final optionsRaw = json['options'] as Map<String, dynamic>? ?? {};
    final options = optionsRaw.map((k, v) => MapEntry(k, v.toString()));

    return ExerciseQuestion(
      id: json['id'] ?? 0,
      questionText: json['question_text'] ?? json['question'] ?? '',
      options: options,
      order: json['order'] ?? 0,
      correctAnswer: json['correct_answer'],
      explanation: json['explanation'],
      codeLanguage: json['code_language'],
      codeBlock: json['code_block'],
    );
  }
}

class ExerciseAttempt {
  final int id;
  final String exerciseTitle;
  final String summaryTitle;
  final double score;
  final DateTime completedAt;
  final int exerciseId;

  const ExerciseAttempt({
    required this.id,
    required this.exerciseTitle,
    required this.summaryTitle,
    required this.score,
    required this.completedAt,
    required this.exerciseId,
  });

  factory ExerciseAttempt.fromJson(Map<String, dynamic> json) {
    return ExerciseAttempt(
      id: json['id'] ?? 0,
      exerciseTitle: json['exercise_title'] ?? '',
      summaryTitle: json['summary_title'] ?? '',
      score: (json['score'] is num) ? json['score'].toDouble() : 0.0,
      completedAt: json['completed_at'] != null
          ? DateTime.parse(json['completed_at'])
          : DateTime.now(),
      exerciseId: json['exercise_id'] ?? 0,
    );
  }

  String get scoreFormatted => '${score.toStringAsFixed(0)}%';

  bool get isPassed => score >= 50;
}

class ExerciseResult {
  final int attemptId;
  final double score;
  final int totalQuestions;
  final int correctAnswers;
  final List<QuestionResult> results;

  const ExerciseResult({
    required this.attemptId,
    required this.score,
    required this.totalQuestions,
    required this.correctAnswers,
    required this.results,
  });

  factory ExerciseResult.fromJson(Map<String, dynamic> json) {
    final resultsList = (json['results'] as List<dynamic>? ?? [])
        .map((r) => QuestionResult.fromJson(r))
        .toList();

    return ExerciseResult(
      attemptId: json['attempt_id'] ?? 0,
      score: (json['score'] is num) ? json['score'].toDouble() : 0.0,
      totalQuestions: json['total_questions'] ?? 0,
      correctAnswers: json['correct_answers'] ?? 0,
      results: resultsList,
    );
  }
}

class QuestionResult {
  final int questionId;
  final String questionText;
  final String? userAnswer;
  final String correctAnswer;
  final bool isCorrect;
  final String? explanation;
  final String? codeLanguage;
  final String? codeBlock;

  const QuestionResult({
    required this.questionId,
    required this.questionText,
    this.userAnswer,
    required this.correctAnswer,
    required this.isCorrect,
    this.explanation,
    this.codeLanguage,
    this.codeBlock,
  });

  factory QuestionResult.fromJson(Map<String, dynamic> json) {
    return QuestionResult(
      questionId: json['question_id'] ?? 0,
      questionText: json['question_text'] ?? json['question'] ?? '',
      userAnswer: json['user_answer'],
      correctAnswer: json['correct_answer'] ?? '',
      isCorrect: json['is_correct'] ?? false,
      explanation: json['explanation'],
      codeLanguage: json['code_language'],
      codeBlock: json['code_block'],
    );
  }
}

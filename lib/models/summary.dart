class Summary {
  final int id;
  final String title;
  final String subject;
  final String filiereName; // Nom filière via FK
  final String imageUrl; // URL pour une image de couverture
  final String content;
  final double price;
  final bool isFree;
  final String authorName;
  final DateTime createdAt;
  final DateTime? updatedAt;
  final bool isPurchased;
  final int? courseId; // ID du cours associé
  final String authorType; // 'cp' ou 'ai'
  final bool isValidated;
  final String professorName;

  const Summary({
    required this.id,
    required this.title,
    required this.subject,
    this.filiereName = '',
    required this.imageUrl,
    required this.content,
    required this.price,
    required this.isFree,
    required this.authorName,
    required this.createdAt,
    this.updatedAt,
    this.isPurchased = false,
    this.courseId,
    this.authorType = 'cp',
    this.isValidated = false,
    this.professorName = '',
  });

  bool get isAiGenerated => authorType == 'ai';
  bool get isCpAuthored => authorType == 'cp';

  factory Summary.fromJson(Map<String, dynamic> json) {
    return Summary(
      id: json['id'] ?? 0,
      title: json['titre'] ?? 'Titre non disponible',
      subject: json['course_name'] ?? 'Matière non disponible',
      filiereName: json['filiere_name'] ?? '',
      imageUrl: json['image_url'] ?? json['pdf_file'] ?? '', // Utiliser pdf_file ou chaîne vide
      content: json['texte_resume'] ?? 'Contenu non disponible',
      price: _parseDouble(json['prix']),
      isFree: json['is_free'] ?? true,
      authorName: json['author_name'] ?? 'Auteur inconnu',
      professorName: _parseProfessorName(json),
      createdAt: _parseDateTime(json['created_at']),
      updatedAt: json['updated_at'] != null ? _parseDateTime(json['updated_at']) : null,
      isPurchased: json['is_purchased'] ?? false,
      courseId: json['course'] is int ? json['course'] : null,
      authorType: json['author_type'] ?? 'cp',
      isValidated: json['is_validated'] ?? false,
    );
  }

  static DateTime _parseDateTime(dynamic value) {
    if (value == null) return DateTime.now();
    if (value is String) {
      try {
        return DateTime.parse(value);
      } catch (e) {
        return DateTime.now();
      }
    }
    return DateTime.now();
  }

  static String _parseProfessorName(Map<String, dynamic> json) {
    // 1. Champ texte direct du backend (fallback universel)
    final display = json['professor_display'];
    if (display is String && display.trim().isNotEmpty) return display.trim();
    // 2. Objet professeur_info (FK)
    final info = json['professeur_info'];
    if (info is Map) {
      final fullName = info['user_full_name'];
      if (fullName is String && fullName.trim().isNotEmpty) return fullName.trim();
      final username = info['user_username'];
      if (username is String && username.trim().isNotEmpty) return username.trim();
    }
    // 3. Nom texte brut si présent
    final rawName = json['professeur'];
    if (rawName is String && rawName.trim().isNotEmpty) return rawName.trim();
    return '';
  }

  static double _parseDouble(dynamic value) {
    if (value == null) return 0.0;
    if (value is double) return value;
    if (value is int) return value.toDouble();
    if (value is String) {
      return double.tryParse(value) ?? 0.0;
    }
    return 0.0;
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'titre': title,
      'course_name': subject,
      'filiere_name': filiereName,
      'image_url': imageUrl,
      'texte_resume': content,
      'prix': price,
      'is_free': isFree,
      'author_name': authorName,
      'created_at': createdAt.toIso8601String(),
      'updated_at': updatedAt?.toIso8601String(),
      'is_purchased': isPurchased,
      'course': courseId,
      'author_type': authorType,
      'is_validated': isValidated,
      'professor_name': professorName,
    };
  }
}

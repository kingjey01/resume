class Course {
  final int id;
  final String nom;
  final String filiere;
  final String description;
  final String university;
  final DateTime createdAt;

  // FK-based fields
  final int? universiteFk;
  final String? universiteNom;
  final int? filiereFk;
  final String? filiereNom;
  final int? promotionFk;
  final String? promotionNom;

  const Course({
    required this.id,
    required this.nom,
    required this.filiere,
    required this.description,
    required this.university,
    required this.createdAt,
    this.universiteFk,
    this.universiteNom,
    this.filiereFk,
    this.filiereNom,
    this.promotionFk,
    this.promotionNom,
  });

  /// Nom de l'université via FK, sinon fallback sur le champ texte
  String get universiteDisplay => universiteNom ?? university;

  /// Nom de la filière via FK, sinon fallback sur le champ texte
  String get filiereDisplay => filiereNom ?? filiere;

  /// Nom de la promotion via FK
  String get promotionDisplay => promotionNom ?? '';

  factory Course.fromJson(Map<String, dynamic> json) {
    return Course(
      id: json['id'] ?? 0,
      nom: json['nom'] ?? '',
      filiere: json['filiere'] ?? '',
      description: json['description'] ?? '',
      university: json['university'] ?? '',
      createdAt: _parseDateTime(json['created_at']),
      universiteFk: json['universite_fk'],
      universiteNom: json['universite_nom'],
      filiereFk: json['filiere_fk'],
      filiereNom: json['filiere_nom'],
      promotionFk: json['promotion_fk'],
      promotionNom: json['promotion_nom'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'nom': nom,
      'filiere': filiere,
      'description': description,
      'university': university,
      'created_at': createdAt.toIso8601String(),
      if (universiteFk != null) 'universite_fk': universiteFk,
      if (filiereFk != null) 'filiere_fk': filiereFk,
      if (promotionFk != null) 'promotion_fk': promotionFk,
    };
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

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is Course && runtimeType == other.runtimeType && id == other.id;

  @override
  int get hashCode => id.hashCode;
}

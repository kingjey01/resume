class Professeur {
  final int id;
  final int userId;
  final String userFullName;
  final String userUsername;
  final String? telephone;
  final String? specialite;
  final int universiteId;
  final String universiteNom;
  final bool isActive;
  final DateTime createdAt;

  Professeur({
    required this.id,
    required this.userId,
    required this.userFullName,
    required this.userUsername,
    this.telephone,
    this.specialite,
    required this.universiteId,
    required this.universiteNom,
    required this.isActive,
    required this.createdAt,
  });

  factory Professeur.fromJson(Map<String, dynamic> json) {
    return Professeur(
      id: json['id'],
      userId: json['user'],
      userFullName: json['user_full_name'] ?? json['user_username'] ?? 'Professeur',
      userUsername: json['user_username'] ?? '',
      telephone: json['telephone'],
      specialite: json['specialite'],
      universiteId: json['universite'],
      universiteNom: json['universite_nom'] ?? '',
      isActive: json['is_active'] ?? true,
      createdAt: json['created_at'] != null
          ? DateTime.parse(json['created_at'])
          : DateTime.now(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'user': userId,
      'user_full_name': userFullName,
      'user_username': userUsername,
      'telephone': telephone,
      'specialite': specialite,
      'universite': universiteId,
      'universite_nom': universiteNom,
      'is_active': isActive,
      'created_at': createdAt.toIso8601String(),
    };
  }

  String get displayName => userFullName.isNotEmpty ? userFullName : userUsername;

  String get displayInfo => specialite != null && specialite!.isNotEmpty
      ? '$displayName - $specialite'
      : displayName;

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is Professeur && runtimeType == other.runtimeType && id == other.id;

  @override
  int get hashCode => id.hashCode;
}

class User {
  final int id;
  final String username;
  final String email;
  final String? firstName;
  final String? lastName;
  final String? avatar;
  final String groupe;
  final int? universiteId;
  final int? promotionId;
  final int? filiereId;
  final DateTime? dateJoined;
  final bool hasActiveSubscription;

  User({
    required this.id,
    required this.username,
    required this.email,
    this.firstName,
    this.lastName,
    this.avatar,
    required this.groupe,
    this.universiteId,
    this.promotionId,
    this.filiereId,
    this.dateJoined,
    this.hasActiveSubscription = false,
  });

  factory User.fromJson(Map<String, dynamic> json) {
    final profile = json['profile'] as Map<String, dynamic>?;
    
    return User(
      id: json['id'] as int,
      username: json['username'] as String,
      email: json['email'] as String,
      firstName: json['first_name'] as String?,
      lastName: json['last_name'] as String?,
      avatar: json['avatar'] as String?,
      groupe: profile?['groupe'] as String? ?? 'ETUDIANT',
      universiteId: profile?['universite'] as int?,
      promotionId: profile?['promotion'] as int?,
      filiereId: profile?['filiere'] as int?,
      hasActiveSubscription: profile?['has_active_subscription'] as bool? ?? false,
      dateJoined: json['date_joined'] != null 
          ? DateTime.parse(json['date_joined'] as String)
          : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'username': username,
      'email': email,
      'first_name': firstName,
      'last_name': lastName,
      'avatar': avatar,
      'groupe': groupe,
      'universite_id': universiteId,
      'promotion_id': promotionId,
      'filiere_id': filiereId,
      'has_active_subscription': hasActiveSubscription,
      'date_joined': dateJoined?.toIso8601String(),
    };
  }

  String get displayName {
    if (firstName != null && lastName != null) {
      return '$firstName $lastName';
    }
    return username;
  }

  bool get isAdmin => groupe == 'ADMIN';
  bool get isCP => groupe == 'CP';
  bool get isStudent => groupe == 'ETUDIANT';

  // Alias for backward compatibility
  String get role => groupe;

  User copyWith({
    int? id,
    String? username,
    String? email,
    String? firstName,
    String? lastName,
    String? avatar,
    String? groupe,
    int? universiteId,
    int? promotionId,
    int? filiereId,
    DateTime? dateJoined,
  }) {
    return User(
      id: id ?? this.id,
      username: username ?? this.username,
      email: email ?? this.email,
      firstName: firstName ?? this.firstName,
      lastName: lastName ?? this.lastName,
      avatar: avatar ?? this.avatar,
      groupe: groupe ?? this.groupe,
      universiteId: universiteId ?? this.universiteId,
      promotionId: promotionId ?? this.promotionId,
      filiereId: filiereId ?? this.filiereId,
      dateJoined: dateJoined ?? this.dateJoined,
    );
  }

  @override
  bool operator ==(Object other) {
    if (identical(this, other)) return true;
    return other is User && other.id == id;
  }

  @override
  int get hashCode => id.hashCode;
}

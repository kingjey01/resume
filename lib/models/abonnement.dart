class Abonnement {
  final int id;
  final String? description;
  final int service;
  final String serviceNom;
  final int etudiant;
  final String etudiantUsername;
  final DateTime dateDebut;
  final DateTime dateFin;
  final double montant;
  final String devise;
  final bool isActive;
  final DateTime createdAt;
  final DateTime updatedAt;

  Abonnement({
    required this.id,
    this.description,
    required this.service,
    required this.serviceNom,
    required this.etudiant,
    required this.etudiantUsername,
    required this.dateDebut,
    required this.dateFin,
    required this.montant,
    required this.devise,
    required this.isActive,
    required this.createdAt,
    required this.updatedAt,
  });

  factory Abonnement.fromJson(Map<String, dynamic> json) {
    return Abonnement(
      id: json['id'] ?? 0,
      description: json['description'],
      service: json['service'] ?? 0,
      serviceNom: json['service_name'] ?? json['service_nom'] ?? '',
      etudiant: json['user'] ?? json['etudiant'] ?? 0,
      etudiantUsername: json['user_username'] ?? json['etudiant_username'] ?? '',
      dateDebut: DateTime.parse(json['date_debut']),
      dateFin: DateTime.parse(json['date_fin']),
      montant: double.tryParse(json['montant']?.toString() ?? '0') ?? 0.0,
      devise: json['devise'] ?? 'CDF',
      isActive: json['status'] == 'active' || json['is_active'] == true,
      createdAt: DateTime.parse(json['created_at']),
      updatedAt: json['updated_at'] != null 
          ? DateTime.parse(json['updated_at']) 
          : DateTime.parse(json['created_at']),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'description': description,
      'service': service,
      'service_nom': serviceNom,
      'etudiant': etudiant,
      'etudiant_username': etudiantUsername,
      'date_debut': dateDebut.toIso8601String(),
      'date_fin': dateFin.toIso8601String(),
      'montant': montant,
      'devise': devise,
      'is_active': isActive,
      'created_at': createdAt.toIso8601String(),
      'updated_at': updatedAt.toIso8601String(),
    };
  }

  Map<String, dynamic> toCreateJson() {
    return {
      'description': description,
      'service': service,
      'date_debut': dateDebut.toIso8601String(),
      'date_fin': dateFin.toIso8601String(),
      'montant': montant,
      'devise': devise,
    };
  }

  String get statusText {
    if (isActive) {
      return 'Actif';
    } else if (DateTime.now().isBefore(dateDebut)) {
      return 'À venir';
    } else {
      return 'Expiré';
    }
  }

  String get formattedMontant {
    switch (devise) {
      case 'USD':
        return '\$${montant.toStringAsFixed(2)}';
      case 'EUR':
        return '€${montant.toStringAsFixed(2)}';
      case 'CDF':
      default:
        return '${montant.toStringAsFixed(0)} FC';
    }
  }

  @override
  String toString() {
    return 'Abonnement{id: $id, service: $serviceNom, isActive: $isActive}';
  }

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is Abonnement &&
          runtimeType == other.runtimeType &&
          id == other.id;

  @override
  int get hashCode => id.hashCode;
}

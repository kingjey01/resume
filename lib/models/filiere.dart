class Filiere {
  final int id;
  final String nom;
  final String? description;
  final DateTime createdAt;

  Filiere({
    required this.id,
    required this.nom,
    this.description,
    required this.createdAt,
  });

  factory Filiere.fromJson(Map<String, dynamic> json) {
    return Filiere(
      id: json['id'],
      nom: json['nom'],
      description: json['description'],
      createdAt: DateTime.parse(json['created_at']),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'nom': nom,
      'description': description,
      'created_at': createdAt.toIso8601String(),
    };
  }
}

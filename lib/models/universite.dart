class Universite {
  final int id;
  final String nom;
  final String? adresse;
  final DateTime createdAt;

  Universite({
    required this.id,
    required this.nom,
    this.adresse,
    required this.createdAt,
  });

  factory Universite.fromJson(Map<String, dynamic> json) {
    return Universite(
      id: json['id'],
      nom: json['nom'],
      adresse: json['adresse'],
      createdAt: DateTime.parse(json['created_at']),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'nom': nom,
      'adresse': adresse,
      'created_at': createdAt.toIso8601String(),
    };
  }
}

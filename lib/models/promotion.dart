class Promotion {
  final int id;
  final String nom;
  final int? annee;
  final DateTime createdAt;

  Promotion({
    required this.id,
    required this.nom,
    this.annee,
    required this.createdAt,
  });

  factory Promotion.fromJson(Map<String, dynamic> json) {
    return Promotion(
      id: json['id'],
      nom: json['nom'],
      annee: json['annee'],
      createdAt: DateTime.parse(json['created_at']),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'nom': nom,
      'annee': annee,
      'created_at': createdAt.toIso8601String(),
    };
  }
}

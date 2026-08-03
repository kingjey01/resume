class Service {
  final int id;
  final String nom;
  final String? description;
  final double prix;
  final DateTime createdAt;
  final DateTime updatedAt;

  Service({
    required this.id,
    required this.nom,
    this.description,
    required this.prix,
    required this.createdAt,
    required this.updatedAt,
  });

  factory Service.fromJson(Map<String, dynamic> json) {
    return Service(
      id: json['id'],
      nom: json['nom'],
      description: json['description'],
      prix: double.tryParse(json['price']?.toString() ?? '0') ?? 0.0,
      createdAt: DateTime.parse(json['created_at']),
      updatedAt: json['updated_at'] != null 
          ? DateTime.parse(json['updated_at']) 
          : DateTime.parse(json['created_at']),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'nom': nom,
      'description': description,
      'prix': prix,
      'created_at': createdAt.toIso8601String(),
      'updated_at': updatedAt.toIso8601String(),
    };
  }

  @override
  String toString() {
    return 'Service{id: $id, nom: $nom, prix: $prix}';
  }

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is Service &&
          runtimeType == other.runtimeType &&
          id == other.id;

  @override
  int get hashCode => id.hashCode;
}

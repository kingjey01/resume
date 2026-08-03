import 'package:json_annotation/json_annotation.dart';
import 'universite.dart';
import 'filiere.dart';

part 'universite_filiere.g.dart';

@JsonSerializable()
class UniversiteFiliere {
  final int id;
  final Universite universite;
  final Filiere filiere;
  final DateTime createdAt;

  UniversiteFiliere({
    required this.id,
    required this.universite,
    required this.filiere,
    required this.createdAt,
  });

  factory UniversiteFiliere.fromJson(Map<String, dynamic> json) => 
      _$UniversiteFiliereFromJson(json);
  
  Map<String, dynamic> toJson() => _$UniversiteFiliereToJson(this);
}

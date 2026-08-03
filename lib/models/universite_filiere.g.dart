// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'universite_filiere.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

UniversiteFiliere _$UniversiteFiliereFromJson(Map<String, dynamic> json) =>
    UniversiteFiliere(
      id: (json['id'] as num).toInt(),
      universite:
          Universite.fromJson(json['universite'] as Map<String, dynamic>),
      filiere: Filiere.fromJson(json['filiere'] as Map<String, dynamic>),
      createdAt: DateTime.parse(json['createdAt'] as String),
    );

Map<String, dynamic> _$UniversiteFiliereToJson(UniversiteFiliere instance) =>
    <String, dynamic>{
      'id': instance.id,
      'universite': instance.universite,
      'filiere': instance.filiere,
      'createdAt': instance.createdAt.toIso8601String(),
    };

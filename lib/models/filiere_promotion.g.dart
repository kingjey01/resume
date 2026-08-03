// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'filiere_promotion.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

FilierePromotion _$FilierePromotionFromJson(Map<String, dynamic> json) =>
    FilierePromotion(
      id: (json['id'] as num).toInt(),
      filiere: Filiere.fromJson(json['filiere'] as Map<String, dynamic>),
      promotion: Promotion.fromJson(json['promotion'] as Map<String, dynamic>),
      createdAt: DateTime.parse(json['createdAt'] as String),
    );

Map<String, dynamic> _$FilierePromotionToJson(FilierePromotion instance) =>
    <String, dynamic>{
      'id': instance.id,
      'filiere': instance.filiere,
      'promotion': instance.promotion,
      'createdAt': instance.createdAt.toIso8601String(),
    };

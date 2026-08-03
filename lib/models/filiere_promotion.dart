import 'package:json_annotation/json_annotation.dart';
import 'filiere.dart';
import 'promotion.dart';

part 'filiere_promotion.g.dart';

@JsonSerializable()
class FilierePromotion {
  final int id;
  final Filiere filiere;
  final Promotion promotion;
  final DateTime createdAt;

  FilierePromotion({
    required this.id,
    required this.filiere,
    required this.promotion,
    required this.createdAt,
  });

  factory FilierePromotion.fromJson(Map<String, dynamic> json) => 
      _$FilierePromotionFromJson(json);
  
  Map<String, dynamic> toJson() => _$FilierePromotionToJson(this);
}

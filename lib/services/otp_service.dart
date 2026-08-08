import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:resume_plus_clean/services/api_service.dart';

class OtpService {
  final Dio _dio;
  static String get baseUrl => ApiService.baseUrl;

  OtpService(this._dio);

  /// Demande un code OTP pour un numéro de téléphone
  Future<Map<String, dynamic>> requestOtp(String phone) async {
    try {
      final response = await _dio.post(
        '$baseUrl/auth/otp/request/',
        data: {'phone': phone},
      );
      
      if (kDebugMode) {
        print('OTP Request Response: ${response.data}');
      }
      
      return {
        'success': true,
        'message': response.data['message'] ?? 'Code OTP envoyé',
        'debug_code': response.data['debug_code'], // Pour les tests
        // Mode test Google Play : code OTP renvoyé par le backend
        // → le frontend le soumet automatiquement (le testeur ne tape rien)
        'otp_code': response.data['otp_code'],
        'test_mode': response.data['test_mode'] ?? false,
      };
    } on DioException catch (e) {
      if (kDebugMode) {
        print('OTP Request Error: ${e.response?.data}');
      }
      
      return {
        'success': false,
        'error': e.response?.data['error'] ?? 'Erreur lors de l\'envoi du code OTP',
      };
    } catch (e) {
      if (kDebugMode) {
        print('OTP Request Unexpected Error: $e');
      }
      
      return {
        'success': false,
        'error': 'Une erreur inattendue est survenue',
      };
    }
  }

  /// Vérifie un code OTP et connecte l'utilisateur
  Future<Map<String, dynamic>> verifyOtp(String phone, String otpCode) async {
    try {
      final response = await _dio.post(
        '$baseUrl/auth/otp/verify/',
        data: {
          'phone': phone,
          'otp_code': otpCode,
        },
      );
      
      if (kDebugMode) {
        print('OTP Verify Response: ${response.data}');
      }
      
      return {
        'success': true,
        'message': response.data['message'] ?? 'Connexion réussie',
        'user': response.data['user'],
        'access_token': response.data['access'],
        'refresh_token': response.data['refresh'],
        'profile_complete': response.data['profile_complete'] ?? false,
        'requires_profile_completion': response.data['requires_profile_completion'] ?? false,
        // Détection du premier accès CP (source de vérité = backend)
        'role': response.data['role'],
        'cp_onboarding_completed': response.data['cp_onboarding_completed'] ?? false,
      };
    } on DioException catch (e) {
      if (kDebugMode) {
        print('OTP Verify Error: ${e.response?.data}');
      }
      
      String errorMessage = 'Erreur lors de la vérification du code';
      
      if (e.response?.statusCode == 429) {
        errorMessage = 'Trop de tentatives. Demandez un nouveau code.';
      } else if (e.response?.statusCode == 400) {
        errorMessage = e.response?.data['error'] ?? 'Code OTP invalide ou expiré';
      } else if (e.response?.statusCode == 404) {
        errorMessage = 'Aucun compte associé à ce numéro de téléphone';
      }
      
      return {
        'success': false,
        'error': errorMessage,
      };
    } catch (e) {
      if (kDebugMode) {
        print('OTP Verify Unexpected Error: $e');
      }
      
      return {
        'success': false,
        'error': 'Une erreur inattendue est survenue',
      };
    }
  }

  /// Complète le profil utilisateur après vérification OTP
  Future<Map<String, dynamic>> completeProfile({
    required String accessToken,
    required String firstName,
    required String lastName,
    required int universiteId,
    required int promotionId,
    required int filiereId,
  }) async {
    try {
      final response = await _dio.post(
        '$baseUrl/auth/profile/complete/',
        data: {
          'first_name': firstName,
          'last_name': lastName,
          'universite_id': universiteId,
          'promotion_id': promotionId,
          'filiere_id': filiereId,
        },
        options: Options(
          headers: {'Authorization': 'Bearer $accessToken'},
        ),
      );
      
      if (kDebugMode) {
        print('Profile Complete Response: ${response.data}');
      }
      
      return {
        'success': true,
        'message': response.data['message'] ?? 'Profil complété avec succès',
        'user': response.data['user'],
        'profile_complete': response.data['profile_complete'] ?? true,
      };
    } on DioException catch (e) {
      if (kDebugMode) {
        print('Profile Complete Error: ${e.response?.data}');
      }
      
      return {
        'success': false,
        'error': e.response?.data['error'] ?? 'Erreur lors de la complétion du profil',
      };
    } catch (e) {
      if (kDebugMode) {
        print('Profile Complete Unexpected Error: $e');
      }
      
      return {
        'success': false,
        'error': 'Une erreur inattendue est survenue',
      };
    }
  }
}

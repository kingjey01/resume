import 'package:dio/dio.dart';

/// Types d'exceptions API structurées
enum ApiExceptionType {
  network,
  timeout,
  server,
  unauthorized,
  forbidden,
  notFound,
  validation,
  noRefreshToken,
  refreshFailed,
  unknown,
}

/// Exception API structurée pour une meilleure gestion des erreurs
class ApiException implements Exception {
  final String message;
  final ApiExceptionType type;
  final int? statusCode;
  final dynamic originalError;
  
  const ApiException(
    this.message, {
    required this.type,
    this.statusCode,
    this.originalError,
  });

  /// Convertit une DioException en ApiException avec un message clair en français
  factory ApiException.fromDioException(DioException error) {
    String message = "Une erreur inattendue est survenue.";
    ApiExceptionType type = ApiExceptionType.unknown;
    int? statusCode = error.response?.statusCode;

    switch (error.type) {
      case DioExceptionType.connectionTimeout:
      case DioExceptionType.sendTimeout:
      case DioExceptionType.receiveTimeout:
        message = "Le délai de connexion a expiré. Veuillez vérifier votre connexion internet.";
        type = ApiExceptionType.timeout;
        break;
      case DioExceptionType.connectionError:
        message = "Impossible de se connecter au serveur. Vérifiez votre connexion internet.";
        type = ApiExceptionType.network;
        break;
      case DioExceptionType.badResponse:
        type = ApiExceptionType.server;
        if (statusCode == 401) {
          message = "Votre session a expiré. Veuillez vous reconnecter.";
          type = ApiExceptionType.unauthorized;
        } else if (statusCode == 403) {
          message = "Vous n'avez pas l'autorisation d'accéder à cette ressource.";
          type = ApiExceptionType.forbidden;
        } else if (statusCode == 404) {
          message = "La ressource demandée est introuvable.";
          type = ApiExceptionType.notFound;
        } else if (statusCode != null && statusCode >= 500) {
          message = "Erreur interne du serveur. Veuillez réessayer plus tard.";
        } else if (error.response?.data is Map && error.response?.data['error'] != null) {
          message = error.response?.data['error'].toString() ?? message;
          type = ApiExceptionType.validation;
        } else if (error.response?.data is Map && error.response?.data['message'] != null) {
          message = error.response?.data['message'].toString() ?? message;
        }
        break;
      case DioExceptionType.cancel:
        message = "La requête a été annulée.";
        break;
      default:
        message = "Erreur de connexion réseau.";
        type = ApiExceptionType.network;
    }

    return ApiException(
      message,
      type: type,
      statusCode: statusCode,
      originalError: error,
    );
  }
  
  @override
  String toString() {
    return message;
  }
}

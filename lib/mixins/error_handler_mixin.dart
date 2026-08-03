import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:resume_plus_clean/exceptions/api_exception.dart';
import 'package:resume_plus_clean/services/api_service.dart';
import 'package:resume_plus_clean/services/snackbar_service.dart';
import 'package:resume_plus_clean/utils/logger.dart';

/// Mixin de gestion d'erreur unifiée pour l'ensemble de l'application.
///
/// Utilise [ApiService.getErrorMessage] pour convertir toute erreur en
/// message lisible, puis affiche via [SnackbarService].
///
/// Exemple :
/// ```dart
/// class MonEcran extends StatefulWidget { ... }
/// class _MonEcranState extends State<MonEcran> with ErrorHandlerMixin {
///   Future<void> chargerDonnees() async {
///     try { ... }
///     catch (e) { handleError(e); }
///   }
/// }
/// ```
mixin ErrorHandlerMixin<T extends StatefulWidget> on State<T> {
  /// Gère une erreur et affiche un message utilisateur.
  ///
  /// [customMessage] : message alternatif si l'erreur n'est pas identifiable.
  /// [onRetry]       : action "Réessayer" dans le Snackbar.
  void handleError(dynamic error, {String? customMessage, VoidCallback? onRetry}) {
    final message = customMessage ?? ApiService.getErrorMessage(error);

    AppLogger.error('Erreur interceptée par ErrorHandlerMixin', error);

    if (mounted) {
      SnackbarService.show(
        message,
        isError: true,
        action: onRetry != null
            ? SnackBarAction(
                label: 'Réessayer',
                textColor: Colors.white,
                onPressed: onRetry,
              )
            : null,
      );
    }
  }

  /// Convertit n'importe quelle erreur en [ApiException] pour analyse.
  ApiException getApiException(dynamic error) {
    if (error is ApiException) return error;
    if (error is DioException) return ApiException.fromDioException(error);
    return ApiException(
      ApiService.getErrorMessage(error),
      type: ApiExceptionType.unknown,
      originalError: error,
    );
  }
}

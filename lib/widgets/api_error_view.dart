import 'package:flutter/material.dart';
import 'package:resume_plus_clean/exceptions/api_exception.dart';
import 'package:resume_plus_clean/theme/app_theme.dart';

class ApiErrorView extends StatelessWidget {
  final dynamic error;
  final VoidCallback onRetry;
  final String? title;
  final IconData? icon;

  const ApiErrorView({
    super.key,
    required this.error,
    required this.onRetry,
    this.title,
    this.icon,
  });

  @override
  Widget build(BuildContext context) {
    String message = "Une erreur est survenue";
    IconData errorIcon = icon ?? Icons.error_outline_rounded;
    Color errorColor = AppTheme.error;

    if (error is ApiException) {
      message = (error as ApiException).message;
      final type = (error as ApiException).type;
      
      if (type == ApiExceptionType.network || type == ApiExceptionType.timeout) {
        errorIcon = Icons.wifi_off_rounded;
        errorColor = AppTheme.warning;
      }
    } else if (error != null) {
      message = error.toString();
    }

    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              width: 80,
              height: 80,
              decoration: BoxDecoration(
                color: errorColor.withOpacity(0.1),
                shape: BoxShape.circle,
              ),
              child: Icon(errorIcon, size: 40, color: errorColor),
            ),
            const SizedBox(height: 24),
            Text(
              title ?? "Oups !",
              style: const TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.bold,
                color: AppTheme.textPrimary,
              ),
            ),
            const SizedBox(height: 12),
            Text(
              message,
              textAlign: TextAlign.center,
              style: const TextStyle(
                fontSize: 14,
                color: AppTheme.textSecondary,
                height: 1.5,
              ),
            ),
            const SizedBox(height: 32),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: onRetry,
                icon: const Icon(Icons.refresh_rounded),
                label: const Text("Réessayer"),
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppTheme.primaryBlue,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

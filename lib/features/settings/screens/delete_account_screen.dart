import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:resume_plus_clean/features/auth/providers/auth_provider.dart';
import 'package:resume_plus_clean/services/snackbar_service.dart';
import 'package:resume_plus_clean/services/api_service.dart';
import 'package:resume_plus_clean/features/auth/screens/login_screen.dart';
import 'package:resume_plus_clean/theme/app_theme.dart';

class DeleteAccountScreen extends ConsumerStatefulWidget {
  const DeleteAccountScreen({super.key});

  @override
  ConsumerState<DeleteAccountScreen> createState() => _DeleteAccountScreenState();
}

class _DeleteAccountScreenState extends ConsumerState<DeleteAccountScreen> {
  final _otpController = TextEditingController();
  final _reasonController = TextEditingController();
  final _apiService = ApiService();

  bool _isLoading = false;
  bool _isSendingOtp = false;
  bool _otpSent = false;
  bool _understandConsequences = false;
  String? _phoneMasked;

  @override
  void dispose() {
    _otpController.dispose();
    _reasonController.dispose();
    super.dispose();
  }

  Future<void> _requestOtp() async {
    setState(() => _isSendingOtp = true);
    try {
      final result = await _apiService.requestDeleteOtp();
      setState(() {
        _otpSent = true;
        _phoneMasked = result['phone_masked'];
      });
      SnackbarService.showSuccess(result['message'] ?? 'Code OTP envoyé');
    } catch (e) {
      SnackbarService.showError('Erreur lors de l\'envoi du code OTP');
    } finally {
      if (mounted) setState(() => _isSendingOtp = false);
    }
  }

  Future<void> _deleteAccount() async {
    if (!_understandConsequences) {
      SnackbarService.showError('Veuillez confirmer que vous comprenez les conséquences');
      return;
    }
    if (!_otpSent) {
      SnackbarService.showError('Veuillez d\'abord demander et recevoir le code OTP');
      return;
    }
    if (_otpController.text.trim().isEmpty) {
      SnackbarService.showError('Veuillez entrer le code OTP reçu par SMS');
      return;
    }

    setState(() => _isLoading = true);
    try {
      await _apiService.deleteAccount(
        otpCode: _otpController.text.trim(),
        reason: _reasonController.text.isNotEmpty ? _reasonController.text : 'Non spécifié',
      );

      if (mounted) {
        await ref.read(authProvider.notifier).logout();
        Navigator.of(context).pushAndRemoveUntil(
          MaterialPageRoute(builder: (_) => const LoginScreen()),
          (route) => false,
        );
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Votre compte a été supprimé avec succès'),
            backgroundColor: AppTheme.success,
          ),
        );
      }
    } catch (e) {
      String msg = 'Erreur lors de la suppression du compte';
      if (e.toString().contains('invalide') || e.toString().contains('expiré')) {
        msg = 'Code OTP invalide ou expiré';
      } else if (e.toString().contains('tentatives')) {
        msg = 'Trop de tentatives. Demandez un nouveau code.';
      }
      SnackbarService.showError(msg);
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final topPadding = MediaQuery.of(context).padding.top;

    return Scaffold(
      backgroundColor: theme.scaffoldBackgroundColor,
      body: Column(
        children: [
          Container(
            padding: EdgeInsets.only(top: topPadding + 16, left: 20, right: 20, bottom: 24),
            decoration: const BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
                colors: [AppTheme.primaryBlueDark, AppTheme.primaryBlue, AppTheme.primaryBlueLight],
              ),
              borderRadius: BorderRadius.only(
                bottomLeft: Radius.circular(24),
                bottomRight: Radius.circular(24),
              ),
            ),
            child: Row(
              children: [
                GestureDetector(
                  onTap: () => Navigator.of(context).pop(),
                  child: Container(
                    width: 40, height: 40,
                    decoration: BoxDecoration(
                      color: Colors.white.withOpacity(0.2),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: const Icon(Icons.arrow_back_rounded, color: Colors.white, size: 22),
                  ),
                ),
                const SizedBox(width: 14),
                Expanded(
                  child: Text(
                    'Supprimer le Compte',
                    style: theme.textTheme.headlineMedium?.copyWith(
                      color: Colors.white,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ),
              ],
            ),
          ),

          Expanded(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Avertissement
                  Container(
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: Colors.red.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: Colors.red.withOpacity(0.3)),
                    ),
                    child: Row(
                      children: [
                        const Icon(Icons.warning_rounded, color: Colors.red, size: 24),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Text(
                            'Cette action est irréversible',
                            style: theme.textTheme.titleMedium?.copyWith(
                              color: Colors.red,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),

                  const SizedBox(height: 20),

                  // Conséquences
                  Container(
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: theme.colorScheme.surface,
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: theme.colorScheme.outline.withOpacity(0.2)),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Ce qui sera supprimé :',
                          style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w600, color: theme.colorScheme.onSurface),
                        ),
                        const SizedBox(height: 10),
                        for (final item in [
                          '• Votre profil et informations personnelles',
                          '• Historique des achats et abonnements',
                          '• Résumés téléchargés',
                          '• Préférences et paramètres',
                        ])
                          Padding(
                            padding: const EdgeInsets.only(bottom: 6, left: 4),
                            child: Text(item, style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.onSurface.withOpacity(0.8))),
                          ),
                      ],
                    ),
                  ),

                  const SizedBox(height: 24),

                  // Étape 1 : Envoyer OTP
                  Text('Étape 1 : Recevoir le code de confirmation',
                      style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w600, color: theme.colorScheme.onSurface)),
                  const SizedBox(height: 8),
                  Text(
                    'Un code OTP sera envoyé par SMS à votre numéro de téléphone enregistré.',
                    style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.onSurface.withOpacity(0.7)),
                  ),
                  const SizedBox(height: 12),
                  SizedBox(
                    width: double.infinity,
                    child: OutlinedButton.icon(
                      onPressed: _isSendingOtp ? null : _requestOtp,
                      icon: _isSendingOtp
                          ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2))
                          : Icon(_otpSent ? Icons.refresh_rounded : Icons.sms_rounded),
                      label: Text(_otpSent ? 'Renvoyer le code' : 'Envoyer le code OTP'),
                      style: OutlinedButton.styleFrom(
                        foregroundColor: AppTheme.primaryBlue,
                        side: const BorderSide(color: AppTheme.primaryBlue),
                        padding: const EdgeInsets.symmetric(vertical: 12),
                      ),
                    ),
                  ),

                  if (_otpSent && _phoneMasked != null) ...[
                    const SizedBox(height: 8),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                      decoration: BoxDecoration(
                        color: AppTheme.primaryBlue.withOpacity(0.08),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Row(
                        children: [
                          const Icon(Icons.check_circle_outline, color: AppTheme.primaryBlue, size: 16),
                          const SizedBox(width: 8),
                          Text(
                            'Code envoyé au $_phoneMasked',
                            style: theme.textTheme.bodySmall?.copyWith(color: AppTheme.primaryBlue, fontWeight: FontWeight.w500),
                          ),
                        ],
                      ),
                    ),
                  ],

                  const SizedBox(height: 24),

                  // Étape 2 : Saisir OTP
                  Text('Étape 2 : Entrer le code de confirmation',
                      style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w600, color: theme.colorScheme.onSurface)),
                  const SizedBox(height: 8),
                  TextField(
                    controller: _otpController,
                    keyboardType: TextInputType.number,
                    maxLength: 6,
                    enabled: _otpSent,
                    decoration: InputDecoration(
                      labelText: 'Code OTP reçu par SMS',
                      hintText: '_ _ _ _',
                      prefixIcon: const Icon(Icons.dialpad_rounded),
                      border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
                      counterText: '',
                    ),
                    textAlign: TextAlign.center,
                    style: const TextStyle(letterSpacing: 6, fontSize: 20, fontWeight: FontWeight.bold),
                  ),

                  const SizedBox(height: 20),

                  // Raison (optionnel)
                  TextField(
                    controller: _reasonController,
                    maxLines: 2,
                    decoration: InputDecoration(
                      labelText: 'Raison de la suppression (optionnel)',
                      hintText: 'Aidez-nous à améliorer nos services',
                      prefixIcon: const Icon(Icons.comment_rounded),
                      border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
                    ),
                  ),

                  const SizedBox(height: 20),

                  // Confirmation checkbox
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: Colors.orange.withOpacity(0.08),
                      borderRadius: BorderRadius.circular(10),
                      border: Border.all(color: Colors.orange.withOpacity(0.3)),
                    ),
                    child: Row(
                      children: [
                        Checkbox(
                          value: _understandConsequences,
                          onChanged: (v) => setState(() => _understandConsequences = v ?? false),
                          activeColor: Colors.orange,
                        ),
                        Expanded(
                          child: Text(
                            'Je comprends que cette action est irréversible et perdrai tous mes accès',
                            style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.onSurface),
                          ),
                        ),
                      ],
                    ),
                  ),

                  const SizedBox(height: 28),

                  // Bouton supprimer
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton.icon(
                      onPressed: (_isLoading || !_otpSent) ? null : _deleteAccount,
                      icon: _isLoading
                          ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                          : const Icon(Icons.delete_forever_rounded),
                      label: Text(_isLoading ? 'Suppression en cours...' : 'Supprimer définitivement mon compte'),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.red,
                        foregroundColor: Colors.white,
                        padding: const EdgeInsets.symmetric(vertical: 14),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                        elevation: 0,
                      ),
                    ),
                  ),

                  const SizedBox(height: 14),

                  Center(
                    child: TextButton(
                      onPressed: () => Navigator.of(context).pop(),
                      child: Text(
                        'Non, je veux garder mon compte',
                        style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.primary, fontWeight: FontWeight.w500),
                      ),
                    ),
                  ),
                  const SizedBox(height: 40),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

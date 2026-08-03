import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:resume_plus_clean/theme/app_theme.dart';
import 'package:resume_plus_clean/services/otp_service.dart';
import 'package:resume_plus_clean/features/auth/screens/otp_verification_screen.dart';
import 'package:dio/dio.dart';

class PhoneLoginScreen extends StatefulWidget {
  final String? prefillPhone;

  const PhoneLoginScreen({super.key, this.prefillPhone});

  @override
  State<PhoneLoginScreen> createState() => _PhoneLoginScreenState();
}

class _PhoneLoginScreenState extends State<PhoneLoginScreen> {
  final _formKey = GlobalKey<FormState>();
  final _phoneController = TextEditingController();
  bool _isLoading = false;
  late OtpService _otpService;

  @override
  void initState() {
    super.initState();
    _otpService = OtpService(Dio());
    if (widget.prefillPhone != null && widget.prefillPhone!.isNotEmpty) {
      _phoneController.text = widget.prefillPhone!;
    }
  }

  @override
  void dispose() {
    _phoneController.dispose();
    super.dispose();
  }

  String _formatPhoneNumber(String phone) {
    // Nettoyer le numéro (supprimer espaces, tirets, etc.)
    String cleaned = phone.replaceAll(RegExp(r'[^\d+]'), '');
    
    // Ajouter le préfixe +243 si nécessaire (RDC)
    if (!cleaned.startsWith('+')) {
      if (cleaned.startsWith('243')) {
        cleaned = '+$cleaned';
      } else if (cleaned.startsWith('0')) {
        cleaned = '+243${cleaned.substring(1)}';
      } else {
        cleaned = '+243$cleaned';
      }
    }
    
    return cleaned;
  }

  Future<void> _requestOtp() async {
    if (_formKey.currentState?.validate() ?? false) {
      FocusScope.of(context).unfocus();
      
      setState(() {
        _isLoading = true;
      });
      
      try {
        String formattedPhone = _formatPhoneNumber(_phoneController.text.trim());
        
        final result = await _otpService.requestOtp(formattedPhone);
        
        if (result['success']) {
          if (mounted) {
            // Naviguer vers l'écran de vérification OTP
            Navigator.of(context).push(
              MaterialPageRoute(
                builder: (_) => OtpVerificationScreen(
                  phoneNumber: formattedPhone,
                  debugCode: result['debug_code'],
                  autoOtpCode: result['otp_code'],
                ),
              ),
            );
          }
        } else {
          if (mounted) {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(
                content: Text(result['error'] ?? 'Erreur lors de l\'envoi du code'),
                backgroundColor: AppTheme.error,
              ),
            );
          }
        }
      } catch (e) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('Une erreur inattendue est survenue'),
              backgroundColor: AppTheme.error,
            ),
          );
        }
      } finally {
        if (mounted) {
          setState(() {
            _isLoading = false;
          });
        }
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final topPadding = MediaQuery.of(context).padding.top;

    return Scaffold(
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      body: SingleChildScrollView(
        child: Column(
          children: [
            // Header bleu courbé
            Container(
              width: double.infinity,
              padding: EdgeInsets.only(top: topPadding + 40, bottom: 40),
              decoration: const BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                  colors: [AppTheme.primaryBlueDark, AppTheme.primaryBlue, AppTheme.primaryBlueLight],
                ),
                borderRadius: BorderRadius.only(
                  bottomLeft: Radius.circular(32),
                  bottomRight: Radius.circular(32),
                ),
              ),
              child: Column(
                children: [
                  Container(
                    width: 70, height: 70,
                    decoration: BoxDecoration(
                      color: Colors.white.withOpacity(0.2),
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: const Icon(Icons.phone_android_rounded, color: Colors.white, size: 36),
                  ),
                  const SizedBox(height: 16),
                  Text(
                    'Connexion par SMS',
                    style: theme.textTheme.headlineSmall?.copyWith(color: Colors.white, fontWeight: FontWeight.w700),
                  ),
                  const SizedBox(height: 6),
                  Text(
                    'Entrez votre numéro pour recevoir un code',
                    style: TextStyle(color: Colors.white.withOpacity(0.8), fontSize: 14),
                  ),
                ],
              ),
            ),

            const SizedBox(height: 28),

            // Formulaire dans carte blanche
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 24),
              child: Container(
                padding: const EdgeInsets.all(24),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(20),
                  boxShadow: AppTheme.softShadow,
                ),
                child: Form(
                  key: _formKey,
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      Text(
                        'Numéro de téléphone',
                        style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w600),
                      ),
                      const SizedBox(height: 8),
                      TextFormField(
                        controller: _phoneController,
                        keyboardType: TextInputType.phone,
                        inputFormatters: [
                          FilteringTextInputFormatter.allow(RegExp(r'[0-9+\-\s]')),
                        ],
                        decoration: InputDecoration(
                          hintText: '+243 XXX XXX XXX',
                          prefixIcon: const Icon(Icons.phone_outlined),
                          border: OutlineInputBorder(borderRadius: BorderRadius.circular(14)),
                          helperText: 'Format: +243XXXXXXXXX ou 0XXXXXXXXX',
                          helperStyle: const TextStyle(fontSize: 12),
                        ),
                        textInputAction: TextInputAction.done,
                        validator: (value) {
                          if (value == null || value.trim().isEmpty) {
                            return 'Veuillez entrer votre numéro de téléphone';
                          }
                          
                          String cleaned = value.replaceAll(RegExp(r'[^\d+]'), '');
                          if (cleaned.length < 10) {
                            return 'Numéro de téléphone invalide';
                          }
                          
                          return null;
                        },
                      ),
                      const SizedBox(height: 24),
                      
                      // Information sur le processus
                      Container(
                        padding: const EdgeInsets.all(16),
                        decoration: BoxDecoration(
                          color: AppTheme.primaryBlue.withOpacity(0.1),
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              children: [
                                Icon(Icons.info_outline, color: AppTheme.primaryBlue, size: 20),
                                const SizedBox(width: 8),
                                Text(
                                  'Comment ça marche ?',
                                  style: TextStyle(
                                    color: AppTheme.primaryBlue,
                                    fontWeight: FontWeight.w600,
                                    fontSize: 14,
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 8),
                            Text(
                              '1. Entrez votre numéro de téléphone\n'
                              '2. Recevez un code de vérification par SMS\n'
                              '3. Complétez votre profil (première connexion)\n'
                              '4. Accédez à votre espace personnel',
                              style: TextStyle(
                                color: AppTheme.textLight,
                                fontSize: 13,
                                height: 1.4,
                              ),
                            ),
                          ],
                        ),
                      ),
                      
                      const SizedBox(height: 24),
                      
                      SizedBox(
                        height: 50,
                        child: ElevatedButton(
                          onPressed: _isLoading ? null : _requestOtp,
                          style: ElevatedButton.styleFrom(
                            backgroundColor: AppTheme.primaryBlue,
                            foregroundColor: Colors.white,
                            elevation: 0,
                            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                          ),
                          child: _isLoading
                              ? const SizedBox(
                                  width: 22, height: 22,
                                  child: CircularProgressIndicator(strokeWidth: 2.5, color: Colors.white),
                                )
                              : const Text('Recevoir le code SMS', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),

            const SizedBox(height: 40),
          ],
        ),
      ),
    );
  }
}

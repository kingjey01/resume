import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:resume_plus_clean/theme/app_theme.dart';
import 'package:resume_plus_clean/services/otp_service.dart';
import 'package:resume_plus_clean/services/storage_service.dart';
import 'package:resume_plus_clean/services/api_service.dart';
import 'package:resume_plus_clean/services/fcm_service.dart';
import 'package:resume_plus_clean/services/badge_service.dart';
import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:dio/dio.dart';
import 'dart:async';

class OtpVerificationScreen extends StatefulWidget {
  final String phoneNumber;
  final String? debugCode;

  /// Mode test Google Play : code OTP renvoyé par le backend.
  /// Si présent, le code est rempli et soumis AUTOMATIQUEMENT
  /// (le testeur n'a rien à taper).
  final String? autoOtpCode;

  const OtpVerificationScreen({
    super.key,
    required this.phoneNumber,
    this.debugCode,
    this.autoOtpCode,
  });

  @override
  State<OtpVerificationScreen> createState() => _OtpVerificationScreenState();
}

class _OtpVerificationScreenState extends State<OtpVerificationScreen> {
  final List<TextEditingController> _controllers = List.generate(4, (_) => TextEditingController());
  final List<FocusNode> _focusNodes = List.generate(4, (_) => FocusNode());
  bool _isLoading = false;
  bool _canResend = false;
  int _resendCountdown = 60;
  Timer? _timer;
  late OtpService _otpService;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    _otpService = OtpService(Dio());
    _startResendTimer();
    _handleAutoOtp();
  }

  /// Mode test Google Play : si le backend a renvoyé le code OTP,
  /// on le remplit automatiquement dans les 4 champs et on le soumet
  /// immédiatement — le testeur n'a pas besoin de taper le code.
  void _handleAutoOtp() {
    final autoCode = widget.autoOtpCode ?? widget.debugCode;
    if (autoCode == null || autoCode.length != 4) return;

    // Petit délai pour laisser l'écran se construire
    Future.delayed(const Duration(milliseconds: 600), () {
      if (!mounted) return;

      // Remplir les 4 champs
      for (int i = 0; i < 4; i++) {
        _controllers[i].text = autoCode[i];
      }
      setState(() {});

      // Soumettre automatiquement
      _verifyOtp();
      print('🤖 [OTP Test Mode] Code OTP auto-soumis: $autoCode');
    });
  }

  @override
  void dispose() {
    for (var controller in _controllers) {
      controller.dispose();
    }
    for (var focusNode in _focusNodes) {
      focusNode.dispose();
    }
    _timer?.cancel();
    super.dispose();
  }

  void _startResendTimer() {
    _canResend = false;
    _resendCountdown = 60;
    _timer = Timer.periodic(const Duration(seconds: 1), (timer) {
      if (mounted) {
        setState(() {
          if (_resendCountdown > 0) {
            _resendCountdown--;
          } else {
            _canResend = true;
            timer.cancel();
          }
        });
      }
    });
  }

  String _getOtpCode() {
    return _controllers.map((controller) => controller.text).join();
  }

  void _onDigitChanged(int index, String value) {
    if (_errorMessage != null) {
      setState(() {
        _errorMessage = null;
      });
    }
    
    if (value.isNotEmpty && index < 3) {
      _focusNodes[index + 1].requestFocus();
    } else if (value.isEmpty && index > 0) {
      _focusNodes[index - 1].requestFocus();
    }

    if (_getOtpCode().length == 4) {
      _verifyOtp();
    }
  }

  Future<void> _verifyOtp() async {
    if (_isLoading) return;
    
    final otpCode = _getOtpCode();
    if (otpCode.length != 4) {
      setState(() {
        _errorMessage = 'Veuillez entrer le code à 4 chiffres';
      });
      return;
    }

    FocusScope.of(context).unfocus();
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      final result = await _otpService.verifyOtp(widget.phoneNumber, otpCode);

      if (result['success']) {
        final storageService = StorageService();
        await storageService.saveTokens(
          result['access_token'],
          result['refresh_token'],
        );
        
        // Enregistrer le token FCM maintenant que l'utilisateur est authentifié
        if (!kIsWeb) {
          try {
            final fcmSuccess = await FcmService().registerCurrentUserToken();
            print('🔔 [OTP] FCM token registration: ${fcmSuccess ? "✅ OK" : "❌ FAILED"}');
          } catch (e) {
            print('⚠️ [OTP] FCM token registration error: $e');
          }
          // Synchroniser le badge d'icône avec le compteur de non lues
          try {
            await BadgeService().refresh();
            print('🔴 [OTP] Badge d\'icône synchronisé');
          } catch (e) {
            print('⚠️ [OTP] Badge sync error: $e');
          }
        }
        
        // Utiliser le flag profile_complete du backend pour décider de la redirection
        // profile_complete = true → profil complet → dashboard
        // profile_complete = false → profil incomplet → complétion de profil
        final profileComplete = result['profile_complete'] == true;

        print('🔍 [OTP] profile_complete: $profileComplete');

        if (mounted) {
          if (profileComplete) {
            print('✅ [OTP] Profil complet → Navigation vers /main');
            Navigator.of(context).pushNamedAndRemoveUntil(
              '/main',
              (route) => false,
            );
          } else {
            print('📝 [OTP] Profil incomplet → Navigation vers /profile-completion');
            Navigator.of(context).pushNamedAndRemoveUntil(
              '/profile-completion',
              (route) => false,
            );
          }
        }
      } else {
        setState(() {
          _errorMessage = result['error'] ?? 'Code invalide';
        });
        _controllers[0].clear();
        _focusNodes[0].requestFocus();
      }
    } catch (e) {
      setState(() {
        _errorMessage = 'Erreur de connexion';
      });
    } finally {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
      }
    }
  }

  Future<void> _resendCode() async {
    if (!_canResend || _isLoading) return;

    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      final result = await _otpService.requestOtp(widget.phoneNumber);
      
      if (result['success']) {
        _startResendTimer();
        setState(() {
          _errorMessage = 'Code renvoyé avec succès';
        });
      } else {
        setState(() {
          _errorMessage = result['error'] ?? 'Erreur lors du renvoi';
        });
      }
    } catch (e) {
      setState(() {
        _errorMessage = 'Erreur de connexion';
      });
    } finally {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_rounded, color: AppTheme.textPrimary),
          onPressed: () => Navigator.of(context).pop(),
        ),
      ),
      body: SingleChildScrollView(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              const SizedBox(height: 20),
              
              Container(
                width: 80, height: 80,
                decoration: BoxDecoration(
                  color: AppTheme.primaryBlue.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(24),
                ),
                child: const Icon(Icons.sms_outlined, color: AppTheme.primaryBlue, size: 40),
              ),
              
              const SizedBox(height: 24),
              
              Text(
                'Vérification SMS',
                style: theme.textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w700),
              ),
              
              const SizedBox(height: 8),
              
              Text(
                'Entrez le code à 4 chiffres envoyé au',
                style: TextStyle(color: AppTheme.textLight, fontSize: 16),
                textAlign: TextAlign.center,
              ),
              
              const SizedBox(height: 4),
              
              Text(
                widget.phoneNumber,
                style: theme.textTheme.titleMedium?.copyWith(
                  fontWeight: FontWeight.w600,
                  color: AppTheme.primaryBlue,
                ),
              ),
              
              const SizedBox(height: 32),
              
              if (_errorMessage != null)
                Container(
                  padding: const EdgeInsets.all(12),
                  margin: const EdgeInsets.only(bottom: 16),
                  decoration: BoxDecoration(
                    color: AppTheme.error.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: AppTheme.error.withOpacity(0.3)),
                  ),
                  child: Row(
                    children: [
                      Icon(Icons.error_outline, color: AppTheme.error, size: 20),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          _errorMessage!,
                          style: TextStyle(color: AppTheme.error, fontSize: 14),
                        ),
                      ),
                    ],
                  ),
                ),
              
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                children: List.generate(4, (index) {
                  return SizedBox(
                    width: 60,
                    height: 60,
                    child: TextFormField(
                      controller: _controllers[index],
                      focusNode: _focusNodes[index],
                      textAlign: TextAlign.center,
                      keyboardType: TextInputType.number,
                      inputFormatters: [
                        FilteringTextInputFormatter.digitsOnly,
                        LengthLimitingTextInputFormatter(1),
                      ],
                      style: theme.textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w600),
                      decoration: InputDecoration(
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(12),
                          borderSide: BorderSide(color: Colors.grey.shade300),
                        ),
                        focusedBorder: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(12),
                          borderSide: BorderSide(color: AppTheme.primaryBlue, width: 2),
                        ),
                        contentPadding: EdgeInsets.zero,
                      ),
                      onChanged: (value) => _onDigitChanged(index, value),
                    ),
                  );
                }),
              ),
              
              const SizedBox(height: 32),
              
              SizedBox(
                width: double.infinity,
                height: 50,
                child: ElevatedButton(
                  onPressed: _isLoading ? null : _verifyOtp,
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
                      : const Text('Vérifier le code', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
                ),
              ),
              
              const SizedBox(height: 24),
              
              Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(
                    "Vous n'avez pas reçu le code ?",
                    style: TextStyle(color: AppTheme.textLight),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 4),
                  if (_canResend)
                    TextButton(
                      onPressed: () => _resendCode(),
                      child: const Text('Renvoyer', style: TextStyle(fontWeight: FontWeight.w600)),
                    )
                  else
                    Text(
                      'Renvoyer dans ${_resendCountdown}s',
                      style: TextStyle(color: AppTheme.textLight),
                    ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}

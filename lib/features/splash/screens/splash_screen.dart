import 'package:flutter/material.dart';
import 'package:resume_plus_clean/features/onboarding/onboarding_screen.dart';
import 'package:resume_plus_clean/features/app/screens/main_navigation_screen.dart';
import 'package:resume_plus_clean/features/auth/screens/phone_login_screen.dart';
import 'package:resume_plus_clean/services/auto_login_service.dart';
import 'package:resume_plus_clean/services/version_service.dart';
import 'package:resume_plus_clean/services/badge_service.dart';
import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:resume_plus_clean/theme/app_theme.dart';
import 'force_update_screen.dart';

class SplashScreen extends StatefulWidget {
  const SplashScreen({super.key});

  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen> with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _fadeAnimation;
  late Animation<double> _scaleAnimation;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(vsync: this, duration: const Duration(milliseconds: 1200));
    _fadeAnimation = Tween<double>(begin: 0, end: 1).animate(CurvedAnimation(parent: _controller, curve: Curves.easeOut));
    _scaleAnimation = Tween<double>(begin: 0.8, end: 1).animate(CurvedAnimation(parent: _controller, curve: Curves.easeOutBack));
    _controller.forward();
    _determineNavigation();
  }

  void _determineNavigation() async {
    // Attendre l'animation du splash
    await Future.delayed(const Duration(milliseconds: 2500));
    if (!mounted) return;

    // ═══════════════════════════════════════════════════════════════
    // ÉTAPE 1 : Vérification de la version de l'application
    // ═══════════════════════════════════════════════════════════════
    final versionResult = await VersionService().checkVersion();
    print('🔄 VersionCheck: résultat = $versionResult');
    if (!mounted) return;

    switch (versionResult) {
      case VersionCheckResult.maintenance:
        // Mode maintenance → écran plein écran, pas de contournement
        Navigator.pushReplacement(
          context,
          MaterialPageRoute(
            builder: (_) => const ForceUpdateScreen(maintenance: true),
          ),
        );
        return; // ⛔ On stoppe ici, pas d'accès à l'app

      case VersionCheckResult.mandatory:
        // Mise à jour OBLIGATOIRE → écran plein écran avec bouton store
        Navigator.pushReplacement(
          context,
          MaterialPageRoute(
            builder: (_) => const ForceUpdateScreen(maintenance: false),
          ),
        );
        return; // ⛔ On stoppe ici

      case VersionCheckResult.optional:
        // Mise à jour SUGGÉRÉE → dialogue informatif, puis continuer
        if (mounted) {
          await _showOptionalUpdateDialog();
          if (!mounted) return;
        }
        break; // On continue vers l'auth

      case VersionCheckResult.upToDate:
      case VersionCheckResult.error:
        // À jour ou API inaccessible → continuer normalement
        break;
    }

    // ═══════════════════════════════════════════════════════════════
    // ÉTAPE 2 : Déterminer l'état de connexion (flux existant)
    // ═══════════════════════════════════════════════════════════════
    final startState = await AutoLoginService.determineStartState();
    if (!mounted) return;

    switch (startState) {
      case AppStartState.loggedIn:
      case AppStartState.sessionRestored:
        // Session active → synchroniser le badge d'icône avec le compteur
        // de notifications non lues (cohérent après redémarrage de l'app)
        if (!kIsWeb) {
          try {
            await BadgeService().refresh();
            print('🔴 [Splash] Badge d\'icône synchronisé (session active)');
          } catch (e) {
            print('⚠️ [Splash] Badge sync error: $e');
          }
        }
        Navigator.pushReplacement(
          context,
          MaterialPageRoute(builder: (_) => MainNavigationScreen(key: MainNavigationScreen.navKey)),
        );
        break;

      case AppStartState.deviceKnownNeedsAuth:
        final phone = await AutoLoginService.getRegisteredPhone();
        if (mounted) {
          Navigator.pushReplacement(
            context,
            MaterialPageRoute(
              builder: (_) => PhoneLoginScreen(prefillPhone: phone),
            ),
          );
        }
        break;

      case AppStartState.newDevice:
        Navigator.pushReplacement(
          context,
          MaterialPageRoute(builder: (_) => const OnboardingScreen()),
        );
        break;
    }
  }

  /// Affiche un dialogue informatif pour une mise à jour optionnelle.
  Future<void> _showOptionalUpdateDialog() async {
    final config = VersionService().config;
    final latestVersion = config?.latestVersion ?? '';

    if (!mounted) return;

    await showDialog(
      context: context,
      barrierDismissible: false, // Ne pas fermer en cliquant à côté
      builder: (ctx) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        title: Row(
          children: [
            Icon(Icons.system_update, color: AppTheme.primaryBlue),
            const SizedBox(width: 10),
            const Expanded(
              child: Text(
                'Nouvelle version disponible',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
              ),
            ),
          ],
        ),
        content: Text(
          'Une nouvelle version de Résumé Plus est disponible sur le store.\n\n'
          'Téléchargez-la pour profiter des dernières fonctionnalités.',
          style: const TextStyle(fontSize: 15, height: 1.4),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(),
            child: const Text(
              'Plus tard',
              style: TextStyle(fontSize: 15),
            ),
          ),
          ElevatedButton(
            onPressed: () {
              Navigator.of(ctx).pop();
              VersionService().openStore();
            },
            style: ElevatedButton.styleFrom(
              backgroundColor: AppTheme.primaryBlue,
              foregroundColor: Colors.white,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(12),
              ),
            ),
            child: Text(
              'Mettre à jour  v$latestVersion',
              style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w600),
            ),
          ),
        ],
      ),
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        width: double.infinity,
        height: double.infinity,
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [AppTheme.primaryBlueDark, AppTheme.primaryBlue, AppTheme.primaryBlueLight],
          ),
        ),
        child: AnimatedBuilder(
          animation: _controller,
          builder: (context, child) {
            return Opacity(
              opacity: _fadeAnimation.value,
              child: Transform.scale(
                scale: _scaleAnimation.value,
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Container(
                      width: 100, height: 100,
                      decoration: BoxDecoration(
                        color: Colors.white.withOpacity(0.15),
                        borderRadius: BorderRadius.circular(28),
                      ),
                      child: const Icon(Icons.school_rounded, size: 52, color: Colors.white),
                    ),
                    const SizedBox(height: 24),
                    const Text(
                      'Résumé+',
                      style: TextStyle(fontSize: 32, fontWeight: FontWeight.w700, color: Colors.white, letterSpacing: -0.5),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      'Vos cours, simplifiés',
                      style: TextStyle(fontSize: 14, color: Colors.white.withOpacity(0.7)),
                    ),
                  ],
                ),
              ),
            );
          },
        ),
      ),
    );
  }
}

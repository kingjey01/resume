import 'package:flutter/material.dart';
import 'package:resume_plus_clean/services/screen_security_service.dart';

/// 🔒 Widget wrapper qui applique automatiquement la sécurité d'écran
class SecureScreenWrapper extends StatefulWidget {
  final Widget child;
  final String? screenName;
  final bool enableSecurity;
  final bool hideInTaskSwitcher;
  final bool showSecurityIndicator;

  const SecureScreenWrapper({
    super.key,
    required this.child,
    this.screenName,
    this.enableSecurity = true,
    this.hideInTaskSwitcher = true,
    this.showSecurityIndicator = true,
  });

  @override
  State<SecureScreenWrapper> createState() => _SecureScreenWrapperState();
}

class _SecureScreenWrapperState extends State<SecureScreenWrapper>
    with WidgetsBindingObserver {
  bool _isSecured = false;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    if (widget.enableSecurity) {
      _enableSecurity();
    }
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    if (_isSecured) {
      _disableSecurity();
    }
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    super.didChangeAppLifecycleState(state);
    
    // Renforcer la sécurité quand l'app passe en arrière-plan
    switch (state) {
      case AppLifecycleState.paused:
      case AppLifecycleState.inactive:
        if (widget.enableSecurity && !_isSecured) {
          _enableSecurity();
        }
        break;
      case AppLifecycleState.resumed:
        // Maintenir la sécurité même quand l'app revient au premier plan
        if (widget.enableSecurity && !_isSecured) {
          _enableSecurity();
        }
        break;
      case AppLifecycleState.detached:
        break;
      case AppLifecycleState.hidden:
        break;
    }
  }

  Future<void> _enableSecurity() async {
    try {
      await ScreenSecurityService.secureScreen(
        screenName: widget.screenName,
        hideInTaskSwitcher: widget.hideInTaskSwitcher,
        preventScreenshots: widget.enableSecurity,
      );
      if (mounted) {
        setState(() {
          _isSecured = true;
        });
      }
    } catch (e) {
      debugPrint('Erreur lors de l\'activation de la sécurité: $e');
    }
  }

  Future<void> _disableSecurity() async {
    try {
      await ScreenSecurityService.unsecureScreen();
      if (mounted) {
        setState(() {
          _isSecured = false;
        });
      }
    } catch (e) {
      debugPrint('Erreur lors de la désactivation de la sécurité: $e');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Stack(
      children: [
        widget.child,
        
        // Indicateur de sécurité (optionnel)
        if (widget.showSecurityIndicator && _isSecured)
          Positioned(
            top: MediaQuery.of(context).padding.top + 8,
            right: 16,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              decoration: BoxDecoration(
                color: Colors.red.withOpacity(0.8),
                borderRadius: BorderRadius.circular(12),
              ),
              child: const Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(
                    Icons.security,
                    color: Colors.white,
                    size: 16,
                  ),
                  SizedBox(width: 4),
                  Text(
                    'Sécurisé',
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ],
              ),
            ),
          ),
      ],
    );
  }
}
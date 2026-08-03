import 'package:flutter/material.dart';
import 'package:resume_plus_clean/services/version_service.dart';
import 'package:resume_plus_clean/theme/app_theme.dart';

/// Écran plein écran NON contournable pour les mises à jour forcées
/// et le mode maintenance.
///
/// Comportement :
/// - `maintenance=true` → affiche le message de maintenance, pas de bouton store
/// - `maintenance=false` → affiche la version minimum + bouton "Mettre à jour"
///   qui ouvre le store approprié (Play Store / App Store)
///
/// Le bouton retour Android est désactivé via [PopScope] avec `canPop: false`.
/// L'utilisateur ne peut PAS contourner cet écran.
class ForceUpdateScreen extends StatefulWidget {
  final bool maintenance;

  const ForceUpdateScreen({super.key, this.maintenance = false});

  @override
  State<ForceUpdateScreen> createState() => _ForceUpdateScreenState();
}

class _ForceUpdateScreenState extends State<ForceUpdateScreen> {
  final VersionService _versionService = VersionService();
  bool _isOpening = false;

  Future<void> _openStore() async {
    if (_isOpening) return;
    setState(() => _isOpening = true);
    await _versionService.openStore();
    if (mounted) setState(() => _isOpening = false);
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;
    final size = MediaQuery.of(context).size;

    return PopScope(
      canPop: false, // 🔒 Empêche tout retour
      child: Scaffold(
        body: Container(
          width: size.width,
          height: size.height,
          decoration: BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.topCenter,
              end: Alignment.bottomCenter,
              colors: isDark
                  ? [AppTheme.primaryBlueDark, Colors.black]
                  : [AppTheme.primaryBlue, AppTheme.primaryBlueLight],
            ),
          ),
          child: SafeArea(
            child: Center(
              child: SingleChildScrollView(
                padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 24),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    // ── Espacement ─────────────────────────────
                    SizedBox(height: size.height * 0.05),

                    // ── Icône ──────────────────────────────────
                    Container(
                      width: 100,
                      height: 100,
                      decoration: BoxDecoration(
                        color: Colors.white.withOpacity(0.15),
                        shape: BoxShape.circle,
                      ),
                      child: Icon(
                        widget.maintenance ? Icons.construction : Icons.system_update,
                        size: 50,
                        color: Colors.white,
                      ),
                    ),

                    const SizedBox(height: 32),

                    // ── Titre ──────────────────────────────────
                    Text(
                      widget.maintenance ? 'Maintenance en cours' : 'Mise à jour requise',
                      textAlign: TextAlign.center,
                      style: const TextStyle(
                        fontSize: 26,
                        fontWeight: FontWeight.bold,
                        color: Colors.white,
                        letterSpacing: 0.5,
                      ),
                    ),

                    const SizedBox(height: 16),

                    // ── Message ────────────────────────────────
                    Text(
                      widget.maintenance
                          ? _versionService.maintenanceMessage
                          : _versionService.mandatoryMessage,
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        fontSize: 16,
                        color: Colors.white.withOpacity(0.85),
                        height: 1.5,
                      ),
                    ),

                    // ── Version minimum (mode force) ──────────
                    if (!widget.maintenance) ...[
                      const SizedBox(height: 20),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                        decoration: BoxDecoration(
                          color: Colors.white.withOpacity(0.12),
                          borderRadius: BorderRadius.circular(12),
                          border: Border.all(
                            color: Colors.white.withOpacity(0.2),
                          ),
                        ),
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Icon(
                              Icons.info_outline,
                              size: 20,
                              color: Colors.white.withOpacity(0.9),
                            ),
                            const SizedBox(width: 10),
                            Text(
                              'Version requise : v${_versionService.config?.minimumVersion ?? '—'}',
                              style: TextStyle(
                                fontSize: 14,
                                fontWeight: FontWeight.w600,
                                color: Colors.white.withOpacity(0.9),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],

                    const SizedBox(height: 40),

                    // ── Bouton d'action ────────────────────────
                    if (!widget.maintenance)
                      SizedBox(
                        width: double.infinity,
                        height: 52,
                        child: ElevatedButton(
                          onPressed: _isOpening ? null : _openStore,
                          style: ElevatedButton.styleFrom(
                            backgroundColor: AppTheme.orange,
                            foregroundColor: Colors.white,
                            elevation: 4,
                            shadowColor: AppTheme.orange.withOpacity(0.4),
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(14),
                            ),
                          ),
                          child: _isOpening
                              ? const SizedBox(
                                  width: 24,
                                  height: 24,
                                  child: CircularProgressIndicator(
                                    strokeWidth: 2.5,
                                    color: Colors.white,
                                  ),
                                )
                              : const Row(
                                  mainAxisAlignment: MainAxisAlignment.center,
                                  children: [
                                    Icon(Icons.shopping_cart_outlined, size: 22),
                                    SizedBox(width: 10),
                                    Text(
                                      'Mettre à jour',
                                      style: TextStyle(
                                        fontSize: 17,
                                        fontWeight: FontWeight.w600,
                                      ),
                                    ),
                                  ],
                                ),
                        ),
                      ),

                    // ── Message supplémentaire pour store ──────
                    if (!widget.maintenance) ...[
                      const SizedBox(height: 14),
                      Text(
                        'Vous serez redirigé vers le store.',
                        style: TextStyle(
                          fontSize: 13,
                          color: Colors.white.withOpacity(0.6),
                        ),
                      ),
                    ],

                    SizedBox(height: size.height * 0.08),

                    // ── Pied de page ───────────────────────────
                    Text(
                      'Résumé Plus v${_versionService.config?.latestVersion ?? ""}',
                      style: TextStyle(
                        fontSize: 13,
                        color: Colors.white.withOpacity(0.4),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}

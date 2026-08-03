import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:resume_plus_clean/services/api_service.dart';
import 'package:resume_plus_clean/theme/app_theme.dart';
import 'package:resume_plus_clean/providers/purchase_badge_provider.dart';

/// Écran de suivi du statut de paiement après initiation FlexPay.
/// Affiche un état d'attente, puis succès ou échec selon le callback.
class PaymentStatusScreen extends ConsumerStatefulWidget {
  final String transactionRef;
  final String summaryTitle;
  final String amount;
  final String currency;
  /// Callback optionnel appelé quand le paiement est confirmé (ex: créer abonnement)
  final Future<void> Function()? onPaymentConfirmed;
  final String successMessage; 
  final String successSubtitle;

  const PaymentStatusScreen({
    super.key,
    required this.transactionRef,
    required this.summaryTitle,
    required this.amount,
    this.currency = 'CDF',
    this.onPaymentConfirmed,
    this.successMessage = 'Paiement réussi !',
    this.successSubtitle = 'Votre résumé est maintenant disponible\ndans « Mes Achats ».',
  });

  @override
  ConsumerState<PaymentStatusScreen> createState() => _PaymentStatusScreenState();
}

enum _PaymentState { waiting, success, failed, timeout }

class _PaymentStatusScreenState extends ConsumerState<PaymentStatusScreen>
    with SingleTickerProviderStateMixin {
  final ApiService _apiService = ApiService();
  Timer? _pollingTimer;
  _PaymentState _state = _PaymentState.waiting;
  int _elapsedSeconds = 0;
  late AnimationController _pulseController;

  static const int _pollIntervalSec = 5;
  static const int _timeoutSec = 120; // 2 minutes

  @override
  void initState() {
    super.initState();
    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1200),
    )..repeat(reverse: true);
    _startPolling();
  }

  @override
  void dispose() {
    _pollingTimer?.cancel();
    _pulseController.dispose();
    super.dispose();
  }

  void _startPolling() {
    // Premier check immédiat après 3s (laisser le temps au push)
    Future.delayed(const Duration(seconds: 3), () {
      if (mounted) _checkStatus();
    });

    _pollingTimer = Timer.periodic(
      const Duration(seconds: _pollIntervalSec),
      (_) {
        _elapsedSeconds += _pollIntervalSec;
        if (_elapsedSeconds >= _timeoutSec) {
          _pollingTimer?.cancel();
          if (mounted && _state == _PaymentState.waiting) {
            setState(() => _state = _PaymentState.timeout);
          }
          return;
        }
        if (mounted && _state == _PaymentState.waiting) {
          _checkStatus();
        }
      },
    );
  }

  Future<void> _checkStatus() async {
    try {
      final result = await _apiService.checkPurchaseStatus(widget.transactionRef);
      if (!mounted) return;
      final status = result['status']?.toString().toLowerCase() ?? '';

      if (status == 'completed') {
        _pollingTimer?.cancel();
        // Exécuter le callback si présent (ex: création abonnement)
        if (widget.onPaymentConfirmed != null) {
          try {
            await widget.onPaymentConfirmed!();
          } catch (_) {}
        }
        if (!mounted) return;
        // Incrémenter le badge "Mes Achats"
        ref.read(purchaseBadgeCountProvider.notifier).incrementBadge();
        setState(() => _state = _PaymentState.success);
      } else if (status == 'failed' || status == 'refunded') {
        _pollingTimer?.cancel();
        setState(() => _state = _PaymentState.failed);
      }
      // 'pending' → on continue le polling
    } catch (_) {
      // Erreur réseau temporaire, on continue
    }
  }

  void _goHome() {
    // Si succès, pop avec true (utile pour le screen abonnement qui attend un résultat)
    // Si le screen a été pushReplacement (achat résumé), pop(true) revient à la route précédente
    if (_state == _PaymentState.success) {
      Navigator.of(context).pop(true);
    } else {
      Navigator.of(context).pop(false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return PopScope(
      canPop: _state != _PaymentState.waiting,
      child: Scaffold(
        backgroundColor: Theme.of(context).scaffoldBackgroundColor,
        body: SafeArea(
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 28, vertical: 24),
            child: Column(
              children: [
                const Spacer(flex: 2),
                _buildStateWidget(),
                const SizedBox(height: 32),
                _buildInfoCard(),
                const Spacer(flex: 3),
                _buildBottomActions(),
                const SizedBox(height: 16),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildStateWidget() {
    switch (_state) {
      case _PaymentState.waiting:
        return _buildWaitingState();
      case _PaymentState.success:
        return _buildSuccessState();
      case _PaymentState.failed:
        return _buildFailedState();
      case _PaymentState.timeout:
        return _buildTimeoutState();
    }
  }

  // ─── WAITING ────────────────────────────────────────────

  Widget _buildWaitingState() {
    return Column(
      children: [
        AnimatedBuilder(
          animation: _pulseController,
          builder: (context, child) {
            final scale = 1.0 + (_pulseController.value * 0.08);
            return Transform.scale(scale: scale, child: child);
          },
          child: Container(
            width: 110,
            height: 110,
            decoration: BoxDecoration(
              color: AppTheme.primaryBlue.withOpacity(0.1),
              shape: BoxShape.circle,
            ),
            child: const Icon(Icons.phone_android_rounded,
                size: 52, color: AppTheme.primaryBlue),
          ),
        ),
        const SizedBox(height: 28),
        Text(
          'Validation en cours…',
          style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                fontWeight: FontWeight.w700,
                color: Theme.of(context).colorScheme.onSurface,
              ),
          textAlign: TextAlign.center,
        ),
        const SizedBox(height: 12),
        Text(
          'Veuillez confirmer le paiement\nsur votre téléphone mobile.',
          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                color: Theme.of(context).colorScheme.onSurface.withOpacity(0.6),
                height: 1.5,
              ),
          textAlign: TextAlign.center,
        ),
        const SizedBox(height: 24),
        SizedBox(
          width: 180,
          child: LinearProgressIndicator(
            backgroundColor: AppTheme.primaryBlue.withOpacity(0.15),
            valueColor: const AlwaysStoppedAnimation(AppTheme.primaryBlue),
            borderRadius: BorderRadius.circular(6),
          ),
        ),
      ],
    );
  }

  // ─── SUCCESS ────────────────────────────────────────────

  Widget _buildSuccessState() {
    return Column(
      children: [
        Container(
          width: 110,
          height: 110,
          decoration: BoxDecoration(
            color: AppTheme.success.withOpacity(0.12),
            shape: BoxShape.circle,
          ),
          child: const Icon(Icons.check_circle_rounded,
              size: 60, color: AppTheme.success),
        ),
        const SizedBox(height: 28),
        Text(
          widget.successMessage,
          style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                fontWeight: FontWeight.w700,
                color: AppTheme.success,
              ),
          textAlign: TextAlign.center,
        ),
        const SizedBox(height: 12),
        Text(
          widget.successSubtitle,
          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                color: Theme.of(context).colorScheme.onSurface.withOpacity(0.6),
                height: 1.5,
              ),
          textAlign: TextAlign.center,
        ),
      ],
    );
  }

  // ─── FAILED ─────────────────────────────────────────────

  Widget _buildFailedState() {
    return Column(
      children: [
        Container(
          width: 110,
          height: 110,
          decoration: BoxDecoration(
            color: AppTheme.error.withOpacity(0.12),
            shape: BoxShape.circle,
          ),
          child: const Icon(Icons.cancel_rounded,
              size: 60, color: AppTheme.error),
        ),
        const SizedBox(height: 28),
        Text(
          'Paiement échoué',
          style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                fontWeight: FontWeight.w700,
                color: AppTheme.error,
              ),
          textAlign: TextAlign.center,
        ),
        const SizedBox(height: 12),
        Text(
          'Le paiement n\'a pas abouti.\nVeuillez réessayer ou utiliser\nun autre moyen de paiement.',
          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                color: Theme.of(context).colorScheme.onSurface.withOpacity(0.6),
                height: 1.5,
              ),
          textAlign: TextAlign.center,
        ),
      ],
    );
  }

  // ─── TIMEOUT ────────────────────────────────────────────

  Widget _buildTimeoutState() {
    return Column(
      children: [
        Container(
          width: 110,
          height: 110,
          decoration: BoxDecoration(
            color: Colors.orange.withOpacity(0.12),
            shape: BoxShape.circle,
          ),
          child: const Icon(Icons.hourglass_bottom_rounded,
              size: 52, color: Colors.orange),
        ),
        const SizedBox(height: 28),
        Text(
          'En attente de confirmation',
          style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                fontWeight: FontWeight.w700,
                color: Colors.orange.shade700,
              ),
          textAlign: TextAlign.center,
        ),
        const SizedBox(height: 12),
        Text(
          'Le paiement est toujours en cours de traitement.\nVérifiez dans « Mes Achats » ultérieurement.',
          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                color: Theme.of(context).colorScheme.onSurface.withOpacity(0.6),
                height: 1.5,
              ),
          textAlign: TextAlign.center,
        ),
      ],
    );
  }

  // ─── INFO CARD ──────────────────────────────────────────

  Widget _buildInfoCard() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surface,
        borderRadius: BorderRadius.circular(16),
        boxShadow: AppTheme.softShadow,
      ),
      child: Column(
        children: [
          _infoRow('Résumé', widget.summaryTitle),
          const Divider(height: 20),
          _infoRow('Montant', '${widget.amount} ${widget.currency}'),
          const Divider(height: 20),
          _infoRow('Réf. transaction', widget.transactionRef),
        ],
      ),
    );
  }

  Widget _infoRow(String label, String value) {
    return Row(
      children: [
        Text(
          label,
          style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: Theme.of(context).colorScheme.onSurface.withOpacity(0.5),
              ),
        ),
        const Spacer(),
        Flexible(
          child: Text(
            value,
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  fontWeight: FontWeight.w600,
                  color: Theme.of(context).colorScheme.onSurface,
                ),
            textAlign: TextAlign.end,
            overflow: TextOverflow.ellipsis,
          ),
        ),
      ],
    );
  }

  // ─── BOTTOM ACTIONS ─────────────────────────────────────

  Widget _buildBottomActions() {
    switch (_state) {
      case _PaymentState.waiting:
        return TextButton(
          onPressed: () {
            _pollingTimer?.cancel();
            setState(() => _state = _PaymentState.timeout);
          },
          child: Text(
            'Fermer sans attendre',
            style: TextStyle(
              color: Theme.of(context).colorScheme.onSurface.withOpacity(0.5),
              fontSize: 14,
            ),
          ),
        );

      case _PaymentState.success:
        return SizedBox(
          width: double.infinity,
          height: 52,
          child: ElevatedButton.icon(
            onPressed: _goHome,
            icon: const Icon(Icons.home_rounded),
            label: const Text('Retour à l\'accueil',
                style: TextStyle(fontSize: 15, fontWeight: FontWeight.w600)),
            style: ElevatedButton.styleFrom(
              backgroundColor: AppTheme.success,
              foregroundColor: Colors.white,
              elevation: 0,
              shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(14)),
            ),
          ),
        );

      case _PaymentState.failed:
        return Column(
          children: [
            SizedBox(
              width: double.infinity,
              height: 52,
              child: ElevatedButton.icon(
                onPressed: () => Navigator.of(context).pop(), // retour au form
                icon: const Icon(Icons.refresh_rounded),
                label: const Text('Réessayer',
                    style:
                        TextStyle(fontSize: 15, fontWeight: FontWeight.w600)),
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppTheme.primaryBlue,
                  foregroundColor: Colors.white,
                  elevation: 0,
                  shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(14)),
                ),
              ),
            ),
            const SizedBox(height: 10),
            TextButton(
              onPressed: _goHome,
              child: const Text('Retour à l\'accueil'),
            ),
          ],
        );

      case _PaymentState.timeout:
        return SizedBox(
          width: double.infinity,
          height: 52,
          child: ElevatedButton.icon(
            onPressed: _goHome,
            icon: const Icon(Icons.home_rounded),
            label: const Text('Retour à l\'accueil',
                style: TextStyle(fontSize: 15, fontWeight: FontWeight.w600)),
            style: ElevatedButton.styleFrom(
              backgroundColor: AppTheme.primaryBlue,
              foregroundColor: Colors.white,
              elevation: 0,
              shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(14)),
            ),
          ),
        );
    }
  }
}

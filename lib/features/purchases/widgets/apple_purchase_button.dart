import 'package:flutter/material.dart';

import 'package:resume_plus_clean/services/apple_iap/apple_iap_service_stub.dart'
    if (dart.library.io)
        'package:resume_plus_clean/services/apple_iap/apple_iap_service_io.dart';
import 'package:resume_plus_clean/services/apple_iap/apple_iap_types.dart';
import 'package:resume_plus_clean/services/snackbar_service.dart';

/// Bouton Apple In-App Purchase (iOS uniquement).
///
/// Sur Android et Web, le widget ne s'affiche pas : le parcours FlexPay reste
/// inchangé. Aucun droit n'est accordé avant la confirmation du backend.
class ApplePurchaseButton extends StatefulWidget {
  final int? summaryId;
  final double? summaryPrice;
  final int? serviceId;
  final String title;
  final VoidCallback? onSuccess;

  const ApplePurchaseButton({
    super.key,
    this.summaryId,
    this.summaryPrice,
    this.serviceId,
    required this.title,
    this.onSuccess,
  }) : assert(
          (summaryId != null && summaryPrice != null) || serviceId != null,
          'Indiquer soit un résumé (summaryId + summaryPrice), soit un service.',
        );

  @override
  State<ApplePurchaseButton> createState() => _ApplePurchaseButtonState();
}

/// Bouton « Restaurer mes achats » (iOS uniquement).
class AppleRestoreButton extends StatefulWidget {
  final VoidCallback? onRestored;

  const AppleRestoreButton({super.key, this.onRestored});

  @override
  State<AppleRestoreButton> createState() => _AppleRestoreButtonState();
}

class _AppleRestoreButtonState extends State<AppleRestoreButton> {
  final AppleIapService _service = AppleIapService.instance;
  bool _handled = false;

  @override
  void initState() {
    super.initState();
    _service.state.addListener(_onStateChanged);
  }

  @override
  void dispose() {
    _service.state.removeListener(_onStateChanged);
    super.dispose();
  }

  void _onStateChanged() {
    if (!mounted) return;
    final state = _service.state.value;
    if (state.status == AppleIapStatus.success && !_handled) {
      _handled = true;
      widget.onRestored?.call();
    } else if (state.status == AppleIapStatus.error && state.message != null) {
      SnackbarService.show(state.message!, isError: true);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (!_service.isSupported) return const SizedBox.shrink();

    return TextButton.icon(
      onPressed: () => _service.restorePurchases(),
      icon: const Icon(Icons.restore_rounded, size: 18),
      label: const Text('Restaurer mes achats'),
    );
  }
}

class _ApplePurchaseButtonState extends State<ApplePurchaseButton> {
  final AppleIapService _service = AppleIapService.instance;

  bool _loading = true;
  bool _successHandled = false;
  bool _pendingFinalizationHandled = false;
  String? _priceLabel;

  @override
  void initState() {
    super.initState();
    _service.state.addListener(_onStateChanged);
    _load();
  }

  Future<void> _load() async {
    if (!_service.isSupported) {
      if (mounted) setState(() => _loading = false);
      return;
    }

    await _service.initialize();
    await _service.loadCatalog();
    if (!mounted) return;

    setState(() {
      _loading = false;
      _priceLabel = widget.summaryId != null
          ? _service.priceForSummary(widget.summaryPrice!)
          : _service.priceForService(widget.serviceId!);
    });
  }

  void _onStateChanged() {
    if (!mounted) return;
    final state = _service.state.value;

    if (state.status == AppleIapStatus.success && !_successHandled) {
      _successHandled = true;
      widget.onSuccess?.call();
    } else if (state.status ==
            AppleIapStatus.validatedPendingFinalization &&
        !_pendingFinalizationHandled) {
      // Le droit est acquis côté Django, mais StoreKit n'a pas encore
      // terminé la transaction : rafraîchir l'accès et l'indiquer clairement.
      _pendingFinalizationHandled = true;
      SnackbarService.show(
        state.message ??
            'Achat validé. Finalisation Apple en attente — '
                'elle reprendra automatiquement.',
        isError: false,
      );
      widget.onSuccess?.call();
      if (!mounted) return;
      setState(() {});
    } else if (state.status == AppleIapStatus.error &&
        state.message != null) {
      SnackbarService.show(state.message!, isError: true);
    } else {
      setState(() {});
    }
  }

  @override
  void dispose() {
    _service.state.removeListener(_onStateChanged);
    super.dispose();
  }

  Future<void> _buy() async {
    final started = widget.summaryId != null
        ? await _service.buySummary(
            summaryId: widget.summaryId!,
            price: widget.summaryPrice!,
            title: widget.title,
          )
        : await _service.buySubscription(
            serviceId: widget.serviceId!,
            title: widget.title,
          );

    if (!started && mounted) {
      final message = _service.state.value.message;
      if (message != null) SnackbarService.show(message, isError: true);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (!_service.isSupported) return const SizedBox.shrink();

    if (_loading) {
      return const Padding(
        padding: EdgeInsets.symmetric(vertical: 12),
        child: Center(
          child: SizedBox(
            width: 22,
            height: 22,
            child: CircularProgressIndicator(strokeWidth: 2),
          ),
        ),
      );
    }

    if (_priceLabel == null) {
      return Container(
        width: double.infinity,
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: Colors.orange.withValues(alpha: 0.08),
          borderRadius: BorderRadius.circular(10),
        ),
        child: const Text(
          'Achats Apple indisponibles pour le moment. '
          'Réessayez plus tard ou contactez le support.',
          style: TextStyle(fontSize: 12),
          textAlign: TextAlign.center,
        ),
      );
    }

    return ValueListenableBuilder<AppleIapState>(
      valueListenable: _service.state,
      builder: (context, state, _) {
        final pendingFinalization =
            state.status == AppleIapStatus.validatedPendingFinalization;
        final busy = pendingFinalization ||
            state.status == AppleIapStatus.purchasing ||
            state.status == AppleIapStatus.verifying ||
            state.status == AppleIapStatus.pending;

        return Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            SizedBox(
              width: double.infinity,
              height: 50,
              child: ElevatedButton.icon(
                onPressed: busy ? null : _buy,
                icon: pendingFinalization
                    ? const Icon(Icons.hourglass_top_rounded, size: 20)
                    : busy
                        ? const SizedBox(
                            width: 18,
                            height: 18,
                            child: CircularProgressIndicator(
                              strokeWidth: 2,
                              color: Colors.white,
                            ),
                          )
                        : const Icon(Icons.apple, size: 22),
                label: Text(
                  pendingFinalization
                      ? 'Finalisation Apple en attente…'
                      : busy
                          ? 'Paiement en cours…'
                          : 'Payer $_priceLabel avec Apple',
                  style: const TextStyle(
                    fontSize: 15,
                    fontWeight: FontWeight.w700,
                  ),
                ),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.black,
                  foregroundColor: Colors.white,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
              ),
            ),
            const SizedBox(height: 6),
            const Text(
              'Paiement sécurisé via l\'App Store. '
              'Le contenu est débloqué après confirmation du serveur.',
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 10.5, color: Colors.grey),
            ),
          ],
        );
      },
    );
  }
}

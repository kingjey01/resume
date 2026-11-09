/// États partagés du service Apple In-App Purchase (tâche 71).
enum AppleIapStatus {
  idle,
  loading,
  purchasing,
  pending,
  verifying,

  /// Droit accordé par Django, mais `completePurchase` StoreKit n'a pas
  /// encore réussi. La transaction sera finalisée lors de sa reprise.
  validatedPendingFinalization,

  success,
  error,
}

class AppleIapState {
  final AppleIapStatus status;
  final String? message;

  const AppleIapState(this.status, {this.message});

  static const idle = AppleIapState(AppleIapStatus.idle);
}

/// État d'interface après une validation backend réussie.
///
/// - `storeKitCompleted` vrai : transaction StoreKit terminée, achat complet.
/// - faux : le droit reste acquis côté Django, mais la finalisation Apple est
///   en attente. On ne présente jamais l'achat comme entièrement terminé.
AppleIapState appleIapStateAfterFinalization({
  required bool isSummaryProduct,
  required bool storeKitCompleted,
}) {
  if (storeKitCompleted) {
    return AppleIapState(
      AppleIapStatus.success,
      message: isSummaryProduct
          ? 'Achat Apple confirmé. Le résumé est disponible.'
          : 'Abonnement Apple confirmé.',
    );
  }
  return const AppleIapState(
    AppleIapStatus.validatedPendingFinalization,
    message: 'Achat validé. Finalisation Apple en attente — '
        'elle reprendra automatiquement.',
  );
}

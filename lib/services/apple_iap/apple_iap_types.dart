/// États partagés du service Apple In-App Purchase (tâche 71).
enum AppleIapStatus {
  idle,
  loading,
  purchasing,
  pending,
  verifying,
  success,
  error,
}

class AppleIapState {
  final AppleIapStatus status;
  final String? message;

  const AppleIapState(this.status, {this.message});

  static const idle = AppleIapState(AppleIapStatus.idle);
}

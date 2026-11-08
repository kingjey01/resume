import 'package:flutter/foundation.dart';

import 'apple_iap_types.dart';

/// Version Web / plateformes non supportées : aucune dépendance StoreKit.
class AppleIapService {
  AppleIapService._();

  static final AppleIapService instance = AppleIapService._();

  final ValueNotifier<AppleIapState> state =
      ValueNotifier(const AppleIapState(AppleIapStatus.idle));

  bool get isSupported => false;
  bool get isCatalogLoaded => false;

  Future<void> initialize() async {}

  Future<void> loadCatalog() async {}

  String? priceForSummary(double price) => null;

  String? priceForService(int serviceId) => null;

  Future<bool> buySummary({
    required int summaryId,
    required double price,
    required String title,
  }) async =>
      false;

  Future<bool> buySubscription({
    required int serviceId,
    required String title,
  }) async =>
      false;

  Future<void> restorePurchases() async {}

  Future<void> dispose() async {}
}

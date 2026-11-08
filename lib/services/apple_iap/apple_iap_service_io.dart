import 'dart:async';
import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:in_app_purchase/in_app_purchase.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'package:resume_plus_clean/exceptions/api_exception.dart';
import 'package:resume_plus_clean/services/api_service.dart';

import 'apple_iap_types.dart';

/// Service Apple In-App Purchase — actif uniquement sur iOS.
///
/// Android et Web ne l'utilisent jamais : `isSupported` est faux et toutes les
/// méthodes sont sans effet. Le flux FlexPay Android reste totalement séparé.
class AppleIapService {
  AppleIapService._();

  static final AppleIapService instance = AppleIapService._();

  final ValueNotifier<AppleIapState> state =
      ValueNotifier(const AppleIapState(AppleIapStatus.idle));

  final InAppPurchase _purchase = InAppPurchase.instance;
  final ApiService _api = ApiService();

  bool _initialized = false;
  bool _available = false;
  StreamSubscription<List<PurchaseDetails>>? _subscription;

  bool _catalogLoading = false;
  bool _catalogLoaded = false;
  String? _appAccountToken;
  final List<_SummaryOffer> _summaryOffers = [];
  final Map<int, String> _subscriptionProductByService = {};
  final Map<String, ProductDetails> _details = {};

  bool get isSupported => !kIsWeb && Platform.isIOS;
  bool get isCatalogLoaded => _catalogLoaded;

  Future<void> initialize() async {
    if (!isSupported || _initialized) return;
    _initialized = true;

    _available = await _purchase.isAvailable();
    if (!_available) {
      _set(AppleIapStatus.error,
          'Les achats intégrés ne sont pas disponibles sur cet appareil.');
      return;
    }

    _subscription = _purchase.purchaseStream.listen(
      _onPurchases,
      onError: (Object error) {
        _set(AppleIapStatus.error, 'Erreur du service d\'achat Apple.');
      },
    );
  }

  Future<void> loadCatalog() async {
    if (!isSupported || _catalogLoading) return;
    _catalogLoading = true;
    _set(AppleIapStatus.loading);

    try {
      final data = await _api.getAppleProducts();
      _appAccountToken = data['app_account_token']?.toString();

      _summaryOffers
        ..clear()
        ..addAll(
          (data['summary_products'] as List<dynamic>? ?? []).map((item) {
            final map = Map<String, dynamic>.from(item as Map);
            return _SummaryOffer(
              productId: map['product_id']?.toString() ?? '',
              price: double.tryParse(map['price']?.toString() ?? '') ?? 0,
            );
          }).where((offer) => offer.productId.isNotEmpty),
        );

      _subscriptionProductByService
        ..clear()
        ..addAll({
          for (final item in (data['subscriptions'] as List<dynamic>? ?? []))
            ((item as Map)['service_id'] as num).toInt():
                item['product_id']?.toString() ?? '',
        });
      _subscriptionProductByService.removeWhere((_, productId) => productId.isEmpty);

      final ids = <String>{
        ..._summaryOffers.map((offer) => offer.productId),
        ..._subscriptionProductByService.values,
      };

      _details.clear();
      if (ids.isNotEmpty) {
        final response = await _purchase.queryProductDetails(ids);
        for (final details in response.productDetails) {
          _details[details.id] = details;
        }
      }

      _catalogLoaded = true;
      _set(AppleIapStatus.idle);
    } catch (e) {
      _set(
        AppleIapStatus.error,
        e is ApiException
            ? e.message
            : 'Impossible de charger les produits Apple.',
      );
    } finally {
      _catalogLoading = false;
    }
  }

  String? priceForSummary(double price) {
    for (final offer in _summaryOffers) {
      if ((offer.price - price).abs() < 0.01) {
        final details = _details[offer.productId];
        if (details != null) return details.price;
      }
    }
    return null;
  }

  String? priceForService(int serviceId) {
    final productId = _subscriptionProductByService[serviceId];
    if (productId == null) return null;
    return _details[productId]?.price;
  }

  Future<bool> buySummary({
    required int summaryId,
    required double price,
    required String title,
  }) async {
    await initialize();
    if (!isSupported || !_available) return false;

    _SummaryOffer? offer;
    for (final candidate in _summaryOffers) {
      if ((candidate.price - price).abs() < 0.01) {
        offer = candidate;
        break;
      }
    }
    final details = offer == null ? null : _details[offer.productId];
    if (details == null) {
      _set(AppleIapStatus.error,
          'Aucun produit Apple n\'est configuré pour ce prix.');
      return false;
    }

    await _savePendingSummary(details.id, summaryId);
    _set(AppleIapStatus.purchasing);

    try {
      await _purchase.buyConsumable(
        purchaseParam: PurchaseParam(
          productDetails: details,
          applicationUserName: _appAccountToken,
        ),
      );
      return true;
    } catch (e) {
      _set(AppleIapStatus.error, 'Impossible de lancer l\'achat Apple.');
      return false;
    }
  }

  Future<bool> buySubscription({
    required int serviceId,
    required String title,
  }) async {
    await initialize();
    if (!isSupported || !_available) return false;

    final productId = _subscriptionProductByService[serviceId];
    final details = productId == null ? null : _details[productId];
    if (details == null) {
      _set(AppleIapStatus.error,
          'Aucun abonnement Apple n\'est configuré pour ce service.');
      return false;
    }

    _set(AppleIapStatus.purchasing);
    try {
      await _purchase.buyNonConsumable(
        purchaseParam: PurchaseParam(
          productDetails: details,
          applicationUserName: _appAccountToken,
        ),
      );
      return true;
    } catch (e) {
      _set(AppleIapStatus.error, 'Impossible de lancer l\'abonnement Apple.');
      return false;
    }
  }

  Future<void> restorePurchases() async {
    await initialize();
    if (!isSupported || !_available) return;
    _set(AppleIapStatus.loading, 'Restauration des achats…');
    try {
      await _purchase.restorePurchases();
    } catch (e) {
      _set(AppleIapStatus.error, 'Restauration impossible.');
    }
  }

  Future<void> _onPurchases(List<PurchaseDetails> purchases) async {
    for (final purchase in purchases) {
      switch (purchase.status) {
        case PurchaseStatus.pending:
          _set(AppleIapStatus.pending, 'Paiement en attente de validation.');
          break;
        case PurchaseStatus.canceled:
          await _clearPendingSummary(purchase.productID);
          _set(AppleIapStatus.error, 'Achat annulé.');
          break;
        case PurchaseStatus.error:
          _set(
            AppleIapStatus.error,
            purchase.error?.message ?? 'L\'achat Apple a échoué.',
          );
          break;
        case PurchaseStatus.purchased:
        case PurchaseStatus.restored:
          await _verifyAndComplete(purchase);
          break;
      }
    }
  }

  Future<void> _verifyAndComplete(PurchaseDetails purchase) async {
    // Le catalogue permet de distinguer un achat de résumé d'un abonnement et
    // de retrouver le summary_id en attente (reprise après redémarrage).
    if (!_catalogLoaded) {
      await loadCatalog();
    }

    final signed = purchase.verificationData.serverVerificationData;
    if (signed.isEmpty) {
      _set(AppleIapStatus.error,
          'Transaction Apple illisible. Aucun droit n\'a été accordé.');
      return;
    }

    final isSummary =
        _summaryOffers.any((offer) => offer.productId == purchase.productID);
    final summaryId = isSummary
        ? await _pendingSummary(purchase.productID)
        : null;

    _set(AppleIapStatus.verifying,
        'Vérification de la transaction auprès du serveur…');

    try {
      await _api.verifyApplePurchase(
        signedTransaction: signed,
        summaryId: summaryId,
      );

      await _purchase.completePurchase(purchase);
      if (summaryId != null) {
        await _clearPendingSummary(purchase.productID);
      }

      _set(
        AppleIapStatus.success,
        isSummary
            ? 'Achat Apple confirmé. Le résumé est disponible.'
            : 'Abonnement Apple confirmé.',
      );
    } catch (e) {
      // Le backend n'a pas confirmé : on ne complète pas l'achat et on ne
      // débloque aucun droit. StoreKit pourra le représenter plus tard.
      _set(
        AppleIapStatus.error,
        e is ApiException
            ? e.message
            : 'Le serveur n\'a pas pu confirmer la transaction Apple.',
      );
    }
  }

  void _set(AppleIapStatus status, [String? message]) {
    state.value = AppleIapState(status, message: message);
  }

  Future<void> _savePendingSummary(String productId, int summaryId) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setInt('apple_pending_summary_$productId', summaryId);
  }

  Future<int?> _pendingSummary(String productId) async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getInt('apple_pending_summary_$productId');
  }

  Future<void> _clearPendingSummary(String productId) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('apple_pending_summary_$productId');
  }

  Future<void> dispose() async {
    await _subscription?.cancel();
    _subscription = null;
  }
}

class _SummaryOffer {
  final String productId;
  final double price;

  const _SummaryOffer({required this.productId, required this.price});
}

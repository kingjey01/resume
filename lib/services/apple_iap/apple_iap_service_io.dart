import 'dart:async';
import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:in_app_purchase/in_app_purchase.dart';

import 'package:resume_plus_clean/exceptions/api_exception.dart';
import 'package:resume_plus_clean/services/api_service.dart';

import 'apple_iap_types.dart';
import 'pending_summary_store.dart';

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
  final PendingSummaryStore _pendingSummaries = PendingSummaryStore();
  late final PendingSummaryLifecycle _pendingLifecycle =
      PendingSummaryLifecycle(_pendingSummaries);

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

    // Purge uniquement les réservations dont la fin StoreKit est CONFIRMÉE
    // (état `completed`) : cas d'un arrêt entre completePurchase et clear.
    try {
      final purgees = await _pendingSummaries.reconcileCompleted();
      if (purgees > 0) {
        debugPrint(
            '🧹 [Apple IAP] $purgees réservation(s) finalisée(s) purgée(s)');
      }
    } catch (e) {
      debugPrint('⚠️ [Apple IAP] Réconciliation des réservations: $e');
    }
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
              // `business_price` (CDF) sert au rapprochement métier ; on
              // garde `price` en repli pour les anciens backends.
              price: double.tryParse(
                    (map['business_price'] ?? map['price'])?.toString() ?? '',
                  ) ??
                  0,
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
      _subscriptionProductByService
          .removeWhere((_, productId) => productId.isEmpty);

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

  bool _isValidAppAccountToken(String? token) {
    if (token == null || token.isEmpty) return false;
    return RegExp(
      r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-'
      r'[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$',
    ).hasMatch(token);
  }

  /// Vérifie l'authentification, le catalogue et le jeton StoreKit avant
  /// de lancer un achat. Aucun appel StoreKit n'est fait si l'un manque.
  Future<bool> _ensureReadyForPurchase() async {
    await initialize();
    if (!isSupported || !_available) {
      _set(AppleIapStatus.error,
          'Les achats intégrés ne sont pas disponibles sur cet appareil.');
      return false;
    }

    if (!await _api.isLoggedIn()) {
      _set(AppleIapStatus.error,
          'Connectez-vous à votre compte avant de lancer un achat Apple.');
      return false;
    }

    if (!_catalogLoaded) {
      await loadCatalog();
    }
    if (!_catalogLoaded) {
      _set(AppleIapStatus.error,
          'Impossible de charger les produits Apple. Réessayez.');
      return false;
    }

    if (!_isValidAppAccountToken(_appAccountToken)) {
      // Le catalogue a peut-être été chargé avant la connexion : on retente
      // une fois pour obtenir le jeton du compte authentifié.
      await loadCatalog();
      if (!_isValidAppAccountToken(_appAccountToken)) {
        _set(
          AppleIapStatus.error,
          'Session Apple incomplète. Reconnectez-vous puis réessayez.',
        );
        return false;
      }
    }

    return true;
  }

  Future<bool> buySummary({
    required int summaryId,
    required double price,
    required String title,
  }) async {
    if (!await _ensureReadyForPurchase()) return false;

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

    // Empêche d'écraser un achat encore en attente pour un autre résumé.
    final reserved = await _pendingSummaries.reserve(details.id, summaryId);
    if (!reserved) {
      _set(
        AppleIapStatus.error,
        'Un achat Apple est déjà en attente pour ce produit. '
        'Attendez sa finalisation avant d\'en lancer un autre.',
      );
      return false;
    }

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
      // L'achat n'a pas démarré : on libère la réservation pour permettre
      // un nouvel essai.
      await _pendingSummaries.clear(details.id);
      _set(AppleIapStatus.error, 'Impossible de lancer l\'achat Apple.');
      return false;
    }
  }

  Future<bool> buySubscription({
    required int serviceId,
    required String title,
  }) async {
    if (!await _ensureReadyForPurchase()) return false;

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
    if (!await _api.isLoggedIn()) {
      _set(AppleIapStatus.error,
          'Connectez-vous à votre compte avant de restaurer vos achats.');
      return;
    }
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
          // Une transaction en attente peut durer longtemps : ne jamais
          // supprimer la réservation ici.
          await _pendingLifecycle.onPending(purchase.productID);
          _set(AppleIapStatus.pending, 'Paiement en attente de validation.');
          break;
        case PurchaseStatus.canceled:
          // Seule une annulation explicitement confirmée par StoreKit
          // libère la réservation.
          await _pendingLifecycle.onCanceled(
            purchase.productID,
            purchaseId: purchase.purchaseID,
          );
          _set(AppleIapStatus.error, 'Achat annulé.');
          break;
        case PurchaseStatus.error:
          // Erreur StoreKit : le contexte reste disponible pour une reprise.
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

  String _messagePourMatch(PendingMatchStatus status) {
    switch (status) {
      case PendingMatchStatus.noReservation:
        return 'Aucune réservation locale pour ce produit. '
            'Aucun droit n\'a été accordé.';
      case PendingMatchStatus.purchaseIdMissing:
        return 'Transaction Apple sans identifiant fiable. '
            'Aucun droit n\'a été accordé — contactez le support si vous '
            'avez été débité.';
      case PendingMatchStatus.purchaseIdMismatch:
        return 'Cette transaction Apple ne correspond pas à l\'achat réservé. '
            'Aucun droit n\'a été accordé.';
      case PendingMatchStatus.staleTransaction:
        return 'Transaction Apple antérieure à cette réservation. '
            'Aucun droit n\'a été accordé.';
      case PendingMatchStatus.completed:
        return 'Cet achat Apple est déjà finalisé.';
      case PendingMatchStatus.matched:
        return '';
    }
  }

  Future<void> _verifyAndComplete(PurchaseDetails purchase) async {
    // Le catalogue permet de distinguer un achat de résumé d'un abonnement et
    // de retrouver le summary_id en attente (reprise après redémarrage).
    if (!_catalogLoaded) {
      await loadCatalog();
    }
    if (!_catalogLoaded) {
      _set(
        AppleIapStatus.error,
        'Catalogue Apple indisponible. Aucun droit n\'a été accordé.',
      );
      return;
    }

    final signed = purchase.verificationData.serverVerificationData;
    if (signed.isEmpty) {
      _set(AppleIapStatus.error,
          'Transaction Apple illisible. Aucun droit n\'a été accordé.');
      return;
    }

    final isSummaryProduct =
        _summaryOffers.any((offer) => offer.productId == purchase.productID);
    final isSubscriptionProduct =
        _subscriptionProductByService.containsValue(purchase.productID);

    if (!isSummaryProduct && !isSubscriptionProduct) {
      // Produit inconnu : ne jamais le traiter comme un abonnement par défaut.
      _set(
        AppleIapStatus.error,
        'Produit Apple inconnu. Aucun droit n\'a été accordé.',
      );
      return;
    }
    if (isSummaryProduct && isSubscriptionProduct) {
      _set(
        AppleIapStatus.error,
        'Configuration Apple ambiguë pour ce produit. Aucun droit accordé.',
      );
      return;
    }

    int? summaryId;
    if (isSummaryProduct) {
      final match = await _pendingSummaries.matchForVerification(
        purchase.productID,
        purchaseId: purchase.purchaseID,
        transactionDate: purchase.transactionDate,
      );
      if (!match.isMatched) {
        _set(
          AppleIapStatus.error,
          _messagePourMatch(match.status),
        );
        return;
      }
      summaryId = match.summaryId;
    }

    _set(AppleIapStatus.verifying,
        'Vérification de la transaction auprès du serveur…');

    // 1. Validation backend AVANT toute fin de transaction StoreKit.
    try {
      await _api.verifyApplePurchase(
        signedTransaction: signed,
        summaryId: summaryId,
      );
    } catch (e) {
      // Le backend n'a pas confirmé : ne pas compléter l'achat, ne débloquer
      // aucun droit et conserver la réservation pour la reprise.
      await _pendingLifecycle.onBackendFailure(purchase.productID);
      _set(
        AppleIapStatus.error,
        e is ApiException
            ? e.message
            : 'Le serveur n\'a pas pu confirmer la transaction Apple.',
      );
      return;
    }

    // 2. Le droit est accordé côté serveur : mémoriser cet état avant la fin
    // StoreKit. La réservation n'est PAS encore supprimée.
    if (isSummaryProduct) {
      await _pendingLifecycle.onBackendConfirmed(
        purchase.productID,
        purchaseId: purchase.purchaseID,
      );
    }

    // 3. Fin de la transaction StoreKit. Si elle échoue, le droit reste
    // acquis (backend) et la réservation est conservée pour la reprise.
    var finalise = false;
    try {
      await _purchase.completePurchase(purchase);
      if (isSummaryProduct) {
        final marked = await _pendingLifecycle.onStoreKitCompleted(
          purchase.productID,
          purchaseId: purchase.purchaseID,
        );
        // Ne purger que si l'état `completed` a bien été écrit : sinon un
        // arrêt avant `clear()` ne serait pas réconcilié au redémarrage.
        if (marked) {
          await _pendingSummaries.clear(purchase.productID);
        }
      }
      finalise = true;
    } catch (e) {
      debugPrint(
        '⚠️ [Apple IAP] completePurchase échoué, droit conservé, '
        'finalisation en attente: $e',
      );
    }

    final resultat = appleIapStateAfterFinalization(
      isSummaryProduct: isSummaryProduct,
      storeKitCompleted: finalise,
    );
    _set(resultat.status, resultat.message);
  }

  void _set(AppleIapStatus status, [String? message]) {
    state.value = AppleIapState(status, message: message);
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

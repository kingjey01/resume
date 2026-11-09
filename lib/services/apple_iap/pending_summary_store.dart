import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Résultat de la recherche d'une réservation pour une transaction StoreKit.
enum PendingMatchStatus {
  /// Réservation trouvée et liée à ce purchaseID (ou premier rattachement).
  matched,

  /// Aucune réservation pour ce produit.
  noReservation,

  /// La transaction n'a pas de purchaseID : aucun rattachement hasardeux.
  purchaseIdMissing,

  /// La réservation est déjà liée à un AUTRE purchaseID.
  purchaseIdMismatch,

  /// Transaction antérieure à la réservation : considérée comme ancienne.
  staleTransaction,

  /// Réservation déjà finalisée (aurait dû être réconciliée).
  completed,
}

class PendingMatch {
  final PendingMatchStatus status;
  final int? summaryId;
  final String? purchaseId;

  const PendingMatch(
    this.status, {
    this.summaryId,
    this.purchaseId,
  });

  bool get isMatched => status == PendingMatchStatus.matched;
}

enum _EntryStatus { reserved, backendConfirmed, completed }

/// File d'attente locale des achats de résumé Apple.
///
/// StoreKit ne fournit pas d'identifiant de transaction avant l'achat. On
/// réserve donc le `summary_id` par `product_id` AVANT l'appel à StoreKit.
///
/// La réservation n'expire JAMAIS automatiquement. Elle n'est libérée que :
/// - après validation backend + fin StoreKit confirmée (`completed`) ;
/// - après une annulation dont le `purchaseID` correspond à celui de la
///   réservation.
///
/// Un `purchaseID` est lié dès que StoreKit le fournit. Une transaction avec
/// un autre identifiant ne peut pas consommer cette réservation.
class PendingSummaryStore {
  static const String _prefix = 'apple_pending_summary_';
  static const Duration _transactionClockTolerance = Duration(minutes: 10);
  static const int _maxRejectedPurchaseIds = 10;

  PendingSummaryStore();

  String _key(String productId) => '$_prefix$productId';

  /// Réserve `summaryId` pour ce produit.
  ///
  /// Retourne `false` si un autre résumé est déjà en attente, si une
  /// transaction StoreKit est déjà liée, ou si la finalisation est en cours.
  Future<bool> reserve(String productId, int summaryId) async {
    final prefs = await SharedPreferences.getInstance();
    final key = _key(productId);
    final existing = await _readEntry(prefs, key);

    if (existing != null) {
      if (existing.status == _EntryStatus.completed) {
        // Finalisation confirmée mais purge locale non faite : on peut
        // repartir sur une nouvelle réservation.
        await prefs.remove(key);
      } else if (existing.status == _EntryStatus.backendConfirmed) {
        // Droit accordé mais fin StoreKit inconnue : ne jamais lancer un
        // second achat tant que la finalisation n'est pas confirmée.
        return false;
      } else if (existing.purchaseId != null &&
          existing.purchaseId!.isNotEmpty) {
        // Une transaction StoreKit est déjà liée à cette réservation :
        // relancer un achat créerait une seconde transaction dont le droit
        // ne pourrait pas être attribué. On refuse, même pour le même
        // résumé.
        return false;
      } else {
        // Aucune transaction liée (achat annulé ou jamais démarré) : la
        // même réservation peut être réessayée, un autre résumé non.
        return existing.summaryId == summaryId;
      }
    }

    await _writeEntry(
      prefs,
      key,
      _PendingEntry(
        summaryId: summaryId,
        createdAt: DateTime.now().toUtc(),
        status: _EntryStatus.reserved,
      ),
    );
    return true;
  }

  /// Lecture informative du summary_id réservé (sans contrôle purchaseID).
  Future<int?> read(String productId) async {
    final prefs = await SharedPreferences.getInstance();
    final entry = await _readEntry(prefs, _key(productId));
    return entry?.summaryId;
  }

  /// Associe la transaction StoreKit à la réservation, sans limite d'âge.
  ///
  /// - purchaseID absent : refus explicite (restauration sans identifiant) ;
  /// - réservation déjà liée à un autre purchaseID : refus ;
  /// - réservation non liée : lie ce purchaseID, sauf si la transaction est
  ///   antérieure à la réservation (transaction ancienne/inattendue).
  Future<PendingMatch> matchForVerification(
    String productId, {
    String? purchaseId,
    String? transactionDate,
  }) async {
    final prefs = await SharedPreferences.getInstance();
    final key = _key(productId);
    final entry = await _readEntry(prefs, key);

    if (entry == null) {
      return const PendingMatch(PendingMatchStatus.noReservation);
    }
    if (entry.status == _EntryStatus.completed) {
      return const PendingMatch(PendingMatchStatus.completed);
    }

    if (purchaseId == null || purchaseId.isEmpty) {
      // Restauration/achat sans identifiant : ne jamais attribuer un résumé
      // sur la seule base du productId.
      return const PendingMatch(PendingMatchStatus.purchaseIdMissing);
    }

    if (entry.purchaseId != null) {
      if (entry.purchaseId == purchaseId) {
        return PendingMatch(
          PendingMatchStatus.matched,
          summaryId: entry.summaryId,
          purchaseId: purchaseId,
        );
      }
      // Transaction incohérente : on conserve son identifiant pour
      // investigation/support, sans jamais modifier la réservation.
      await _recordRejectedPurchaseId(prefs, key, entry, purchaseId);
      debugPrint(
        '⚠️ [Apple IAP] Transaction $purchaseId refusée pour $productId : '
        'réservation liée à ${entry.purchaseId}',
      );
      return PendingMatch(
        PendingMatchStatus.purchaseIdMismatch,
        summaryId: entry.summaryId,
        purchaseId: purchaseId,
      );
    }

    // Première transaction : vérifier qu'elle n'est pas antérieure à la
    // réservation (cas d'une transaction ancienne/inattendue).
    final dateTransaction = _parseTransactionDate(transactionDate);
    if (dateTransaction != null &&
        dateTransaction.isBefore(
          entry.createdAt.subtract(_transactionClockTolerance),
        )) {
      // Transaction antérieure à la réservation : conservée pour
      // investigation, aucun droit attaché.
      await _recordRejectedPurchaseId(prefs, key, entry, purchaseId);
      debugPrint(
        '⚠️ [Apple IAP] Transaction $purchaseId antérieure à la réservation '
        'de $productId : refusée',
      );
      return PendingMatch(
        PendingMatchStatus.staleTransaction,
        summaryId: entry.summaryId,
        purchaseId: purchaseId,
      );
    }

    await _writeEntry(
      prefs,
      key,
      entry.copyWith(purchaseId: purchaseId),
    );

    return PendingMatch(
      PendingMatchStatus.matched,
      summaryId: entry.summaryId,
      purchaseId: purchaseId,
    );
  }

  /// Raccourci retournant le summary_id uniquement si la transaction correspond.
  Future<int?> readForVerification(
    String productId, {
    String? purchaseId,
    String? transactionDate,
  }) async {
    final match = await matchForVerification(
      productId,
      purchaseId: purchaseId,
      transactionDate: transactionDate,
    );
    return match.isMatched ? match.summaryId : null;
  }

  /// Marque la validation backend réussie (droits accordés, StoreKit pas
  /// encore terminé). La réservation est conservée.
  Future<bool> markBackendConfirmed(
    String productId, {
    String? purchaseId,
  }) async {
    final prefs = await SharedPreferences.getInstance();
    final key = _key(productId);
    final entry = await _readEntry(prefs, key);
    if (entry == null || !_samePurchaseId(entry.purchaseId, purchaseId)) {
      return false;
    }

    await _writeEntry(
      prefs,
      key,
      entry.copyWith(status: _EntryStatus.backendConfirmed),
    );
    return true;
  }

  /// Marque la fin StoreKit confirmée (`completePurchase` réussi).
  ///
  /// La clé n'est pas supprimée ici : `reconcileCompleted()` peut la purger au
  /// prochain démarrage si l'application s'arrête avant le `clear()`.
  Future<bool> markStoreKitCompleted(
    String productId, {
    String? purchaseId,
  }) async {
    final prefs = await SharedPreferences.getInstance();
    final key = _key(productId);
    final entry = await _readEntry(prefs, key);
    if (entry == null || !_samePurchaseId(entry.purchaseId, purchaseId)) {
      return false;
    }

    await _writeEntry(
      prefs,
      key,
      entry.copyWith(status: _EntryStatus.completed),
    );
    return true;
  }

  /// Libère la réservation uniquement si l'annulation correspond au
  /// purchaseID qui la détient.
  Future<bool> cancelIfMatching(
    String productId, {
    String? purchaseId,
  }) async {
    final prefs = await SharedPreferences.getInstance();
    final key = _key(productId);
    final entry = await _readEntry(prefs, key);
    if (entry == null) return false;

    if (!_samePurchaseId(entry.purchaseId, purchaseId)) {
      debugPrint(
        '⚠️ [Apple IAP] Annulation ignorée pour $productId : '
        'purchaseID ${purchaseId ?? "absent"} ≠ ${entry.purchaseId ?? "absent"}',
      );
      return false;
    }

    await prefs.remove(key);
    return true;
  }

  /// Purge les réservations dont la fin StoreKit est CONFIRMÉE.
  ///
  /// Une réservation `backendConfirmed` mais non `completed` est conservée :
  /// l'état StoreKit n'est pas prouvé. Retourne le nombre de clés purgées.
  Future<int> reconcileCompleted() async {
    final prefs = await SharedPreferences.getInstance();
    var supprimees = 0;

    for (final key in prefs.getKeys().where((k) => k.startsWith(_prefix))) {
      final entry = await _readEntry(prefs, key);
      if (entry != null && entry.status == _EntryStatus.completed) {
        await prefs.remove(key);
        supprimees++;
      }
    }
    return supprimees;
  }

  Future<void> clear(String productId) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_key(productId));
  }

  bool _samePurchaseId(String? stored, String? incoming) {
    return stored != null &&
        stored.isNotEmpty &&
        incoming != null &&
        incoming.isNotEmpty &&
        stored == incoming;
  }

  /// Mémorise un identifiant de transaction refusé pour investigation.
  ///
  /// N'influence jamais la correspondance : la liste est purement
  /// informative (support, diagnostic) et bornée.
  Future<void> _recordRejectedPurchaseId(
    SharedPreferences prefs,
    String key,
    _PendingEntry entry,
    String purchaseId,
  ) async {
    final rejected = List<String>.from(entry.rejectedPurchaseIds);
    if (!rejected.contains(purchaseId)) {
      rejected.add(purchaseId);
      while (rejected.length > _maxRejectedPurchaseIds) {
        rejected.removeAt(0);
      }
      await _writeEntry(
        prefs,
        key,
        entry.copyWith(rejectedPurchaseIds: rejected),
      );
    }
  }

  DateTime? _parseTransactionDate(String? raw) {
    if (raw == null || raw.isEmpty) return null;
    final millis = int.tryParse(raw);
    if (millis != null) {
      return DateTime.fromMillisecondsSinceEpoch(millis, isUtc: true);
    }
    return DateTime.tryParse(raw)?.toUtc();
  }

  Future<_PendingEntry?> _readEntry(
    SharedPreferences prefs,
    String key,
  ) async {
    final value = prefs.get(key);
    if (value == null) return null;

    // Ancien format : int simple, sans date ni purchaseID.
    if (value is int) {
      final entry = _PendingEntry(
        summaryId: value,
        createdAt: DateTime.now().toUtc(),
        status: _EntryStatus.reserved,
      );
      await _writeEntry(prefs, key, entry);
      return entry;
    }

    if (value is! String) {
      await prefs.remove(key);
      return null;
    }

    try {
      final map = jsonDecode(value) as Map<String, dynamic>;
      final summaryId = (map['summary_id'] as num?)?.toInt();
      final createdAt = DateTime.tryParse(
        map['created_at']?.toString() ?? '',
      );
      if (summaryId == null || createdAt == null) {
        await prefs.remove(key);
        return null;
      }

      return _PendingEntry(
        summaryId: summaryId,
        createdAt: createdAt,
        purchaseId: map['purchase_id']?.toString(),
        status: _statusDepuis(map['status']?.toString()),
        rejectedPurchaseIds: (map['rejected_purchase_ids'] as List<dynamic>?)
                ?.map((id) => id.toString())
                .where((id) => id.isNotEmpty)
                .toList() ??
            const [],
      );
    } catch (_) {
      await prefs.remove(key);
      return null;
    }
  }

  _EntryStatus _statusDepuis(String? raw) {
    switch (raw) {
      case 'backend_confirmed':
        return _EntryStatus.backendConfirmed;
      case 'completed':
        return _EntryStatus.completed;
      default:
        return _EntryStatus.reserved;
    }
  }

  Future<void> _writeEntry(
    SharedPreferences prefs,
    String key,
    _PendingEntry entry,
  ) async {
    await prefs.setString(
      key,
      jsonEncode({
        'summary_id': entry.summaryId,
        'created_at': entry.createdAt.toUtc().toIso8601String(),
        if (entry.purchaseId != null) 'purchase_id': entry.purchaseId,
        if (entry.rejectedPurchaseIds.isNotEmpty)
          'rejected_purchase_ids': entry.rejectedPurchaseIds,
        'status': _statusTexte(entry.status),
      }),
    );
  }

  String _statusTexte(_EntryStatus status) {
    switch (status) {
      case _EntryStatus.reserved:
        return 'reserved';
      case _EntryStatus.backendConfirmed:
        return 'backend_confirmed';
      case _EntryStatus.completed:
        return 'completed';
    }
  }
}

class _PendingEntry {
  final int summaryId;
  final DateTime createdAt;
  final String? purchaseId;
  final _EntryStatus status;

  /// Transactions refusées pour cette réservation (diagnostic uniquement).
  final List<String> rejectedPurchaseIds;

  const _PendingEntry({
    required this.summaryId,
    required this.createdAt,
    this.purchaseId,
    required this.status,
    this.rejectedPurchaseIds = const [],
  });

  _PendingEntry copyWith({
    String? purchaseId,
    _EntryStatus? status,
    List<String>? rejectedPurchaseIds,
  }) {
    return _PendingEntry(
      summaryId: summaryId,
      createdAt: createdAt,
      purchaseId: purchaseId ?? this.purchaseId,
      status: status ?? this.status,
      rejectedPurchaseIds: rejectedPurchaseIds ?? this.rejectedPurchaseIds,
    );
  }
}

/// Politique de cycle de vie d'une réservation de résumé.
///
/// Une transaction `pending`, une erreur réseau ou un échec de validation
/// backend ne suppriment jamais la réservation.
class PendingSummaryLifecycle {
  final PendingSummaryStore store;

  PendingSummaryLifecycle(this.store);

  Future<void> onPending(String productId) async {}

  Future<void> onBackendFailure(String productId) async {}

  /// Validation backend réussie : on mémorise l'état, sans supprimer.
  Future<bool> onBackendConfirmed(
    String productId, {
    String? purchaseId,
  }) =>
      store.markBackendConfirmed(productId, purchaseId: purchaseId);

  /// `completePurchase` réussi : l'état `completed` sera purgé au prochain
  /// démarrage si l'application s'arrête avant le `clear()`.
  Future<bool> onStoreKitCompleted(
    String productId, {
    String? purchaseId,
  }) =>
      store.markStoreKitCompleted(productId, purchaseId: purchaseId);

  /// Annulation : libère uniquement si le purchaseID correspond.
  Future<bool> onCanceled(
    String productId, {
    String? purchaseId,
  }) =>
      store.cancelIfMatching(productId, purchaseId: purchaseId);
}

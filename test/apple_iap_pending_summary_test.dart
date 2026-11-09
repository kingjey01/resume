import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'package:resume_plus_clean/services/apple_iap/apple_iap_types.dart';
import 'package:resume_plus_clean/services/apple_iap/pending_summary_store.dart';

void main() {
  const productId = 'com.kingjey01.resumeplus.summary.300';
  const key = 'apple_pending_summary_$productId';

  String nowMillis() =>
      DateTime.now().toUtc().millisecondsSinceEpoch.toString();

  setUp(() {
    SharedPreferences.setMockInitialValues({});
  });

  test('purchaseID identique : réservation acceptée et conservée', () async {
    final store = PendingSummaryStore();

    expect(await store.reserve(productId, 123), isTrue);
    final first = await store.matchForVerification(
      productId,
      purchaseId: 'tx-1',
      transactionDate: nowMillis(),
    );
    final second = await store.matchForVerification(
      productId,
      purchaseId: 'tx-1',
      transactionDate: nowMillis(),
    );

    expect(first.status, PendingMatchStatus.matched);
    expect(first.summaryId, 123);
    expect(second.status, PendingMatchStatus.matched);
    expect(second.summaryId, 123);
  });

  test('purchaseID différent : transaction refusée pour cette réservation',
      () async {
    final store = PendingSummaryStore();

    await store.reserve(productId, 123);
    await store.matchForVerification(
      productId,
      purchaseId: 'tx-1',
      transactionDate: nowMillis(),
    );

    final mismatch = await store.matchForVerification(
      productId,
      purchaseId: 'tx-2',
      transactionDate: nowMillis(),
    );

    expect(mismatch.status, PendingMatchStatus.purchaseIdMismatch);
    expect(await store.read(productId), 123);
  });

  test('annulation avec identifiant correspondant : réservation libérée',
      () async {
    final store = PendingSummaryStore();
    final lifecycle = PendingSummaryLifecycle(store);

    await store.reserve(productId, 123);
    await store.matchForVerification(
      productId,
      purchaseId: 'tx-1',
      transactionDate: nowMillis(),
    );

    expect(
      await lifecycle.onCanceled(productId, purchaseId: 'tx-1'),
      isTrue,
    );
    expect(await store.read(productId), isNull);
  });

  test('annulation avec identifiant différent : réservation conservée',
      () async {
    final store = PendingSummaryStore();
    final lifecycle = PendingSummaryLifecycle(store);

    await store.reserve(productId, 123);
    await store.matchForVerification(
      productId,
      purchaseId: 'tx-1',
      transactionDate: nowMillis(),
    );

    expect(
      await lifecycle.onCanceled(productId, purchaseId: 'tx-old'),
      isFalse,
    );
    expect(await store.read(productId), 123);
  });

  test('pending et erreur réseau ne suppriment pas la réservation', () async {
    final store = PendingSummaryStore();
    final lifecycle = PendingSummaryLifecycle(store);

    await store.reserve(productId, 123);
    await lifecycle.onPending(productId);
    await lifecycle.onBackendFailure(productId);

    expect(await store.read(productId), 123);
  });

  test('échec completePurchase : réservation backendConfirmed conservée',
      () async {
    final store = PendingSummaryStore();
    final lifecycle = PendingSummaryLifecycle(store);

    await store.reserve(productId, 123);
    await store.matchForVerification(
      productId,
      purchaseId: 'tx-1',
      transactionDate: nowMillis(),
    );
    await lifecycle.onBackendConfirmed(productId, purchaseId: 'tx-1');

    // Pas de markStoreKitCompleted : finalisation Apple inconnue.
    expect(await PendingSummaryStore().reconcileCompleted(), 0);
    expect(await store.read(productId), 123);
  });

  test('aucun second achat pendant une finalisation en attente', () async {
    final store = PendingSummaryStore();
    final lifecycle = PendingSummaryLifecycle(store);

    await store.reserve(productId, 123);
    await store.matchForVerification(
      productId,
      purchaseId: 'tx-1',
      transactionDate: nowMillis(),
    );
    await lifecycle.onBackendConfirmed(productId, purchaseId: 'tx-1');

    expect(await store.reserve(productId, 123), isFalse);
    expect(await store.read(productId), 123);
  });

  test('completePurchase réussi + arrêt avant clear : réconcilié au démarrage',
      () async {
    final store = PendingSummaryStore();
    final lifecycle = PendingSummaryLifecycle(store);

    await store.reserve(productId, 123);
    await store.matchForVerification(
      productId,
      purchaseId: 'tx-1',
      transactionDate: nowMillis(),
    );
    await lifecycle.onBackendConfirmed(productId, purchaseId: 'tx-1');
    await lifecycle.onStoreKitCompleted(productId, purchaseId: 'tx-1');

    // Simule un arrêt avant clear : nouvelle instance au redémarrage.
    final restarted = PendingSummaryStore();
    expect(await restarted.reconcileCompleted(), 1);
    expect(await restarted.read(productId), isNull);
  });

  test('plusieurs transactions même produit : aucune attribution croisée',
      () async {
    final store = PendingSummaryStore();

    await store.reserve(productId, 123);
    final first = await store.matchForVerification(
      productId,
      purchaseId: 'tx-1',
      transactionDate: nowMillis(),
    );
    final second = await store.matchForVerification(
      productId,
      purchaseId: 'tx-2',
      transactionDate: nowMillis(),
    );

    expect(first.status, PendingMatchStatus.matched);
    expect(second.status, PendingMatchStatus.purchaseIdMismatch);
    expect(await store.read(productId), 123);
  });

  test('transaction restaurée sans purchaseID : aucun rattachement', () async {
    final store = PendingSummaryStore();

    await store.reserve(productId, 123);
    final match = await store.matchForVerification(productId);

    expect(match.status, PendingMatchStatus.purchaseIdMissing);
    expect(await store.readForVerification(productId), isNull);
    expect(await store.read(productId), 123);
  });

  test('une réservation de plus de 24 h reste disponible', () async {
    SharedPreferences.setMockInitialValues({
      key: jsonEncode({
        'summary_id': 123,
        'created_at': '2020-01-01T00:00:00.000Z',
        'status': 'reserved',
      }),
    });
    final store = PendingSummaryStore();

    expect(await store.read(productId), 123);
    final match = await store.matchForVerification(
      productId,
      purchaseId: 'tx-now',
      transactionDate: nowMillis(),
    );
    expect(match.status, PendingMatchStatus.matched);
  });

  test('transaction antérieure à la réservation : staleTransaction', () async {
    final store = PendingSummaryStore();

    await store.reserve(productId, 123);
    final match = await store.matchForVerification(
      productId,
      purchaseId: 'tx-old',
      transactionDate:
          DateTime.utc(2020, 1, 1).millisecondsSinceEpoch.toString(),
    );

    expect(match.status, PendingMatchStatus.staleTransaction);
    expect(await store.read(productId), 123);
  });

  test('deux résumés différents ne peuvent pas écraser la réservation',
      () async {
    final store = PendingSummaryStore();

    expect(await store.reserve(productId, 123), isTrue);
    expect(await store.reserve(productId, 456), isFalse);
    expect(await store.read(productId), 123);
  });

  test('migre l’ancien format int', () async {
    SharedPreferences.setMockInitialValues({key: 42});
    final store = PendingSummaryStore();

    expect(await store.read(productId), 42);

    final prefs = await SharedPreferences.getInstance();
    expect(prefs.get(key), isA<String>());
  });

  test('mémorise purchaseID et le statut sans remplacer le summary_id',
      () async {
    final store = PendingSummaryStore();

    await store.reserve(productId, 123);
    await store.matchForVerification(
      productId,
      purchaseId: 'tx-123',
      transactionDate: nowMillis(),
    );

    final prefs = await SharedPreferences.getInstance();
    final map = jsonDecode(prefs.get(key) as String) as Map<String, dynamic>;
    expect(map['summary_id'], 123);
    expect(map['purchase_id'], 'tx-123');
    expect(map['status'], 'reserved');
  });

  test('réservation liée à une transaction : second achat refusé', () async {
    final store = PendingSummaryStore();

    await store.reserve(productId, 123);
    await store.matchForVerification(
      productId,
      purchaseId: 'tx-1',
      transactionDate: nowMillis(),
    );

    // Même résumé, mais une transaction StoreKit existe déjà : relancer un
    // achat produirait une seconde transaction sans droit attribuable.
    expect(await store.reserve(productId, 123), isFalse);
    expect(await store.read(productId), 123);
  });

  test('transaction refusée conservée pour investigation', () async {
    final store = PendingSummaryStore();

    await store.reserve(productId, 123);
    await store.matchForVerification(
      productId,
      purchaseId: 'tx-1',
      transactionDate: nowMillis(),
    );
    final mismatch = await store.matchForVerification(
      productId,
      purchaseId: 'tx-2',
      transactionDate: nowMillis(),
    );

    expect(mismatch.status, PendingMatchStatus.purchaseIdMismatch);

    final prefs = await SharedPreferences.getInstance();
    final map = jsonDecode(prefs.get(key) as String) as Map<String, dynamic>;
    expect(map['summary_id'], 123);
    expect(map['purchase_id'], 'tx-1');
    expect(map['rejected_purchase_ids'], contains('tx-2'));

    // Une nouvelle instance relit les identifiants refusés.
    final reloaded = PendingSummaryStore();
    await reloaded.matchForVerification(
      productId,
      purchaseId: 'tx-3',
      transactionDate: nowMillis(),
    );
    final map2 = jsonDecode(
      (await SharedPreferences.getInstance()).get(key) as String,
    ) as Map<String, dynamic>;
    expect(
        map2['rejected_purchase_ids'], containsAll(<String>['tx-2', 'tx-3']));
  });

  test('échec completePurchase : état d\'attente, aucun succès affiché', () {
    final etat = appleIapStateAfterFinalization(
      isSummaryProduct: true,
      storeKitCompleted: false,
    );

    expect(etat.status, AppleIapStatus.validatedPendingFinalization);
    expect(etat.message, contains('Finalisation Apple en attente'));
    expect(etat.status, isNot(AppleIapStatus.success));
  });

  test('completePurchase réussi : état de succès', () {
    final etat = appleIapStateAfterFinalization(
      isSummaryProduct: true,
      storeKitCompleted: true,
    );

    expect(etat.status, AppleIapStatus.success);
    expect(etat.message, contains('confirmé'));
  });
}

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:resume_plus_clean/services/api_service.dart';

final apiServiceProvider = Provider<ApiService>((ref) => ApiService());

/// État paginé des achats (TACHE4 : chargement progressif, 10 par page).
class PurchasedSummariesState {
  final List<dynamic> items;
  final int count;
  final bool isLoading;
  final bool isLoadingMore;
  final String? error;

  const PurchasedSummariesState({
    this.items = const [],
    this.count = 0,
    this.isLoading = false,
    this.isLoadingMore = false,
    this.error,
  });

  bool get hasMore => items.length < count;

  PurchasedSummariesState copyWith({
    List<dynamic>? items,
    int? count,
    bool? isLoading,
    bool? isLoadingMore,
    String? error,
    bool clearError = false,
  }) {
    return PurchasedSummariesState(
      items: items ?? this.items,
      count: count ?? this.count,
      isLoading: isLoading ?? this.isLoading,
      isLoadingMore: isLoadingMore ?? this.isLoadingMore,
      error: clearError ? null : (error ?? this.error),
    );
  }
}

/// Source des données de la liste :
/// - [PurchasedListSource.achetes] → endpoint `/summaries/achetes/` : une
///   entrée par résumé réellement acheté (dédupliqué côté serveur) ;
/// - [PurchasedListSource.purchases] → endpoint `/purchases/` : journal brut
///   des transactions (historique, tous statuts, conservé intact).
enum PurchasedListSource { achetes, purchases }

/// Notifier paginé : `refresh()` recharge la page 1, `loadMore()` ajoute
/// la page suivante (appelé automatiquement au défilement).
class PurchasedSummariesNotifier extends StateNotifier<PurchasedSummariesState> {
  PurchasedSummariesNotifier({required this.source})
      : super(const PurchasedSummariesState());

  final ApiService _api = ApiService();
  static const int _pageSize = 10;

  final PurchasedListSource source;

  int _page = 1;

  Future<PurchasesPage> _fetch(int page) async {
    return switch (source) {
      PurchasedListSource.achetes =>
        await _api.getAchetesSummaries(page: page, pageSize: _pageSize),
      PurchasedListSource.purchases =>
        await _api.getPurchasedSummaries(page: page, pageSize: _pageSize),
    };
  }

  Future<void> refresh() async {
    _page = 1;
    state = state.copyWith(isLoading: true, clearError: true);
    try {
      final page = await _fetch(1);
      state = PurchasedSummariesState(items: page.items, count: page.count);
    } catch (e) {
      state = state.copyWith(isLoading: false, error: 'Impossible de charger la liste: $e');
    }
  }

  Future<void> loadMore() async {
    if (state.isLoading || state.isLoadingMore || !state.hasMore) return;
    state = state.copyWith(isLoadingMore: true);
    try {
      final page = await _fetch(_page + 1);
      _page += 1;
      state = PurchasedSummariesState(
        items: [...state.items, ...page.items],
        count: page.count,
      );
    } catch (e) {
      // Échec de chargement d'une page : on laisse l'utilisateur réessayer
      // en remontant/redescendant (le footer réapparaît au prochain scroll).
      state = state.copyWith(isLoadingMore: false);
    }
  }
}

/// « Résumés Achetés » : résumés réellement achetés, DÉDUPLIQUÉS (une carte par
/// résumé) — source `/summaries/achetes/` (le serveur ne renvoie que les achats
/// au statut `completed`).
final purchasedSummariesProvider =
    StateNotifierProvider<PurchasedSummariesNotifier, PurchasedSummariesState>(
  (ref) {
    final notifier = PurchasedSummariesNotifier(source: PurchasedListSource.achetes);
    Future.microtask(notifier.refresh); // chargement initial page 1
    return notifier;
  },
);

/// « Historique des Paiements » : journal brut des transactions (tous statuts,
/// tentatives échouées comprises) — source `/purchases/`.
final purchaseHistoryProvider =
    StateNotifierProvider<PurchasedSummariesNotifier, PurchasedSummariesState>(
  (ref) {
    final notifier = PurchasedSummariesNotifier(source: PurchasedListSource.purchases);
    Future.microtask(notifier.refresh); // chargement initial page 1
    return notifier;
  },
);

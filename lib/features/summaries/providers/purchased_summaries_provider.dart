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

/// Notifier paginé : `refresh()` recharge la page 1, `loadMore()` ajoute
/// la page suivante (appelé automatiquement au défilement).
class PurchasedSummariesNotifier extends StateNotifier<PurchasedSummariesState> {
  PurchasedSummariesNotifier({this.statusFilter}) : super(const PurchasedSummariesState());

  final ApiService _api = ApiService();
  static const int _pageSize = 10;

  /// Filtre serveur : `completed` pour « Résumés Achetés », null pour
  /// « Historique des Paiements » (tous les statuts).
  final String? statusFilter;

  int _page = 1;

  Future<void> refresh() async {
    _page = 1;
    state = state.copyWith(isLoading: true, clearError: true);
    try {
      final page = await _api.getPurchasedSummaries(
        page: 1,
        pageSize: _pageSize,
        status: statusFilter,
      );
      state = PurchasedSummariesState(items: page.items, count: page.count);
    } catch (e) {
      state = state.copyWith(isLoading: false, error: 'Impossible de charger les achats: $e');
    }
  }

  Future<void> loadMore() async {
    if (state.isLoading || state.isLoadingMore || !state.hasMore) return;
    state = state.copyWith(isLoadingMore: true);
    try {
      final page = await _api.getPurchasedSummaries(
        page: _page + 1,
        pageSize: _pageSize,
        status: statusFilter,
      );
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

/// « Résumés Achetés » : uniquement les achats complétés.
final purchasedSummariesProvider =
    StateNotifierProvider<PurchasedSummariesNotifier, PurchasedSummariesState>(
  (ref) {
    final notifier = PurchasedSummariesNotifier(statusFilter: 'completed');
    Future.microtask(notifier.refresh); // chargement initial page 1
    return notifier;
  },
);

/// « Historique des Paiements » : tous les achats (tous statuts).
final purchaseHistoryProvider =
    StateNotifierProvider<PurchasedSummariesNotifier, PurchasedSummariesState>(
  (ref) {
    final notifier = PurchasedSummariesNotifier();
    Future.microtask(notifier.refresh); // chargement initial page 1
    return notifier;
  },
);

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:resume_plus_clean/models/summary.dart';
import 'package:resume_plus_clean/services/api_service.dart';

/// Filtres partagés par les onglets de l'écran Résumés (tâche 60, axe 2).
class SummaryFeedFilter {
  final String search;
  final String professeurNom;
  final DateTime? dateDebut;
  final DateTime? dateFin;

  const SummaryFeedFilter({
    this.search = '',
    this.professeurNom = '',
    this.dateDebut,
    this.dateFin,
  });

  SummaryFeedFilter copyWith({
    String? search,
    String? professeurNom,
    DateTime? dateDebut,
    DateTime? dateFin,
    bool clearDates = false,
  }) {
    return SummaryFeedFilter(
      search: search ?? this.search,
      professeurNom: professeurNom ?? this.professeurNom,
      dateDebut: clearDates ? null : (dateDebut ?? this.dateDebut),
      dateFin: clearDates ? null : (dateFin ?? this.dateFin),
    );
  }
}

class SummaryFeedState {
  final List<Summary> items;
  final bool isLoading;
  final bool isLoadingMore;
  final bool hasMore;
  final String? error;
  final int page;
  final int? count;
  final String tab;
  final SummaryFeedFilter filter;

  const SummaryFeedState({
    this.items = const [],
    this.isLoading = false,
    this.isLoadingMore = false,
    this.hasMore = false,
    this.error,
    this.page = 1,
    this.count,
    this.tab = 'all',
    this.filter = const SummaryFeedFilter(),
  });

  SummaryFeedState copyWith({
    List<Summary>? items,
    bool? isLoading,
    bool? isLoadingMore,
    bool? hasMore,
    String? error,
    bool clearError = false,
    int? page,
    int? count,
    String? tab,
    SummaryFeedFilter? filter,
  }) {
    return SummaryFeedState(
      items: items ?? this.items,
      isLoading: isLoading ?? this.isLoading,
      isLoadingMore: isLoadingMore ?? this.isLoadingMore,
      hasMore: hasMore ?? this.hasMore,
      error: clearError ? null : (error ?? this.error),
      page: page ?? this.page,
      count: count ?? this.count,
      tab: tab ?? this.tab,
      filter: filter ?? this.filter,
    );
  }
}

/// Charge les pages de résumés côté serveur.
///
/// Un changement d'onglet ou de filtre incrémente [_generation] : une réponse
/// lente de l'ancienne requête ne peut donc pas écraser le nouvel état.
class SummaryFeedNotifier extends StateNotifier<SummaryFeedState> {
  SummaryFeedNotifier(this._api) : super(const SummaryFeedState());

  final ApiService _api;
  int _generation = 0;
  static const int pageSize = 20;

  bool? _isFreeFor(String tab) {
    if (tab == 'free') return true;
    if (tab == 'paid') return false;
    return null;
  }

  Future<void> load({
    required String tab,
    SummaryFeedFilter? filter,
  }) async {
    final filtre = filter ?? state.filter;
    final generation = ++_generation;

    state = state.copyWith(
      tab: tab,
      filter: filtre,
      items: const [],
      isLoading: true,
      isLoadingMore: false,
      hasMore: false,
      page: 1,
      count: null,
      clearError: true,
    );

    try {
      final page = await _api.getSummariesPage(
        page: 1,
        pageSize: pageSize,
        search: filtre.search,
        isFree: _isFreeFor(tab),
        professeurNom: filtre.professeurNom,
        dateDebut: filtre.dateDebut,
        dateFin: filtre.dateFin,
        ordering: '-created_at',
      );
      if (!mounted || generation != _generation) return;
      state = state.copyWith(
        items: page.items,
        isLoading: false,
        hasMore: page.hasMore,
        page: 1,
        count: page.count,
        clearError: true,
      );
    } catch (e) {
      if (!mounted || generation != _generation) return;
      state = state.copyWith(
        isLoading: false,
        error: ApiService.getErrorMessage(e),
      );
    }
  }

  Future<void> loadMore() async {
    if (state.isLoading || state.isLoadingMore || !state.hasMore) return;

    final generation = _generation;
    state = state.copyWith(isLoadingMore: true, clearError: true);

    try {
      final page = await _api.getSummariesPage(
        page: state.page + 1,
        pageSize: pageSize,
        search: state.filter.search,
        isFree: _isFreeFor(state.tab),
        professeurNom: state.filter.professeurNom,
        dateDebut: state.filter.dateDebut,
        dateFin: state.filter.dateFin,
        ordering: '-created_at',
      );
      if (!mounted || generation != _generation) return;
      state = state.copyWith(
        items: [...state.items, ...page.items],
        isLoadingMore: false,
        hasMore: page.hasMore,
        page: state.page + 1,
        count: page.count,
        clearError: true,
      );
    } catch (e) {
      if (!mounted || generation != _generation) return;
      state = state.copyWith(
        isLoadingMore: false,
        error: ApiService.getErrorMessage(e),
      );
    }
  }

  Future<void> refresh() => load(tab: state.tab, filter: state.filter);
}

final summaryFeedProvider =
    StateNotifierProvider<SummaryFeedNotifier, SummaryFeedState>(
  (ref) => SummaryFeedNotifier(ApiService()),
);

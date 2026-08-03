import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:resume_plus_clean/models/summary.dart' as model;
import 'package:resume_plus_clean/services/api_service.dart';
import 'package:shared_preferences/shared_preferences.dart';

// 1. Provider pour l'ApiService
final apiServiceProvider = Provider<ApiService>((ref) => ApiService());

// 2. StateProvider pour le terme de recherche
final searchQueryProvider = StateProvider<String>((ref) => '');

// 3. FutureProvider pour récupérer les résumés avec recherche (triés en ordre décroissant)
final summariesProvider = FutureProvider.autoDispose<List<model.Summary>>((ref) async {
  final apiService = ref.watch(apiServiceProvider);
  final searchQuery = ref.watch(searchQueryProvider);
  // La méthode getSummaries retourne maintenant directement la liste des résumés parsée.
  final summaries = await apiService.getSummaries(search: searchQuery.isEmpty ? null : searchQuery);
  
  // Trier en ordre décroissant (plus récents d'abord)
  summaries.sort((a, b) {
    final dateA = a.createdAt;
    final dateB = b.createdAt;
    return dateB.compareTo(dateA); // Décroissant (plus récents d'abord)
  });
  
  return summaries;
});

// 4. Provider pour le badge "Résumés" (résumés validés récemment, non encore consultés)
final validatedSummariesBadgeProvider = StateNotifierProvider<ValidatedSummariesBadgeNotifier, int>((ref) {
  return ValidatedSummariesBadgeNotifier(ref.watch(apiServiceProvider));
});

class ValidatedSummariesBadgeNotifier extends StateNotifier<int> {
  final ApiService _apiService;
  static const String _lastViewedKey = 'badge_last_viewed_summaries';
  bool _initialized = false;

  ValidatedSummariesBadgeNotifier(this._apiService) : super(0);

  /// Compte les résumés validés APRÈS la dernière consultation
  /// Doit être appelé explicitement (pas dans le constructeur)
  Future<void> refreshBadge() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final lastViewedStr = prefs.getString(_lastViewedKey);
      // Si jamais consulté : compter sur les 48h pour le premier chargement
      final lastViewed = lastViewedStr != null
          ? DateTime.parse(lastViewedStr)
          : DateTime.now().subtract(const Duration(hours: 48));

      print('🔵 [Badge Résumés] lastViewed: $lastViewed');

      final summaries = await _apiService.getSummaries();
      print('🔵 [Badge Résumés] ${summaries.length} résumés reçus de l\'API');
      int count = 0;

      for (var summary in summaries) {
        final relevantDate = summary.updatedAt ?? summary.createdAt;
        print('🔵 [Badge Résumés] ID=${summary.id} "${summary.title}" validated=${summary.isValidated} updated=$relevantDate');
        if (summary.isValidated) {
          // Utiliser updatedAt pour détecter les résumés récemment validés
          // (updatedAt change quand is_validated passe à true)
          // Fallback sur createdAt si updatedAt n'est pas disponible
          // Compter uniquement ceux mis à jour APRÈS la dernière consultation
          if (relevantDate.isAfter(lastViewed)) {
            count++;
            print('🔵 [Badge Résumés] +1 → ${summary.title} (updated: $relevantDate)');
          }
        }
      }

      print('🔵 [Badge Résumés] Total: $count');
      if (mounted) state = count;
      _initialized = true;
    } catch (e) {
      print('❌ Erreur badge résumés: $e');
    }
  }

  /// Marque l'onglet comme consulté — enregistre le timestamp, badge → 0
  Future<void> resetBadge() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final now = DateTime.now().toIso8601String();
      await prefs.setString(_lastViewedKey, now);
      print('🟢 [Badge Résumés] RESET → lastViewed = $now');
      if (mounted) state = 0;
    } catch (e) {
      print('⚠️ Erreur sauvegarde badge_last_viewed_summaries: $e');
      // Reset quand même l'état visuel
      if (mounted) state = 0;
    }
  }

  void incrementBadge() {
    if (mounted) {
      state = state + 1;
      print('🔵 [Badge Résumés] INCREMENT → $state');
    }
  }
}

// 5. Provider pour le badge "Validation" (résumés créés/générés à valider, non encore consultés)
final createdSummariesBadgeProvider = StateNotifierProvider<CreatedSummariesBadgeNotifier, int>((ref) {
  return CreatedSummariesBadgeNotifier(ref.watch(apiServiceProvider));
});

class CreatedSummariesBadgeNotifier extends StateNotifier<int> {
  final ApiService _apiService;
  static const String _lastViewedKey = 'badge_last_viewed_validation';
  bool _initialized = false;

  CreatedSummariesBadgeNotifier(this._apiService) : super(0);

  /// Compte les résumés non validés (en attente) APRÈS la dernière consultation CP
  /// Utilise l'API /summaries/validation/ qui retourne tous les résumés (validés et non validés)
  /// Doit être appelé explicitement (pas dans le constructeur)
  Future<void> refreshBadge() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final lastViewedStr = prefs.getString(_lastViewedKey);
      final lastViewed = lastViewedStr != null
          ? DateTime.parse(lastViewedStr)
          : DateTime.now().subtract(const Duration(hours: 48));

      print('🟠 [Badge Validation] lastViewed: $lastViewed');

      // Utiliser l'API validation qui retourne TOUS les résumés (y compris non validés)
      final data = await _apiService.getSummariesForValidation();
      final summariesRaw = data['summaries'] as List<dynamic>? ?? [];
      print('🟠 [Badge Validation] ${summariesRaw.length} résumés reçus de l\'API');
      
      int count = 0;

      for (var json in summariesRaw) {
        final isValidated = json['is_validated'] ?? false;
        final createdAtStr = json['created_at'] as String?;
        final updatedAtStr = json['updated_at'] as String?;
        final title = json['titre'] ?? 'Sans titre';
        final id = json['id'];
        
        // Parser les dates
        DateTime? createdAt;
        DateTime? updatedAt;
        try {
          if (createdAtStr != null) createdAt = DateTime.parse(createdAtStr);
          if (updatedAtStr != null) updatedAt = DateTime.parse(updatedAtStr);
        } catch (_) {}
        
        // Utiliser updatedAt ou createdAt
        final relevantDate = updatedAt ?? createdAt ?? DateTime.now();
        
        print('🟠 [Badge Validation] ID=$id "$title" validated=$isValidated updated=$relevantDate');
        
        if (!isValidated) {
          // Pour les résumés en attente, compter ceux créés/mis à jour APRÈS la dernière consultation
          if (relevantDate.isAfter(lastViewed)) {
            count++;
            print('🟠 [Badge Validation] +1 → $title (date: $relevantDate)');
          }
        }
      }

      print('🟠 [Badge Validation] Total: $count');
      if (mounted) state = count;
      _initialized = true;
    } catch (e) {
      print('❌ Erreur badge validation: $e');
    }
  }

  /// Marque l'onglet validation comme consulté — enregistre le timestamp, badge → 0
  Future<void> resetBadge() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final now = DateTime.now().toIso8601String();
      await prefs.setString(_lastViewedKey, now);
      print('🟢 [Badge Validation] RESET → lastViewed = $now');
      if (mounted) state = 0;
    } catch (e) {
      print('⚠️ Erreur sauvegarde badge_last_viewed_validation: $e');
      // Reset quand même l'état visuel
      if (mounted) state = 0;
    }
  }

  void incrementBadge() {
    if (mounted) {
      state = state + 1;
      print('🟠 [Badge Validation] INCREMENT → $state');
    }
  }
}

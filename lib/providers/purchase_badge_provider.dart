import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:resume_plus_clean/services/api_service.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Provider pour gérer le compteur de badges sur "Mes Achats"
/// Compte les achats/abonnements récents (non lus)
final purchaseBadgeCountProvider = StateNotifierProvider<PurchaseBadgeNotifier, int>((ref) {
  return PurchaseBadgeNotifier();
});

class PurchaseBadgeNotifier extends StateNotifier<int> {
  PurchaseBadgeNotifier() : super(0);

  final ApiService _apiService = ApiService();
  static const String _lastViewedKey = 'purchase_badge_last_viewed';

  /// Charge le nombre d'achats/abonnements récents
  Future<void> loadBadgeCount() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final lastViewedStr = prefs.getString(_lastViewedKey);
      final lastViewed = lastViewedStr != null ? DateTime.parse(lastViewedStr) : DateTime(2000);
      
      final purchases = await _apiService.getPurchasedSummaries();
      
      // Compter les achats complétés APRÈS la dernière visite
      int recentCount = 0;
      
      for (var purchase in purchases) {
        if (purchase['status'] == 'completed') {
          try {
            final completedAt = DateTime.parse(purchase['completed_at'] ?? '');
            
            // Compter les achats complétés APRÈS la dernière visite
            if (completedAt.isAfter(lastViewed)) {
              recentCount++;
            }
          } catch (_) {
            // Si la date n'est pas parsable, ignorer
          }
        }
      }
      
      state = recentCount;
    } catch (e) {
      print('❌ Erreur chargement badge count: $e');
      state = 0;
    }
  }

  /// Ajoute 1 au compteur (quand un achat/abonnement réussit)
  void incrementBadge() {
    state = state + 1;
  }

  /// Réinitialise le compteur et enregistre la date de visite
  Future<void> resetBadge() async {
    state = 0;
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString(_lastViewedKey, DateTime.now().toIso8601String());
    } catch (e) {
      print('⚠️ Erreur sauvegarde last_viewed: $e');
    }
  }

  /// Décrémente le compteur
  void decrementBadge() {
    if (state > 0) {
      state = state - 1;
    }
  }
}

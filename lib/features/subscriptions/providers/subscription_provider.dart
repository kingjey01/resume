import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:resume_plus_clean/models/abonnement.dart';
import 'package:resume_plus_clean/services/api_service.dart';
import 'package:resume_plus_clean/features/home/providers/summary_provider.dart';

final subscriptionApiProvider = Provider<SubscriptionApi>((ref) {
  final apiService = ref.watch(apiServiceProvider);
  return SubscriptionApi(apiService);
});

final subscriptionsProvider = FutureProvider.autoDispose<List<Abonnement>>((ref) async {
  final subscriptionApi = ref.watch(subscriptionApiProvider);
  return subscriptionApi.getSubscriptions();
});

final subscriptionProvider = FutureProvider.family<Abonnement, int>((ref, subscriptionId) async {
  final subscriptionApi = ref.watch(subscriptionApiProvider);
  return subscriptionApi.getSubscription(subscriptionId);
});

class SubscriptionApi {
  final ApiService _apiService;

  SubscriptionApi(this._apiService);

  Future<List<Abonnement>> getSubscriptions() async {
    try {
      final response = await _apiService.get('/abonnements/');
      print('Abonnements API Response: ${response.data}');
      print('Response Type: ${response.data.runtimeType}');
      
      final dynamic responseData = response.data;
      
      if (responseData is List) {
        return responseData.map((json) => Abonnement.fromJson(json as Map<String, dynamic>)).toList();
      } else if (responseData is Map && responseData.containsKey('results')) {
        // Handle paginated response
        final List results = responseData['results'];
        return results.map((json) => Abonnement.fromJson(json as Map<String, dynamic>)).toList();
      } else {
        print('Unexpected response format: $responseData');
        throw Exception('Format de réponse inattendu: attendu List, reçu ${responseData.runtimeType}');
      }
    } catch (e) {
      print('Abonnement loading error: $e');
      throw Exception('Erreur lors du chargement des abonnements: $e');
    }
  }

  Future<Abonnement> getSubscription(int id) async {
    try {
      final response = await _apiService.get('/abonnements/$id/');
      return Abonnement.fromJson(response.data as Map<String, dynamic>);
    } catch (e) {
      throw Exception('Erreur lors du chargement de l\'abonnement: $e');
    }
  }

  Future<Abonnement> createSubscription(Map<String, dynamic> subscriptionData) async {
    try {
      final response = await _apiService.post('/abonnements/', data: subscriptionData);
      return Abonnement.fromJson(response.data as Map<String, dynamic>);
    } catch (e) {
      throw Exception('Erreur lors de la création de l\'abonnement: $e');
    }
  }

  Future<Abonnement> updateSubscription(int id, Map<String, dynamic> subscriptionData) async {
    try {
      final response = await _apiService.put('/abonnements/$id/', data: subscriptionData);
      return Abonnement.fromJson(response.data as Map<String, dynamic>);
    } catch (e) {
      throw Exception('Erreur lors de la mise à jour de l\'abonnement: $e');
    }
  }

  Future<void> deleteSubscription(int id) async {
    try {
      await _apiService.delete('/abonnements/$id/');
    } catch (e) {
      throw Exception('Erreur lors de la suppression de l\'abonnement: $e');
    }
  }
}

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:resume_plus_clean/models/service.dart';
import 'package:resume_plus_clean/services/api_service.dart';
import 'package:resume_plus_clean/features/home/providers/summary_provider.dart';

final serviceApiProvider = Provider<ServiceApi>((ref) {
  final apiService = ref.watch(apiServiceProvider);
  return ServiceApi(apiService);
});

final servicesProvider = FutureProvider<List<Service>>((ref) async {
  final serviceApi = ref.watch(serviceApiProvider);
  return serviceApi.getServices();
});

final serviceProvider = FutureProvider.family<Service, int>((ref, serviceId) async {
  final serviceApi = ref.watch(serviceApiProvider);
  return serviceApi.getService(serviceId);
});

class ServiceApi {
  final ApiService _apiService;

  ServiceApi(this._apiService);

  Future<List<Service>> getServices() async {
    try {
      final response = await _apiService.get('/services/');
      print('Services API Response: ${response.data}');
      print('Response Type: ${response.data.runtimeType}');
      
      final dynamic responseData = response.data;
      
      if (responseData is List) {
        final services = responseData.map((serviceJson) {
          try {
            return Service.fromJson(serviceJson as Map<String, dynamic>);
          } catch (e) {
            print('Error parsing service: $serviceJson');
            print('Parse error: $e');
            rethrow;
          }
        }).toList();
        return services;
      } else if (responseData is Map && responseData.containsKey('results')) {
        // Handle paginated response
        final List results = responseData['results'];
        return results.map((json) => Service.fromJson(json as Map<String, dynamic>)).toList();
      } else {
        print('Unexpected response format: $responseData');
        throw Exception('Format de réponse inattendu: attendu List, reçu ${responseData.runtimeType}');
      }
    } catch (e) {
      print('Service loading error: $e');
      throw Exception('Erreur lors du chargement des services: $e');
    }
  }

  Future<Service> getService(int id) async {
    try {
      final response = await _apiService.get('/services/$id/');
      return Service.fromJson(response.data as Map<String, dynamic>);
    } catch (e) {
      throw Exception('Erreur lors du chargement du service: $e');
    }
  }

  Future<Service> createService(Map<String, dynamic> serviceData) async {
    try {
      final response = await _apiService.post('/services/', data: serviceData);
      return Service.fromJson(response.data as Map<String, dynamic>);
    } catch (e) {
      throw Exception('Erreur lors de la création du service: $e');
    }
  }

  Future<Service> updateService(int id, Map<String, dynamic> serviceData) async {
    try {
      final response = await _apiService.put('/services/$id/', data: serviceData);
      return Service.fromJson(response.data as Map<String, dynamic>);
    } catch (e) {
      throw Exception('Erreur lors de la mise à jour du service: $e');
    }
  }

  Future<void> deleteService(int id) async {
    try {
      await _apiService.delete('/services/$id/');
    } catch (e) {
      throw Exception('Erreur lors de la suppression du service: $e');
    }
  }
}

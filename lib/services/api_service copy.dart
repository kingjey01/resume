import 'package:dio/dio.dart';
import 'package:resume_plus_clean/services/storage_service.dart';

class ApiService {
  final Dio _dio;
  final StorageService _storageService;
  
  static const String baseUrl = 'https://resumecours.gestionhospitaliare.site/api';
  
  ApiService({Dio? dio, StorageService? storageService})
      : _dio = dio ?? Dio(BaseOptions(baseUrl: baseUrl)),
        _storageService = storageService ?? StorageService() {
    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) async {
        final token = await _storageService.accessToken;
        if (token != null) {
          options.headers['Authorization'] = 'Bearer $token';
        }
        return handler.next(options);
      },
    ));
  }

  Future<Map<String, dynamic>> login(String username, String password) async {
    try {
      final response = await _dio.post('/auth/login/', data: {
        'username': username,
        'password': password,
      });
      
      if (response.statusCode == 200) {
        final data = response.data;
        await _storageService.saveTokens(data['access'], data['refresh']);
        return {'success': true, ...data};
      }
      return {'success': false, 'error': 'Login failed'};
    } catch (e) {
      return {'success': false, 'error': e.toString()};
    }
  }

  Future<Map<String, dynamic>> getUserProfile() async {
    try {
      final response = await _dio.get('/auth/user/');
      if (response.statusCode == 200) {
        return {'success': true, 'data': response.data};
      }
      return {'success': false, 'error': 'Failed to get profile'};
    } catch (e) {
      return {'success': false, 'error': e.toString()};
    }
  }
}

import 'dart:async';
import 'dart:typed_data';
import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:resume_plus_clean/models/summary.dart' as model;
import 'package:resume_plus_clean/services/storage_service.dart';
import 'package:resume_plus_clean/models/universite.dart';
import 'package:resume_plus_clean/models/promotion.dart';
import 'package:resume_plus_clean/models/filiere.dart';
import 'package:resume_plus_clean/utils/logger.dart';
import 'package:resume_plus_clean/exceptions/api_exception.dart';
import 'package:resume_plus_clean/services/demo_data_service.dart';

/// Page d'achats paginée (TACHE4 : affichage progressif des résumés achetés).
class PurchasesPage {
  final List<dynamic> items;
  final int count;
  final int page;
  final int pageSize;

  const PurchasesPage({
    required this.items,
    required this.count,
    required this.page,
    required this.pageSize,
  });

  bool get hasMore => page * pageSize < count;
}

class ApiService {
  final Dio _dio;
  final StorageService _storageService;

  static const String productionUrl = 'https://resumecours.gestionhospitaliare.site/api';

  static String get developmentUrl {
    if (kIsWeb) {
      return 'http://127.0.0.1:8000/api';
    }
    return 'http://172.16.1.253:8000/api';
  }

  static const bool isProduction = true;
  static String get baseUrl => productionUrl;

  // Système robuste de refresh token sans concurrence
  Completer<String?>? _refreshCompleter;
  String? _currentAccessToken;
  String? _currentRefreshToken;

  // Cache avec expiration (10 minutes)
  static const Duration _cacheExpiration = Duration(minutes: 10);
  DateTime? _cacheTimestamp;

  List<Universite>? _cachedUniversites;
  Map<int, List<Filiere>> _cachedFilieresByUniversite = {};
  Map<int, List<Promotion>> _cachedPromotionsByFiliere = {};

  ApiService({Dio? dio, StorageService? storageService})
      : _dio = dio ?? Dio(BaseOptions(baseUrl: baseUrl)),
        _storageService = storageService ?? StorageService() {
    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: _onRequest,
      onError: _onError,
      onResponse: _onResponse,
    ));
  }

  /// Réinitialise complètement la session en mémoire
  void clearSession() {
    _currentAccessToken = null;
    _currentRefreshToken = null;
    _refreshCompleter = null;
    _cachedUniversites = null;
    _cachedFilieresByUniversite.clear();
    _cachedPromotionsByFiliere.clear();
    _cacheTimestamp = null;
    debugPrint('🧹 [API] Session en mémoire réinitialisée');
  }

  // ─── Méthode statique : message d'erreur lisible pour l'utilisateur ───────

  /// Convertit N'IMPORTE QUELLE erreur en un message lisible en français.
  ///
  /// Centralise TOUTE la logique de traduction d'erreur. À utiliser dans
  /// tous les catch blocks try/catch et dans [ErrorHandlerMixin].
  ///
  /// Exemple :
  /// ```dart
  /// try { ... } catch (e) {
  ///   SnackbarService.showError(ApiService.getErrorMessage(e));
  /// }
  /// ```
  static String getErrorMessage(dynamic error) {
    // 1) ApiException → message déjà prêt (meilleur cas)
    if (error is ApiException) {
      return error.message;
    }

    // 2) DioException → convertir via le factory existant
    if (error is DioException) {
      // Si _onError a déjà enrichi le message, l'utiliser directement
      if (error.message != null &&
          error.message!.length > 3 &&
          !error.message!.contains('DioException') &&
          !error.message!.contains('HttpException') &&
          !error.message!.contains('type')) {
        return error.message!;
      }
      return ApiException.fromDioException(error).message;
    }

    // 3) Exception standard → nettoyer le préfixe
    if (error is Exception) {
      final msg = error.toString();
      // Nettoyer les wrapper Dart inutiles
      return msg
          .replaceAll('Exception: ', '')
          .replaceAll('DioException: ', '')
          .replaceAll('HandshakeException: ', '')
          .trim();
    }

    // 4) String directe
    if (error is String) return error;

    // 5) Fallback
    return 'Une erreur inattendue est survenue. Veuillez réessayer.';
  }

  /// Extrait le message d'erreur renvoyé par le backend depuis la réponse.
  static String? _extractBackendMessage(Response? response) {
    if (response?.data == null) return null;
    final data = response!.data;

    if (data is Map) {
      // Formats Django/Django REST Framework courants
      for (final key in ['error', 'message', 'detail', 'non_field_errors']) {
        if (data.containsKey(key)) {
          final val = data[key];
          if (val is String && val.isNotEmpty) return val;
          if (val is List && val.isNotEmpty) return val.first.toString();
        }
      }
    }
    return null;
  }

  // ─── Intercepteurs Dio ───────────────────────────────────────────────

  Future<void> _onRequest(RequestOptions options, RequestInterceptorHandler handler) async {
    final publicEndpoints = [
      '/auth/token/refresh/',
      '/auth/otp/request/',
      '/auth/otp/verify/',
      '/courses/universites/',
      '/courses/promotions/',
      '/courses/filieres/',
      '/app-version/',
    ];

    final isPublicEndpoint = publicEndpoints.any((endpoint) => options.path.endsWith(endpoint));

    if (!isPublicEndpoint) {
      String? token = _currentAccessToken;
      if (token == null) {
        try {
          token = await _storageService.accessToken;
          _currentAccessToken = token;
          debugPrint('🔑 [API] Token récupéré: ${token != null ? "✅" : "❌"}');
        } catch (e) {
          AppLogger.error('Erreur storage dans _onRequest', e);
        }
      }

      if (token != null) {
        options.headers['Authorization'] = 'Bearer $token';
      } else {
        debugPrint('⚠️ [API] Pas de token pour ${options.path}');
      }
    }

    handler.next(options);
  }

  void _onResponse(Response response, ResponseInterceptorHandler handler) {
    return handler.next(response);
  }

  Future<void> _onError(DioException err, ErrorInterceptorHandler handler) async {
    final response = err.response;
    final path = err.requestOptions.path;
    final statusCode = response?.statusCode;

    // Log serveur
    AppLogger.error('Erreur API [$statusCode] $path', err);

    // Refresh token automatique pour 401
    if (statusCode == 401 &&
        !path.endsWith('/auth/token/refresh/') &&
        !path.endsWith('/auth/otp/request/') &&
        !path.endsWith('/auth/otp/verify/')) {
      AppLogger.info('🔄 Tentative refresh token pour $path');
      try {
        final newToken = await refreshToken();
        if (newToken != null) {
          err.requestOptions.headers['Authorization'] = 'Bearer $newToken';
          final opts = Options(
            method: err.requestOptions.method,
            headers: err.requestOptions.headers,
            responseType: err.requestOptions.responseType,
          );
          try {
            final newResponse = await _dio.request<dynamic>(
              path,
              options: opts,
              data: err.requestOptions.data,
              queryParameters: err.requestOptions.queryParameters,
            );
            return handler.resolve(newResponse);
          } catch (retryError) {
            AppLogger.error('❌ Requête après refresh échouée', retryError);
          }
        }
      } catch (e) {
        AppLogger.error('❌ Refresh token échoué', e);
      }
    }

    // ═══════════════════════════════════════════════════════════════════
    // CONVERSION EN MESSAGE LISIBLE POUR L'UTILISATEUR
    // On crée une nouvelle DioException avec un message utilisateur clair.
    // Comme l'intercepteur doit passer un DioException (pas ApiException),
    // on écrase le message technique par le message compréhensible.
    // ═══════════════════════════════════════════════════════════════════
    final backendMsg = _extractBackendMessage(response);
    final apiEx = ApiException.fromDioException(err);
    // Le message backend est prioritaire (le plus précis)
    final userMessage = backendMsg ?? apiEx.message;

    final enrichedError = DioException(
      requestOptions: err.requestOptions,
      response: response,
      type: err.type,
      error: userMessage,
      message: userMessage,
      stackTrace: err.stackTrace,
    );

    return handler.next(enrichedError);
  }

  // ─── Refresh token ──────────────────────────────────────────────────

  Future<String?> refreshToken() async {
    if (_refreshCompleter != null) {
      return _refreshCompleter!.future;
    }

    _refreshCompleter = Completer<String?>();

    try {
      String? refreshToken = _currentRefreshToken;
      if (refreshToken == null) {
        refreshToken = await _storageService.refreshToken;
      }

      if (refreshToken == null) {
        throw ApiException('Session expirée. Veuillez vous reconnecter.',
            type: ApiExceptionType.noRefreshToken);
      }

      final response = await _dio.post('/auth/token/refresh/', data: {
        'refresh': refreshToken,
      });

      if (response.statusCode == 200) {
        final newAccessToken = response.data['access'];
        _currentAccessToken = newAccessToken;
        await _storageService.saveAccessToken(newAccessToken);
        // Rotation du refresh token : le backend (ROTATE_REFRESH_TOKENS +
        // BLACKLIST_AFTER_ROTATION) renvoie un NOUVEAU refresh token et
        // blackliste l'ancien. Sans sauvegarde, le refresh token en storage
        // devient obsolète → le prochain refresh échoue (session perdue).
        final newRefreshToken = response.data['refresh'];
        if (newRefreshToken != null && newRefreshToken.toString().isNotEmpty) {
          _currentRefreshToken = newRefreshToken;
          await _storageService.saveRefreshToken(newRefreshToken.toString());
        }
        _refreshCompleter!.complete(newAccessToken);
        return newAccessToken;
      } else {
        throw ApiException('Session expirée. Veuillez vous reconnecter.',
            type: ApiExceptionType.refreshFailed);
      }
    } catch (e) {
      AppLogger.error('Erreur refresh token', e);
      await _invalidateTokens();
      final error = e is ApiException
          ? e
          : ApiException('Session expirée. Veuillez vous reconnecter.',
              type: ApiExceptionType.refreshFailed, originalError: e);
      _refreshCompleter!.completeError(error);
      rethrow;
    } finally {
      _refreshCompleter = null;
    }
  }

  Future<void> _invalidateTokens() async {
    _currentAccessToken = null;
    _currentRefreshToken = null;
    await _storageService.deleteTokens();
  }

  // ─── Gestion du cache ───────────────────────────────────────────────

  bool _isCacheExpired() {
    if (_cacheTimestamp == null) return true;
    return DateTime.now().difference(_cacheTimestamp!) > _cacheExpiration;
  }

  void _updateCacheTimestamp() {
    _cacheTimestamp = DateTime.now();
  }

  // ─── HTTP génériques (avec erreur enrichie) ─────────────────────────

  Future<Response> get(String path, {Map<String, dynamic>? queryParameters}) async {
    try {
      return await _dio.get(path, queryParameters: queryParameters);
    } catch (e) {
      throw ApiException(getErrorMessage(e),
          type: ApiExceptionType.unknown, originalError: e);
    }
  }

  Future<Response> post(String path, {dynamic data}) async {
    try {
      return await _dio.post(path, data: data);
    } catch (e) {
      throw ApiException(getErrorMessage(e),
          type: ApiExceptionType.unknown, originalError: e);
    }
  }

  Future<Response> put(String path, {dynamic data}) async {
    try {
      return await _dio.put(path, data: data);
    } catch (e) {
      throw ApiException(getErrorMessage(e),
          type: ApiExceptionType.unknown, originalError: e);
    }
  }

  Future<Response> delete(String path) async {
    try {
      return await _dio.delete(path);
    } catch (e) {
      throw ApiException(getErrorMessage(e),
          type: ApiExceptionType.unknown, originalError: e);
    }
  }

  // ═════════════════════════════════════════════════════════════════════
  // MÉTHODES API SPÉCIFIQUES
  // Toutes les méthodes suivantes utilisent désormais les helpers
  // centralisés : getErrorMessage() pour les messages + ApiException.
  //
  // IMPORTANT : fini les `rethrow` silencieux ou les `throw Exception(msg)`.
  // Les erreurs remontent sous forme d'ApiException avec message en français.
  // ═════════════════════════════════════════════════════════════════════

  // ─── Authentification ───────────────────────────────────────────────

  Future<void> logout() async {
    try {
      final refreshToken = await _storageService.refreshToken;
      if (refreshToken != null) {
        await _dio.post('/auth/logout/', data: {'refresh': refreshToken});
      }
    } catch (e) {
      // Non bloquant : on supprime les tokens localement quoi qu'il arrive
      AppLogger.warning('Logout API error (non bloquant)', e.toString());
    } finally {
      await _invalidateTokens();
    }
  }

  Future<Map<String, dynamic>> getUserProfile() async {
    try {
      final response = await _dio.get('/auth/user/');
      if (response.statusCode == 200) {
        return response.data as Map<String, dynamic>;
      }
      throw ApiException('Impossible de charger votre profil.',
          type: ApiExceptionType.server);
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException(getErrorMessage(e), type: ApiExceptionType.unknown, originalError: e);
    }
  }

  Future<bool> isLoggedIn() async {
    final token = await _storageService.accessToken;
    return token != null;
  }

  Future<String?> getAccessToken() async {
    return await _storageService.accessToken;
  }

  Future<void> initializeTokens() async {
    try {
      _currentAccessToken = await _storageService.accessToken;
      _currentRefreshToken = await _storageService.refreshToken;
    } catch (e) {
      AppLogger.error('Error initializing tokens', e);
    }
  }

  // ─── Universités, Filières, Promotions ──────────────────────────────

  Future<List<Universite>> getUniversites({bool forceRefresh = false}) async {
    try {
      if (_cachedUniversites != null && !forceRefresh && !_isCacheExpired()) {
        return _cachedUniversites!;
      }
      final response = await _dio.get('/courses/universites/');
      if (response.statusCode == 200) {
        _cachedUniversites = (response.data as List)
            .map((json) => Universite.fromJson(json))
            .toList();
        _updateCacheTimestamp();
        return _cachedUniversites!;
      }
      return [];
    } catch (e) {
      AppLogger.error('Erreur chargement universités', e);
      throw ApiException(getErrorMessage(e), type: ApiExceptionType.server, originalError: e);
    }
  }

  Future<List<Filiere>> getFilieresByUniversite(int universiteId, {bool forceRefresh = false}) async {
    try {
      if (_cachedFilieresByUniversite[universiteId] != null && !forceRefresh && !_isCacheExpired()) {
        return _cachedFilieresByUniversite[universiteId]!;
      }
      final response = await _dio.get('/courses/universites/$universiteId/filieres/');
      if (response.statusCode == 200) {
        final filieres = (response.data as List)
            .map((json) => Filiere.fromJson(json))
            .toList();
        _cachedFilieresByUniversite[universiteId] = filieres;
        _updateCacheTimestamp();
        return filieres;
      }
      return [];
    } catch (e) {
      AppLogger.error('Erreur chargement filières', e);
      throw ApiException(getErrorMessage(e), type: ApiExceptionType.server, originalError: e);
    }
  }

  Future<List<Promotion>> getPromotionsByFiliere(int filiereId, {bool forceRefresh = false}) async {
    try {
      if (_cachedPromotionsByFiliere[filiereId] != null && !forceRefresh && !_isCacheExpired()) {
        return _cachedPromotionsByFiliere[filiereId]!;
      }
      final response = await _dio.get('/courses/filieres/$filiereId/promotions/');
      if (response.statusCode == 200) {
        final promotions = (response.data as List)
            .map((json) => Promotion.fromJson(json))
            .toList();
        _cachedPromotionsByFiliere[filiereId] = promotions;
        _updateCacheTimestamp();
        return promotions;
      }
      return [];
    } catch (e) {
      AppLogger.error('Erreur chargement promotions', e);
      throw ApiException(getErrorMessage(e), type: ApiExceptionType.server, originalError: e);
    }
  }

  // ─── Résumés ────────────────────────────────────────────────────────

  Future<List<model.Summary>> getSummaries({String? search}) async {
    try {
      final queryParams = <String, dynamic>{};
      if (search != null && search.isNotEmpty) queryParams['search'] = search;

      final response = await _dio.get('/summaries/', queryParameters: queryParams);
      if (response.statusCode == 200) {
        dynamic data = response.data;
        List<dynamic> summariesList;

        if (data is List) {
          summariesList = data;
        } else if (data is Map && data.containsKey('results')) {
          summariesList = data['results'] as List;
        } else {
          throw ApiException('Format de réponse inattendu du serveur.',
              type: ApiExceptionType.server);
        }
        return summariesList.map((s) => model.Summary.fromJson(s)).toList();
      }
      throw ApiException('Impossible de charger les résumés.',
          type: ApiExceptionType.server);
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException(getErrorMessage(e), type: ApiExceptionType.server, originalError: e);
    }
  }

  Future<model.Summary> getSummaryById(int id) async {
    try {
      final response = await _dio.get('/summaries/$id/');
      if (response.statusCode == 200) {
        return model.Summary.fromJson(response.data as Map<String, dynamic>);
      }
      throw ApiException('Résumé introuvable.', type: ApiExceptionType.notFound);
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException(getErrorMessage(e), type: ApiExceptionType.unknown, originalError: e);
    }
  }

  Future<model.Summary> createSummary({
    required String titre,
    required String texteResume,
    required int courseId,
    required double prix,
    bool? isFree,
    int? professeurId,
  }) async {
    try {
      final data = <String, dynamic>{
        'titre': titre,
        'texte_resume': texteResume,
        'course': courseId,
        'author_type': 'cp',
        'prix': prix,
        'is_free': isFree ?? false,
      };
      if (professeurId != null) data['professeur'] = professeurId;

      final response = await _dio.post('/summaries/', data: data);
      if (response.statusCode == 201) {
        return model.Summary.fromJson(response.data);
      }
      throw ApiException('Erreur lors de la création du résumé.',
          type: ApiExceptionType.validation);
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException(getErrorMessage(e), type: ApiExceptionType.unknown, originalError: e);
    }
  }

  Future<void> editSummary(int summaryId, Map<String, dynamic> data) async {
    try {
      final response = await _dio.put('/summaries/$summaryId/edit/', data: data);
      if (response.statusCode != 200) {
        throw ApiException('Erreur lors de la modification du résumé.',
            type: ApiExceptionType.validation);
      }
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException(getErrorMessage(e), type: ApiExceptionType.unknown, originalError: e);
    }
  }

  Future<void> validateSummary(int summaryId, bool isValid) async {
    try {
      final response = await _dio.post('/summaries/$summaryId/validate/', data: {
        'is_validated': isValid,
      });
      if (response.statusCode != 200) {
        throw ApiException('Erreur lors de la validation du résumé.',
            type: ApiExceptionType.validation);
      }
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException(getErrorMessage(e), type: ApiExceptionType.unknown, originalError: e);
    }
  }

  Future<Map<String, dynamic>> getSummariesForValidation({String? search}) async {
    try {
      final response = await _dio.get(
        '/summaries/validation/',
        queryParameters: search != null && search.isNotEmpty ? {'search': search} : null,
      );
      if (response.statusCode == 200) {
        return response.data as Map<String, dynamic>;
      }
      throw ApiException('Impossible de charger les résumés en validation.',
          type: ApiExceptionType.server);
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException(getErrorMessage(e), type: ApiExceptionType.unknown, originalError: e);
    }
  }

  Future<Map<String, dynamic>> requestDeleteOtp() async {
    try {
      final response = await _dio.post('/auth/delete-account/request-otp/');
      if (response.statusCode == 200) {
        return response.data as Map<String, dynamic>;
      }
      throw ApiException('Erreur lors de l\'envoi du code.',
          type: ApiExceptionType.server);
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException(getErrorMessage(e), type: ApiExceptionType.unknown, originalError: e);
    }
  }

  Future<void> deleteAccount({required String otpCode, String? reason}) async {
    try {
      final response = await _dio.delete('/auth/delete-account/', data: {
        'otp_code': otpCode,
        'reason': reason ?? '',
      });
      if (response.statusCode != 200) {
        throw ApiException('Erreur lors de la suppression du compte.',
            type: ApiExceptionType.server);
      }
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException(getErrorMessage(e), type: ApiExceptionType.unknown, originalError: e);
    }
  }

  // ─── Cours ──────────────────────────────────────────────────────────

  Future<List<dynamic>> getCourses() async {
    try {
      final response = await _dio.get('/course-list/');
      if (response.statusCode == 200) {
        dynamic data = response.data;
        List<dynamic> coursesList;

        if (data is List) {
          coursesList = data;
        } else if (data is Map) {
          if (data.containsKey('results')) {
            coursesList = data['results'] as List;
          } else if (data.containsKey('data')) {
            coursesList = data['data'] as List;
          } else {
            coursesList = [];
          }
        } else {
          throw ApiException('Format de réponse inattendu.',
              type: ApiExceptionType.server);
        }
        return coursesList;
      }
      throw ApiException('Impossible de charger les cours.',
          type: ApiExceptionType.server);
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException(getErrorMessage(e), type: ApiExceptionType.unknown, originalError: e);
    }
  }

  // ─── Audio ──────────────────────────────────────────────────────────

  Future<Map<String, dynamic>> uploadAudio({
    required Uint8List audioBytes,
    required String fileName,
    required String mimeType,
    Map<String, dynamic>? metadata,
    void Function(int sent, int total)? onSendProgress,
  }) async {
    try {
      final formData = FormData();
      formData.files.add(MapEntry(
        'audio_file',
        MultipartFile.fromBytes(audioBytes, filename: fileName),
      ));
      if (metadata != null) {
        metadata.forEach((key, value) {
          formData.fields.add(MapEntry(key, value.toString()));
        });
      }

      final response = await _dio.post(
        '/courses/sessions/upload-audio/',
        data: formData,
        options: Options(headers: {'Content-Type': 'multipart/form-data'}),
        onSendProgress: onSendProgress != null
            ? (sent, total) => onSendProgress(sent.toInt(), total.toInt())
            : null,
      );

      if (response.statusCode == 201) {
        return {'success': true, 'message': response.data['message'], 'session': response.data['session']};
      }
      throw ApiException('Erreur lors de l\'envoi du fichier audio.',
          type: ApiExceptionType.server);
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException(getErrorMessage(e), type: ApiExceptionType.unknown, originalError: e);
    }
  }

  Future<Map<String, dynamic>> uploadAudioSummary(String audioPath, Map<String, dynamic> metadata) async {
    try {
      final formData = FormData();
      try {
        if (kIsWeb) {
          final bytes = await _getWebAudioBytes(audioPath);
          formData.files.add(MapEntry(
            'audio_file',
            MultipartFile.fromBytes(bytes, filename: 'recording_${DateTime.now().millisecondsSinceEpoch}.wav'),
          ));
        } else {
          formData.files.add(MapEntry('audio_file', await MultipartFile.fromFile(audioPath)));
        }
      } catch (e) {
        throw ApiException('Erreur lors de la lecture du fichier audio.',
            type: ApiExceptionType.unknown);
      }

      formData.fields.add(MapEntry('course_id', metadata['course_id']?.toString() ?? '1'));
      formData.fields.add(MapEntry('title', metadata['title'] ?? 'Enregistrement audio'));

      final response = await _dio.post(
        '/courses/sessions/upload-audio/',
        data: formData,
        options: Options(headers: {'Content-Type': 'multipart/form-data'}),
      );

      if (response.statusCode == 201) {
        return {'success': true, 'message': response.data['message'], 'session': response.data['session']};
      }
      throw ApiException('Erreur lors de l\'envoi du fichier audio.',
          type: ApiExceptionType.server);
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException(getErrorMessage(e), type: ApiExceptionType.unknown, originalError: e);
    }
  }

  Future<List<int>> _getWebAudioBytes(String audioPath) async {
    // Version simplifiée pour le web
    final List<int> wavHeader = [
      0x52, 0x49, 0x46, 0x46, 0x24, 0x00, 0x00, 0x00, 0x57, 0x41, 0x56, 0x45,
      0x66, 0x6D, 0x74, 0x20, 0x10, 0x00, 0x00, 0x00, 0x01, 0x00, 0x01, 0x00,
      0x44, 0xAC, 0x00, 0x00, 0x88, 0x58, 0x01, 0x00, 0x02, 0x00, 0x10, 0x00,
      0x64, 0x61, 0x74, 0x61, 0x00, 0x00, 0x00, 0x00,
    ];
    return [...wavHeader, ...List.filled(1000, 0)];
  }

  Future<List<dynamic>> getAudioSessions() async {
    try {
      final response = await _dio.get('/courses/sessions/');
      if (response.statusCode == 200) {
        dynamic data = response.data;
        if (data is List) return data;
        if (data is Map && data.containsKey('results')) return data['results'] as List;
        throw ApiException('Format de réponse inattendu.', type: ApiExceptionType.server);
      }
      throw ApiException('Impossible de charger les sessions audio.',
          type: ApiExceptionType.server);
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException(getErrorMessage(e), type: ApiExceptionType.unknown, originalError: e);
    }
  }

  Future<List<dynamic>> getAudioSessionsDetailed() async {
    try {
      final response = await _dio.get('/courses/sessions/detailed/');
      if (response.statusCode == 200) return response.data as List<dynamic>;
      throw ApiException('Impossible de charger les sessions audio.',
          type: ApiExceptionType.server);
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException(getErrorMessage(e), type: ApiExceptionType.unknown, originalError: e);
    }
  }

  Future<Map<String, dynamic>> getAudioProcessingStats() async {
    try {
      final response = await _dio.get('/courses/sessions/stats/');
      if (response.statusCode == 200) return response.data as Map<String, dynamic>;
      throw ApiException('Impossible de charger les statistiques.',
          type: ApiExceptionType.server);
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException(getErrorMessage(e), type: ApiExceptionType.unknown, originalError: e);
    }
  }

  Future<Map<String, dynamic>> processAudioSession(int sessionId) async {
    try {
      final response = await _dio.post('/courses/sessions/$sessionId/process-audio/');
      if (response.statusCode == 200) return response.data as Map<String, dynamic>;
      throw ApiException('Impossible de lancer le traitement audio.',
          type: ApiExceptionType.server);
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException(getErrorMessage(e), type: ApiExceptionType.unknown, originalError: e);
    }
  }

  Future<Map<String, dynamic>> retryFailedSession(int sessionId) async {
    try {
      final response = await _dio.post('/courses/sessions/$sessionId/retry/');
      if (response.statusCode == 200) return response.data as Map<String, dynamic>;
      throw ApiException('Impossible de relancer le traitement.',
          type: ApiExceptionType.server);
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException(getErrorMessage(e), type: ApiExceptionType.unknown, originalError: e);
    }
  }

  Future<Map<String, dynamic>> getAudioSessionStatus(int sessionId) async {
    try {
      final response = await _dio.get('/courses/sessions/$sessionId/');
      if (response.statusCode == 200) {
        final data = response.data as Map<String, dynamic>;
        return {'status': data['processing_status'] ?? 'unknown', 'session': data};
      }
      throw ApiException('Impossible de récupérer le statut de la session.',
          type: ApiExceptionType.server);
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException(getErrorMessage(e), type: ApiExceptionType.unknown, originalError: e);
    }
  }

  Future<Map<String, dynamic>> autoProcessPendingSessions() async {
    try {
      final response = await _dio.post('/courses/sessions/auto-process/');
      if (response.statusCode == 200) return response.data as Map<String, dynamic>;
      throw ApiException('Impossible de traiter automatiquement les sessions.',
          type: ApiExceptionType.server);
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException(getErrorMessage(e), type: ApiExceptionType.unknown, originalError: e);
    }
  }

  Future<Map<String, dynamic>> getAudioFileUrl(int sessionId) async {
    try {
      final response = await _dio.get('/courses/sessions/$sessionId/audio-url/');
      if (response.statusCode == 200) return response.data as Map<String, dynamic>;
      throw ApiException('Impossible de récupérer le fichier audio.',
          type: ApiExceptionType.server);
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException(getErrorMessage(e), type: ApiExceptionType.unknown, originalError: e);
    }
  }

  Future<Map<String, dynamic>> getSessionsQueue() async {
    try {
      final response = await _dio.get('/courses/sessions/audio/queue/');
      if (response.statusCode == 200) return response.data as Map<String, dynamic>;
      throw ApiException('Impossible de charger la file d\'attente.',
          type: ApiExceptionType.server);
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException(getErrorMessage(e), type: ApiExceptionType.unknown, originalError: e);
    }
  }

  // ─── Professeurs ────────────────────────────────────────────────────

  Future<List<dynamic>> getProfesseurs() async {
    try {
      final response = await _dio.get('/professeurs/');
      if (response.statusCode == 200) return response.data as List<dynamic>;
      throw ApiException('Impossible de charger les professeurs.',
          type: ApiExceptionType.server);
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException(getErrorMessage(e), type: ApiExceptionType.unknown, originalError: e);
    }
  }

  Future<Map<String, dynamic>> resolveProfessor(int courseId) async {
    try {
      final response = await _dio.get('/courses/resolve-professor/', queryParameters: {
        'course_id': courseId,
      });
      if (response.statusCode == 200) return response.data as Map<String, dynamic>;
      return {'found': false, 'professor': null};
    } catch (e) {
      // Non bloquant : retourne found=false silencieusement
      AppLogger.warning('resolveProfessor error', e.toString());
      return {'found': false, 'professor': null};
    }
  }

  // ─── Achats et Paiements ────────────────────────────────────────────

  /// Page d'achats renvoyée par `/purchases/` (TACHE4 : pagination).
  Future<PurchasesPage> getPurchasedSummaries({
    int page = 1,
    int pageSize = 10,
    String? status,
  }) async {
    try {
      final response = await _dio.get('/purchases/', queryParameters: {
        'page': page,
        'page_size': pageSize,
        if (status != null) 'status': status,
      });
      if (response.statusCode == 200) {
        dynamic data = response.data;
        if (data is Map) {
          final results = (data['results'] as List?) ?? [];
          final count = data['count'] as int? ?? results.length;
          return PurchasesPage(items: results, count: count, page: page, pageSize: pageSize);
        }
        if (data is List) {
          // Ancien format (liste brute) : considéré comme une page complète
          return PurchasesPage(items: data, count: data.length, page: 1, pageSize: data.length);
        }
        throw ApiException('Format de réponse inattendu.', type: ApiExceptionType.server);
      }
      throw ApiException('Impossible de charger les achats.',
          type: ApiExceptionType.server);
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException(getErrorMessage(e), type: ApiExceptionType.unknown, originalError: e);
    }
  }

  /// Charge TOUTES les pages d'achats (badges, compteurs…).
  Future<List<dynamic>> getAllPurchases({String? status}) async {
    final all = <dynamic>[];
    var page = 1;
    while (true) {
      final result = await getPurchasedSummaries(page: page, pageSize: 50, status: status);
      all.addAll(result.items);
      if (!result.hasMore) break;
      page++;
    }
    return all;
  }

  Future<bool> hasPurchasedSummary(int summaryId) async {
    try {
      // Filtre côté serveur (summary_id + status) : rapide même paginé
      final response = await _dio.get('/purchases/', queryParameters: {
        'summary_id': summaryId,
        'status': 'completed',
      });
      if (response.statusCode != 200) return false;
      final data = response.data;
      if (data is Map) {
        return ((data['results'] as List?) ?? []).isNotEmpty;
      }
      if (data is List) return data.isNotEmpty;
      return false;
    } catch (e) {
      return false;
    }
  }

  Future<Map<String, dynamic>> checkPurchaseStatus(String transactionRef) async {
    try {
      final response = await _dio.get('/purchases/check-status/$transactionRef/');
      if (response.statusCode == 200) return response.data as Map<String, dynamic>;
      throw ApiException('Impossible de vérifier le statut du paiement.',
          type: ApiExceptionType.server);
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException(getErrorMessage(e), type: ApiExceptionType.unknown, originalError: e);
    }
  }

  Future<Map<String, dynamic>> initiateSummaryPurchase({
    required int summaryId,
    required String phoneNumber,
  }) async {
    try {
      final response = await _dio.post('/purchases/initiate/', data: {
        'summary_id': summaryId,
        'phone_number': phoneNumber,
      });
      if (response.statusCode == 200 || response.statusCode == 201) {
        return response.data as Map<String, dynamic>;
      }
      throw ApiException('Impossible d\'initier le paiement.',
          type: ApiExceptionType.server);
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException(getErrorMessage(e), type: ApiExceptionType.unknown, originalError: e);
    }
  }

  // ─── Services et Abonnements ────────────────────────────────────────

  Future<List<dynamic>> getServices() async {
    try {
      final response = await _dio.get('/services/');
      if (response.statusCode == 200) return response.data as List<dynamic>;
      throw ApiException('Impossible de charger les services.',
          type: ApiExceptionType.server);
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException(getErrorMessage(e), type: ApiExceptionType.unknown, originalError: e);
    }
  }

  Future<Map<String, dynamic>> initiateSubscriptionPayment(int serviceId, String phoneNumber) async {
    try {
      final response = await _dio.post('/initiate-subscription-payment/', data: {
        'service_id': serviceId,
        'phone_number': phoneNumber,
      });
      if (response.statusCode == 200 || response.statusCode == 201) {
        return response.data as Map<String, dynamic>;
      }
      throw ApiException('Impossible d\'initier le paiement de l\'abonnement.',
          type: ApiExceptionType.server);
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException(getErrorMessage(e), type: ApiExceptionType.unknown, originalError: e);
    }
  }

  Future<void> createSubscriptionAfterPayment(String reference, int serviceId) async {
    try {
      final response = await _dio.post('/create-subscription-after-payment/', data: {
        'transaction_id': reference,
        'service_id': serviceId,
      });
      if (response.statusCode != 200 && response.statusCode != 201) {
        throw ApiException('Erreur lors de la création de l\'abonnement.',
            type: ApiExceptionType.server);
      }
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException(getErrorMessage(e), type: ApiExceptionType.unknown, originalError: e);
    }
  }

  // ─── Exercices ──────────────────────────────────────────────────────

  Future<Map<String, dynamic>> checkExerciseSubscription() async {
    try {
      final response = await _dio.get('/exercises/subscription/check/');
      if (response.statusCode == 200) return response.data as Map<String, dynamic>;
      throw ApiException('Impossible de vérifier votre abonnement aux exercices.',
          type: ApiExceptionType.server);
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException(getErrorMessage(e), type: ApiExceptionType.unknown, originalError: e);
    }
  }

  Future<Map<String, dynamic>> generateExercise(int summaryId, {String? difficulty, bool forceRegenerate = false}) async {
    try {
      final data = <String, dynamic>{};
      if (difficulty != null) data['difficulty'] = difficulty;
      if (forceRegenerate) data['force_regenerate'] = true;

      final response = await _dio.post(
        '/summaries/$summaryId/generate-exercise/',
        data: data.isNotEmpty ? data : null,
      );

      if (response.statusCode == 200 || response.statusCode == 201) {
        return response.data as Map<String, dynamic>;
      }
      throw ApiException('Impossible de générer l\'exercice.',
          type: ApiExceptionType.server);
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException(getErrorMessage(e), type: ApiExceptionType.unknown, originalError: e);
    }
  }

  Future<Map<String, dynamic>> getExercise(int exerciseId) async {
    try {
      final response = await _dio.get('/exercises/$exerciseId/');
      if (response.statusCode == 200) return response.data as Map<String, dynamic>;
      throw ApiException('Exercice introuvable.', type: ApiExceptionType.notFound);
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException(getErrorMessage(e), type: ApiExceptionType.unknown, originalError: e);
    }
  }

  Future<Map<String, dynamic>> submitExercise(int exerciseId, Map<String, String> answers) async {
    try {
      final response = await _dio.post('/exercises/$exerciseId/submit/', data: {'answers': answers});
      if (response.statusCode == 200) return response.data as Map<String, dynamic>;
      throw ApiException('Erreur lors de la soumission de l\'exercice.',
          type: ApiExceptionType.server);
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException(getErrorMessage(e), type: ApiExceptionType.unknown, originalError: e);
    }
  }

  Future<List<dynamic>> getExerciseAttempts() async {
    try {
      final response = await _dio.get('/exercises/attempts/');
      if (response.statusCode == 200) {
        final data = response.data as Map<String, dynamic>;
        return data['attempts'] as List<dynamic>? ?? [];
      }
      throw ApiException('Impossible de charger les tentatives.',
          type: ApiExceptionType.server);
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException(getErrorMessage(e), type: ApiExceptionType.unknown, originalError: e);
    }
  }

  Future<Map<String, dynamic>> getAttemptResult(int attemptId) async {
    try {
      final response = await _dio.get('/exercises/attempts/$attemptId/result/');
      if (response.statusCode == 200) return response.data as Map<String, dynamic>;
      throw ApiException('Impossible de charger le résultat.',
          type: ApiExceptionType.server);
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException(getErrorMessage(e), type: ApiExceptionType.unknown, originalError: e);
    }
  }

  // ─── Notifications ──────────────────────────────────────────────────

  Future<bool> registerFcmToken(String token, {String deviceType = 'android'}) async {
    try {
      await _dio.post('/notifications/devices/register/', data: {
        'fcm_token': token,
        'device_type': deviceType,
      });
      return true;
    } catch (e) {
      AppLogger.error('registerFcmToken error (non bloquant)', e);
      return false;
    }
  }

  Future<bool> unregisterFcmToken(String token) async {
    try {
      await _dio.delete('/notifications/devices/unregister/', data: {'fcm_token': token});
      return true;
    } catch (e) {
      AppLogger.error('unregisterFcmToken error (non bloquant)', e);
      return false;
    }
  }

  Future<Map<String, dynamic>> getNotifications({
    int page = 1,
    int pageSize = 20,
    String search = '',
    String type = '',
    bool unreadOnly = false,
  }) async {
    try {
      final params = <String, dynamic>{
        'page': page,
        'page_size': pageSize,
        if (search.isNotEmpty) 'search': search,
        if (type.isNotEmpty) 'type': type,
        if (unreadOnly) 'unread_only': 'true',
      };
      final response = await _dio.get('/notifications/', queryParameters: params);
      if (response.statusCode == 200) return response.data as Map<String, dynamic>;
      throw ApiException('Impossible de charger les notifications.',
          type: ApiExceptionType.server);
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException(getErrorMessage(e), type: ApiExceptionType.unknown, originalError: e);
    }
  }

  Future<int> getUnreadNotificationCount() async {
    try {
      final response = await _dio.get('/notifications/unread-count/');
      if (response.statusCode == 200) {
        return (response.data as Map<String, dynamic>)['unread_count'] as int? ?? 0;
      }
      return 0;
    } catch (_) {
      return 0; // Non bloquant
    }
  }

  Future<Map<String, dynamic>> getNotificationDetail(int userNotificationId) async {
    try {
      final response = await _dio.get('/notifications/$userNotificationId/');
      if (response.statusCode == 200) return response.data as Map<String, dynamic>;
      throw ApiException('Notification introuvable.', type: ApiExceptionType.notFound);
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException(getErrorMessage(e), type: ApiExceptionType.unknown, originalError: e);
    }
  }

  Future<void> markNotificationRead(int userNotificationId) async {
    try {
      await _dio.post('/notifications/$userNotificationId/read/');
    } catch (e) {
      AppLogger.error('markNotificationRead error (non bloquant)', e);
    }
  }

  Future<void> markAllNotificationsRead() async {
    try {
      await _dio.post('/notifications/mark-all-read/');
    } catch (e) {
      AppLogger.error('markAllNotificationsRead error (non bloquant)', e);
    }
  }

  // ─── Configuration Prix Résumé ────────────────────────────────────

  /// Récupère le prix minimum des résumés depuis le backend.
  /// Cette valeur est configurable dans l'admin Django (ResumePricingConfig).
  /// En cas d'erreur → retourne 3000 (valeur par défaut, ne pas bloquer).
  Future<double> getMinimumResumePrice() async {
    try {
      final response = await _dio.get('/resume-pricing-config/');
      if (response.statusCode == 200 && response.data is Map) {
        final value = (response.data as Map)['minimum_resume_price'];
        if (value != null) {
          return double.tryParse(value.toString()) ?? 3000.0;
        }
      }
    } catch (e) {
      AppLogger.warning('getMinimumResumePrice error', e.toString());
    }
    return 3000.0;
  }

  // ─── Demande pour devenir CP ───────────────────────────────────────

  /// Crée une demande pour devenir CP (uniquement si aucune en attente).
  Future<Map<String, dynamic>> createCPRequest({
    String motivation = '',
    String email = '',
    String phone = '',
  }) async {
    try {
      final data = <String, dynamic>{'motivation': motivation};
      if (email.isNotEmpty) data['email'] = email;
      if (phone.isNotEmpty) data['phone'] = phone;
      final response = await _dio.post('/auth/cp-request/', data: data);
      if (response.statusCode == 201 || response.statusCode == 200) {
        return response.data as Map<String, dynamic>;
      }
      throw ApiException('Erreur lors de l\'envoi de la demande.',
          type: ApiExceptionType.server);
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException(getErrorMessage(e), type: ApiExceptionType.unknown, originalError: e);
    }
  }

  /// Récupère le statut de la demande CP de l'utilisateur connecté.
  Future<Map<String, dynamic>> getCPRequestStatus() async {
    try {
      final response = await _dio.get('/auth/cp-request/status/');
      if (response.statusCode == 200) return response.data as Map<String, dynamic>;
      throw ApiException('Impossible de vérifier le statut de la demande.',
          type: ApiExceptionType.server);
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException(getErrorMessage(e), type: ApiExceptionType.unknown, originalError: e);
    }
  }

  // ─── Onboarding CP ──────────────────────────────────────────────────

  /// Termine l'onboarding CP de manière ATOMIQUE : le backend crée le
  /// professeur + le cours + l'association (Dispense) en une seule transaction,
  /// puis marque l'onboarding comme terminé. Aucune création partielle.
  Future<void> completeCPOnboarding({
    required String professeurNom,
    required String professeurTelephone,
    required String professeurSpecialite,
    required String coursNom,
    String coursDescription = '',
  }) async {
    try {
      await _dio.post('/onboarding/complete-cp/', data: {
        'professeur_nom': professeurNom,
        'professeur_telephone': professeurTelephone,
        'professeur_specialite': professeurSpecialite,
        'cours_nom': coursNom,
        'cours_description': coursDescription,
      });
    } catch (e) {
      // L'appel est bloquant ici : en cas d'échec, rien n'a été créé côté
      // backend (transaction atomique) → l'utilisateur peut réessayer.
      AppLogger.warning('completeCPOnboarding error', e.toString());
      rethrow;
    }
  }

  Future<Map<String, dynamic>> getOnboardingStatus() async {
    try {
      final response = await _dio.get('/onboarding/status/');
      if (response.statusCode == 200) return response.data as Map<String, dynamic>;
      throw ApiException('Impossible de vérifier l\'état du onboarding.',
          type: ApiExceptionType.server);
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException(getErrorMessage(e), type: ApiExceptionType.unknown, originalError: e);
    }
  }

  Future<Map<String, dynamic>> createProfesseurSimple({
    required String nomComplet,
    required String telephone,
    required String specialite,
    bool isOnboarding = false,
  }) async {
    try {
      final data = <String, dynamic>{
        'nom_complet': nomComplet,
        'telephone': telephone,
        'specialite': specialite,
      };
      if (isOnboarding) data['is_onboarding'] = true;

      final response = await _dio.post('/professeurs/create-simple/', data: data);
      if (response.statusCode == 200 || response.statusCode == 201) {
        return response.data as Map<String, dynamic>;
      }
      throw ApiException('Erreur lors de la création du professeur.',
          type: ApiExceptionType.server);
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException(getErrorMessage(e), type: ApiExceptionType.unknown, originalError: e);
    }
  }

  Future<Map<String, dynamic>> createCourse({
    required String nom,
    String? description,
    bool isOnboarding = false,
  }) async {
    try {
      final data = <String, dynamic>{
        'nom': nom,
        if (description != null && description.isNotEmpty) 'description': description,
      };
      if (isOnboarding) data['is_onboarding'] = true;

      final response = await _dio.post('/course-list/', data: data);
      if (response.statusCode == 200 || response.statusCode == 201) {
        return response.data as Map<String, dynamic>;
      }
      throw ApiException('Erreur lors de la création du cours.',
          type: ApiExceptionType.server);
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException(getErrorMessage(e), type: ApiExceptionType.unknown, originalError: e);
    }
  }

  Future<Map<String, dynamic>> createDispense({
    required int professeurId,
    required int coursId,
  }) async {
    try {
      final response = await _dio.post('/dispenses/create/', data: {
        'professeur_id': professeurId,
        'cours_id': coursId,
      });
      if (response.statusCode == 200 || response.statusCode == 201) {
        return response.data as Map<String, dynamic>;
      }
      throw ApiException('Erreur lors de la création de l\'association.',
          type: ApiExceptionType.server);
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException(getErrorMessage(e), type: ApiExceptionType.unknown, originalError: e);
    }
  }

  Future<void> deleteProfesseur(int professeurId) async {
    try {
      await _dio.delete('/courses/professeurs/$professeurId/delete/');
    } catch (e) {
      throw ApiException(getErrorMessage(e), type: ApiExceptionType.unknown, originalError: e);
    }
  }

  Future<void> deleteCourse(int courseId) async {
    try {
      await _dio.delete('/courses/$courseId/');
    } catch (e) {
      throw ApiException(getErrorMessage(e), type: ApiExceptionType.unknown, originalError: e);
    }
  }

  Future<List<dynamic>> listDispenses() async {
    try {
      final response = await _dio.get('/courses/dispenses/');
      if (response.statusCode == 200) return response.data as List<dynamic>;
      return [];
    } catch (e) {
      AppLogger.error('listDispenses error', e);
      throw ApiException(getErrorMessage(e), type: ApiExceptionType.unknown, originalError: e);
    }
  }

  Future<void> deleteDispense(int dispenseId) async {
    try {
      await _dio.delete('/courses/dispenses/$dispenseId/delete/');
    } catch (e) {
      throw ApiException(getErrorMessage(e), type: ApiExceptionType.unknown, originalError: e);
    }
  }

  // ═══════════════════════════════════════════════════════════════════════════════
  //  EXERCICES PERSONNALISÉS (QCM uniques par utilisateur avec difficulté)
  // ═══════════════════════════════════════════════════════════════════════════════

  /// Vérifie si un exercice personnalisé existe déjà pour ce résumé.
  /// [difficulty] (optionnel) : ne vérifie QUE ce niveau — c'est la règle
  /// « Utilisateur + Résumé + Niveau = un exercice unique ».
  Future<Map<String, dynamic>> checkPersonalizedExercise(
    int summaryId, {
    String? difficulty,
  }) async {
    try {
      final response = await _dio.get(
        '/courses/summaries/$summaryId/personalized-exercise/check/',
        queryParameters: difficulty != null ? {'difficulty': difficulty} : null,
      );
      return response.data as Map<String, dynamic>;
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  /// Génère un exercice personnalisé avec niveau de difficulté
  Future<Map<String, dynamic>> generatePersonalizedExercise({
    required int summaryId,
    required String difficulty, // 'easy', 'medium', 'hard'
    bool regenerate = false,
  }) async {
    try {
      final response = await _dio.post(
        '/courses/summaries/$summaryId/personalized-exercise/generate/',
        data: {
          'difficulty': difficulty,
          'regenerate': regenerate,
        },
      );
      return response.data as Map<String, dynamic>;
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  /// Récupère un exercice personnalisé avec ses questions (polling possible)
  Future<Map<String, dynamic>> getPersonalizedExercise(int exerciseId) async {
    try {
      final response = await _dio.get(
        '/courses/personalized-exercises/$exerciseId/',
      );
      return response.data as Map<String, dynamic>;
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  /// Soumet les réponses et récupère le score
  Future<Map<String, dynamic>> submitPersonalizedExercise({
    required int exerciseId,
    required Map<String, String> answers, // {"0": "A", "1": "B", ...}
  }) async {
    try {
      final response = await _dio.post(
        '/courses/personalized-exercises/$exerciseId/submit/',
        data: {'answers': answers},
      );
      return response.data as Map<String, dynamic>;
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  /// Récupère l'historique des tentatives
  Future<Map<String, dynamic>> getPersonalizedExerciseAttempts({
    int? summaryId,
  }) async {
    try {
      final params = summaryId != null ? {'summary_id': summaryId} : null;
      final response = await _dio.get(
        '/courses/personalized-exercises/attempts/',
        queryParameters: params,
      );
      return response.data as Map<String, dynamic>;
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  /// Récupère le détail d'une tentative avec corrections
  Future<Map<String, dynamic>> getPersonalizedAttemptDetail(int attemptId) async {
    try {
      final response = await _dio.get(
        '/courses/personalized-exercises/attempts/$attemptId/',
      );
      return response.data as Map<String, dynamic>;
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  Exception _handleError(DioException e) {
    if (e.response?.statusCode == 403) {
      final data = e.response?.data as Map<String, dynamic>?;
      if (data?['code'] == 'subscription_required') {
        return ApiException(
          'Abonnement requis pour accéder aux exercices',
          type: ApiExceptionType.forbidden,
          statusCode: 403,
        );
      }
      if (data?['code'] == 'purchase_required') {
        return ApiException(
          "Vous devez d'abord acheter ce résumé pour accéder au QCM",
          type: ApiExceptionType.forbidden,
          statusCode: 403,
        );
      }
    }
    return ApiException(
      e.message ?? 'Une erreur est survenue',
      type: ApiExceptionType.unknown,
      statusCode: e.response?.statusCode,
    );
  }
}

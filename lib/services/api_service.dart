import 'dart:async';
import 'dart:typed_data';
import 'package:dio/dio.dart';
import 'package:uuid/uuid.dart';
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

  // Upload audio (fichiers longs, limite métier 3 h) — voir uploadAudio() :
  // le garde-fou anti-blocage annule la requête si plus aucun octet n'est
  // transmis pendant ce délai (liaison réellement coupée en plein envoi).
  // 60 s → 5 min → 30 MINUTES (2026-10-16), LA CAUSE RÉELLE DE L'ÉCHEC.
  //
  // CE GARDE-FOU MESURE LA DURÉE TOTALE DE L'ENVOI, PAS UNE PANNE.
  //
  // Dio rapporte la progression quand il remet le corps à la couche HTTP de
  // Dart. Pour un corps gardé en mémoire (`MultipartFile.fromBytes`), il le
  // remet d'un coup : la progression bondit près du total, puis plus rien
  // jusqu'à ce que le socket se vide. Le minuteur, armé une seule fois, court
  // donc pendant TOUT le transfert — et annule un envoi parfaitement sain qui
  // dépasse la fenêtre.
  //
  // LA PREUVE, chiffrée : le même fichier de 65 Mo, envoyé par curl en dehors
  // du serveur, aboutit en **306,9 s** (HTTP 401, corps entièrement reçu).
  // L'application, elle, s'arrêtait à **300 s** avec 33 octets manquants —
  // soit le même trajet, à la même vitesse (~215 Ko/s), six secondes trop tôt.
  // Le serveur n'a jamais failli : c'est cette fenêtre qui était trop courte.
  //
  // 30 minutes couvrent la limite métier (3 h d'audio, ~170 Mo) au débit
  // observé. Contrepartie assumée : une liaison réellement morte n'est
  // signalée qu'au bout de 30 minutes.
  //
  // AMÉLIORATION DURABLE À PRÉVOIR : envoyer le fichier depuis le disque
  // (`MultipartFile.fromFile`) plutôt qu'en mémoire. La progression suivrait
  // alors le réseau — le système ne pouvant pas tamponner 65 Mo — et une
  // fenêtre courte redeviendrait un vrai détecteur de panne.
  static const Duration _uploadStallLimit = Duration(minutes: 30);

  // NOMBRE DE TENTATIVES POUR UN ENVOI (tâche 40, étape C). Une liaison mobile
  // qui lâche, un écran verrouillé, un changement de réseau : trois essais
  // couvrent ces cas sans transformer une erreur métier en acharnement. Chaque
  // essai renvoie LA MÊME clé d'idempotence, donc aucun doublon n'est possible.
  static const int _uploadMaxTentatives = 3;
  // Fenêtre d'attente de la réponse serveur après envoi complet du corps.
  static const Duration _uploadResponseTimeout = Duration(minutes: 10);

  List<Universite>? _cachedUniversites;
  Map<int, List<Filiere>> _cachedFilieresByUniversite = {};
  Map<int, List<Promotion>> _cachedPromotionsByFiliere = {};

  ApiService({Dio? dio, StorageService? storageService})
      : _dio = dio ?? Dio(BaseOptions(
          baseUrl: baseUrl,
          // Timeouts indispensables : sans eux, une requête vers un serveur
          // lent/indisponible attend INDÉFINIMENT (app figée au démarrage /
          // blocage à la vérification OTP, sans message d'erreur).
          // connectTimeout PORTÉ DE 10 s À 30 s (2026-10-15) : dans Dio 5 il
          // n'existe que sur BaseOptions, donc la requête d'upload ne peut pas
          // le surcharger. Or c'était le SEUL délai court restant sur cet envoi
          // — sendTimeout y est neutralisé et receiveTimeout porté à 10 minutes.
          // Sur un réseau mobile, ouvrir la connexion (radio, TLS) peut à lui
          // seul dépasser dix secondes. 30 s reste une borne : au-delà, le
          // serveur est réellement injoignable.
          connectTimeout: const Duration(seconds: 30),
          sendTimeout: const Duration(seconds: 15),
          receiveTimeout: const Duration(seconds: 20),
        )),
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

      // ERREUR DE CHAMP — ex. {"nom": ["Le cours « X » existe déjà…"]}.
      //
      // Une ValidationError de DRF sur un champ porte la clé DU CHAMP, pas
      // `detail` : sans ce repli, un refus parfaitement explicite du serveur
      // (doublon de cours, par exemple) s'affichait à l'écran comme « une
      // erreur inattendue ». On prend la première valeur lisible de la réponse.
      for (final valeur in data.values) {
        if (valeur is String && valeur.isNotEmpty) return valeur;
        if (valeur is List && valeur.isNotEmpty) return valeur.first.toString();
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
      // On ne détruit les jetons QUE si le serveur a réellement rejeté le
      // refresh (400/401/403 → jeton invalide ou blacklisté). Une panne réseau,
      // un timeout ou une 5xx ne disent RIEN de la validité de la session :
      // effacer les jetons dans ce cas transformait une simple perte de
      // connexion en déconnexion définitive.
      if (_isRefreshRejected(e)) {
        await _invalidateTokens();
      }
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

  /// Le serveur a-t-il explicitement rejeté le refresh token ?
  ///
  /// Seul ce cas autorise la suppression des jetons stockés. Un échec réseau
  /// n'est pas un rejet.
  bool _isRefreshRejected(Object error) {
    if (error is DioException) {
      final code = error.response?.statusCode;
      return code == 400 || code == 401 || code == 403;
    }
    if (error is ApiException) {
      // `noRefreshToken` : rien à conserver de toute façon.
      // `refreshFailed` : le serveur a répondu autre chose que 200.
      return error.type == ApiExceptionType.noRefreshToken ||
          error.type == ApiExceptionType.refreshFailed;
    }
    return false;
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
      // Conserver le TYPE d'origine : c'est lui qui permet aux appelants de
      // distinguer une session réellement rejetée (401 → unauthorized) d'une
      // simple panne réseau. Sans cela, tout devenait `unknown` et
      // l'authentification traitait une perte de connexion comme une
      // déconnexion (jetons effacés).
      if (e is DioException) throw ApiException.fromDioException(e);
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

  /// Supprime un résumé encore EN ATTENTE de validation (CP / Admin).
  /// Le backend refuse la suppression d'un résumé validé ou lié à des achats
  /// et renvoie alors un message métier explicite, remonté tel quel.
  Future<void> deleteSummary(int summaryId) async {
    try {
      final response = await _dio.delete('/summaries/$summaryId/delete/');
      if (response.statusCode != 200) {
        throw ApiException('Erreur lors de la suppression du résumé.',
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

  /// Upload d'une session audio (enregistrement natif OU fichier importé).
  ///
  /// Les timeouts globaux de l'[ApiService] (10/15/20 s) sont adaptés aux
  /// requêtes courtes (OTP, profil…), mais le `sendTimeout` de 15 s borne
  /// l'ÉCRITURE COMPLÈTE du corps : tout fichier volumineux (audio d'1 h,
  /// limite métier 3 h) est coupé avant la fin de l'envoi sur un réseau
  /// mobile, d'où le message « délai de connexion expiré » — alors que la
  /// connexion est saine. C'est l'upload des fichiers importés qui échoue,
  /// pas l'enregistrement natif (petit m4a envoyé en quelques secondes).
  ///
  /// Ici, pour CETTE requête uniquement :
  ///  * `sendTimeout` est neutralisé (corps envoyé en continu aussi
  ///    longtemps que nécessaire pour un fichier de plusieurs heures) ;
  ///  * un garde-fou anti-blocage remplace le cap en temps : si plus aucun
  ///    octet n'est transmis pendant [_uploadStallLimit], on annule
  ///    proprement la requête (liaison réellement coupée en plein envoi) ;
  ///  * `receiveTimeout` est élargi pour laisser au serveur le temps de
  ///    stocker le fichier et répondre après réception complète du corps.
  Future<Map<String, dynamic>> uploadAudio({
    required Uint8List audioBytes,
    String? audioFilePath,
    required String fileName,
    required String mimeType,
    Map<String, dynamic>? metadata,
    void Function(int sent, int total)? onSendProgress,
    String? idempotenceKey,
  }) async {
    // Garde-fou : chaque octet transmis relance le délai ; il est désarmé dès
    // que le corps est entièrement envoyé (le receiveTimeout prend le relais
    // pour l'attente de la réponse serveur).
    var cancelToken = CancelToken();
    Timer? stallTimer;
    var sendCompleted = false;

    // CE QUI A ÉTÉ TRANSMIS, ET DEPUIS QUAND (diagnostic 2026-10-15).
    //
    // Le serveur est mis hors de cause : un POST de 5 Mo limité à 100 Ko/s
    // (50 s d'envoi) y passe sans erreur. Reste à savoir QUI ferme la
    // connexion en plein envoi — l'application, ou la plateforme. Ces trois
    // valeurs le disent :
    //   • 0 octet transmis            → la requête n'est jamais partie
    //     (connexion, TLS, réseau) ;
    //   • quelques centaines de Ko    → l'envoi a commencé puis s'est arrêté ;
    //   • total atteint               → tout est parti, l'échec est après.
    // Et le temps écoulé distingue le garde-fou anti-blocage (60 s) de toute
    // autre cause, plus rapide.
    var octetsTransmis = 0;
    var octetsTotal = 0;
    var annuleParGardeFou = false;
    final debutEnvoi = DateTime.now();

    Duration ecoule() => DateTime.now().difference(debutEnvoi);

    void armStallGuard() {
      stallTimer?.cancel();
      stallTimer = Timer(_uploadStallLimit, () {
        annuleParGardeFou = true;
        cancelToken.cancel('garde-fou');
      });
    }

    void handleSendProgress(int sent, int total) {
      octetsTransmis = sent;
      octetsTotal = total;
      if (!sendCompleted) {
        if (total > 0 && sent >= total) {
          // Corps entièrement envoyé : on attend désormais la réponse.
          sendCompleted = true;
          stallTimer?.cancel();
          stallTimer = null;
        } else {
          // Avancée (ou premier octet) : on relance le compteur anti-blocage.
          armStallGuard();
        }
      }
      onSendProgress?.call(sent, total);
    }

    try {
      final formData = FormData();

      // ENVOYER DEPUIS LE FICHIER QUAND IL EXISTE (2026-10-16).
      //
      // La progression de Dio compte ce qu'il remet à la couche HTTP de Dart.
      // Avec un corps en mémoire (`fromBytes`), il le remet d'un bloc : la
      // progression bondit près du total, puis se tait jusqu'à ce que le socket
      // se vide. Le garde-fou anti-blocage mesurait donc la DURÉE TOTALE de
      // l'envoi au lieu d'une panne — un fichier de 65 Mo a été coupé à 300 s
      // alors que le MÊME fichier aboutissait en 306,9 s par curl.
      //
      // Lu depuis le disque, le corps ne peut PAS être tamponné en entier : la
      // lecture avance au rythme du réseau, la progression suit la liaison, et
      // le garde-fou retrouve son rôle — signaler une liaison morte.
      // L'application y gagne aussi tout le poids du fichier en mémoire.
      var audioJoint = false;
      if (audioFilePath != null && audioFilePath.isNotEmpty) {
        try {
          formData.files.add(MapEntry(
            'audio_file',
            await MultipartFile.fromFile(audioFilePath, filename: fileName),
          ));
          audioJoint = true;
        } catch (_) {
          // Fichier disparu ou illisible, ou plateforme sans accès au disque
          // (web) : on retombe sur les octets, exactement comme avant.
        }
      }
      if (!audioJoint) {
        formData.files.add(MapEntry(
          'audio_file',
          MultipartFile.fromBytes(audioBytes, filename: fileName),
        ));
      }
      if (metadata != null) {
        metadata.forEach((key, value) {
          formData.fields.add(MapEntry(key, value.toString()));
        });
      }

      // CLÉ D'IDEMPOTENCE (tâche 40, étape C). Elle est produite UNE fois pour
      // cette tentative d'envoi et renvoyée à l'identique à chaque reprise : le
      // serveur y reconnaît un envoi déjà enregistré et rend SA session au lieu
      // d'en créer une seconde. Sans elle, une réponse perdue après un
      // verrouillage d'écran produirait un doublon.
      final cleIdempotence = (idempotenceKey != null && idempotenceKey.isNotEmpty)
          ? idempotenceKey
          : const Uuid().v4();
      formData.fields.add(MapEntry('idempotence_key', cleIdempotence));

      // REPRISE AUTOMATIQUE (tâche 40, étape C).
      //
      // Un envoi de plusieurs mégaoctets peut être coupé par un verrouillage
      // d'écran, un changement de réseau ou une liaison qui lâche. Jusqu'ici,
      // cela condamnait l'envoi : l'utilisateur devait relancer à la main, et
      // risquait un doublon côté serveur.
      //
      // On rejoue donc la MÊME tentative — même clé d'idempotence, donc aucun
      // doublon possible — avec une attente croissante. Sur iOS, l'attente est
      // suspendue avec l'application et reprend au déverrouillage : l'envoi
      // repart de lui-même, sans que l'utilisateur ait rien à faire.
      late Response<dynamic> response;
      for (var essai = 1; ; essai++) {
        // UN JETON NEUF À CHAQUE TENTATIVE : un jeton annulé le reste, et le
        // garde-fou de la tentative précédente aurait donc condamné toutes les
        // suivantes. On repart aussi d'une progression vierge, pour que le
        // message d'erreur décrive la tentative en cours et non l'ancienne.
        cancelToken = CancelToken();
        sendCompleted = false;
        octetsTransmis = 0;
        octetsTotal = 0;
        annuleParGardeFou = false;
        try {
          response = await _dio.post(
            '/courses/sessions/upload-audio/',
            data: formData,
            options: Options(
              headers: {'Content-Type': 'multipart/form-data'},
              // sendTimeout : 0 = désactivé pour cette requête (géré par le
              // garde-fou). connectTimeout, lui, n'est PAS réglable ici : dans
              // Dio 5 il n'existe que sur BaseOptions, donc il se règle sur
              // l'instance entière (voir connectTimeout plus haut).
              sendTimeout: Duration.zero,
              receiveTimeout: _uploadResponseTimeout,
            ),
            cancelToken: cancelToken,
            onSendProgress: handleSendProgress,
          );
          break;
        } catch (e) {
          if (essai >= _uploadMaxTentatives || !_envoiMeriteReprise(e)) {
            rethrow;
          }
          final attente = Duration(seconds: essai == 1 ? 5 : 20);
          stallTimer?.cancel();
          stallTimer = null;
          debugPrint(
            '↻ Envoi interrompu (tentative $essai/$_uploadMaxTentatives) : '
            'nouvelle tentative dans ${attente.inSeconds} s, '
            'clé $cleIdempotence.',
          );
          await Future.delayed(attente);
        }
      }

      if (response.statusCode == 201) {
        return {'success': true, 'message': response.data['message'], 'session': response.data['session']};
      }
      throw ApiException('Erreur lors de l\'envoi du fichier audio.',
          type: ApiExceptionType.server);
    } catch (e) {
      if (e is ApiException) rethrow;
      if (e is DioException && e.type == DioExceptionType.cancel) {
        // LE MESSAGE DIT MAINTENANT COMBIEN D'OCTETS SONT PARTIS, ET EN COMBIEN
        // DE TEMPS. C'est ce qui distingue les causes, qui étaient jusqu'ici
        // confondues derrière « plus aucune donnée transmise » :
        //   • « 0 / 3 000 000 »  → la requête n'est jamais partie ;
        //   • « 850 000 / 3 000 000 » → l'envoi a commencé puis s'est arrêté ;
        //   • « 3 000 000 / 3 000 000 » → tout est parti, l'échec est après.
        // Et « garde-fou » signale les 60 s sans progression — sans ce mot,
        // l'annulation vient d'ailleurs.
        final transmis = octetsTotal > 0
            ? '$octetsTransmis / $octetsTotal octets'
            : '$octetsTransmis octets';
        final motif = annuleParGardeFou
            ? 'garde-fou : ${_uploadStallLimit.inSeconds} s sans progression'
            : 'cause inconnue';
        throw ApiException(
          'L\'envoi du fichier a été interrompu ($motif) — $transmis '
          'transmis en ${ecoule().inSeconds} s. '
          'Vérifiez votre connexion et réessayez.',
          type: ApiExceptionType.network,
          originalError: e,
        );
      }
      throw ApiException(getErrorMessage(e), type: ApiExceptionType.unknown, originalError: e);
    } finally {
      stallTimer?.cancel();
    }
  }

  /// Télécharge un fichier du serveur et renvoie ses octets.
  ///
  /// POURQUOI NE PAS CONFIER L'URL AU LECTEUR : `audioplayers` remet l'URL à
  /// AVPlayer (iOS), qui n'envoie AUCUN en-tête — ni jeton d'authentification,
  /// ni origine. Et quand la réponse ne lui convient pas — fichier absent, page
  /// d'erreur HTML, redirection, absence de support des requêtes « Range » — il
  /// ne dit rien d'autre que :
  ///
  ///   AVPlayerItem.Status.failed on setSourceUrl: Unknown error, null
  ///
  /// Impossible d'en déduire quoi que ce soit. En passant par Dio, la requête
  /// porte le jeton de l'application et les mêmes délais que le reste de l'API,
  /// et un échec devient un vrai code HTTP, affichable à l'utilisateur.
  /// Une erreur qui MÉRITE d'être rejouée.
  ///
  /// Liaison coupée, délai dépassé, serveur en erreur : la même tentative peut
  /// aboutir. En revanche une erreur MÉTIER — fichier refusé, accès interdit,
  /// requête invalide — donnerait exactement le même résultat : la rejouer ne
  /// ferait que retarder le message à l'utilisateur.
  static bool _envoiMeriteReprise(Object e) {
    if (e is ApiException) {
      return e.type == ApiExceptionType.network ||
          e.type == ApiExceptionType.timeout ||
          e.type == ApiExceptionType.server;
    }
    // Erreur brute de Dio (connexion interrompue, réponse jamais reçue) : c'est
    // précisément le cas d'un verrouillage d'écran en plein envoi.
    return e is DioException;
  }

  Future<Uint8List> telechargerFichier(String url) async {
    final reponse = await _dio.get<List<int>>(
      url,
      options: Options(
        responseType: ResponseType.bytes,
        receiveTimeout: const Duration(minutes: 5),
      ),
    );
    return Uint8List.fromList(reponse.data ?? const <int>[]);
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

  /// Résumés réellement ACHETÉS, dédupliqués (endpoint `/summaries/achetes/`).
  ///
  /// Le serveur ne renvoie qu'une entrée par résumé (statut completed), même si
  /// plusieurs transactions complétées existent en base. Chaque entrée est un
  /// objet `Summary` (sérialisé), pas une ligne `Purchase`.
  Future<PurchasesPage> getAchetesSummaries({
    int page = 1,
    int pageSize = 10,
  }) async {
    try {
      final response = await _dio.get('/summaries/achetes/', queryParameters: {
        'page': page,
        'page_size': pageSize,
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
      throw ApiException('Impossible de charger les résumés achetés.',
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
  ///
  /// [timeSpentSeconds] : durée réellement passée sur l'exercice, mesurée par
  /// le chronomètre de l'écran de quiz. Elle doit être envoyée par le client :
  /// côté serveur la tentative est créée à la soumission même, donc la durée
  /// calculable y est nulle. Omise, le temps enregistré reste 0.
  Future<Map<String, dynamic>> submitPersonalizedExercise({
    required int exerciseId,
    required Map<String, String> answers, // {"0": "A", "1": "B", ...}
    int? timeSpentSeconds,
  }) async {
    try {
      final response = await _dio.post(
        '/courses/personalized-exercises/$exerciseId/submit/',
        data: {
          'answers': answers,
          if (timeSpentSeconds != null) 'time_spent_seconds': timeSpentSeconds,
        },
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

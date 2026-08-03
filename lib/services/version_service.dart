import 'dart:math';
import 'package:flutter/foundation.dart';
import 'package:package_info_plus/package_info_plus.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:dio/dio.dart';
import 'api_service.dart';

// ─── Résultat de la vérification de version ────────────────────────

/// Résultat de la vérification de version côté client.
enum VersionCheckResult {
  /// Mode maintenance activé → bloquer avec le message de maintenance
  maintenance,

  /// Mise à jour obligatoire (version installée < minimum_version)
  /// → bloquer avec bouton "Mettre à jour" vers le store
  mandatory,

  /// Mise à jour suggérée (minimum <= installée < latest)
  /// → dialogue informatif, l'utilisateur peut continuer
  optional,

  /// Version à jour (installée >= latest) → aucune action
  upToDate,

  /// API inaccessible ou erreur réseau → ne pas bloquer, skip
  error,
}

/// Données retournées par l'API /api/app-version/
class AppVersionConfig {
  final String latestVersion;
  final String minimumVersion;
  final bool forceUpdate;
  final bool maintenanceMode;
  final String maintenanceMessage;
  final String playStoreUrl;
  final String appStoreUrl;
  final String mandatoryUpdateMessage;
  final String platform;

  AppVersionConfig({
    required this.latestVersion,
    required this.minimumVersion,
    required this.forceUpdate,
    required this.maintenanceMode,
    required this.maintenanceMessage,
    required this.playStoreUrl,
    required this.appStoreUrl,
    required this.mandatoryUpdateMessage,
    required this.platform,
  });

  factory AppVersionConfig.fromJson(Map<String, dynamic> json) {
    return AppVersionConfig(
      latestVersion: json['latest_version'] as String? ?? '1.0.0',
      minimumVersion: json['minimum_version'] as String? ?? '1.0.0',
      forceUpdate: json['force_update'] as bool? ?? false,
      maintenanceMode: json['maintenance_mode'] as bool? ?? false,
      maintenanceMessage: json['maintenance_message'] as String? ?? '',
      playStoreUrl: json['play_store_url'] as String? ?? '',
      appStoreUrl: json['app_store_url'] as String? ?? '',
      mandatoryUpdateMessage: json['mandatory_update_message'] as String? ?? '',
      platform: json['platform'] as String? ?? 'unknown',
    );
  }
}

// ─── Service de vérification de version ────────────────────────────

/// Service singleton de vérification et de mise à jour de l'application.
///
/// Appelé au démarrage depuis [SplashScreen]. Compare la version installée
/// avec la configuration serveur et décide de l'action à prendre.
///
/// ## Cas d'usage
/// - `maintenance`  → écran plein écran avec message
/// - `mandatory`    → écran plein écran avec bouton store (version < minimum)
/// - `optional`     → simple dialogue (min <= version < latest)
/// - `upToDate`     → rien
/// - `error`        → skip (API down), pas de blocage
class VersionService {
  // ─── Singleton ──────────────────────────────────────────────────
  static final VersionService _instance = VersionService._internal();
  factory VersionService() => _instance;
  VersionService._internal();

  // ─── État interne ──────────────────────────────────────────────
  AppVersionConfig? _cachedConfig;
  DateTime? _lastFetch;
  static const Duration _cacheDuration = Duration(minutes: 30);

  // ─── Comparateur de versions (semver) ───────────────────────────

  /// Compare deux chaînes de version au format X.Y.Z.
  ///
  /// Retourne :
  ///   -1 si [a] < [b]
  ///    0 si [a] == [b]
  ///    1 si [a] > [b]
  ///
  /// Gère correctement les segments multi-chiffres (1.9.0 < 1.10.0).
  int _compareVersions(String a, String b) {
    final partsA = a.split('.').map((e) => int.tryParse(e) ?? 0).toList();
    final partsB = b.split('.').map((e) => int.tryParse(e) ?? 0).toList();

    // Normaliser les longueurs (1.0 → 1.0.0)
    final maxLen = max(partsA.length, partsB.length);
    while (partsA.length < maxLen) {
      partsA.add(0);
    }
    while (partsB.length < maxLen) {
      partsB.add(0);
    }

    for (int i = 0; i < maxLen; i++) {
      if (partsA[i] < partsB[i]) return -1;
      if (partsA[i] > partsB[i]) return 1;
    }
    return 0;
  }

  // ─── Récupération de la config serveur ──────────────────────────

  /// Récupère la configuration de version depuis l'API.
  ///
  /// Le résultat est mis en cache 30 minutes.
  /// En cas d'erreur réseau, retourne `null` (pas de blocage).
  Future<AppVersionConfig?> _fetchConfig() async {
    // Cache valide
    if (_cachedConfig != null &&
        _lastFetch != null &&
        DateTime.now().difference(_lastFetch!) < _cacheDuration) {
      return _cachedConfig;
    }

    try {
      final dio = Dio(BaseOptions(
        baseUrl: ApiService.baseUrl,
        connectTimeout: const Duration(seconds: 8),
        receiveTimeout: const Duration(seconds: 8),
      ));

      final response = await dio.get('/app-version/');

      if (response.statusCode == 200 && response.data is Map) {
        _cachedConfig = AppVersionConfig.fromJson(response.data as Map<String, dynamic>);
        _lastFetch = DateTime.now();
        print('✅ VersionService: config récupérée: '
            'latest=${_cachedConfig!.latestVersion}, '
            'min=${_cachedConfig!.minimumVersion}');
        return _cachedConfig;
      }
    } catch (e) {
      // Erreur réseau ou timeout → pas de blocage, on skip
      print('⚠️ VersionService: API inaccessible: $e');
    }

    return null;
  }

  // ─── Vérification principale ────────────────────────────────────

  /// Vérifie la version installée contre la configuration serveur.
  ///
  /// À appeler UNE SEULE FOIS au démarrage de l'application.
  /// La logique est protégée contre les timeouts (5s max).
  Future<VersionCheckResult> checkVersion() async {
    try {
      // 1) Version installée via package_info_plus
      final packageInfo = await PackageInfo.fromPlatform().timeout(
        const Duration(seconds: 3),
        onTimeout: () {
          print('⏱️ VersionService: timeout package_info_plus');
          return PackageInfo(
            appName: 'Résumé+',
            packageName: 'com.resumeplus.app',
            version: '1.0.0',
            buildNumber: '1',
            buildSignature: '',
            installerStore: '',
          );
        },
      );

      final installedVersion = packageInfo.version;
      print('📱 VersionService: installée v$installedVersion');

      // 2) Config serveur
      final config = await _fetchConfig();
      if (config == null) {
        print('⚠️ VersionService: pas de config, skip');
        return VersionCheckResult.error;
      }

      // 3) Mode maintenance
      if (config.maintenanceMode) {
        print('🛑 VersionService: MODE MAINTENANCE');
        return VersionCheckResult.maintenance;
      }

      // 4) Comparaison
      final cmpMin = _compareVersions(installedVersion, config.minimumVersion);
      final cmpLatest = _compareVersions(installedVersion, config.latestVersion);

      if (cmpMin < 0 && config.forceUpdate) {
        // installée < minimum + force active → MAJ OBLIGATOIRE
        print('📲 VersionService: MAJ OBLIGATOIRE '
            '(v$installedVersion < v${config.minimumVersion})');
        return VersionCheckResult.mandatory;
      }

      if (cmpLatest < 0) {
        // installée < latest → MAJ SUGGÉRÉE
        print('📲 VersionService: MAJ SUGGÉRÉE '
            '(v$installedVersion < v${config.latestVersion})');
        return VersionCheckResult.optional;
      }

      // installée >= latest → à jour
      print('✅ VersionService: à jour');
      return VersionCheckResult.upToDate;
    } catch (e) {
      print('❌ VersionService: erreur vérification: $e');
      return VersionCheckResult.error;
    }
  }

  /// Retourne la config récupérée (utilisée par l'écran de force update).
  AppVersionConfig? get config => _cachedConfig;

  // ─── Ouverture des stores ───────────────────────────────────────

  /// Ouvre la page de l'application sur le store approprié.
  ///
  /// Détecte la plateforme via [defaultTargetPlatform] (Flutter natif)
  /// plutôt que la valeur renvoyée par l'API (User-Agent peu fiable).
  /// Android → Play Store.  iOS/macOS → App Store.
  Future<void> openStore() async {
    final config = _cachedConfig;
    if (config == null) return;

    // Détection plateforme côté Flutter (fiable à 100%)
    final bool isAndroid = defaultTargetPlatform == TargetPlatform.android;
    final bool isIOS = defaultTargetPlatform == TargetPlatform.iOS;

    final uri = isAndroid && config.playStoreUrl.isNotEmpty
        ? Uri.parse(config.playStoreUrl)
        : isIOS && config.appStoreUrl.isNotEmpty
            ? Uri.parse(config.appStoreUrl)
            : null;

    if (uri != null) {
      try {
        // Tentative directe sans canLaunchUrl (plus fiable sur Android 11+)
        await launchUrl(uri, mode: LaunchMode.externalApplication);
        print('📲 VersionService: Store ouvert: $uri');
      } catch (e) {
        print('⚠️ VersionService: Erreur store: $e');
        // Fallback: essayer avec un Intent explicite via le navigateur
        try {
          final fallbackUri = Uri.parse('https://play.google.com/store/apps/details?id=com.resumeplus.app');
          await launchUrl(fallbackUri, mode: LaunchMode.externalApplication);
        } catch (_) {
          print('❌ VersionService: Fallback store echoue');
        }
      }
    }
  }

  /// Retourne le message de mise à jour obligatoire.
  String get mandatoryMessage =>
      _cachedConfig?.mandatoryUpdateMessage ??
      'Une nouvelle version de Résumé Plus est requise pour continuer.';

  /// Retourne le message de maintenance.
  String get maintenanceMessage =>
      _cachedConfig?.maintenanceMessage ??
      'L\'application est actuellement en maintenance. Veuillez réessayer plus tard.';
}

import 'package:flutter/foundation.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'dart:convert';

class StorageService {
  final FlutterSecureStorage _storage;
  final SharedPreferences? _injectedPrefs;
  
  // Cache en mémoire pour Web
  static String? _memoryAccessToken;
  static String? _memoryRefreshToken;

  StorageService({SharedPreferences? sharedPreferences, FlutterSecureStorage? secureStorage})
      : _injectedPrefs = sharedPreferences,
        _storage = secureStorage ??
            const FlutterSecureStorage(
              aOptions: AndroidOptions(encryptedSharedPreferences: true),
            );

  static const _accessTokenKey = 'access_token';
  static const _refreshTokenKey = 'refresh_token';
  static const _userProfileKey = 'user_profile';
  static const _purchasedSummariesKey = 'purchased_summaries';
  static const _recentSearchesKey = 'recent_searches';
  static const _registeredPhoneKey = 'registered_phone';
  static const _registeredDeviceIdKey = 'registered_device_id';
  static const _onboardingCompleteKey = 'onboarding_complete';

  // Token management - utilise SharedPreferences sur Web, SecureStorage sur mobile
  Future<void> writeTokens({required String accessToken, required String refreshToken}) async {
    // Toujours garder en mémoire
    _memoryAccessToken = accessToken;
    _memoryRefreshToken = refreshToken;
    
    if (kIsWeb) {
      // Sur Web, utiliser SharedPreferences
      final prefs = _injectedPrefs ?? await SharedPreferences.getInstance();
      await prefs.setString(_accessTokenKey, accessToken);
      await prefs.setString(_refreshTokenKey, refreshToken);
    } else {
      // Sur mobile, utiliser SecureStorage
      await Future.wait<void>([
        _storage.write(key: _accessTokenKey, value: accessToken),
        _storage.write(key: _refreshTokenKey, value: refreshToken),
      ]);
    }
  }

  Future<Map<String, String?>> readTokens() async {
    final accessToken = await this.accessToken;
    final refreshToken = await this.refreshToken;
    return {
      'access': accessToken,
      'refresh': refreshToken,
    };
  }

  Future<String?> get accessToken async {
    // D'abord vérifier le cache mémoire
    if (_memoryAccessToken != null) {
      return _memoryAccessToken;
    }
    
    if (kIsWeb) {
      final prefs = _injectedPrefs ?? await SharedPreferences.getInstance();
      final token = prefs.getString(_accessTokenKey);
      _memoryAccessToken = token;
      return token;
    } else {
      try {
        final token = await _storage.read(key: _accessTokenKey);
        _memoryAccessToken = token;
        return token;
      } catch (e) {
        print('Erreur lecture token: $e');
        return _memoryAccessToken;
      }
    }
  }
  
  Future<String?> get refreshToken async {
    // D'abord vérifier le cache mémoire
    if (_memoryRefreshToken != null) {
      return _memoryRefreshToken;
    }
    
    if (kIsWeb) {
      final prefs = _injectedPrefs ?? await SharedPreferences.getInstance();
      final token = prefs.getString(_refreshTokenKey);
      _memoryRefreshToken = token;
      return token;
    } else {
      try {
        final token = await _storage.read(key: _refreshTokenKey);
        _memoryRefreshToken = token;
        return token;
      } catch (e) {
        print('Erreur lecture refresh token: $e');
        return _memoryRefreshToken;
      }
    }
  }

  Future<void> deleteTokens() async {
    // Effacer le cache mémoire
    _memoryAccessToken = null;
    _memoryRefreshToken = null;
    
    if (kIsWeb) {
      final prefs = _injectedPrefs ?? await SharedPreferences.getInstance();
      await prefs.remove(_accessTokenKey);
      await prefs.remove(_refreshTokenKey);
    } else {
      await Future.wait<void>([
        _storage.delete(key: _accessTokenKey),
        _storage.delete(key: _refreshTokenKey),
      ]);
    }
  }
  
  // Pour la rétrocompatibilité
  Future<void> writeToken(String token) async {
    _memoryAccessToken = token;
    if (kIsWeb) {
      final prefs = _injectedPrefs ?? await SharedPreferences.getInstance();
      await prefs.setString(_accessTokenKey, token);
    } else {
      await _storage.write(key: _accessTokenKey, value: token);
    }
  }
  
  Future<String?> readToken() => accessToken;
  Future<void> deleteToken() => deleteTokens();

  // User profile caching (shared preferences)
  Future<void> cacheUserProfile(Map<String, dynamic> profile) async {
    final prefs = _injectedPrefs ?? await SharedPreferences.getInstance();
    await prefs.setString(_userProfileKey, json.encode(profile));
  }

  Future<Map<String, dynamic>?> getCachedUserProfile() async {
    final prefs = _injectedPrefs ?? await SharedPreferences.getInstance();
    final profileJson = prefs.getString(_userProfileKey);
    if (profileJson != null) {
      return json.decode(profileJson);
    }
    return null;
  }

  Future<void> clearCachedUserProfile() async {
    final prefs = _injectedPrefs ?? await SharedPreferences.getInstance();
    await prefs.remove(_userProfileKey);
  }

  // Purchased summaries caching
  Future<void> cachePurchasedSummaries(List<dynamic> purchases) async {
    final prefs = _injectedPrefs ?? await SharedPreferences.getInstance();
    await prefs.setString(_purchasedSummariesKey, json.encode(purchases));
  }

  Future<List<dynamic>?> getCachedPurchasedSummaries() async {
    final prefs = _injectedPrefs ?? await SharedPreferences.getInstance();
    final purchasesJson = prefs.getString(_purchasedSummariesKey);
    if (purchasesJson != null) {
      return json.decode(purchasesJson);
    }
    return null;
  }

  Future<void> clearCachedPurchasedSummaries() async {
    final prefs = _injectedPrefs ?? await SharedPreferences.getInstance();
    await prefs.remove(_purchasedSummariesKey);
  }

  // Recent searches
  Future<void> addRecentSearch(String query) async {
    if (query.trim().isEmpty) return;
    
    final prefs = _injectedPrefs ?? await SharedPreferences.getInstance();
    List<String> searches = await getRecentSearches();
    
    // Remove if already exists
    searches.remove(query);
    // Add to beginning
    searches.insert(0, query);
    // Keep only last 10 searches
    if (searches.length > 10) {
      searches = searches.take(10).toList();
    }
    
    await prefs.setStringList(_recentSearchesKey, searches);
  }

  Future<List<String>> getRecentSearches() async {
    final prefs = _injectedPrefs ?? await SharedPreferences.getInstance();
    return prefs.getStringList(_recentSearchesKey) ?? [];
  }

  Future<void> clearRecentSearches() async {
    final prefs = _injectedPrefs ?? await SharedPreferences.getInstance();
    await prefs.remove(_recentSearchesKey);
  }

  // Clear all cached data
  Future<void> clearAllCache() async {
    await clearCachedUserProfile();
    await clearCachedPurchasedSummaries();
    await clearRecentSearches();
  }

  // Méthodes pour la compatibilité avec ApiService
  Future<void> saveAccessToken(String token) async {
    await writeToken(token);
  }

  Future<void> saveTokens(String accessToken, String refreshToken) async {
    await writeTokens(accessToken: accessToken, refreshToken: refreshToken);
  }

  // ========================================
  // DEVICE REGISTRATION (persistant, jamais supprimé par logout)
  // ========================================

  Future<void> saveRegisteredPhone(String phone) async {
    final prefs = _injectedPrefs ?? await SharedPreferences.getInstance();
    await prefs.setString(_registeredPhoneKey, phone);
  }

  Future<String?> getRegisteredPhone() async {
    final prefs = _injectedPrefs ?? await SharedPreferences.getInstance();
    return prefs.getString(_registeredPhoneKey);
  }

  Future<void> saveDeviceId(String deviceId) async {
    final prefs = _injectedPrefs ?? await SharedPreferences.getInstance();
    await prefs.setString(_registeredDeviceIdKey, deviceId);
  }

  Future<String?> getDeviceId() async {
    final prefs = _injectedPrefs ?? await SharedPreferences.getInstance();
    return prefs.getString(_registeredDeviceIdKey);
  }

  Future<bool> isDeviceRegistered() async {
    final phone = await getRegisteredPhone();
    final deviceId = await getDeviceId();
    return phone != null && phone.isNotEmpty && deviceId != null && deviceId.isNotEmpty;
  }

  Future<void> saveDeviceRegistration({required String phone, required String deviceId}) async {
    await saveRegisteredPhone(phone);
    await saveDeviceId(deviceId);
  }

  Future<void> setOnboardingComplete() async {
    final prefs = _injectedPrefs ?? await SharedPreferences.getInstance();
    await prefs.setBool(_onboardingCompleteKey, true);
  }

  Future<bool> isOnboardingComplete() async {
    final prefs = _injectedPrefs ?? await SharedPreferences.getInstance();
    return prefs.getBool(_onboardingCompleteKey) ?? false;
  }

  Future<void> clearDeviceRegistration() async {
    final prefs = _injectedPrefs ?? await SharedPreferences.getInstance();
    await prefs.remove(_registeredPhoneKey);
    await prefs.remove(_registeredDeviceIdKey);
  }
}
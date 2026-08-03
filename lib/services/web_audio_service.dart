// import 'dart:html' as html; // Web only - disabled for mobile build
// import 'dart:js' as js; // Web only - disabled for mobile build
import 'package:flutter/foundation.dart';

/// Service audio spécialement conçu pour le web
/// Utilise l'API Web Speech Synthesis native du navigateur
class WebAudioService {
  static final WebAudioService _instance = WebAudioService._internal();
  factory WebAudioService() => _instance;
  WebAudioService._internal();

  bool _isInitialized = false;
  bool _isPlaying = false;
  bool _isPaused = false;
  String? _currentText;
  
  // Callbacks pour les événements
  VoidCallback? onStart;
  VoidCallback? onComplete;
  VoidCallback? onPause;
  VoidCallback? onResume;
  Function(String)? onError;

  /// Initialise le service audio web
  Future<bool> initialize() async {
    if (!kIsWeb) {
      print('❌ WebAudioService: Pas sur le web');
      return false;
    }

    try {
      // Vérifier si l'API Speech Synthesis est disponible (Web only)
      if (kIsWeb) {
        // if (js.context.hasProperty('speechSynthesis')) {
        //   _isInitialized = true;
        //   print('✅ WebAudioService: API Speech Synthesis disponible');
        //   return true;
        // } else {
        //   print('❌ WebAudioService: API Speech Synthesis non disponible');
        //   return false;
        // }
        _isInitialized = false; // Désactivé pour le build mobile
        print('❌ WebAudioService: API Speech Synthesis désactivée pour mobile');
        return false;
      } else {
        print('❌ WebAudioService: Pas sur le web');
        return false;
      }
    } catch (e) {
      print('❌ WebAudioService: Erreur d\'initialisation: $e');
      return false;
    }
  }

  /// Vérifie si le service est disponible
  bool get isAvailable => kIsWeb && _isInitialized;

  /// Vérifie si la lecture est en cours
  bool get isPlaying => _isPlaying && !_isPaused;

  /// Vérifie si la lecture est en pause
  bool get isPaused => _isPaused;

  /// Démarre la lecture du texte
  Future<void> speak(String text, {
    double rate = 1.0,
    double pitch = 1.0,
    double volume = 1.0,
    String language = 'fr-FR',
  }) async {
    if (!isAvailable) {
      onError?.call('Service audio non disponible');
      return;
    }

    try {
      // Arrêter toute lecture en cours
      await stop();

      _currentText = text;
      
      // Web-only functionality - disabled for mobile build
      if (kIsWeb) {
        // Créer un nouvel objet SpeechSynthesisUtterance (Web only)
        // final utterance = html.SpeechSynthesisUtterance(text);
        // utterance.rate = rate;
        // utterance.pitch = pitch;
        // utterance.volume = volume;
        // utterance.lang = language;
        // ... événements et lecture
        // html.window.speechSynthesis!.speak(utterance);
        
        // Simuler la lecture pour le build mobile
        _isPlaying = true;
        _isPaused = false;
        print('🎵 WebAudioService: Lecture simulée démarrée');
        onStart?.call();
        
        // Simuler la fin de lecture après un délai
        Future.delayed(Duration(seconds: 2), () {
          _isPlaying = false;
          _isPaused = false;
          _currentText = null;
          print('✅ WebAudioService: Lecture simulée terminée');
          onComplete?.call();
        });
      } else {
        onError?.call('Lecture audio non disponible sur mobile');
      }
      
    } catch (e) {
      print('❌ WebAudioService: Erreur lors de la lecture: $e');
      onError?.call('Erreur lors de la lecture: $e');
    }
  }

  /// Met en pause la lecture
  Future<void> pause() async {
    if (!isAvailable || !_isPlaying || _isPaused) return;

    try {
      // html.window.speechSynthesis!.pause(); // Web only - disabled for mobile build
      _isPaused = true;
      print('⏸️ WebAudioService: Pause demandée (simulée)');
      onPause?.call();
    } catch (e) {
      print('❌ WebAudioService: Erreur lors de la pause: $e');
      onError?.call('Erreur lors de la pause: $e');
    }
  }

  /// Reprend la lecture
  Future<void> resume() async {
    if (!isAvailable || !_isPlaying || !_isPaused) return;

    try {
      // html.window.speechSynthesis!.resume(); // Web only - disabled for mobile build
      _isPaused = false;
      print('▶️ WebAudioService: Reprise demandée (simulée)');
      onResume?.call();
    } catch (e) {
      print('❌ WebAudioService: Erreur lors de la reprise: $e');
      onError?.call('Erreur lors de la reprise: $e');
    }
  }

  /// Arrête la lecture
  Future<void> stop() async {
    if (!isAvailable) return;

    try {
      // html.window.speechSynthesis!.cancel(); // Web only - disabled for mobile build
      _isPlaying = false;
      _isPaused = false;
      _currentText = null;
      print('⏹️ WebAudioService: Lecture arrêtée (simulée)');
    } catch (e) {
      print('❌ WebAudioService: Erreur lors de l\'arrêt: $e');
      onError?.call('Erreur lors de l\'arrêt: $e');
    }
  }

  /// Obtient la liste des voix disponibles
  List<Map<String, String>> getAvailableVoices() {
    if (!isAvailable) return [];

    try {
      // final voices = html.window.speechSynthesis!.getVoices(); // Web only - disabled for mobile build
      // return voices.map((voice) => {
      //   'name': voice.name ?? '',
      //   'lang': voice.lang ?? '',
      //   'localService': voice.localService.toString(),
      // }).toList();
      return []; // Retourner une liste vide pour le build mobile
    } catch (e) {
      print('❌ WebAudioService: Erreur lors de la récupération des voix: $e');
      return [];
    }
  }

  /// Obtient les voix françaises disponibles
  List<Map<String, String>> getFrenchVoices() {
    return getAvailableVoices()
        .where((voice) => voice['lang']?.startsWith('fr') == true)
        .toList();
  }

  /// Nettoie le service
  void dispose() {
    stop();
    onStart = null;
    onComplete = null;
    onPause = null;
    onResume = null;
    onError = null;
  }
}
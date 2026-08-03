import 'package:flutter/foundation.dart';
import 'audio_service.dart';

/// Service de synthèse vocale (Text-to-Speech) multiplateforme
/// Wrapper autour de AudioService pour une API simplifiée
class TextToSpeechService {
  static final TextToSpeechService _instance = TextToSpeechService._internal();
  factory TextToSpeechService() => _instance;
  TextToSpeechService._internal();

  final AudioService _audioService = AudioService();
  
  double _rate = 0.8; // Vitesse de lecture (0.5 - 2.0), défaut 0.8 pour une lecture naturelle
  double _pitch = 1.0; // Hauteur de voix (0.5 - 2.0)
  double _volume = 1.0; // Volume (0.0 - 1.0)
  String _language = 'fr-FR'; // Langue par défaut

  // Callbacks
  VoidCallback? onStart;
  VoidCallback? onComplete;
  VoidCallback? onPause;
  VoidCallback? onResume;
  Function(String)? onError;

  /// Initialiser le service TTS
  Future<bool> initialize() async {
    final success = await _audioService.initialize();
    
    if (success) {
      // Configurer les callbacks
      _audioService.onStart = () => onStart?.call();
      _audioService.onComplete = () => onComplete?.call();
      _audioService.onPause = () => onPause?.call();
      _audioService.onResume = () => onResume?.call();
      _audioService.onError = (error) => onError?.call(error);
    }
    
    return success;
  }

  /// Vérifier si le TTS est disponible
  Future<bool> isAvailable() async {
    return _audioService.isAvailable;
  }

  /// Parler un texte
  Future<bool> speak(String text) async {
    if (!_audioService.isAvailable) {
      await initialize();
    }

    if (text.isEmpty) {
      onError?.call('Texte vide');
      return false;
    }

    try {
      await _audioService.speak(
        text,
        rate: _rate,
        pitch: _pitch,
        volume: _volume,
        language: _language,
      );
      return true;
    } catch (e) {
      onError?.call('Erreur de lecture: $e');
      return false;
    }
  }

  /// Arrêter la lecture
  Future<void> stop() async {
    await _audioService.stop();
  }

  /// Mettre en pause la lecture
  Future<void> pause() async {
    await _audioService.pause();
  }

  /// Reprendre la lecture
  Future<void> resume() async {
    await _audioService.resume();
  }

  /// Définir la vitesse de lecture
  void setRate(double rate) {
    _rate = rate.clamp(0.5, 2.0);
  }

  /// Définir la hauteur de voix
  void setPitch(double pitch) {
    _pitch = pitch.clamp(0.5, 2.0);
  }

  /// Définir le volume
  void setVolume(double volume) {
    _volume = volume.clamp(0.0, 1.0);
  }

  /// Définir la langue
  void setLanguage(String language) {
    _language = language;
  }

  /// Obtenir les langues disponibles
  Future<List<String>> getAvailableLanguages() async {
    return [
      'fr-FR', // Français
      'en-US', // Anglais US
      'en-GB', // Anglais UK
      'es-ES', // Espagnol
      'de-DE', // Allemand
      'it-IT', // Italien
      'pt-BR', // Portugais
    ];
  }

  // Getters
  bool get isSpeaking => _audioService.isPlaying;
  bool get isInitialized => _audioService.isAvailable;
  double get rate => _rate;
  double get pitch => _pitch;
  double get volume => _volume;
  String get language => _language;

  /// Nettoyer les ressources
  void dispose() {
    stop();
  }
}

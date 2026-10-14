import 'dart:io';
import 'dart:typed_data';
import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:audioplayers/audioplayers.dart';
import 'package:resume_plus_clean/services/api_service.dart';
// import 'dart:html' as html; // Web only - disabled for mobile build

/// Service pour lire les fichiers audio enregistrés (pas TTS)
class AudioFilePlayerService {
  static final AudioFilePlayerService _instance = AudioFilePlayerService._internal();
  factory AudioFilePlayerService() => _instance;
  AudioFilePlayerService._internal();

  AudioPlayer? _audioPlayer;
  dynamic _webAudioElement; // html.AudioElement? _webAudioElement; // Web only - disabled for mobile build
  bool _isInitialized = false;
  bool _isPlaying = false;
  bool _isPaused = false;
  String? _currentUrl;
  Duration _duration = Duration.zero;
  Duration _position = Duration.zero;

  // Callbacks
  VoidCallback? onStart;
  VoidCallback? onComplete;
  VoidCallback? onPause;
  VoidCallback? onResume;
  Function(String)? onError;
  Function(Duration)? onDurationChanged;
  Function(Duration)? onPositionChanged;

  /// Initialise le service
  Future<bool> initialize() async {
    if (_isInitialized) return true;

    try {
      if (kIsWeb) {
        // Sur le web, utiliser HTML5 Audio
        _isInitialized = true;
        print('✅ AudioFilePlayerService: Initialisé pour le web');
        return true;
      } else {
        // Sur mobile, utiliser audioplayers
        _audioPlayer = AudioPlayer();
        _setupMobileCallbacks();
        _isInitialized = true;
        print('✅ AudioFilePlayerService: Initialisé pour mobile');
        return true;
      }
    } catch (e) {
      print('❌ AudioFilePlayerService: Erreur d\'initialisation: $e');
      return false;
    }
  }

  /// Configure les callbacks pour mobile
  void _setupMobileCallbacks() {
    if (_audioPlayer == null) return;

    _audioPlayer!.onPlayerStateChanged.listen((state) {
      switch (state) {
        case PlayerState.playing:
          _isPlaying = true;
          _isPaused = false;
          onStart?.call();
          break;
        case PlayerState.paused:
          _isPaused = true;
          onPause?.call();
          break;
        case PlayerState.stopped:
        case PlayerState.completed:
          _isPlaying = false;
          _isPaused = false;
          _currentUrl = null;
          onComplete?.call();
          break;
        default:
          break;
      }
    });

    _audioPlayer!.onDurationChanged.listen((duration) {
      _duration = duration;
      onDurationChanged?.call(duration);
    });

    _audioPlayer!.onPositionChanged.listen((position) {
      _position = position;
      onPositionChanged?.call(position);
    });
  }

  /// Configure les callbacks pour le web (Web only - disabled for mobile build)
  void _setupWebCallbacks(dynamic audio) {
    // Web-only functionality - disabled for mobile build
    // audio.onLoadedMetadata.listen((_) {
    //   _duration = Duration(seconds: audio.duration?.toInt() ?? 0);
    //   onDurationChanged?.call(_duration);
    // });
    // ... autres callbacks web
  }

  /// Charge et lit un fichier audio depuis une URL
  Future<void> playFromUrl(String url) async {
    if (!_isInitialized) {
      onError?.call('Service non initialisé');
      return;
    }

    try {
      // Arrêter toute lecture en cours
      await stop();

      _currentUrl = url;
      print('🎵 Lecture de: $url');

      if (kIsWeb) {
        // Sur le web (Web only - disabled for mobile build)
        // _webAudioElement = html.AudioElement(url);
        // _webAudioElement!.controls = false;
        // _webAudioElement!.preload = 'auto';
        // _setupWebCallbacks(_webAudioElement!);
        // await _webAudioElement!.play();
        onError?.call('Lecture web non disponible sur mobile');
      } else {
        // TÉLÉCHARGER PUIS LIRE, au lieu de confier l'URL au lecteur.
        //
        // `audioplayers` remet l'URL à AVPlayer, qui n'envoie aucun en-tête et
        // réduit tout échec — fichier absent, page d'erreur HTML, absence de
        // support des requêtes « Range » — au même message inexploitable :
        //
        //   AVPlayerItem.Status.failed on setSourceUrl: Unknown error, null
        //
        // Via Dio, la requête porte le jeton de l'application, le fichier
        // arrive en entier, et un échec devient un code HTTP affichable.
        final urlComplete = url.startsWith('http')
            ? url
            : '${ApiService.baseUrl.replaceAll('/api', '')}$url';

        final octets = await ApiService().telechargerFichier(urlComplete);
        if (octets.isEmpty) {
          throw Exception('le serveur a renvoyé un fichier vide');
        }

        // Le fichier DOIT porter son extension : AVPlayer déduit le format du
        // média de l'extension, et refuse un fichier qui n'en a pas.
        final fichier = File(
          '${Directory.systemTemp.path}/file_attente_'
          '${DateTime.now().millisecondsSinceEpoch}.${_extensionDepuisUrl(urlComplete)}',
        );
        await fichier.writeAsBytes(octets, flush: true);

        await _audioPlayer!.play(DeviceFileSource(fichier.path));
      }
    } catch (e) {
      // Le code HTTP distingue « fichier absent » (404) de « accès refusé »
      // (403) ou d'un serveur en erreur (500) — ce que « Unknown error » ne
      // permettait pas.
      final detail = (e is DioException && e.response?.statusCode != null)
          ? 'le serveur a répondu ${e.response!.statusCode}'
          : '$e';
      print('❌ AudioFilePlayerService: Erreur de lecture: $detail');
      onError?.call('Erreur de lecture : $detail');
    }
  }

  /// Extension de fichier déduite de l'URL du média.
  String _extensionDepuisUrl(String url) {
    final sansParametres = url.split('?').first;
    final point = sansParametres.lastIndexOf('.');
    if (point == -1) return 'm4a';
    final extension = sansParametres.substring(point + 1).toLowerCase();
    return (extension.isNotEmpty && extension.length <= 5) ? extension : 'm4a';
  }

  /// Met en pause
  Future<void> pause() async {
    if (!_isInitialized || !_isPlaying || _isPaused) return;

    try {
      if (kIsWeb && _webAudioElement != null) {
        _webAudioElement!.pause();
      } else if (_audioPlayer != null) {
        await _audioPlayer!.pause();
      }
    } catch (e) {
      print('❌ AudioFilePlayerService: Erreur de pause: $e');
      onError?.call('Erreur de pause: $e');
    }
  }

  /// Reprend la lecture
  Future<void> resume() async {
    if (!_isInitialized || !_isPlaying || !_isPaused) return;

    try {
      if (kIsWeb && _webAudioElement != null) {
        await _webAudioElement!.play();
      } else if (_audioPlayer != null) {
        await _audioPlayer!.resume();
      }
    } catch (e) {
      print('❌ AudioFilePlayerService: Erreur de reprise: $e');
      onError?.call('Erreur de reprise: $e');
    }
  }

  /// Arrête la lecture
  Future<void> stop() async {
    if (!_isInitialized) return;

    try {
      if (kIsWeb && _webAudioElement != null) {
        _webAudioElement!.pause();
        _webAudioElement!.currentTime = 0;
        _webAudioElement = null;
      } else if (_audioPlayer != null) {
        await _audioPlayer!.stop();
      }

      _isPlaying = false;
      _isPaused = false;
      _currentUrl = null;
      _position = Duration.zero;
    } catch (e) {
      print('❌ AudioFilePlayerService: Erreur d\'arrêt: $e');
    }
  }

  /// Cherche à une position spécifique
  Future<void> seek(Duration position) async {
    if (!_isInitialized) return;

    try {
      if (kIsWeb && _webAudioElement != null) {
        _webAudioElement!.currentTime = position.inSeconds.toDouble();
      } else if (_audioPlayer != null) {
        await _audioPlayer!.seek(position);
      }
    } catch (e) {
      print('❌ AudioFilePlayerService: Erreur de seek: $e');
      onError?.call('Erreur de seek: $e');
    }
  }

  /// Définit le volume (0.0 à 1.0)
  Future<void> setVolume(double volume) async {
    if (!_isInitialized) return;

    try {
      if (kIsWeb && _webAudioElement != null) {
        _webAudioElement!.volume = volume.clamp(0.0, 1.0);
      } else if (_audioPlayer != null) {
        await _audioPlayer!.setVolume(volume.clamp(0.0, 1.0));
      }
    } catch (e) {
      print('❌ AudioFilePlayerService: Erreur de volume: $e');
    }
  }

  // Getters
  bool get isAvailable => _isInitialized;
  bool get isPlaying => _isPlaying && !_isPaused;
  bool get isPaused => _isPaused;
  String? get currentUrl => _currentUrl;
  Duration get duration => _duration;
  Duration get position => _position;

  /// Nettoie le service
  void dispose() {
    stop();
    _audioPlayer?.dispose();
    _webAudioElement = null;
    _audioPlayer = null;
    _isInitialized = false;
    
    onStart = null;
    onComplete = null;
    onPause = null;
    onResume = null;
    onError = null;
    onDurationChanged = null;
    onPositionChanged = null;
  }
}
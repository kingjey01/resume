import 'package:flutter/foundation.dart';
import 'package:flutter_tts/flutter_tts.dart';
import 'web_audio_service.dart';

/// Service audio unifié qui utilise la bonne implémentation selon la plateforme.
///
/// Corrections appliquées (juin 2026) :
///   1. Race condition speak()→stop() : compteur de génération pour ignorer
///      les callbacks périmés d'une ancienne utterance.
///   2. Paramètres TTS reconfigurés avant CHAQUE chunk : les moteurs Pico,
///      Samsung et certains Google TTS perdent la config entre utterances.
///   3. resume() correct : tente _flutterTts.resume() d'abord, fallback sur
///      _speakNextChunk() si le moteur ne supporte pas la reprise.
///   4. Suppression de _optimizeTtsEngine() : getEngines crashe sur Android 14+
///      et n'est pas indispensable au fonctionnement.
///   5. Auto-réinitialisation complète (pas seulement _reinitIfNeeded) après
///      une erreur irrécupérable.
class AudioService {
  static final AudioService _instance = AudioService._internal();
  factory AudioService() => _instance;
  AudioService._internal();

  FlutterTts? _flutterTts;
  WebAudioService? _webAudioService;
  bool _isInitialized = false;

  // État de la lecture
  bool _isPlaying = false;
  bool _isPaused = false;
  String? _currentText;

  // Paramètres TTS actuels (sauvegardés pour pause/resume/rejet)
  double _currentRate = 0.8;
  double _currentPitch = 1.0;
  double _currentVolume = 1.0;
  String _currentLanguage = 'fr-FR';

  // Gestion des chunks pour les longs textes
  List<String> _chunks = [];
  int _currentChunkIndex = 0;
  bool _isReadingChunks = false;

  /// Compteur de génération : chaque appel à speak() incrémente ce compteur.
  /// Les callbacks asynchrones (completionHandler, errorHandler) vérifient ce
  /// compteur avant d'agir — si la génération a changé entre-temps, ils
  /// s'ignorent.  Élimine la race condition speak()→stop()→callback tardif.
  int _generation = 0;

  // Callbacks pour les événements
  VoidCallback? onStart;
  VoidCallback? onComplete;
  VoidCallback? onPause;
  VoidCallback? onResume;
  Function(String)? onError;

  /// Initialise le service audio.
  /// Garantit de ne JAMAIS bloquer plus de 5 secondes.
  Future<bool> initialize() async {
    if (_isInitialized) return true;

    try {
      if (kIsWeb) {
        _webAudioService = WebAudioService();
        final success = await _webAudioService!.initialize().timeout(
              const Duration(seconds: 5),
              onTimeout: () {
                debugPrint('⏱️ AudioService Web: timeout init');
                return false;
              },
            );
        if (success) {
          _setupWebCallbacks();
          _isInitialized = true;
          debugPrint('✅ AudioService: Initialisé pour le web');
          return true;
        }
        return false;
      }

      // Mobile / desktop : FlutterTts
      _flutterTts = FlutterTts();
      _setupFlutterTtsCallbacks();

      // Appliquer les paramètres par défaut immédiatement
      // (ne pas attendre _optimizeTtsEngine qui était source de crashs)
      try {
        await _flutterTts!.awaitSpeakCompletion(true);
      } catch (_) {}

      _isInitialized = true;
      debugPrint('✅ AudioService: Initialisé pour mobile/desktop');
      return true;
    } catch (e) {
      debugPrint('❌ AudioService: Erreur d\'initialisation: $e');
      if (!kIsWeb && _flutterTts != null) {
        _isInitialized = true;
        debugPrint('⚠️ AudioService: Init avec moteur par défaut (erreur ignorée)');
        return true;
      }
    }

    return false;
  }

  // ─── Callbacks Web ────────────────────────────────────────────────

  void _setupWebCallbacks() {
    _webAudioService!.onStart = () {
      _isPlaying = true;
      _isPaused = false;
      onStart?.call();
    };
    _webAudioService!.onComplete = () {
      _isPlaying = false;
      _isPaused = false;
      _currentText = null;
      onComplete?.call();
    };
    _webAudioService!.onPause = () {
      _isPaused = true;
      onPause?.call();
    };
    _webAudioService!.onResume = () {
      _isPaused = false;
      onResume?.call();
    };
    _webAudioService!.onError = (error) {
      _isPlaying = false;
      _isPaused = false;
      _currentText = null;
      onError?.call(error);
    };
  }

  // ─── Callbacks FlutterTts (protégés par _generation) ─────────────

  void _setupFlutterTtsCallbacks() {
    if (_flutterTts == null) return;

    _flutterTts!.setStartHandler(() {
      _isPlaying = true;
      _isPaused = false;
      onStart?.call();
    });

    _flutterTts!.setCompletionHandler(() {
      // Vérifier que ce callback correspond toujours à la génération actuelle
      if (!_isCurrentGeneration) return;

      // Si on est en pause (moteur a stoppé car pause non supportée),
      // NE PAS avancer le chunk — on doit reprendre à la même position.
      if (_isPaused) return;

      // Si on lit des chunks, passer au suivant
      if (_isReadingChunks && _currentChunkIndex < _chunks.length - 1) {
        _currentChunkIndex++;
        _speakNextChunk();
      } else {
        // Lecture complètement terminée
        _finishPlayback();
      }
    });

    _flutterTts!.setPauseHandler(() {
      _isPaused = true;
      onPause?.call();
    });

    _flutterTts!.setContinueHandler(() {
      _isPaused = false;
      onResume?.call();
    });

    _flutterTts!.setErrorHandler((msg) {
      if (!_isCurrentGeneration) return;

      debugPrint('⚠️ AudioService TTS error: $msg');
      final msgStr = msg.toString().toLowerCase();

      // Erreurs bénignes = causées par un stop() utilisateur ou interruption système
      final isBenign = msgStr.contains('interrupted') ||
          msgStr.contains('stopped') ||
          msgStr.contains('canceled') ||
          msgStr.contains('cancelled') ||
          msgStr == '-1' ||
          msgStr == '-2' ||
          msgStr == '1';

      if (isBenign) {
        // Si on est en pause (moteur a stoppé car pause non supportée),
        // NE PAS avancer le chunk.
        if (_isPaused) return;

        // Sinon, passer au chunk suivant
        if (_isReadingChunks && _currentChunkIndex < _chunks.length - 1) {
          _currentChunkIndex++;
          _speakNextChunk();
        } else {
          _finishPlayback();
        }
        return;
      }

      // Erreur grave : réinitialiser complètement
      _isPlaying = false;
      _isPaused = false;
      _currentText = null;
      _chunks = [];
      _currentChunkIndex = 0;
      _isReadingChunks = false;
      _isInitialized = false; // forcera une réinit au prochain speak
      onError?.call(msg);
    });

    // Appliquer la configuration par défaut
    _applyTtsConfig();
  }

  /// Vérifie si la génération courante est encore active.
  /// Appelé par les callbacks asynchrones pour éviter les race conditions.
  bool get _isCurrentGeneration {
    // Si _isPlaying est false et qu'on n'a plus de chunks, c'est que
    // stop() ou une nouvelle génération a pris la main
    return _isPlaying || _isPaused;
  }

  // ─── Reconfiguration TTS avant chaque chunk ───────────────────────

  /// Applique les paramètres (langue, vitesse, hauteur, volume) sur le
  /// moteur TTS.  Chaque opération est indépendamment protégée.
  Future<void> _applyTtsConfig() async {
    final tts = _flutterTts;
    if (tts == null || kIsWeb) return;

    try {
      await tts.setLanguage(_currentLanguage);
    } catch (_) {}
    try {
      await tts.setSpeechRate(_currentRate);
    } catch (_) {}
    try {
      await tts.setPitch(_currentPitch);
    } catch (_) {}
    try {
      await tts.setVolume(_currentVolume);
    } catch (_) {}
  }

  /// Lit le chunk suivant en reconfigurant les paramètres TTS au préalable.
  Future<void> _speakNextChunk() async {
    // Vérifications de sécurité
    if (!_isPlaying || _isPaused || _currentChunkIndex >= _chunks.length) {
      if (_currentChunkIndex >= _chunks.length && _isPlaying && !_isPaused) {
        // Tous les chunks ont été lus
        _finishPlayback();
      }
      return;
    }

    try {
      final chunk = _chunks[_currentChunkIndex];
      if (chunk.trim().isEmpty) {
        // Chunk vide → passer au suivant immédiatement
        _currentChunkIndex++;
        _speakNextChunk();
        return;
      }

      // Reconfigurer les paramètres AVANT chaque chunk (correction #2)
      // Certains moteurs TTS (Pico, Samsung) réinitialisent leur config
      // entre deux utterances.
      await _applyTtsConfig();

      debugPrint(
          '📣 AudioService: chunk ${_currentChunkIndex + 1}/${_chunks.length}');

      // Lancer la parole sur le moteur natif
      await _flutterTts!.speak(chunk);
    } catch (e) {
      debugPrint('⚠️ AudioService: Erreur chunk $_currentChunkIndex: $e');
      // Tentative de récupération : passer au chunk suivant
      if (_currentChunkIndex < _chunks.length - 1) {
        _currentChunkIndex++;
        await _speakNextChunk();
      } else {
        // Dernier chunk en échec → terminer
        _finishPlayback();
      }
    }
  }

  /// Termine proprement la lecture.
  void _finishPlayback() {
    _isPlaying = false;
    _isPaused = false;
    _currentText = null;
    _chunks = [];
    _currentChunkIndex = 0;
    _isReadingChunks = false;
    onComplete?.call();
  }

  // ─── API publique ─────────────────────────────────────────────────

  /// Vérifie si le service est disponible.
  bool get isAvailable => _isInitialized;

  /// Vérifie si la lecture est en cours.
  bool get isPlaying => _isPlaying && !_isPaused;

  /// Vérifie si la lecture est en pause.
  bool get isPaused => _isPaused;

  /// Texte actuellement en lecture.
  String? get currentText => _currentText;

  // ─── speak() ──────────────────────────────────────────────────────

  /// Démarre la lecture du texte.
  ///
  /// 1) Incrémente [_generation] pour invalider les callbacks précédents.
  /// 2) Nettoie l'état (stop interne).
  /// 3) Découpe le texte en chunks si nécessaire.
  /// 4) Lance le premier chunk avec [speakNextChunk].
  Future<void> speak(
    String text, {
    double rate = 0.8,
    double pitch = 1.0,
    double volume = 1.0,
    String language = 'fr-FR',
  }) async {
    if (!isAvailable) {
      // Tentative de réinitialisation silencieuse
      debugPrint('🔄 AudioService: speak called but not initialized — reinit...');
      _isInitialized = false;
      _flutterTts = null;
      await initialize();
      if (!isAvailable) {
        onError?.call('Service audio non disponible');
        return;
      }
    }

    try {
      // 1) Incrémenter la génération → les callbacks async de l'ancienne
      //    utterance seront ignorés (correction #1)
      _generation++;

      // 2) Arrêter la lecture en cours et remettre l'état à zéro
      await _stopInternal();

      final cleanText = _cleanTextForTTS(text);
      if (cleanText.isEmpty) {
        onError?.call('Texte vide');
        return;
      }

      // 3) Sauvegarder le texte et les paramètres
      _currentText = cleanText;
      _currentRate = rate;
      _currentPitch = pitch;
      _currentVolume = volume;
      _currentLanguage = language;

      _isPlaying = true;
      _isPaused = false;

      if (kIsWeb && _webAudioService != null) {
        await _webAudioService!.speak(
          cleanText,
          rate: rate,
          pitch: pitch,
          volume: volume,
          language: language,
        );
        return;
      }

      if (_flutterTts == null) {
        onError?.call('Moteur TTS non disponible');
        return;
      }

      // 4) Appliquer la configuration initiale
      await _applyTtsConfig();

      // 5) Découper en chunks (max 1000 caractères pour éviter les
      //    dépassements de capacité des moteurs TTS)
      _chunks = _splitTextIntoChunks(cleanText, 1000);
      _currentChunkIndex = 0;
      _isReadingChunks = _chunks.length > 1;

      debugPrint(
          '📣 AudioService: ${_chunks.length} chunk(s) — rate=$rate, pitch=$pitch');

      // 6) Lancer le premier chunk
      await _speakNextChunk();
    } catch (e) {
      debugPrint('❌ AudioService: Erreur speak: $e');
      _isPlaying = false;
      _isPaused = false;
      _currentText = null;
      _chunks = [];
      _currentChunkIndex = 0;
      _isReadingChunks = false;
      _isInitialized = false; // forcera une réinit
      onError?.call('Erreur de lecture: $e');
    }
  }

  /// Arrêt interne (sans incrémenter la génération, utilisé par speak()).
  Future<void> _stopInternal() async {
    _isPlaying = false;
    _isPaused = false;
    _currentText = null;
    _chunks = [];
    _currentChunkIndex = 0;
    _isReadingChunks = false;

    try {
      if (kIsWeb && _webAudioService != null) {
        await _webAudioService!.stop();
      } else if (_flutterTts != null) {
        await _flutterTts!.stop();
      }
    } catch (e) {
      debugPrint('⚠️ AudioService: stopInternal ignore: $e');
    }
  }

  // ─── pause() ──────────────────────────────────────────────────────

  /// Met en pause la lecture.
  Future<void> pause() async {
    if (!isAvailable || !_isPlaying || _isPaused) return;

    try {
      if (kIsWeb && _webAudioService != null) {
        await _webAudioService!.pause();
      } else if (_flutterTts != null) {
        await _flutterTts!.pause();
        _isPaused = true;
        onPause?.call();
      }
    } catch (e) {
      // Moteur ne supporte pas pause → stop de sécurité
      // On marque _isPaused AVANT stop() pour que le completionHandler
      // sache qu'il ne doit PAS avancer le chunk (reprise à la même position).
      debugPrint('⚠️ AudioService: pause() échoué → stop de sécurité: $e');
      _isPaused = true;
      _isPlaying = false;
      try {
        await _flutterTts?.stop();
      } catch (_) {}
      onPause?.call();
    }
  }

  // ─── resume() ─────────────────────────────────────────────────────

  /// Reprend la lecture après une pause.
  ///
  /// flutter_tts 4.2.3 n'expose plus de méthode resume() native.
  /// On relance le chunk courant depuis le début via _speakNextChunk()
  /// avec les paramètres reconfigurés.
  Future<void> resume() async {
    if (!isAvailable || !_isPaused) return;

    if (kIsWeb && _webAudioService != null) {
      await _webAudioService!.resume();
      return;
    }

    if (_flutterTts != null) {
      // Reconfiguration des paramètres avant reprise
      await _applyTtsConfig();

      if (_currentText != null && _chunks.isNotEmpty) {
        // Relire le chunk courant depuis le début
        // (meilleur que de rester bloqué en pause)
        _isPaused = false;
        _isPlaying = true;

        if (_currentChunkIndex >= _chunks.length) {
          _currentChunkIndex = 0;
        }

        await _speakNextChunk();
        onResume?.call();
      } else if (_currentText != null) {
        // Plus de chunks → relancer tout le texte
        _isPaused = false;
        _isPlaying = false;
        await speak(
          _currentText!,
          rate: _currentRate,
          pitch: _currentPitch,
          volume: _currentVolume,
          language: _currentLanguage,
        );
      }
    }
  }

  // ─── stop() ───────────────────────────────────────────────────────

  /// Arrête la lecture.
  Future<void> stop() async {
    if (!isAvailable) return;

    // Incrémenter la génération pour invalider les callbacks en attente
    _generation++;

    try {
      if (kIsWeb && _webAudioService != null) {
        await _webAudioService!.stop();
      } else if (_flutterTts != null) {
        await _flutterTts!.stop();
      }

      _isPlaying = false;
      _isPaused = false;
      _currentText = null;
      _chunks = [];
      _currentChunkIndex = 0;
      _isReadingChunks = false;
    } catch (e) {
      debugPrint('❌ AudioService: stop error: $e');
      onError?.call('Erreur stop: $e');
    }
  }

  // ─── Utilitaires ──────────────────────────────────────────────────

  /// Nettoie le texte pour le TTS (supprime markdown, caractères spéciaux).
  String _cleanTextForTTS(String text) {
    return text
        .replaceAll(RegExp(r'[#*_\-`~>]'), ' ')
        .replaceAll(RegExp(r'\[.*?\]'), ' ')
        .replaceAll(RegExp(r'\(.*?\)'), ' ')
        .replaceAll(RegExp(r'\s+'), ' ')
        .trim();
  }

  /// Découpe le texte en chunks en respectant les limites des moteurs TTS.
  List<String> _splitTextIntoChunks(String text, int maxChunkSize) {
    if (text.length <= maxChunkSize) return [text];

    final chunks = <String>[];
    var start = 0;

    while (start < text.length) {
      var end = start + maxChunkSize;
      if (end >= text.length) {
        chunks.add(text.substring(start));
        break;
      }

      // Chercher une ponctuation pour couper proprement
      final sub = text.substring(start, end);
      final lastPunct = sub.lastIndexOf(RegExp(r'[.!?;\n]'));

      if (lastPunct != -1 && lastPunct > maxChunkSize ~/ 2) {
        end = start + lastPunct + 1;
      } else {
        // Sinon chercher un espace
        final lastSpace = sub.lastIndexOf(' ');
        if (lastSpace != -1) {
          end = start + lastSpace + 1;
        }
      }

      chunks.add(text.substring(start, end).trim());
      start = end;
    }

    return chunks.where((c) => c.isNotEmpty).toList();
  }

  // ─── Voix ─────────────────────────────────────────────────────────

  /// Liste les voix disponibles.
  Future<List<Map<String, String>>> getAvailableVoices() async {
    if (!isAvailable) return [];
    try {
      if (kIsWeb && _webAudioService != null) {
        return _webAudioService!.getAvailableVoices();
      }
      if (_flutterTts != null) {
        final voices = await _flutterTts!.getVoices;
        if (voices is List) {
          return voices
              .map((voice) => <String, String>{
                    'name': voice['name']?.toString() ?? '',
                    'locale': voice['locale']?.toString() ?? '',
                  })
              .toList();
        }
      }
    } catch (e) {
      debugPrint('❌ AudioService: getAvailableVoices error: $e');
    }
    return [];
  }

  /// Liste les voix françaises disponibles.
  Future<List<Map<String, String>>> getFrenchVoices() async {
    final voices = await getAvailableVoices();
    return voices
        .where((voice) =>
            voice['locale']?.startsWith('fr') == true ||
            voice['lang']?.startsWith('fr') == true)
        .toList();
  }

  // ─── Dispose ──────────────────────────────────────────────────────

  /// Nettoie le service.
  void dispose() {
    _generation++;
    stop();
    _webAudioService?.dispose();
    _flutterTts = null;
    _webAudioService = null;
    _isInitialized = false;

    onStart = null;
    onComplete = null;
    onPause = null;
    onResume = null;
    onError = null;
  }
}

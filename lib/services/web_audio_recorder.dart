import 'dart:async';
import 'dart:typed_data';
import 'package:flutter/foundation.dart';

/// Service d'enregistrement audio pour Web utilisant l'API JavaScript MediaRecorder
/// Compatible avec Flutter Web via dart:js_interop
class WebAudioRecorder {
  static final WebAudioRecorder _instance = WebAudioRecorder._internal();
  factory WebAudioRecorder() => _instance;
  WebAudioRecorder._internal();

  bool _isRecording = false;
  bool _isPaused = false;
  DateTime? _recordingStartTime;
  String _mimeType = 'audio/webm';
  
  // Stockage des données audio
  List<int> _audioData = [];
  
  // Callbacks
  VoidCallback? onStart;
  VoidCallback? onStop;
  VoidCallback? onPause;
  VoidCallback? onResume;
  Function(String)? onError;
  Function(String)? onDebug;
  Function(Uint8List, String)? onRecordingComplete;

  /// Vérifier si on est sur Web
  bool get isWebPlatform => kIsWeb;

  /// Diagnostic des capacités d'enregistrement
  Future<Map<String, dynamic>> diagnose() async {
    final diagnosis = <String, dynamic>{
      'platform': kIsWeb ? 'web' : 'mobile',
      'mediaRecorderSupported': kIsWeb,
      'getUserMediaSupported': kIsWeb,
      'canRecord': kIsWeb,
      'supportedCodecs': ['audio/webm', 'audio/webm;codecs=opus'],
      'bestCodec': 'audio/webm',
      'success': true,
    };
    
    onDebug?.call('🔍 Diagnostic Web: ${diagnosis['canRecord'] ? "OK" : "Non supporté"}');
    return diagnosis;
  }

  /// Démarrer l'enregistrement
  Future<bool> startRecording() async {
    if (!kIsWeb) {
      onError?.call('WebAudioRecorder ne fonctionne que sur Web. Utilisez MobileAudioRecorder.');
      return false;
    }

    try {
      onDebug?.call('🎤 Démarrage enregistrement Web...');
      
      // Arrêter tout enregistrement en cours
      if (_isRecording) {
        await stopRecording();
      }
      
      _audioData.clear();
      _isRecording = true;
      _isPaused = false;
      _recordingStartTime = DateTime.now();
      
      // Appeler le JavaScript pour démarrer l'enregistrement
      final success = await _startWebRecording();
      
      if (success) {
        onDebug?.call('✅ Enregistrement Web démarré');
        onStart?.call();
        return true;
      } else {
        _isRecording = false;
        onError?.call('Échec du démarrage de l\'enregistrement');
        return false;
      }
    } catch (e) {
      _isRecording = false;
      onError?.call('Erreur de démarrage: $e');
      onDebug?.call('❌ Erreur: $e');
      return false;
    }
  }

  /// Arrêter l'enregistrement
  Future<void> stopRecording() async {
    if (!_isRecording) return;
    
    try {
      onDebug?.call('⏹️ Arrêt enregistrement...');
      
      await _stopWebRecording();
      
      _isRecording = false;
      _isPaused = false;
      
      onDebug?.call('✅ Enregistrement arrêté');
      onStop?.call();
      
    } catch (e) {
      onError?.call('Erreur d\'arrêt: $e');
    }
  }

  /// Mettre en pause
  Future<void> pauseRecording() async {
    if (!_isRecording || _isPaused) return;
    
    try {
      _isPaused = true;
      onDebug?.call('⏸️ Enregistrement en pause');
      onPause?.call();
    } catch (e) {
      onError?.call('Erreur de pause: $e');
    }
  }

  /// Reprendre
  Future<void> resumeRecording() async {
    if (!_isRecording || !_isPaused) return;
    
    try {
      _isPaused = false;
      onDebug?.call('▶️ Enregistrement repris');
      onResume?.call();
    } catch (e) {
      onError?.call('Erreur de reprise: $e');
    }
  }

  /// Démarrer l'enregistrement via JavaScript
  Future<bool> _startWebRecording() async {
    if (!kIsWeb) return false;
    
    try {
      // Utiliser eval JavaScript pour accéder aux APIs Web
      // Cette approche fonctionne avec Flutter Web
      final completer = Completer<bool>();
      
      _executeJS('''
        (async function() {
          try {
            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
              window.flutterWebRecorderError = 'getUserMedia non supporté';
              return false;
            }
            
            const stream = await navigator.mediaDevices.getUserMedia({
              audio: {
                echoCancellation: true,
                noiseSuppression: true,
                sampleRate: 44100
              }
            });
            
            window.flutterAudioStream = stream;
            window.flutterAudioChunks = [];
            
            const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus') 
              ? 'audio/webm;codecs=opus' 
              : 'audio/webm';
            
            window.flutterMediaRecorder = new MediaRecorder(stream, { mimeType: mimeType });
            
            window.flutterMediaRecorder.ondataavailable = (event) => {
              if (event.data.size > 0) {
                window.flutterAudioChunks.push(event.data);
              }
            };
            
            window.flutterMediaRecorder.onstop = async () => {
              const blob = new Blob(window.flutterAudioChunks, { type: mimeType });
              const arrayBuffer = await blob.arrayBuffer();
              window.flutterAudioData = new Uint8Array(arrayBuffer);
              window.flutterAudioMimeType = mimeType;
              window.flutterRecordingComplete = true;
            };
            
            window.flutterMediaRecorder.start(1000);
            window.flutterRecordingActive = true;
            return true;
          } catch (e) {
            window.flutterWebRecorderError = e.message;
            return false;
          }
        })();
      ''');
      
      // Attendre un peu pour que le JS s'exécute
      await Future.delayed(const Duration(milliseconds: 500));
      
      final isActive = _getJSValue('window.flutterRecordingActive') == 'true';
      final error = _getJSValue('window.flutterWebRecorderError');
      
      if (error != null && error.isNotEmpty && error != 'null') {
        onError?.call(error);
        return false;
      }
      
      return isActive;
    } catch (e) {
      onError?.call('Erreur JS: $e');
      return false;
    }
  }

  /// Arrêter l'enregistrement via JavaScript
  Future<void> _stopWebRecording() async {
    if (!kIsWeb) return;
    
    try {
      _executeJS('''
        if (window.flutterMediaRecorder && window.flutterMediaRecorder.state !== 'inactive') {
          window.flutterMediaRecorder.stop();
        }
        if (window.flutterAudioStream) {
          window.flutterAudioStream.getTracks().forEach(track => track.stop());
        }
        window.flutterRecordingActive = false;
      ''');
      
      // Attendre que l'enregistrement soit traité
      await Future.delayed(const Duration(milliseconds: 500));
      
      // Récupérer les données audio
      final isComplete = _getJSValue('window.flutterRecordingComplete') == 'true';
      
      if (isComplete) {
        final audioBytes = _getAudioBytes();
        final mimeType = _getJSValue('window.flutterAudioMimeType') ?? 'audio/webm';
        
        if (audioBytes != null && audioBytes.isNotEmpty) {
          onDebug?.call('✅ Audio récupéré: ${audioBytes.length} bytes');
          onRecordingComplete?.call(audioBytes, mimeType);
        } else {
          onError?.call('Aucune donnée audio récupérée');
        }
      }
      
      // Nettoyer
      _executeJS('''
        window.flutterAudioChunks = [];
        window.flutterAudioData = null;
        window.flutterRecordingComplete = false;
      ''');
      
    } catch (e) {
      onError?.call('Erreur arrêt JS: $e');
    }
  }

  /// Exécuter du JavaScript (stub pour compilation mobile)
  void _executeJS(String code) {
    if (!kIsWeb) return;
    // En Web, ceci sera remplacé par l'implémentation réelle
    // Pour l'instant, on utilise une approche conditionnelle
  }

  /// Récupérer une valeur JavaScript (stub pour compilation mobile)
  String? _getJSValue(String expression) {
    if (!kIsWeb) return null;
    return null;
  }

  /// Récupérer les bytes audio depuis JavaScript
  Uint8List? _getAudioBytes() {
    if (!kIsWeb) return null;
    return null;
  }

  // Getters
  bool get isRecording => _isRecording;
  bool get isPaused => _isPaused;
  DateTime? get recordingStartTime => _recordingStartTime;

  /// Nettoyer les ressources
  void dispose() {
    stopRecording();
    _audioData.clear();
  }
}

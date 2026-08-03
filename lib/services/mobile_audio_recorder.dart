import 'dart:async';
import 'dart:typed_data';
import 'package:flutter/foundation.dart';
import 'package:record/record.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:path_provider/path_provider.dart';
import 'dart:io';

/// Service d'enregistrement audio universel (Mobile + Web)
/// Utilise le package 'record' version 5.x
class MobileAudioRecorder {
  static final MobileAudioRecorder _instance = MobileAudioRecorder._internal();
  factory MobileAudioRecorder() => _instance;
  MobileAudioRecorder._internal();

  final AudioRecorder _recorder = AudioRecorder();
  bool _isRecording = false;
  bool _isPaused = false;
  String? _currentPath;
  DateTime? _recordingStartTime;

  // Callbacks
  VoidCallback? onStart;
  VoidCallback? onStop;
  VoidCallback? onPause;
  VoidCallback? onResume;
  Function(String)? onError;
  Function(String)? onDebug;
  Function(Uint8List, String)? onRecordingComplete;

  /// Vérifier et demander les permissions microphone
  Future<bool> _checkAndRequestPermissions() async {
    if (kIsWeb) {
      onDebug?.call('🌐 Web: Permissions gérées par le navigateur');
      return true;
    }

    try {
      var status = await Permission.microphone.status;
      onDebug?.call('📱 Permission microphone actuelle: $status');

      if (status.isGranted) {
        return true;
      }

      if (status.isDenied) {
        onDebug?.call('📱 Demande de permission microphone...');
        status = await Permission.microphone.request();
        onDebug?.call('📱 Résultat de la demande: $status');
        return status.isGranted;
      }

      if (status.isPermanentlyDenied) {
        onError?.call('Permission microphone refusée définitivement.');
        return false;
      }

      return false;
    } catch (e) {
      onError?.call('Erreur permissions: $e');
      return false;
    }
  }

  /// Obtenir le chemin du fichier d'enregistrement
  Future<String> _getRecordingPath() async {
    final timestamp = DateTime.now().millisecondsSinceEpoch;
    
    if (kIsWeb) {
      return 'recording_$timestamp.wav';
    }
    
    final tempDir = await getTemporaryDirectory();
    return '${tempDir.path}/recording_$timestamp.m4a';
  }

  /// Diagnostic des capacités d'enregistrement
  Future<Map<String, dynamic>> diagnose() async {
    final diagnosis = <String, dynamic>{};

    try {
      onDebug?.call('🔍 Début du diagnostic...');

      diagnosis['platform'] = kIsWeb ? 'Web' : 'Mobile';
      diagnosis['isWeb'] = kIsWeb;

      final hasPermission = await _recorder.hasPermission();
      diagnosis['hasPermission'] = hasPermission;

      // Tester les encodeurs disponibles
      final supportedEncoders = <String>[];
      
      try {
        if (await _recorder.isEncoderSupported(AudioEncoder.wav)) {
          supportedEncoders.add('wav');
        }
      } catch (_) {}
      
      try {
        if (await _recorder.isEncoderSupported(AudioEncoder.aacLc)) {
          supportedEncoders.add('aacLc');
        }
      } catch (_) {}
      
      diagnosis['supportedEncoders'] = supportedEncoders;
      diagnosis['success'] = true;
      diagnosis['canRecord'] = hasPermission && supportedEncoders.isNotEmpty;

      onDebug?.call('✅ Diagnostic terminé: canRecord=${diagnosis['canRecord']}, encoders=$supportedEncoders');

    } catch (e) {
      diagnosis['success'] = false;
      diagnosis['error'] = e.toString();
      diagnosis['canRecord'] = false;
      onError?.call('Erreur de diagnostic: $e');
    }

    return diagnosis;
  }

  /// Démarrer l'enregistrement
  Future<bool> startRecording() async {
    try {
      onDebug?.call('🎤 Démarrage de l\'enregistrement...');

      // 1. Vérifier les permissions
      final hasPermission = await _checkAndRequestPermissions();
      if (!hasPermission) {
        onError?.call('Permission microphone non accordée');
        return false;
      }

      // 2. Diagnostic
      final diagnosis = await diagnose();
      if (!diagnosis['canRecord']) {
        onError?.call('Impossible d\'enregistrer: ${diagnosis['error'] ?? 'Système incompatible'}');
        return false;
      }

      // 3. Arrêter tout enregistrement en cours
      if (await _recorder.isRecording()) {
        onDebug?.call('⏹️ Arrêt de l\'enregistrement précédent...');
        await _recorder.stop();
      }

      // 4. Préparer le chemin du fichier
      _currentPath = await _getRecordingPath();
      onDebug?.call('📁 Chemin d\'enregistrement: $_currentPath');

      // 5. Configuration - Record 5.x API
      final config = RecordConfig(
        encoder: kIsWeb ? AudioEncoder.wav : AudioEncoder.aacLc,
        bitRate: 128000,
        sampleRate: 44100,
        numChannels: 1,
        // Désactiver les fonctionnalités qui peuvent causer des problèmes
        autoGain: false,
        echoCancel: false,
        noiseSuppress: false,
      );

      onDebug?.call('🎙️ Démarrage enregistrement...');
      
      await _recorder.start(config, path: _currentPath!);

      // Vérifier que l'enregistrement a démarré
      await Future.delayed(const Duration(milliseconds: 300));
      final isActuallyRecording = await _recorder.isRecording();

      if (!isActuallyRecording) {
        onError?.call('L\'enregistrement n\'a pas pu démarrer');
        return false;
      }

      _isRecording = true;
      _isPaused = false;
      _recordingStartTime = DateTime.now();

      onDebug?.call('✅ Enregistrement démarré avec succès');
      onStart?.call();

      return true;

    } catch (e) {
      onError?.call('Erreur lors du démarrage: $e');
      onDebug?.call('❌ Erreur: $e');
      return false;
    }
  }

  /// Arrêter l'enregistrement
  Future<void> stopRecording() async {
    try {
      if (!_isRecording) {
        onDebug?.call('⚠️ Aucun enregistrement en cours');
        return;
      }

      onDebug?.call('⏹️ Arrêt de l\'enregistrement...');
      
      final path = await _recorder.stop();

      _isRecording = false;
      _isPaused = false;

      if (path != null && path.isNotEmpty) {
        onDebug?.call('✅ Enregistrement terminé: $path');
        
        if (kIsWeb) {
          final webBytes = Uint8List.fromList(path.codeUnits);
          onRecordingComplete?.call(webBytes, 'audio/wav');
        } else {
          await _readAndSendFile(path);
        }
      } else {
        onError?.call('Aucun fichier généré');
      }

      onStop?.call();

    } catch (e) {
      onError?.call('Erreur lors de l\'arrêt: $e');
      onDebug?.call('❌ Erreur: $e');
    }
  }

  /// Lire un fichier audio et envoyer les bytes (mobile uniquement)
  Future<void> _readAndSendFile(String path) async {
    if (kIsWeb) return;
    
    try {
      final file = File(path);
      if (await file.exists()) {
        final bytes = await file.readAsBytes();
        onDebug?.call('📊 Taille du fichier: ${bytes.length} bytes');
        
        final mimeType = path.endsWith('.m4a') ? 'audio/mp4' : 
                         path.endsWith('.aac') ? 'audio/aac' : 
                         path.endsWith('.wav') ? 'audio/wav' : 'audio/mpeg';
        
        onRecordingComplete?.call(bytes, mimeType);
      } else {
        onError?.call('Fichier non trouvé: $path');
      }
    } catch (e) {
      onError?.call('Erreur lecture fichier: $e');
    }
  }

  /// Mettre en pause l'enregistrement
  Future<void> pauseRecording() async {
    try {
      if (!_isRecording || _isPaused) {
        return;
      }

      await _recorder.pause();
      _isPaused = true;

      onDebug?.call('⏸️ Enregistrement mis en pause');
      onPause?.call();

    } catch (e) {
      onError?.call('Erreur lors de la pause: $e');
    }
  }

  /// Reprendre l'enregistrement
  Future<void> resumeRecording() async {
    try {
      if (!_isRecording || !_isPaused) {
        return;
      }

      await _recorder.resume();
      _isPaused = false;

      onDebug?.call('▶️ Enregistrement repris');
      onResume?.call();

    } catch (e) {
      onError?.call('Erreur lors de la reprise: $e');
    }
  }

  /// Obtenir le chemin du dernier enregistrement
  String? get currentPath => _currentPath;

  /// Vérifier si un enregistrement est en cours
  bool get isRecording => _isRecording;

  /// Vérifier si l'enregistrement est en pause
  bool get isPaused => _isPaused;

  /// Obtenir la date de début d'enregistrement
  DateTime? get recordingStartTime => _recordingStartTime;

  /// Réinitialiser l'état sans détruire le recorder (pour réutilisation)
  void reset() {
    _isRecording = false;
    _isPaused = false;
    _currentPath = null;
    _recordingStartTime = null;
  }

  /// Nettoyer les ressources - NE PAS appeler depuis les widgets
  void dispose() {
    reset();
  }
  
  /// Dispose complet - uniquement pour fermeture de l'app
  Future<void> disposeCompletely() async {
    try {
      await _recorder.dispose();
    } catch (e) {
      // Ignorer les erreurs si déjà disposé
    }
  }
}

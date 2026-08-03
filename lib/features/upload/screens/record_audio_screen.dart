import 'dart:async';
import 'dart:io';
import 'dart:typed_data';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';
import 'package:dio/dio.dart';
import 'package:resume_plus_clean/services/api_service.dart';
import 'package:resume_plus_clean/services/snackbar_service.dart';
import 'package:resume_plus_clean/services/audio_draft_service.dart';
import 'package:resume_plus_clean/models/course.dart';
import 'package:resume_plus_clean/models/professeur.dart';
import 'package:resume_plus_clean/features/upload/screens/course_selection_screen.dart';
import '../../../services/mobile_audio_recorder.dart';
import 'package:audioplayers/audioplayers.dart';
import 'package:resume_plus_clean/theme/app_theme.dart';

/// Classe pour gérer les enregistrements sauvegardés
class SavedRecording {
  final String id;
  final Uint8List bytes;
  final String mimeType;
  final String fileName;
  final Course course;
  final DateTime createdAt;
  final int duration;

  SavedRecording({
    required this.id,
    required this.bytes,
    required this.mimeType,
    required this.fileName,
    required this.course,
    required this.createdAt,
    required this.duration,
  });
}

class RecordAudioScreen extends StatefulWidget {
  const RecordAudioScreen({super.key});

  @override
  State<RecordAudioScreen> createState() => _RecordAudioScreenState();
}

enum RecordingState { idle, recording, paused, stopped }

class _RecordAudioScreenState extends State<RecordAudioScreen> with TickerProviderStateMixin {
  // Utiliser le recorder universel (supporte Web et Mobile)
  final MobileAudioRecorder _audioRecorder = MobileAudioRecorder();
  final ApiService _apiService = ApiService();
  final AudioPlayer _audioPlayer = AudioPlayer();
  
  Course? _selectedCourse;
  Professeur? _selectedProfesseur;
  List<Professeur> _professeurs = [];
  bool _isLoadingProfesseurs = false;
  
  // Auto-résolution du professeur via Dispense (Objectif 7)
  String? _autoResolvedProfessorName;
  int? _autoResolvedProfessorId;
  bool _isResolvingProfessor = false;
  final TextEditingController _professorNameController = TextEditingController();
  Uint8List? _recordedBytes;
  String? _recordedMimeType;
  int _recordDuration = 0;
  bool _isPlaying = false;
  bool _isUploading = false;
  int _uploadProgress = 0; // Pourcentage de progression (0-100)
  double _uploadSpeed = 0; // KB/s
  int _estimatedSecondsRemaining = 0;
  DateTime? _uploadStartTime;
  RecordingState _recordingState = RecordingState.idle;
  Timer? _timer;
  
  // Champs obligatoires pour le résumé
  final TextEditingController _titleController = TextEditingController();
  final TextEditingController _priceController = TextEditingController(text: '0');
  double _minimumPrice = 3000; // Valeur par défaut, mise à jour via API
  final _formKey = GlobalKey<FormState>();
  
  // Brouillons audio locaux
  List<AudioDraft> _localDrafts = [];
  bool _isLoadingDrafts = false;
  String? _activeDraftId; // ID du brouillon actuellement chargé dans le formulaire

  // Sauvegarde locale - Liste des 5 derniers enregistrements
  List<SavedRecording> _savedRecordings = [];
  static const int maxSavedRecordings = 5;
  
  // Upload fichier audio existant
  bool _isFileUploaded = false;
  String? _uploadedFileName;
  bool _isImporting = false; // Indique qu'une importation est en cours
  
  // Animation controllers pour les effets visuels
  late AnimationController _pulseController;
  late Animation<double> _pulseAnimation;

  @override
  void initState() {
    super.initState();
    _initializeAnimations();
    _setupRecorderCallbacks();
    _loadProfesseurs();
    _loadPricingConfig();
    _loadDraftsList();
  }

  /// Charge la liste des brouillons locaux depuis le service.
  Future<void> _loadDraftsList() async {
    if (!mounted) return;
    setState(() => _isLoadingDrafts = true);
    final drafts = await AudioDraftService().listDrafts();
    if (mounted) {
      setState(() {
        _localDrafts = drafts;
        _isLoadingDrafts = false;
      });
    }
  }

  /// Charge un brouillon spécifique dans le formulaire.
  Future<void> _loadDraftIntoForm(AudioDraft draft) async {
    if (!mounted) return;

    // Restaurer le titre
    if (draft.title != null && draft.title!.isNotEmpty) {
      _titleController.text = draft.title!;
    }

    // Restaurer la durée
    if (draft.duration > 0) {
      _recordDuration = draft.duration;
    }

    // Restaurer le prix
    if (draft.price != null && draft.price! > 0) {
      _priceController.text = draft.price!.toStringAsFixed(0);
    }

    // Restaurer le cours
    if (draft.courseId != null && draft.courseName != null) {
      _selectedCourse = Course(
        id: draft.courseId!,
        nom: draft.courseName!,
        filiere: '',
        description: '',
        university: '',
        createdAt: DateTime.now(),
      );
    }

    // Restaurer les bytes audio
    Uint8List? audioBytes = draft.audioBytes;
    if (audioBytes == null && draft.audioFilePath != null) {
      try {
        final file = File(draft.audioFilePath!);
        if (await file.exists()) {
          audioBytes = await file.readAsBytes();
        }
      } catch (e) {
        print('⚠️ AudioDraft: erreur lecture fichier: $e');
      }
    }

    if (audioBytes != null) {
      _recordedBytes = audioBytes;
      _recordedMimeType = draft.mimeType ?? 'audio/m4a';
    }

    _activeDraftId = draft.id;

    if (mounted) setState(() {});
  }

  Future<void> _loadPricingConfig() async {
    final minPrice = await _apiService.getMinimumResumePrice();
    if (mounted) {
      setState(() {
        _minimumPrice = minPrice;
        _priceController.text = minPrice.toStringAsFixed(0);
      });
    }
  }

  Future<void> _loadProfesseurs({int retryCount = 0}) async {
    const maxRetries = 3;
    setState(() {
      _isLoadingProfesseurs = true;
    });

    try {
      print('🔍 [Flutter] Chargement des professeurs... (tentative ${retryCount + 1}/$maxRetries)');
      final professeursData = await _apiService.getProfesseurs();
      print('✅ [Flutter] ${professeursData.length} professeurs chargés');

      setState(() {
        _professeurs = professeursData.map((json) => Professeur.fromJson(json)).toList();
        _isLoadingProfesseurs = false;
      });
    } on DioException catch (e) {
      print('❌ [Flutter] DioException chargement professeurs: ${e.type} | ${e.message} | status: ${e.response?.statusCode}');
      setState(() {
        _isLoadingProfesseurs = false;
      });

      if (retryCount < maxRetries - 1) {
        print('🔄 [Flutter] Retry dans 2s...');
        await Future.delayed(const Duration(seconds: 2));
        return _loadProfesseurs(retryCount: retryCount + 1);
      }

      // Message utilisateur clair sans DioException brut
      final statusCode = e.response?.statusCode;
      String userMessage;
      if (statusCode == 500) {
        userMessage = 'Le serveur rencontre un problème temporaire. Veuillez réessayer plus tard.';
      } else if (statusCode == 403) {
        userMessage = 'Accès refusé. Vérifiez vos permissions.';
      } else if (statusCode == 404) {
        userMessage = 'Service indisponible.';
      } else {
        userMessage = 'Impossible de charger la liste des professeurs. Vérifiez votre connexion.';
      }
      SnackbarService.show(userMessage, isError: true);
    } catch (e) {
      print('❌ [Flutter] Erreur inattendue chargement professeurs: $e');
      setState(() {
        _isLoadingProfesseurs = false;
      });
      SnackbarService.show('Impossible de charger la liste des professeurs.', isError: true);
    }
  }

  void _initializeAnimations() {
    _pulseController = AnimationController(
      duration: const Duration(milliseconds: 1000),
      vsync: this,
    );
    _pulseAnimation = Tween<double>(begin: 0.8, end: 1.2).animate(
      CurvedAnimation(parent: _pulseController, curve: Curves.easeInOut),
    );
  }

  void _setupRecorderCallbacks() {
    // Callbacks pour le recorder universel (Web + Mobile)
    _audioRecorder.onStart = _onRecordingStart;
    _audioRecorder.onStop = _onRecordingStop;
    _audioRecorder.onPause = _onRecordingPause;
    _audioRecorder.onResume = _onRecordingResume;
    _audioRecorder.onRecordingComplete = _onRecordingComplete;
    _audioRecorder.onError = _onRecordingError;
    _audioRecorder.onDebug = (msg) => print('🎤 Recorder: $msg');

    // Configurer le player audio
    _audioPlayer.onPlayerComplete.listen((_) {
      if (!mounted) return;
      setState(() {
        _isPlaying = false;
      });
    });
  }

  void _onRecordingStart() {
    if (!mounted) return;
    setState(() {
      _recordingState = RecordingState.recording;
    });
    _startTimer();
    _pulseController.repeat(reverse: true);
  }

  void _onRecordingStop() {
    if (!mounted) return;
    setState(() {
      _recordingState = RecordingState.stopped;
    });
    _stopTimer();
    _pulseController.stop();
  }

  void _onRecordingPause() {
    if (!mounted) return;
    setState(() {
      _recordingState = RecordingState.paused;
    });
    _stopTimer();
    _pulseController.stop();
  }

  void _onRecordingResume() {
    if (!mounted) return;
    setState(() {
      _recordingState = RecordingState.recording;
    });
    _startTimer();
    _pulseController.repeat(reverse: true);
  }

  void _onRecordingComplete(Uint8List bytes, String mimeType) {
    if (!mounted) return;
    setState(() {
      _recordedBytes = bytes;
      _recordedMimeType = mimeType;
    });
    // Sauvegarder automatiquement le brouillon
    _autoSaveDraft(bytes, mimeType);
  }

  /// Sauvegarde automatique du brouillon audio après chaque enregistrement.
  Future<void> _autoSaveDraft(Uint8List bytes, String mimeType) async {
    final draftService = AudioDraftService();

    // Vérifier la limite avant d'ajouter
    if (await draftService.isFull()) {
      SnackbarService.show(
        'Limite de ${AudioDraftService.maxDrafts} brouillons atteinte. '
        'Envoyez ou supprimez un brouillon avant d\'en créer un nouveau.',
        isError: true,
      );
      return;
    }

    final draft = AudioDraft(
      id: DateTime.now().millisecondsSinceEpoch.toString(),
      audioBytes: bytes,
      mimeType: mimeType,
      fileName: 'recording_${DateTime.now().millisecondsSinceEpoch}.m4a',
      courseId: _selectedCourse?.id,
      courseName: _selectedCourse?.nom,
      title: _titleController.text.trim(),
      duration: _recordDuration,
      professeurNom: _professorNameController.text.trim().isNotEmpty
          ? _professorNameController.text.trim()
          : _autoResolvedProfessorName,
      professeurId: _autoResolvedProfessorId ?? _selectedProfesseur?.id,
    );

    final price = double.tryParse(_priceController.text.trim());
    if (price != null) draft.price = price;

    final added = await draftService.addDraft(draft);
    if (added) {
      _activeDraftId = draft.id;
      await _loadDraftsList();
    }
  }

  void _onRecordingError(String error) {
    SnackbarService.show('❌ Erreur d\'enregistrement: $error', isError: true);
  }

  void _startTimer() {
    _timer = Timer.periodic(const Duration(seconds: 1), (timer) {
      setState(() {
        _recordDuration++;
      });
    });
  }

  void _stopTimer() {
    _timer?.cancel();
    _timer = null;
  }

  String _formatDuration(int seconds) {
    final minutes = seconds ~/ 60;
    final remainingSeconds = seconds % 60;
    return '${minutes.toString().padLeft(2, '0')}:${remainingSeconds.toString().padLeft(2, '0')}';
  }

  Future<void> _selectCourse() async {
    final selectedCourse = await Navigator.of(context).push<Course>(
      MaterialPageRoute(
        builder: (ctx) => CourseSelectionScreen(
          onCourseSelected: (course) {
            Navigator.of(ctx).pop(course);
          },
        ),
      ),
    );
    
    if (selectedCourse != null && mounted) {
      setState(() {
        _selectedCourse = selectedCourse;
        _autoResolvedProfessorName = null;
        _autoResolvedProfessorId = null;
        _selectedProfesseur = null;
        _professorNameController.clear();
        _isResolvingProfessor = true;
      });
      SnackbarService.show('✅ Cours sélectionné: ${selectedCourse.nom}', isError: false);
      
      // Auto-résoudre le professeur via Dispense (Objectif 7)
      try {
        final result = await _apiService.resolveProfessor(selectedCourse.id);
        if (!mounted) return;
        if (result['found'] == true && result['professor'] != null) {
          final prof = result['professor'] as Map<String, dynamic>;
          setState(() {
            _autoResolvedProfessorName = prof['name'] as String?;
            _autoResolvedProfessorId = prof['professeur_fk'] as int?;
            _isResolvingProfessor = false;
          });
        } else {
          setState(() => _isResolvingProfessor = false);
        }
      } catch (_) {
        if (mounted) setState(() => _isResolvingProfessor = false);
      }
    }
  }

  /// Sélectionner un fichier audio depuis l'appareil
  Future<void> _pickAudioFile() async {
    try {
      final result = await FilePicker.platform.pickFiles(
        type: FileType.audio,
        allowMultiple: false,
      );

      if (result == null || result.files.isEmpty) return;

      final pickedFile = result.files.first;

      // Feedback immédiat dès que le fichier est sélectionné
      if (mounted) {
        setState(() => _isImporting = true);
        SnackbarService.show(
          '⏳ Importation de "${pickedFile.name}"...',
          isError: false,
        );
      }

      if (pickedFile.path == null) {
        if (mounted) setState(() => _isImporting = false);
        SnackbarService.show('Impossible de lire le fichier', isError: true);
        return;
      }

      // Lire les bytes du fichier
      final file = File(pickedFile.path!);
      final bytes = await file.readAsBytes();

      if (bytes.isEmpty) {
        if (mounted) setState(() => _isImporting = false);
        SnackbarService.show('Le fichier est vide', isError: true);
        return;
      }

      // Vérifier la durée de l'audio (<= 3h)
      const int maxDurationSeconds = 10800; // 3 heures = 180 minutes
      final tempPlayer = AudioPlayer();
      try {
        await tempPlayer.setSource(DeviceFileSource(pickedFile.path!));
        final duration = await tempPlayer.getDuration();
        await tempPlayer.dispose();

        // Logs de debug détaillés
        if (duration != null) {
          final totalSeconds = duration.inSeconds;
          final totalMinutes = totalSeconds / 60.0;
          print('🎵 [Flutter] Fichier audio sélectionné: ${pickedFile.name}');
          print('🎵 [Flutter] Durée brute (Duration): $duration');
          print('🎵 [Flutter] Durée en secondes: $totalSeconds');
          print('🎵 [Flutter] Durée en minutes: ${totalMinutes.toStringAsFixed(2)}');
          print('🎵 [Flutter] Limite max: ${maxDurationSeconds}s (${maxDurationSeconds ~/ 60}min)');
        } else {
          print('⚠️ [Flutter] Impossible de lire la durée du fichier');
        }

        if (duration != null && duration.inSeconds > maxDurationSeconds) {
          SnackbarService.show(
            'La durée de l\'audio ne doit pas dépasser 3 heures (${_formatDuration(duration.inSeconds)} détecté)',
            isError: true,
          );
          return;
        }

        // Déterminer le type MIME
        final extension = pickedFile.extension?.toLowerCase() ?? '';
        String mimeType;
        switch (extension) {
          case 'mp3':
            mimeType = 'audio/mpeg';
            break;
          case 'wav':
            mimeType = 'audio/wav';
            break;
          case 'ogg':
            mimeType = 'audio/ogg';
            break;
          case 'm4a':
          case 'aac':
            mimeType = 'audio/aac';
            break;
          case 'webm':
            mimeType = 'audio/webm';
            break;
          default:
            mimeType = 'audio/$extension';
        }

        setState(() {
          _recordedBytes = bytes;
          _recordedMimeType = mimeType;
          _recordDuration = duration?.inSeconds ?? 0;
          _recordingState = RecordingState.stopped;
          _isFileUploaded = true;
          _uploadedFileName = pickedFile.name;
          _isImporting = false;
        });

        SnackbarService.show(
          '✅ Fichier importé avec succès: ${pickedFile.name}',
          isError: false,
        );
      } catch (e) {
        await tempPlayer.dispose();
        // Si on ne peut pas lire la durée, accepter quand même le fichier
        // mais avec un avertissement
        setState(() {
          _recordedBytes = bytes;
          _recordedMimeType = 'audio/${pickedFile.extension?.toLowerCase() ?? 'wav'}';
          _recordDuration = 0;
          _recordingState = RecordingState.stopped;
          _isFileUploaded = true;
          _uploadedFileName = pickedFile.name;
          _isImporting = false;
        });

        SnackbarService.show(
          '✅ Fichier importé (durée non vérifiable): ${pickedFile.name}',
          isError: false,
        );
      }
    } catch (e) {
      if (mounted) setState(() => _isImporting = false);
      SnackbarService.show('❌ Erreur lors de l\'importation: $e', isError: true);
    }
  }

  /// Supprimer le fichier audio uploadé et remettre en mode enregistrement
  void _clearUploadedFile() {
    _stopPlayback();
    setState(() {
      _recordedBytes = null;
      _recordedMimeType = null;
      _recordDuration = 0;
      _recordingState = RecordingState.idle;
      _isFileUploaded = false;
      _uploadedFileName = null;
    });
  }

  Future<void> _startRecording() async {
    if (_selectedCourse == null) {
      SnackbarService.show('⚠️ Veuillez d\'abord sélectionner un cours', isError: true);
      return;
    }

    // Vérifier la limite de brouillons avant d'enregistrer
    if (await AudioDraftService().isFull()) {
      SnackbarService.show(
        '⚠️ Limite de ${AudioDraftService.maxDrafts} brouillons atteinte. '
        'Envoyez ou supprimez un brouillon avant d\'en créer un nouveau.',
        isError: true,
      );
      return;
    }

    final success = await _audioRecorder.startRecording();
    
    if (!success) {
      SnackbarService.show('❌ Impossible de démarrer l\'enregistrement', isError: true);
    }
  }

  Future<void> _stopRecording() async {
    await _audioRecorder.stopRecording();
  }

  Future<void> _pauseRecording() async {
    await _audioRecorder.pauseRecording();
  }

  Future<void> _resumeRecording() async {
    await _audioRecorder.resumeRecording();
  }

  /// Lecture de l'enregistrement audio local
  Future<void> _playRecording() async {
    if (_recordedBytes == null || _recordedBytes!.isEmpty) {
      SnackbarService.show('❌ Aucun audio à lire', isError: true);
      return;
    }

    try {
      setState(() {
        _isPlaying = true;
      });

      // Utiliser audioplayers pour lire les bytes audio
      await _audioPlayer.play(BytesSource(_recordedBytes!));
      SnackbarService.show('🎵 Lecture en cours...');

    } catch (e) {
      setState(() {
        _isPlaying = false;
      });
      SnackbarService.show('❌ Erreur de lecture: $e', isError: true);
    }
  }

  /// Lecture d'un enregistrement sauvegardé
  Future<void> _playSavedRecording(SavedRecording recording) async {
    try {
      setState(() {
        _isPlaying = true;
      });

      // Utiliser audioplayers pour lire les bytes audio
      await _audioPlayer.play(BytesSource(recording.bytes));
      SnackbarService.show('🎵 Lecture ${recording.course.nom}...');

    } catch (e) {
      setState(() {
        _isPlaying = false;
      });
      SnackbarService.show('❌ Erreur de lecture: $e', isError: true);
    }
  }

  /// Arrêter la lecture audio
  void _stopPlayback() {
    try {
      _audioPlayer.stop();
      
      setState(() {
        _isPlaying = false;
      });
      
      SnackbarService.show('⏹️ Lecture arrêtée');
      
    } catch (e) {
      print('❌ Erreur arrêt lecture: $e');
    }
  }

  /// Ajouter un enregistrement à la liste sauvegardée
  void _addSavedRecording(SavedRecording recording) {
    setState(() {
      _savedRecordings.insert(0, recording);
      
      // Limiter à 5 enregistrements maximum
      if (_savedRecordings.length > maxSavedRecordings) {
        _savedRecordings = _savedRecordings.take(maxSavedRecordings).toList();
      }
    });
  }

  /// Supprimer un enregistrement sauvegardé
  void _removeSavedRecording(String recordingId) {
    setState(() {
      _savedRecordings.removeWhere((recording) => recording.id == recordingId);
    });
  }

  Future<void> _uploadRecording() async {
    // Valider le formulaire
    if (!_formKey.currentState!.validate()) {
      SnackbarService.show('❌ Veuillez remplir tous les champs obligatoires', isError: true);
      return;
    }

    if (_recordedBytes == null) {
      SnackbarService.show('❌ Aucun enregistrement audio', isError: true);
      return;
    }

    if (_selectedCourse == null) {
      SnackbarService.show('❌ Veuillez sélectionner un cours', isError: true);
      return;
    }

    setState(() {
      _isUploading = true;
      _uploadProgress = 0;
      _uploadSpeed = 0;
      _estimatedSecondsRemaining = 0;
      _uploadStartTime = DateTime.now();
    });

    int? sessionId;

    try {
      final timestamp = DateTime.now().millisecondsSinceEpoch;
      final fileName = _isFileUploaded && _uploadedFileName != null
          ? _uploadedFileName!
          : 'session_${_selectedCourse!.id}_$timestamp.webm';
      final summaryTitle = _titleController.text.trim();
      final summaryPrice = double.tryParse(_priceController.text.trim()) ?? 0.0;

      // Logs de debug avant upload
      print('🚀 [Flutter Upload] Préparation upload audio:');
      print('   - Fichier: $fileName');
      print('   - Taille: ${_recordedBytes!.length} bytes (${(_recordedBytes!.length / 1024 / 1024).toStringAsFixed(2)} MB)');
      print('   - MIME: ${_recordedMimeType ?? "audio/wav"}');
      print('   - Durée: ${_recordDuration}s (${(_recordDuration / 60).toStringAsFixed(2)}min)');
      print('   - Limite max: 10800s (180min)');
      print('   - Statut durée: ${_recordDuration <= 10800 ? "✅ Valide" : "❌ Trop longue"}');

      final metadata = <String, dynamic>{
        'course_id': _selectedCourse!.id,
        'title': 'Session ${_selectedCourse!.nom}',
        'description': 'Enregistrement de session pour le cours ${_selectedCourse!.nom}',
        'summary_title': summaryTitle,
        'summary_price': summaryPrice.toString(),
        'audio_duration': _recordDuration.toString(),
      };
      if (_selectedProfesseur != null) {
        metadata['professeur_id'] = _selectedProfesseur!.id;
      }
      // Envoyer le professeur auto-résolu ou le nom saisi manuellement (Objectif 7)
      if (_autoResolvedProfessorId != null) {
        metadata['professeur_id'] = _autoResolvedProfessorId!;
      }
      final profName = _professorNameController.text.trim();
      if (profName.isNotEmpty) {
        metadata['professeur_nom'] = profName;
      }

      final response = await _apiService.uploadAudio(
        audioBytes: _recordedBytes!,
        fileName: fileName,
        mimeType: _recordedMimeType ?? 'audio/wav',
        metadata: metadata,
        onSendProgress: (sent, total) {
          if (total > 0) {
            final now = DateTime.now();
            final elapsed = _uploadStartTime != null
                ? now.difference(_uploadStartTime!).inMilliseconds / 1000.0
                : 0.0;

            double speed = 0;
            int remainingSeconds = 0;

            if (elapsed > 0) {
              speed = (sent / 1024.0) / elapsed; // KB/s
              final remainingBytes = total - sent;
              if (speed > 0) {
                remainingSeconds = (remainingBytes / 1024.0 / speed).round();
              }
            }

            // Upload phase: 0-80%
            final uploadPercent = (sent / total) * 80;

            setState(() {
              _uploadProgress = uploadPercent.round();
              _uploadSpeed = speed;
              _estimatedSecondsRemaining = remainingSeconds;
            });
          }
        },
      );

      // Get session ID from response
      sessionId = response['session']?['id'];

      // Upload complete - show 100% briefly
      if (mounted) {
        setState(() {
          _uploadProgress = 100;
        });
        await Future.delayed(const Duration(milliseconds: 500));
      }

      // Start polling for status in background (non-blocking)
      if (sessionId != null && mounted) {
        _pollProcessingStatus(sessionId);
      }

      // Afficher un dialogue clair de confirmation
      if (mounted) {
        showDialog(
          context: context,
          builder: (ctx) => AlertDialog(
            icon: const Icon(Icons.check_circle, color: Colors.green, size: 48),
            title: const Text('Session enregistrée avec succès'),
            content: const Text(
              'Votre audio est en cours de traitement.\n\n'
              'Pour voir le résultat, allez dans Accueil puis cliquez '
              'sur l\'icône en haut à droite (🎙️) pour accéder à vos sessions audio.',
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.pop(ctx),
                child: const Text('Compris'),
              ),
            ],
          ),
        );
      }
      
      // Créer un enregistrement sauvegardé
      final savedRecording = SavedRecording(
        id: timestamp.toString(),
        bytes: Uint8List.fromList(_recordedBytes!),
        mimeType: _recordedMimeType ?? 'audio/webm',
        fileName: fileName,
        course: _selectedCourse!,
        createdAt: DateTime.now(),
        duration: _recordDuration,
      );
      
      // Ajouter à la liste des enregistrements sauvegardés
      _addSavedRecording(savedRecording);
      
      // Supprimer le brouillon local après envoi réussi
      if (_activeDraftId != null) {
        await AudioDraftService().deleteDraft(_activeDraftId!);
        _activeDraftId = null;
      } else {
        // Fallback : supprimer le plus ancien brouillon sans fichier
        final drafts = await AudioDraftService().listDrafts();
        if (drafts.isNotEmpty) {
          await AudioDraftService().deleteDraft(drafts.first.id);
        }
      }
      await _loadDraftsList();
      print('🗑️ AudioDraft: brouillon supprimé après upload réussi');

      // Réinitialiser l'enregistrement en cours
      setState(() {
        _recordedBytes = null;
        _recordedMimeType = null;
        _recordDuration = 0;
        _recordingState = RecordingState.idle;
        _selectedCourse = null;
        _isPlaying = false;
        _isFileUploaded = false;
        _uploadedFileName = null;
        _titleController.clear();
        _priceController.text = _minimumPrice.toStringAsFixed(0);
      });

      // Arrêter la lecture si en cours
      _stopPlayback();

    } catch (e) {
      SnackbarService.show('❌ Erreur d\'upload: $e', isError: true);
    } finally {
      setState(() {
        _isUploading = false;
      });
    }
  }

  @override
  void dispose() {
    _pulseController.dispose();
    _titleController.dispose();
    _priceController.dispose();
    _professorNameController.dispose();
    // Ne pas disposer le recorder car c'est un singleton - juste reset
    _audioRecorder.reset();
    _audioPlayer.dispose();
    _stopTimer();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final topPadding = MediaQuery.of(context).padding.top;

    return Scaffold(
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      body: SingleChildScrollView(
        child: Column(
          children: [
            // Header bleu courbé
            Container(
              padding: EdgeInsets.only(top: topPadding + 8, left: 20, right: 20, bottom: 20),
              decoration: const BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                  colors: [AppTheme.primaryBlueDark, AppTheme.primaryBlue, AppTheme.primaryBlueLight],
                ),
                borderRadius: BorderRadius.only(
                  bottomLeft: Radius.circular(24),
                  bottomRight: Radius.circular(24),
                ),
              ),
              child: Row(
                children: [
                  GestureDetector(
                    onTap: () => Navigator.of(context).pop(),
                    child: Container(
                      width: 40, height: 40,
                      decoration: BoxDecoration(
                        color: Colors.white.withOpacity(0.2),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: const Icon(Icons.arrow_back_rounded, color: Colors.white, size: 22),
                    ),
                  ),
                  const SizedBox(width: 14),
                  Text(
                    'Enregistrement Audio',
                    style: theme.textTheme.titleLarge?.copyWith(color: Colors.white, fontWeight: FontWeight.w700),
                  ),
                ],
              ),
            ),

            Padding(
              padding: const EdgeInsets.all(20),
              child: Form(
          key: _formKey,
          child: Column(
            children: [
              // Sélection de cours (obligatoire)
              Container(
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(14),
                  boxShadow: AppTheme.softShadow,
                ),
                child: ListTile(
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                  leading: Container(
                    width: 40, height: 40,
                    decoration: BoxDecoration(
                      color: (_selectedCourse != null ? AppTheme.success : AppTheme.primaryBlue).withOpacity(0.1),
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: Icon(
                      Icons.school_rounded, 
                      color: _selectedCourse != null ? AppTheme.success : AppTheme.primaryBlue,
                      size: 20,
                    ),
                  ),
                  title: Text(_selectedCourse?.nom ?? 'Sélectionner un cours *', style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14, color: AppTheme.textPrimary)),
                  subtitle: _selectedCourse != null 
                      ? Text('${_selectedCourse!.universiteDisplay} - ${_selectedCourse!.filiereDisplay}', style: const TextStyle(color: AppTheme.textLight, fontSize: 12))
                      : const Text('Obligatoire', style: TextStyle(color: AppTheme.error, fontSize: 12)),
                  trailing: const Icon(Icons.chevron_right_rounded, color: AppTheme.textLight),
                  onTap: _selectCourse,
                ),
              ),
              
              const SizedBox(height: 16),
              
              // Titre du résumé (obligatoire)
              TextFormField(
                controller: _titleController,
                decoration: InputDecoration(
                  labelText: 'Titre du résumé *',
                  hintText: 'Ex: Chapitre 1 - Introduction',
                  prefixIcon: const Icon(Icons.title),
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                  filled: true,
                ),
                validator: (value) {
                  if (value == null || value.trim().isEmpty) {
                    return 'Le titre est obligatoire';
                  }
                  return null;
                },
              ),
              
              const SizedBox(height: 16),
              
              // Prix du résumé (minimum dynamique depuis ResumePricingConfig)
              TextFormField(
                controller: _priceController,
                decoration: InputDecoration(
                  labelText: 'Prix du résumé (CDF) *',
                  hintText: 'Prix minimum : ${_minimumPrice.toStringAsFixed(0)} CDF',
                  prefixIcon: const Icon(Icons.attach_money),
                  suffixText: 'CDF',
                  helperText: 'Prix minimum : ${_minimumPrice.toStringAsFixed(0)} CDF. Les résumés gratuits ne sont pas autorisés.',
                  helperMaxLines: 2,
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                  filled: true,
                ),
                keyboardType: const TextInputType.numberWithOptions(decimal: true),
                validator: (value) {
                  if (value == null || value.trim().isEmpty) {
                    return 'Le prix est obligatoire';
                  }
                  final price = double.tryParse(value);
                  if (price == null) {
                    return 'Entrez un prix valide (nombre)';
                  }
                  if (price < _minimumPrice) {
                    return 'Le prix minimum est ${_minimumPrice.toStringAsFixed(0)} CDF';
                  }
                  return null;
                },
              ),
              
              const SizedBox(height: 16),

              // Professeur (auto-résolu ou saisie libre) — Objectif 7
              if (_isResolvingProfessor)
                const Padding(
                  padding: EdgeInsets.symmetric(vertical: 12),
                  child: Center(child: CircularProgressIndicator()),
                )
              else if (_autoResolvedProfessorName != null)
                // Cas 1 : Professeur trouvé via Dispense → affichage en lecture seule
                Container(
                  padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 16),
                  decoration: BoxDecoration(
                    color: AppTheme.success.withOpacity(0.08),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: AppTheme.success.withOpacity(0.3)),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.check_circle, color: AppTheme.success, size: 20),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text('Professeur', style: TextStyle(fontSize: 11, color: AppTheme.textLight)),
                            Text(_autoResolvedProfessorName!, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14)),
                          ],
                        ),
                      ),
                    ],
                  ),
                )
              else
                // Cas 2 : Aucune dispense → champ libre
                TextFormField(
                  controller: _professorNameController,
                  decoration: InputDecoration(
                    labelText: 'Nom du professeur',
                    hintText: 'Ex: Mme Judith',
                    prefixIcon: const Icon(Icons.person),
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                    filled: true,
                  ),
                ),
              
              const SizedBox(height: 24),

            // Bouton d'import de fichier audio (visible uniquement si pas en cours d'enregistrement)
            if (!_isFileUploaded && _recordingState == RecordingState.idle && _recordedBytes == null)
              Container(
                width: double.infinity,
                decoration: BoxDecoration(
                  border: Border.all(
                    color: _isImporting
                        ? AppTheme.primaryBlue.withOpacity(0.6)
                        : AppTheme.primaryBlue.withOpacity(0.3),
                    width: 1.5,
                  ),
                  borderRadius: BorderRadius.circular(14),
                  color: _isImporting
                      ? AppTheme.primaryBlue.withOpacity(0.08)
                      : AppTheme.primaryBlue.withOpacity(0.05),
                ),
                child: Material(
                  color: Colors.transparent,
                  borderRadius: BorderRadius.circular(14),
                  child: InkWell(
                    borderRadius: BorderRadius.circular(14),
                    onTap: _isImporting ? null : _pickAudioFile,
                    child: Padding(
                      padding: const EdgeInsets.symmetric(vertical: 18, horizontal: 16),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Container(
                            width: 40, height: 40,
                            decoration: BoxDecoration(
                              color: AppTheme.primaryBlue.withOpacity(0.1),
                              borderRadius: BorderRadius.circular(10),
                            ),
                            child: _isImporting
                                ? const Padding(
                                    padding: EdgeInsets.all(10),
                                    child: CircularProgressIndicator(
                                      strokeWidth: 2.5,
                                      color: AppTheme.primaryBlue,
                                    ),
                                  )
                                : const Icon(Icons.upload_file_rounded, color: AppTheme.primaryBlue, size: 22),
                          ),
                          const SizedBox(width: 12),
                          Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                _isImporting ? 'Importation en cours...' : 'Importer un fichier audio',
                                style: theme.textTheme.titleSmall?.copyWith(
                                  fontWeight: FontWeight.w600,
                                  color: AppTheme.primaryBlue,
                                ),
                              ),
                              Text(
                                _isImporting
                                    ? 'Lecture et vérification du fichier...'
                                    : 'MP3, WAV, OGG, M4A • Max 3 heures',
                                style: TextStyle(color: AppTheme.textLight, fontSize: 12),
                              ),
                            ],
                          ),
                          const Spacer(),
                          if (_isImporting)
                            const SizedBox(width: 20)
                          else
                            const Icon(Icons.chevron_right_rounded, color: AppTheme.primaryBlue),
                        ],
                      ),
                    ),
                  ),
                ),
              ),

            if (!_isFileUploaded && _recordingState == RecordingState.idle && _recordedBytes == null)
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 12),
                child: Row(
                  children: [
                    const Expanded(child: Divider()),
                    Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 16),
                      child: Text('OU', style: TextStyle(color: AppTheme.textLight, fontWeight: FontWeight.w600, fontSize: 13)),
                    ),
                    const Expanded(child: Divider()),
                  ],
                ),
              ),

            // Fichier audio uploadé - info card
            if (_isFileUploaded && _recordedBytes != null)
              _buildUploadedFileInfo(),

            // Visualisation de l'enregistrement (masquée si fichier uploadé)
            if (!_isFileUploaded)
              SizedBox(
                height: 300,
                child: Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      // Bouton d'enregistrement principal
                      AnimatedBuilder(
                        animation: _pulseAnimation,
                        builder: (context, child) {
                          return Transform.scale(
                            scale: _recordingState == RecordingState.recording 
                                ? _pulseAnimation.value 
                                : 1.0,
                            child: Container(
                              width: 120,
                              height: 120,
                              decoration: BoxDecoration(
                                shape: BoxShape.circle,
                                color: _getRecordingColor(),
                                boxShadow: [
                                  BoxShadow(
                                    color: _getRecordingColor().withOpacity(0.3),
                                    blurRadius: 20,
                                    spreadRadius: 5,
                                  ),
                                ],
                              ),
                              child: Icon(
                                _getRecordingIcon(),
                                size: 48,
                                color: Colors.white,
                              ),
                            ),
                          );
                        },
                      ),
                      
                      const SizedBox(height: 24),
                      
                      // Durée d'enregistrement
                      Text(
                        _formatDuration(_recordDuration),
                        style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                          fontWeight: FontWeight.bold,
                          color: _getRecordingColor(),
                        ),
                      ),
                      
                      const SizedBox(height: 16),
                      
                      // État de l'enregistrement
                      Text(
                        _getRecordingStateText(),
                        style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                          color: Colors.grey[600],
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            
            // Contrôles d'enregistrement (masqués si fichier uploadé)
            if (!_isFileUploaded) _buildRecordingControls(),
            
            const SizedBox(height: 16),
            
            // Contrôles de session
            if (_recordedBytes != null) _buildSessionControls(),
            
            const SizedBox(height: 16),
            
            // Section des enregistrements sauvegardés
            if (_savedRecordings.isNotEmpty) _buildSavedRecordingsSection(),
            ],
          ),
        ),
      ),
          ],
        ),
      ),
    );
  }

  Widget _buildUploadedFileInfo() {
    final theme = Theme.of(context);
    return Container(
      width: double.infinity,
      decoration: BoxDecoration(
        color: theme.colorScheme.surface,
        borderRadius: BorderRadius.circular(16),
        boxShadow: AppTheme.softShadow,
        border: Border.all(color: AppTheme.success.withOpacity(0.3)),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            Row(
              children: [
                Container(
                  width: 44, height: 44,
                  decoration: BoxDecoration(
                    color: AppTheme.success.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: const Icon(Icons.audio_file_rounded, color: AppTheme.success, size: 24),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        _uploadedFileName ?? 'Fichier audio',
                        style: theme.textTheme.titleSmall?.copyWith(
                          fontWeight: FontWeight.w600,
                          color: theme.colorScheme.onSurface,
                        ),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                      const SizedBox(height: 2),
                      Text(
                        'Durée: ${_formatDuration(_recordDuration)} • Taille: ${(_recordedBytes!.length / 1024).toStringAsFixed(1)} KB',
                        style: TextStyle(color: theme.colorScheme.onSurface.withOpacity(0.6), fontSize: 12),
                      ),
                    ],
                  ),
                ),
                IconButton(
                  onPressed: _clearUploadedFile,
                  icon: const Icon(Icons.close_rounded, size: 20),
                  tooltip: 'Retirer le fichier',
                  style: IconButton.styleFrom(
                    foregroundColor: AppTheme.error,
                    backgroundColor: AppTheme.error.withOpacity(0.1),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
              decoration: BoxDecoration(
                color: AppTheme.warning.withOpacity(0.1),
                borderRadius: BorderRadius.circular(10),
              ),
              child: Row(
                children: [
                  const Icon(Icons.info_outline_rounded, size: 16, color: AppTheme.warning),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      'L\'enregistrement audio est désactivé lorsqu\'un fichier est importé.',
                      style: TextStyle(color: AppTheme.warning, fontSize: 12, fontWeight: FontWeight.w500),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  /// Panneau listant tous les brouillons audio locaux.
  /// Chaque brouillon peut être chargé dans le formulaire ou supprimé.
  Widget _buildDraftsPanel() {
    if (_localDrafts.isEmpty) return const SizedBox.shrink();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Icon(Icons.save_rounded, size: 16, color: AppTheme.warning),
            const SizedBox(width: 6),
            Text(
              'Brouillons locaux (${_localDrafts.length}/${AudioDraftService.maxDrafts})',
              style: const TextStyle(
                fontSize: 13, fontWeight: FontWeight.w600, color: AppTheme.textSecondary,
              ),
            ),
          ],
        ),
        const SizedBox(height: 8),
        ..._localDrafts.map((draft) => _buildDraftTile(draft)),
      ],
    );
  }

  /// Tuile compacte d'un brouillon local, responsive petit/moyen écran.
  Widget _buildDraftTile(AudioDraft draft) {
    final isActive = draft.id == _activeDraftId;
    final theme = Theme.of(context);

    return Container(
      margin: const EdgeInsets.only(bottom: 6),
      padding: const EdgeInsets.fromLTRB(10, 8, 4, 8),
      decoration: BoxDecoration(
        color: isActive ? AppTheme.primaryBlue.withOpacity(0.06) : theme.colorScheme.surface,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(
          color: isActive ? AppTheme.primaryBlue.withOpacity(0.3) : theme.dividerTheme.color ?? Colors.grey.shade200,
          width: isActive ? 1.5 : 1,
        ),
      ),
      child: Row(
        children: [
          // Icône
          Icon(Icons.audio_file_rounded, size: 24,
              color: isActive ? AppTheme.primaryBlue : AppTheme.textLight),
          const SizedBox(width: 8),
          // Texte
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  draft.title ?? draft.fileName ?? 'Sans titre',
                  style: TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.w600,
                    color: theme.colorScheme.onSurface,
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                const SizedBox(height: 1),
                Flexible(
                  child: Text(
                    '${draft.durationFormatted} — ${draft.createdAt.toString().substring(0, 10)}',
                    style: TextStyle(fontSize: 11, color: theme.colorScheme.onSurface.withOpacity(0.5)),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
              ],
            ),
          ),
          // Charger
          if (!isActive)
            SizedBox(
              width: 30, height: 30,
              child: IconButton(
                onPressed: () async {
                  await _loadDraftIntoForm(draft);
                  if (mounted) setState(() {});
                },
                icon: Icon(Icons.download_rounded, size: 16, color: AppTheme.primaryBlue),
                tooltip: 'Charger',
                padding: EdgeInsets.zero,
              ),
            ),
          // Supprimer
          SizedBox(
            width: 30, height: 30,
            child: IconButton(
              onPressed: () async {
                await AudioDraftService().deleteDraft(draft.id);
                if (_activeDraftId == draft.id) {
                  _activeDraftId = null;
                }
                await _loadDraftsList();
                if (mounted) setState(() {});
                SnackbarService.show('Brouillon supprimé', isError: false);
              },
              icon: Icon(Icons.delete_outline_rounded, size: 16, color: AppTheme.error),
              tooltip: 'Supprimer',
              padding: EdgeInsets.zero,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildRecordingControls() {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceEvenly,
      children: [
        if (_recordingState == RecordingState.idle || _recordingState == RecordingState.stopped)
          ElevatedButton.icon(
            onPressed: _startRecording,
            icon: const Icon(Icons.mic_rounded),
            label: const Text('Démarrer'),
            style: ElevatedButton.styleFrom(
              backgroundColor: AppTheme.success,
              foregroundColor: Colors.white,
              elevation: 0,
              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
            ),
          ),
        
        if (_recordingState == RecordingState.recording)
          ElevatedButton.icon(
            onPressed: _pauseRecording,
            icon: const Icon(Icons.pause_rounded),
            label: const Text('Pause'),
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.orange,
              foregroundColor: Colors.white,
              elevation: 0,
              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
            ),
          ),
        
        if (_recordingState == RecordingState.paused)
          ElevatedButton.icon(
            onPressed: _resumeRecording,
            icon: const Icon(Icons.play_arrow_rounded),
            label: const Text('Reprendre'),
            style: ElevatedButton.styleFrom(
              backgroundColor: AppTheme.primaryBlue,
              foregroundColor: Colors.white,
              elevation: 0,
              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
            ),
          ),
        
        if (_recordingState == RecordingState.recording || _recordingState == RecordingState.paused)
          ElevatedButton.icon(
            onPressed: _stopRecording,
            icon: const Icon(Icons.stop_rounded),
            label: const Text('Arrêter'),
            style: ElevatedButton.styleFrom(
              backgroundColor: AppTheme.error,
              foregroundColor: Colors.white,
              elevation: 0,
              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
            ),
          ),
      ],
    );
  }

  Widget _buildSessionControls() {
    return Stack(
      children: [
        Container(
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(16),
            boxShadow: AppTheme.softShadow,
          ),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              children: [
                Row(
                  children: [
                    Container(
                      width: 36, height: 36,
                      decoration: BoxDecoration(
                        color: AppTheme.success.withOpacity(0.1),
                        borderRadius: BorderRadius.circular(10),
                      ),
                      child: const Icon(Icons.check_circle_rounded, color: AppTheme.success, size: 20),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Text(
                        'Enregistrement terminé',
                        style: Theme.of(context).textTheme.titleMedium?.copyWith(
                          fontWeight: FontWeight.w600, color: AppTheme.textPrimary,
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 10),
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Text('Taille: ${(_recordedBytes!.length / 1024).toStringAsFixed(1)} KB', style: const TextStyle(color: AppTheme.textLight, fontSize: 13)),
                    const SizedBox(width: 16),
                    Text('Durée: ${_formatDuration(_recordDuration)}', style: const TextStyle(color: AppTheme.textLight, fontSize: 13)),
                  ],
                ),
                const SizedBox(height: 8),

                // Panneau des brouillons locaux
                _buildDraftsPanel(),
                const SizedBox(height: 8),

                Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  alignment: WrapAlignment.center,
                  children: [
                ElevatedButton.icon(
                  onPressed: (_isUploading || _isPlaying) ? null : _playRecording,
                  icon: _isPlaying 
                      ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                      : const Icon(Icons.play_arrow_rounded, size: 18),
                  label: Text(_isPlaying ? 'Lecture...' : 'Écouter'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppTheme.success,
                    foregroundColor: Colors.white,
                    elevation: 0,
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                  ),
                ),
                
                if (_isPlaying)
                  ElevatedButton.icon(
                    onPressed: _stopPlayback,
                    icon: const Icon(Icons.stop_rounded, size: 18),
                    label: const Text('Arrêter'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.orange,
                      foregroundColor: Colors.white,
                      elevation: 0,
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                    ),
                  ),
                
                ElevatedButton.icon(
                  onPressed: (_isUploading || _isPlaying) ? null : () {
                    _stopPlayback();
                    setState(() {
                      _recordedBytes = null;
                      _recordedMimeType = null;
                      _recordDuration = 0;
                      _recordingState = RecordingState.idle;
                    });
                  },
                  icon: const Icon(Icons.delete_rounded, size: 18),
                  label: const Text('Supprimer'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppTheme.error,
                    foregroundColor: Colors.white,
                    elevation: 0,
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                  ),
                ),
                
                ElevatedButton.icon(
                  onPressed: (_isUploading || _isPlaying) ? null : _uploadRecording,
                  icon: _isUploading 
                      ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                      : const Icon(Icons.cloud_upload_rounded, size: 18),
                  label: Text(_isUploading ? 'Upload...' : 'Sauvegarder'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppTheme.primaryBlue,
                    foregroundColor: Colors.white,
                    elevation: 0,
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
      ),
      
      // Overlay de chargement pendant l'upload avec progression
      if (_isUploading == true)
        Positioned.fill(
          child: Container(
            decoration: BoxDecoration(
              color: Colors.white.withOpacity(0.9),
              borderRadius: BorderRadius.circular(16),
            ),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                // Barre de progression
                Container(
                  width: 200,
                  height: 8,
                  decoration: BoxDecoration(
                    color: Colors.grey.shade200,
                    borderRadius: BorderRadius.circular(4),
                  ),
                  child: ClipRRect(
                    borderRadius: BorderRadius.circular(4),
                    child: LinearProgressIndicator(
                      value: _uploadProgress / 100,
                      backgroundColor: Colors.transparent,
                      color: AppTheme.primaryBlue,
                      minHeight: 8,
                    ),
                  ),
                ),
                const SizedBox(height: 12),
                // Pourcentage
                Text(
                  '$_uploadProgress%',
                  style: Theme.of(context).textTheme.titleLarge?.copyWith(
                    fontWeight: FontWeight.w700,
                    color: AppTheme.primaryBlue,
                  ),
                ),
                const SizedBox(height: 8),
                Text(
                  'Sauvegarde en cours...',
                  style: Theme.of(context).textTheme.titleSmall?.copyWith(
                    fontWeight: FontWeight.w600,
                    color: AppTheme.textPrimary,
                  ),
                ),
                const SizedBox(height: 4),
                // Vitesse et temps restant
                Text(
                  '${_uploadSpeed.toStringAsFixed(1)} KB/s · ${_estimatedSecondsRemaining}s restantes',
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: AppTheme.textLight,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  'Ne fermez pas cette page',
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: AppTheme.textLight,
                    fontSize: 11,
                  ),
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildSavedRecordingsSection() {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: AppTheme.softShadow,
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  width: 36, height: 36,
                  decoration: BoxDecoration(
                    color: AppTheme.primaryBlue.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: const Icon(Icons.history_rounded, color: AppTheme.primaryBlue, size: 20),
                ),
                const SizedBox(width: 10),
                Text(
                  'Enregistrements récents (${_savedRecordings.length}/$maxSavedRecordings)',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.w600, color: AppTheme.textPrimary,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            
            ListView.separated(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              itemCount: _savedRecordings.length,
              separatorBuilder: (context, index) => const SizedBox(height: 8),
              itemBuilder: (context, index) {
                final recording = _savedRecordings[index];
                return _buildSavedRecordingCard(recording);
              },
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSavedRecordingCard(SavedRecording recording) {
    final theme = Theme.of(context);
    
    return Container(
      decoration: BoxDecoration(
        color: Theme.of(context).scaffoldBackgroundColor,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppTheme.primaryBlue.withOpacity(0.15)),
      ),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(6),
                  decoration: BoxDecoration(
                    color: AppTheme.primaryBlue.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: const Icon(Icons.school_rounded, color: AppTheme.primaryBlue, size: 16),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        recording.course.nom,
                        style: theme.textTheme.titleSmall?.copyWith(
                          fontWeight: FontWeight.w600, color: AppTheme.textPrimary,
                        ),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                      Text(
                        '${recording.course.universiteDisplay} • ${_formatDuration(recording.duration)}',
                        style: const TextStyle(color: AppTheme.textLight, fontSize: 12),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ],
                  ),
                ),
                Text(
                  _formatDate(recording.createdAt),
                  style: const TextStyle(color: AppTheme.textLight, fontSize: 11),
                ),
              ],
            ),
            
            const SizedBox(height: 8),
            
            Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(10),
              ),
              child: Column(
                children: [
                  Row(
                    children: [
                      const Icon(Icons.info_outline_rounded, size: 14, color: AppTheme.textLight),
                      const SizedBox(width: 4),
                      Text(
                        'Détails du fichier',
                        style: theme.textTheme.bodySmall?.copyWith(
                          fontWeight: FontWeight.w600, color: AppTheme.textPrimary,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 4),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(
                        'Taille: ${(recording.bytes.length / 1024).toStringAsFixed(1)} KB',
                        style: const TextStyle(color: AppTheme.textLight, fontSize: 11),
                      ),
                      Text(
                        'Format: ${recording.mimeType.split('/').last.toUpperCase()}',
                        style: const TextStyle(color: AppTheme.textLight, fontSize: 11),
                      ),
                    ],
                  ),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(
                        'Filière: ${recording.course.filiereDisplay}',
                        style: const TextStyle(color: AppTheme.textLight, fontSize: 11),
                      ),
                      Text(
                        'ID: ${recording.id.substring(recording.id.length - 6)}',
                        style: const TextStyle(color: AppTheme.textLight, fontSize: 11),
                      ),
                    ],
                  ),
                ],
              ),
            ),
            
            const SizedBox(height: 12),
            
            Row(
              children: [
                Expanded(
                  child: ElevatedButton.icon(
                    onPressed: _isPlaying ? null : () => _playSavedRecording(recording),
                    icon: const Icon(Icons.play_arrow_rounded, size: 16),
                    label: const Text('Écouter'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppTheme.success,
                      foregroundColor: Colors.white,
                      elevation: 0,
                      padding: const EdgeInsets.symmetric(vertical: 8),
                      textStyle: const TextStyle(fontSize: 12),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                
                if (_isPlaying)
                  ElevatedButton.icon(
                    onPressed: _stopPlayback,
                    icon: const Icon(Icons.stop_rounded, size: 16),
                    label: const Text('Arrêter'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.orange,
                      foregroundColor: Colors.white,
                      elevation: 0,
                      padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 12),
                      textStyle: const TextStyle(fontSize: 12),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                    ),
                  ),
                
                const SizedBox(width: 8),
                
                ElevatedButton.icon(
                  onPressed: _isPlaying ? null : () => _removeSavedRecording(recording.id),
                  icon: const Icon(Icons.delete_rounded, size: 16),
                  label: const Text('Suppr.'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppTheme.error,
                    foregroundColor: Colors.white,
                    elevation: 0,
                    padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 12),
                    textStyle: const TextStyle(fontSize: 12),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  String _formatDate(DateTime date) {
    final now = DateTime.now();
    final difference = now.difference(date);
    
    if (difference.inMinutes < 1) {
      return 'À l\'instant';
    } else if (difference.inHours < 1) {
      return '${difference.inMinutes}min';
    } else if (difference.inDays < 1) {
      return '${difference.inHours}h';
    } else {
      return '${difference.inDays}j';
    }
  }

  Color _getRecordingColor() {
    switch (_recordingState) {
      case RecordingState.recording:
        return Colors.red;
      case RecordingState.paused:
        return Colors.orange;
      case RecordingState.stopped:
        return Colors.blue;
      default:
        return Colors.grey;
    }
  }

  IconData _getRecordingIcon() {
    switch (_recordingState) {
      case RecordingState.recording:
        return Icons.mic;
      case RecordingState.paused:
        return Icons.pause;
      case RecordingState.stopped:
        return Icons.stop;
      default:
        return Icons.mic_none;
    }
  }

  String _getRecordingStateText() {
    switch (_recordingState) {
      case RecordingState.recording:
        return 'Enregistrement en cours...';
      case RecordingState.paused:
        return 'Enregistrement en pause';
      case RecordingState.stopped:
        return 'Enregistrement terminé';
      default:
        return 'Prêt à enregistrer';
    }
  }

  /// Polling du statut de traitement en arrière-plan (non-bloquant)
  /// Pour les fichiers longs (2h+), le traitement peut prendre 15-30 min
  void _pollProcessingStatus(int sessionId) async {
    // Attendre que l'UI se stabilise
    await Future.delayed(const Duration(seconds: 2));

    if (!mounted) return;

    // Mettre à jour la barre pour montrer le traitement
    setState(() {
      _uploadProgress = 90;
    });

    // Poll pour le statut (max 200 tentatives x 10s = ~33 minutes)
    // Suffisant pour transcription Deepgram + résumé DeepSeek de fichiers longs
    bool isComplete = false;
    int attempts = 0;
    const maxAttempts = 200;

    while (!isComplete && attempts < maxAttempts && mounted) {
      await Future.delayed(const Duration(seconds: 10));
      attempts++;

      try {
        final statusResponse = await _apiService.getAudioSessionStatus(sessionId);
        final status = statusResponse['status'] as String?;

        if (status == null) {
          print('⚠️ Status null, retry...');
          continue;
        }

        if (status == 'summarized' || status == 'completed') {
          isComplete = true;
          if (mounted) {
            setState(() => _uploadProgress = 100);
          }
          print('✅ Traitement terminé!');
        } else if (status == 'failed') {
          print('❌ Traitement échoué');
          break;
        } else if (status == 'transcribed') {
          // Transcription terminée, résumé en cours → 95%
          if (mounted) {
            setState(() => _uploadProgress = 95);
          }
          print('📝 Transcription OK, génération du résumé...');
        } else {
          // Processing: 90-94% based on attempts (progression lente)
          final processingProgress = 90 + ((attempts / maxAttempts) * 4).round();
          if (mounted) {
            setState(() => _uploadProgress = processingProgress.clamp(90, 94));
          }
        }
      } catch (e) {
        // Continue polling on error
        print('⚠️ Erreur polling status: $e');
      }
    }

    if (!isComplete && mounted) {
      print('⏱️ Polling arrêté après ${attempts * 10}s, traitement toujours en cours en arrière-plan');
    }
  }
}
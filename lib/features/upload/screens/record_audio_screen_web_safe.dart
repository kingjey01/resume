import 'dart:async';
import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:resume_plus_clean/services/api_service.dart';
import 'package:resume_plus_clean/services/mobile_audio_recorder.dart';
import 'package:resume_plus_clean/services/snackbar_service.dart';
import 'package:resume_plus_clean/models/course.dart';
import 'package:resume_plus_clean/features/upload/screens/course_selection_screen.dart';
import 'package:resume_plus_clean/theme/app_theme.dart';

/// Écran d'enregistrement audio pour la cible Web/PWA.
///
/// Il utilise le même `MobileAudioRecorder` que le mobile (MediaRecorder sur
/// le Web) et envoie les octets réels au backend via `ApiService.uploadAudio`.
/// L'écran mobile Android/iOS (`record_audio_screen.dart`) n'est pas modifié.
class RecordAudioScreenWebSafe extends StatefulWidget {
  const RecordAudioScreenWebSafe({super.key});

  @override
  State<RecordAudioScreenWebSafe> createState() =>
      _RecordAudioScreenWebSafeState();
}

class _RecordAudioScreenWebSafeState extends State<RecordAudioScreenWebSafe> {
  final ApiService _apiService = ApiService();
  final MobileAudioRecorder _recorder = MobileAudioRecorder();
  final TextEditingController _titleController = TextEditingController();
  final TextEditingController _priceController = TextEditingController();

  Course? _selectedCourse;
  bool _isRecording = false;
  bool _isUploading = false;
  int _seconds = 0;
  double _minimumPrice = 300;
  String? _error;
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    _setupRecorder();
    _loadPricing();
  }

  @override
  void dispose() {
    _timer?.cancel();
    if (_recorder.isRecording) {
      _recorder.stopRecording();
    }
    _recorder.onRecordingComplete = null;
    _recorder.onError = null;
    _recorder.onStart = null;
    _recorder.onStop = null;
    _titleController.dispose();
    _priceController.dispose();
    super.dispose();
  }

  void _setupRecorder() {
    _recorder.onStart = () {
      if (!mounted) return;
      setState(() {
        _isRecording = true;
        _error = null;
        _seconds = 0;
      });
      _startTimer();
    };

    _recorder.onStop = () {
      if (!mounted) return;
      _timer?.cancel();
      setState(() => _isRecording = false);
    };

    _recorder.onError = (message) {
      if (!mounted) return;
      setState(() {
        _isRecording = false;
        _error = message;
      });
      SnackbarService.show(message, isError: true);
    };

    _recorder.onRecordingComplete = _uploadRecording;
  }

  Future<void> _loadPricing() async {
    final minimum = await _apiService.getMinimumResumePrice();
    if (!mounted) return;
    setState(() {
      _minimumPrice = minimum;
      if (_priceController.text.isEmpty) {
        _priceController.text = minimum.toStringAsFixed(0);
      }
    });
  }

  void _startTimer() {
    _timer?.cancel();
    _timer = Timer.periodic(const Duration(seconds: 1), (_) {
      if (mounted) setState(() => _seconds++);
    });
  }

  String get _durationLabel {
    final minutes = (_seconds ~/ 60).toString().padLeft(2, '0');
    final seconds = (_seconds % 60).toString().padLeft(2, '0');
    return '$minutes:$seconds';
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
        if (_titleController.text.trim().isEmpty) {
          _titleController.text = 'Résumé - ${selectedCourse.nom}';
        }
      });
      SnackbarService.show('✅ Cours sélectionné: ${selectedCourse.nom}',
          isError: false);
    }
  }

  String? _validateBeforeRecording() {
    if (_selectedCourse == null) {
      return 'Veuillez d\'abord sélectionner un cours.';
    }
    if (_titleController.text.trim().isEmpty) {
      return 'Donnez un titre au résumé.';
    }
    final price = double.tryParse(_priceController.text.trim());
    if (price == null || price < _minimumPrice) {
      return 'Le prix minimum est ${_minimumPrice.toStringAsFixed(0)} CDF.';
    }
    return null;
  }

  Future<void> _startRecording() async {
    final error = _validateBeforeRecording();
    if (error != null) {
      SnackbarService.show(error, isError: true);
      return;
    }

    final started = await _recorder.startRecording();
    if (!started) {
      // `onError` du recorder a déjà affiché le message.
      setState(() => _isRecording = false);
    }
  }

  Future<void> _stopRecording() async {
    _timer?.cancel();
    await _recorder.stopRecording();
  }

  /// Appelé par le recorder avec les OCTETS réels de l'enregistrement Web.
  Future<void> _uploadRecording(Uint8List bytes, String mimeType) async {
    final course = _selectedCourse;
    if (course == null || bytes.isEmpty) return;

    final price = double.tryParse(_priceController.text.trim()) ?? _minimumPrice;
    if (price < _minimumPrice) {
      SnackbarService.show(
        'Le prix minimum est ${_minimumPrice.toStringAsFixed(0)} CDF.',
        isError: true,
      );
      return;
    }

    final extension = mimeType.contains('mp4')
        ? 'm4a'
        : mimeType.contains('wav')
            ? 'wav'
            : 'webm';

    final metadata = <String, dynamic>{
      'course_id': course.id,
      'title': 'Session ${course.nom}',
      'description': 'Enregistrement de session pour le cours ${course.nom}',
      'summary_title': _titleController.text.trim(),
      'summary_price': price.toString(),
      'audio_duration': _seconds.toString(),
    };
    if (course.universiteFk != null) {
      metadata['universite_id'] = course.universiteFk;
    }

    setState(() => _isUploading = true);
    try {
      await _apiService.uploadAudio(
        audioBytes: bytes,
        fileName: 'recording_${DateTime.now().millisecondsSinceEpoch}.$extension',
        mimeType: mimeType,
        metadata: metadata,
      );
      if (!mounted) return;
      SnackbarService.show('🎉 Enregistrement envoyé avec succès !',
          isError: false);
      setState(() {
        _seconds = 0;
        _error = null;
      });
    } catch (e) {
      if (!mounted) return;
      SnackbarService.show('❌ Erreur d\'envoi: $e', isError: true);
    } finally {
      if (mounted) setState(() => _isUploading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final topPadding = MediaQuery.of(context).padding.top;

    return Scaffold(
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      body: Column(
        children: [
          _buildHeader(theme, topPadding),
          Expanded(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                children: [
                  _buildInfoCard(theme),
                  _buildCourseSelection(theme),
                  const SizedBox(height: 16),
                  _buildDetailsCard(theme),
                  const SizedBox(height: 16),
                  _buildRecordingInterface(theme),
                  if (_error != null) ...[
                    const SizedBox(height: 16),
                    _buildErrorCard(theme),
                  ],
                  const SizedBox(height: 32),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildHeader(ThemeData theme, double topPadding) {
    return Container(
      width: double.infinity,
      padding:
          EdgeInsets.only(top: topPadding + 8, left: 20, right: 20, bottom: 24),
      decoration: const BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            AppTheme.primaryBlueDark,
            AppTheme.primaryBlue,
            AppTheme.primaryBlueLight,
          ],
        ),
        borderRadius: BorderRadius.only(
          bottomLeft: Radius.circular(24),
          bottomRight: Radius.circular(24),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          GestureDetector(
            onTap: () => Navigator.of(context).pop(),
            child: Container(
              width: 40,
              height: 40,
              decoration: BoxDecoration(
                color: Colors.white.withValues(alpha: 0.2),
                borderRadius: BorderRadius.circular(12),
              ),
              child: const Icon(Icons.arrow_back_rounded,
                  color: Colors.white, size: 22),
            ),
          ),
          const SizedBox(height: 16),
          Text(
            'Enregistrer un cours',
            style: theme.textTheme.headlineMedium?.copyWith(
              color: Colors.white,
              fontWeight: FontWeight.w700,
            ),
          ),
          const SizedBox(height: 6),
          Text(
            'Enregistrez votre cours directement dans le navigateur',
            style: TextStyle(
                color: Colors.white.withValues(alpha: 0.8), fontSize: 14),
          ),
        ],
      ),
    );
  }

  Widget _buildInfoCard(ThemeData theme) {
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppTheme.primaryBlue.withValues(alpha: 0.06),
        border: Border.all(color: AppTheme.primaryBlue.withValues(alpha: 0.2)),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        children: [
          const Icon(Icons.mic_rounded, color: AppTheme.primaryBlue),
          const SizedBox(width: 10),
          const Expanded(
            child: Text(
              'Le navigateur demandera l\'accès au microphone. '
              'Utilisez une connexion HTTPS et laissez l\'onglet ouvert '
              'pendant l\'enregistrement.',
              style: TextStyle(fontSize: 13),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildCourseSelection(ThemeData theme) {
    return Card(
      elevation: 2,
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.school, color: theme.colorScheme.primary),
                const SizedBox(width: 8),
                Text(
                  'Cours à enregistrer',
                  style: theme.textTheme.titleMedium
                      ?.copyWith(fontWeight: FontWeight.bold),
                ),
              ],
            ),
            const SizedBox(height: 12),
            InkWell(
              onTap: _isRecording ? null : _selectCourse,
              child: Container(
                width: double.infinity,
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  border: Border.all(
                    color: _selectedCourse != null
                        ? theme.colorScheme.primary
                        : theme.colorScheme.outline,
                  ),
                  borderRadius: BorderRadius.circular(8),
                  color: _selectedCourse != null
                      ? theme.colorScheme.primary.withValues(alpha: 0.1)
                      : null,
                ),
                child: Row(
                  children: [
                    Expanded(
                      child: Text(
                        _selectedCourse?.nom ?? 'Sélectionner un cours...',
                        style: theme.textTheme.bodyMedium?.copyWith(
                          color: _selectedCourse != null
                              ? theme.colorScheme.primary
                              : theme.colorScheme.onSurfaceVariant,
                          fontWeight: _selectedCourse != null
                              ? FontWeight.w500
                              : null,
                        ),
                      ),
                    ),
                    Icon(Icons.arrow_drop_down,
                        color: theme.colorScheme.primary),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildDetailsCard(ThemeData theme) {
    return Card(
      elevation: 2,
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            TextField(
              controller: _titleController,
              enabled: !_isRecording,
              textCapitalization: TextCapitalization.sentences,
              decoration: const InputDecoration(
                labelText: 'Titre du résumé',
                hintText: 'Ex. Résumé du cours de mathématiques',
                prefixIcon: Icon(Icons.title_rounded),
              ),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _priceController,
              enabled: !_isRecording,
              keyboardType: TextInputType.number,
              decoration: InputDecoration(
                labelText: 'Prix du résumé (CDF)',
                hintText:
                    'Minimum : ${_minimumPrice.toStringAsFixed(0)} CDF',
                prefixIcon: const Icon(Icons.payments_outlined),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildRecordingInterface(ThemeData theme) {
    return Card(
      elevation: 4,
      child: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          children: [
            GestureDetector(
              onTap: _isUploading
                  ? null
                  : (_isRecording ? _stopRecording : _startRecording),
              child: Container(
                width: 120,
                height: 120,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: _isRecording
                      ? AppTheme.error.withValues(alpha: 0.1)
                      : theme.colorScheme.primary.withValues(alpha: 0.1),
                  border: Border.all(
                    color: _isRecording ? AppTheme.error : theme.colorScheme.primary,
                    width: 3,
                  ),
                ),
                child: Icon(
                  _isRecording ? Icons.stop_rounded : Icons.mic,
                  size: 60,
                  color: _isRecording ? AppTheme.error : theme.colorScheme.primary,
                ),
              ),
            ),
            const SizedBox(height: 20),
            Text(
              _isRecording ? _durationLabel : 'Enregistrement audio',
              style: theme.textTheme.headlineSmall?.copyWith(
                fontWeight: FontWeight.bold,
                color: _isRecording ? AppTheme.error : null,
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 10),
            Text(
              _isUploading
                  ? 'Envoi de l\'enregistrement…'
                  : _isRecording
                      ? 'Appuyez sur le bouton rouge pour arrêter.'
                      : 'Appuyez sur le micro pour commencer.',
              style: theme.textTheme.bodyMedium?.copyWith(
                color: theme.colorScheme.onSurfaceVariant,
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 24),
            SizedBox(
              width: double.infinity,
              height: 50,
              child: ElevatedButton.icon(
                onPressed: _isUploading
                    ? null
                    : (_isRecording ? _stopRecording : _startRecording),
                icon: _isUploading
                    ? const SizedBox(
                        width: 20,
                        height: 20,
                        child: CircularProgressIndicator(
                          strokeWidth: 2,
                          color: Colors.white,
                        ),
                      )
                    : Icon(_isRecording
                        ? Icons.stop_rounded
                        : Icons.fiber_manual_record_rounded),
                label: Text(
                  _isUploading
                      ? 'Envoi en cours…'
                      : _isRecording
                          ? 'Arrêter et envoyer'
                          : 'Commencer l\'enregistrement',
                ),
                style: ElevatedButton.styleFrom(
                  backgroundColor:
                      _isRecording ? AppTheme.error : theme.colorScheme.primary,
                  foregroundColor: Colors.white,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildErrorCard(ThemeData theme) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: AppTheme.error.withValues(alpha: 0.08),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: AppTheme.error.withValues(alpha: 0.3)),
      ),
      child: Row(
        children: [
          const Icon(Icons.error_outline_rounded, color: AppTheme.error),
          const SizedBox(width: 8),
          Expanded(
            child: Text(_error!, style: const TextStyle(fontSize: 13)),
          ),
        ],
      ),
    );
  }
}

import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:resume_plus_clean/services/api_service.dart';
import 'package:resume_plus_clean/services/snackbar_service.dart';
import 'package:resume_plus_clean/models/course.dart';
import 'package:resume_plus_clean/features/upload/screens/course_selection_screen.dart';
import 'package:resume_plus_clean/theme/app_theme.dart';

/// 🔥 Version web-safe de l'écran d'enregistrement audio
/// Évite les erreurs de rendu sur Flutter Web
class RecordAudioScreenWebSafe extends StatefulWidget {
  const RecordAudioScreenWebSafe({super.key});

  @override
  State<RecordAudioScreenWebSafe> createState() => _RecordAudioScreenWebSafeState();
}

class _RecordAudioScreenWebSafeState extends State<RecordAudioScreenWebSafe> {
  final ApiService _apiService = ApiService();
  Course? _selectedCourse;
  bool _isUploading = false;
  bool _isRecordingSupported = false;

  @override
  void initState() {
    super.initState();
    _checkRecordingSupport();
  }

  void _checkRecordingSupport() {
    // Sur Flutter Web, l'enregistrement audio est limité
    setState(() {
      _isRecordingSupported = !kIsWeb;
    });
  }

  void _selectCourse() async {
    final selectedCourse = await Navigator.of(context).push<Course>(
      MaterialPageRoute(
        builder: (ctx) => CourseSelectionScreen(
          onCourseSelected: (course) {
            // Utiliser ctx pour pop avec le cours sélectionné
            Navigator.of(ctx).pop(course);
          },
        ),
      ),
    );
    
    if (selectedCourse != null && mounted) {
      setState(() {
        _selectedCourse = selectedCourse;
      });
      SnackbarService.show('✅ Cours sélectionné: ${selectedCourse.nom}', isError: false);
    }
  }

  Future<void> _simulateAudioUpload() async {
    if (_selectedCourse == null) {
      SnackbarService.show('❌ Veuillez sélectionner un cours', isError: true);
      return;
    }

    setState(() => _isUploading = true);
    
    try {
      // Simuler un enregistrement audio pour le web
      await _apiService.uploadAudioSummary('simulation_web_audio.wav', {
        'title': 'Enregistrement simulé - ${_selectedCourse!.nom}',
        'course_id': _selectedCourse!.id,
        'duration': 60, // 1 minute simulée
      });
      
      SnackbarService.show('🎉 Résumé IA généré avec succès !', isError: false);
      
      if (mounted) {
        // Réinitialiser l'état au lieu de pop (évite écran blanc dans IndexedStack)
        setState(() {
          _selectedCourse = null;
          _isUploading = false;
        });
        
        // Si on peut pop (écran pushé), le faire. Sinon, rester sur place.
        if (Navigator.of(context).canPop()) {
          Navigator.of(context).pop();
        }
      }
      return;
      
    } catch (e) {
      SnackbarService.show('❌ Erreur d\'upload: $e', isError: true);
    } finally {
      if (mounted) {
        setState(() => _isUploading = false);
      }
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
          // Header bleu gradient — même design que le reste de l'app
          Container(
            width: double.infinity,
            padding: EdgeInsets.only(top: topPadding + 8, left: 20, right: 20, bottom: 24),
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
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
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
                const SizedBox(height: 16),
                Text(
                  'Enregistrer un cours',
                  style: theme.textTheme.headlineMedium?.copyWith(
                    color: Colors.white, fontWeight: FontWeight.w700,
                  ),
                ),
                const SizedBox(height: 6),
                Text(
                  kIsWeb ? 'Génération de résumé IA simulée' : 'Enregistrez votre cours audio',
                  style: TextStyle(color: Colors.white.withOpacity(0.8), fontSize: 14),
                ),
              ],
            ),
          ),
          // Corps scrollable
          Expanded(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                children: [
                  const SizedBox(height: 8),
                  // Avertissement Web
                  if (kIsWeb) _buildWebWarning(theme),

                  // Sélection de cours
                  _buildCourseSelection(theme),
                  const SizedBox(height: 24),

                  // Interface d'enregistrement
                  _buildRecordingInterface(theme),

                  const SizedBox(height: 32),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildWebWarning(ThemeData theme) {
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.orange.shade50,
        border: Border.all(color: Colors.orange.shade300),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        children: [
          Row(
            children: [
              Icon(Icons.warning_amber, color: Colors.orange.shade700),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  'Mode Web Détecté',
                  style: theme.textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.bold,
                    color: Colors.orange.shade700,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            'L\'enregistrement audio sur le web a des limitations. '
            'Pour une expérience complète, utilisez l\'application mobile.',
            style: theme.textTheme.bodyMedium?.copyWith(
              color: Colors.orange.shade700,
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
                Icon(
                  Icons.school,
                  color: theme.colorScheme.primary,
                ),
                const SizedBox(width: 8),
                Text(
                  'Cours à enregistrer',
                  style: theme.textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            InkWell(
              onTap: _selectCourse,
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
                      ? theme.colorScheme.primary.withOpacity(0.1)
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
                    Icon(
                      Icons.arrow_drop_down,
                      color: theme.colorScheme.primary,
                    ),
                  ],
                ),
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
            // Icône d'enregistrement
            Container(
              width: 120,
              height: 120,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: kIsWeb 
                    ? Colors.grey.shade300 
                    : theme.colorScheme.primary.withOpacity(0.1),
                border: Border.all(
                  color: kIsWeb 
                      ? Colors.grey.shade400 
                      : theme.colorScheme.primary,
                  width: 3,
                ),
              ),
              child: Icon(
                Icons.mic,
                size: 60,
                color: kIsWeb 
                    ? Colors.grey.shade600 
                    : theme.colorScheme.primary,
              ),
            ),
            const SizedBox(height: 24),
            
            // Titre
            Text(
              kIsWeb 
                  ? 'Enregistrement Simulé'
                  : 'Enregistrement Audio',
              style: theme.textTheme.headlineSmall?.copyWith(
                fontWeight: FontWeight.bold,
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 12),
            
            // Description
            Text(
              kIsWeb
                  ? 'Sur le web, nous simulons l\'enregistrement audio.\n'
                    'L\'IA générera un résumé de test pour le cours sélectionné.'
                  : 'Enregistrez votre cours et l\'IA créera automatiquement\n'
                    'un résumé à partir de l\'audio.',
              style: theme.textTheme.bodyMedium?.copyWith(
                color: theme.colorScheme.onSurfaceVariant,
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 32),
            
            // Bouton d'action
            SizedBox(
              width: double.infinity,
              height: 50,
              child: ElevatedButton.icon(
                onPressed: _isUploading || _selectedCourse == null 
                    ? null 
                    : _simulateAudioUpload,
                icon: _isUploading 
                    ? const SizedBox(
                        width: 20,
                        height: 20,
                        child: CircularProgressIndicator(
                          strokeWidth: 2,
                          color: Colors.white,
                        ),
                      )
                    : Icon(kIsWeb ? Icons.smart_toy : Icons.mic),
                label: Text(
                  _isUploading 
                      ? 'Traitement en cours...'
                      : kIsWeb 
                          ? 'Générer Résumé IA'
                          : 'Commencer l\'enregistrement',
                ),
                style: ElevatedButton.styleFrom(
                  backgroundColor: kIsWeb 
                      ? Colors.purple 
                      : theme.colorScheme.primary,
                  foregroundColor: Colors.white,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
              ),
            ),
            
            // Note sur la sélection de cours
            if (_selectedCourse == null) ...[
              const SizedBox(height: 16),
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.amber.shade50,
                  border: Border.all(color: Colors.amber.shade300),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Row(
                  children: [
                    Icon(Icons.info_outline, 
                         color: Colors.amber.shade700, 
                         size: 20),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        'Veuillez d\'abord sélectionner un cours',
                        style: theme.textTheme.bodySmall?.copyWith(
                          color: Colors.amber.shade700,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
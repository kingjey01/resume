import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'dart:typed_data';
import 'dart:html' as html;
import '../services/web_audio_recorder.dart';
import '../services/api_service.dart';

/// Page de test audio Flutter utilisant la même config que le HTML réussi
class AudioTestPage extends StatefulWidget {
  const AudioTestPage({super.key});

  @override
  State<AudioTestPage> createState() => _AudioTestPageState();
}

class _AudioTestPageState extends State<AudioTestPage> {
  final WebAudioRecorder _recorder = WebAudioRecorder();
  final ApiService _apiService = ApiService();
  
  bool _isRecording = false;
  bool _isPaused = false;
  List<String> _debugMessages = [];
  Map<String, dynamic>? _diagnosis;
  Uint8List? _recordedBytes;
  String? _recordedMimeType;
  bool _isUploading = false;
  bool _isPlaying = false;
  html.AudioElement? _audioPlayer;

  @override
  void initState() {
    super.initState();
    _setupRecorderCallbacks();
    _runDiagnosis();
  }

  void _setupRecorderCallbacks() {
    _recorder.onStart = () {
      setState(() {
        _isRecording = true;
        _isPaused = false;
      });
      _addDebugMessage('✅ Enregistrement démarré');
    };

    _recorder.onStop = () {
      setState(() {
        _isRecording = false;
        _isPaused = false;
      });
      _addDebugMessage('⏹️ Enregistrement arrêté');
    };

    _recorder.onPause = () {
      setState(() {
        _isPaused = true;
      });
      _addDebugMessage('⏸️ Enregistrement en pause');
    };

    _recorder.onResume = () {
      setState(() {
        _isPaused = false;
      });
      _addDebugMessage('▶️ Enregistrement repris');
    };

    _recorder.onError = (error) {
      _addDebugMessage('❌ Erreur: $error');
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Erreur: $error'),
          backgroundColor: Colors.red,
        ),
      );
    };

    _recorder.onDebug = (message) {
      _addDebugMessage('🔍 $message');
    };

    _recorder.onRecordingComplete = (bytes, mimeType) {
      setState(() {
        _recordedBytes = bytes;
        _recordedMimeType = mimeType;
      });
      _addDebugMessage('✅ Enregistrement prêt: ${bytes.length} bytes, type: $mimeType');
    };
  }

  void _addDebugMessage(String message) {
    setState(() {
      _debugMessages.insert(0, '${DateTime.now().toString().substring(11, 19)} - $message');
      if (_debugMessages.length > 30) {
        _debugMessages.removeLast();
      }
    });
  }

  Future<void> _runDiagnosis() async {
    _addDebugMessage('🔍 Lancement du diagnostic...');
    
    try {
      final diagnosis = await _recorder.diagnose();
      setState(() {
        _diagnosis = diagnosis;
      });
      
      if (diagnosis['canRecord']) {
        _addDebugMessage('✅ Diagnostic réussi - Configuration identique au HTML');
      } else {
        _addDebugMessage('❌ Diagnostic échoué: ${diagnosis['error']}');
      }
    } catch (e) {
      _addDebugMessage('❌ Erreur de diagnostic: $e');
    }
  }

  Future<void> _startRecording() async {
    _addDebugMessage('🎤 Démarrage avec la config HTML réussie...');
    final success = await _recorder.startRecording();
    
    if (!success) {
      _addDebugMessage('❌ Échec du démarrage');
    }
  }

  Future<void> _stopRecording() async {
    _addDebugMessage('⏹️ Arrêt de l\'enregistrement...');
    await _recorder.stopRecording();
  }

  Future<void> _pauseRecording() async {
    await _recorder.pauseRecording();
  }

  Future<void> _resumeRecording() async {
    await _recorder.resumeRecording();
  }



  Widget _buildDiagnosisCard() {
    if (_diagnosis == null) {
      return const Card(
        child: Padding(
          padding: EdgeInsets.all(16),
          child: Row(
            children: [
              CircularProgressIndicator(),
              SizedBox(width: 16),
              Text('Diagnostic en cours...'),
            ],
          ),
        ),
      );
    }

    final canRecord = _diagnosis!['canRecord'] ?? false;
    final color = canRecord ? Colors.green : Colors.red;
    final icon = canRecord ? Icons.check_circle : Icons.error;

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(icon, color: color),
                const SizedBox(width: 8),
                Text(
                  'Diagnostic Flutter (Config HTML)',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.bold,
                    color: color,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            
            _buildDiagnosisItem('MediaRecorder', _diagnosis!['mediaRecorderSupported'] ? 'Supporté ✅' : 'Non supporté ❌'),
            _buildDiagnosisItem('getUserMedia', _diagnosis!['getUserMediaSupported'] ? 'Supporté ✅' : 'Non supporté ❌'),
            _buildDiagnosisItem('HTTPS', _diagnosis!['isHTTPS'] ? 'Sécurisé ✅' : 'Non sécurisé ⚠️'),
            _buildDiagnosisItem('Meilleur Codec', _diagnosis!['bestCodec'] ?? 'Aucun'),
            _buildDiagnosisItem('Peut Enregistrer', canRecord ? 'Oui ✅' : 'Non ❌'),
            
            if (_diagnosis!['supportedCodecs'] != null) ...[
              const SizedBox(height: 8),
              Text(
                'Codecs Supportés:',
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 4),
              Wrap(
                spacing: 4,
                children: (_diagnosis!['supportedCodecs'] as List<String>)
                    .map((codec) => Chip(
                          label: Text(codec, style: const TextStyle(fontSize: 10)),
                          backgroundColor: Colors.blue.shade100,
                        ))
                    .toList(),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildDiagnosisItem(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 2),
      child: Row(
        children: [
          SizedBox(
            width: 120,
            child: Text(
              '$label:',
              style: const TextStyle(fontWeight: FontWeight.w500),
            ),
          ),
          Expanded(child: Text(value)),
        ],
      ),
    );
  }

  Widget _buildControlsCard() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Contrôles (Config HTML Réussie)',
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 16),
            
            // Boutons de contrôle
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                ElevatedButton.icon(
                  onPressed: _isRecording ? null : _startRecording,
                  icon: const Icon(Icons.mic),
                  label: const Text('Démarrer'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.green,
                    foregroundColor: Colors.white,
                  ),
                ),
                
                ElevatedButton.icon(
                  onPressed: _isRecording && !_isPaused ? _pauseRecording : null,
                  icon: const Icon(Icons.pause),
                  label: const Text('Pause'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.orange,
                    foregroundColor: Colors.white,
                  ),
                ),
                
                ElevatedButton.icon(
                  onPressed: _isRecording && _isPaused ? _resumeRecording : null,
                  icon: const Icon(Icons.play_arrow),
                  label: const Text('Reprendre'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.blue,
                    foregroundColor: Colors.white,
                  ),
                ),
                
                ElevatedButton.icon(
                  onPressed: _isRecording ? _stopRecording : null,
                  icon: const Icon(Icons.stop),
                  label: const Text('Arrêter'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.red,
                    foregroundColor: Colors.white,
                  ),
                ),
              ],
            ),
            
            const SizedBox(height: 16),
            
            // État actuel
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: _isRecording 
                    ? (_isPaused ? Colors.orange.shade50 : Colors.green.shade50)
                    : Colors.grey.shade50,
                borderRadius: BorderRadius.circular(8),
                border: Border.all(
                  color: _isRecording 
                      ? (_isPaused ? Colors.orange.shade200 : Colors.green.shade200)
                      : Colors.grey.shade200,
                ),
              ),
              child: Row(
                children: [
                  Icon(
                    _isRecording 
                        ? (_isPaused ? Icons.pause_circle : Icons.fiber_manual_record)
                        : Icons.stop_circle,
                    color: _isRecording 
                        ? (_isPaused ? Colors.orange : Colors.red)
                        : Colors.grey,
                  ),
                  const SizedBox(width: 8),
                  Text(
                    _isRecording 
                        ? (_isPaused ? 'En pause' : 'Enregistrement en cours...')
                        : 'Arrêté',
                    style: TextStyle(
                      fontWeight: FontWeight.bold,
                      color: _isRecording 
                          ? (_isPaused ? Colors.orange.shade700 : Colors.green.shade700)
                          : Colors.grey.shade700,
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

  Widget _buildResultCard() {
    if (_recordedBytes == null) {
      return const SizedBox.shrink();
    }

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Résultat de l\'Enregistrement',
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.bold,
                color: Colors.green.shade700,
              ),
            ),
            const SizedBox(height: 12),
            
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.green.shade50,
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: Colors.green.shade200),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Icon(Icons.check_circle, color: Colors.green.shade700),
                      const SizedBox(width: 8),
                      Text(
                        'Enregistrement Réussi!',
                        style: TextStyle(
                          fontWeight: FontWeight.bold,
                          color: Colors.green.shade700,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Text('Taille: ${(_recordedBytes!.length / 1024).toStringAsFixed(1)} KB'),
                  Text('Type: $_recordedMimeType'),
                  Text('Qualité: ${_recordedBytes!.length > 10000 ? 'Bonne' : 'Faible'}'),
                ],
              ),
            ),
            
            const SizedBox(height: 12),
            
            // Boutons d'action
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                ElevatedButton.icon(
                  onPressed: _isPlaying ? null : _playRecording,
                  icon: _isPlaying 
                      ? const SizedBox(
                          width: 16,
                          height: 16,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Icon(Icons.play_arrow),
                  label: Text(_isPlaying ? 'Lecture...' : 'Écouter'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.green,
                    foregroundColor: Colors.white,
                  ),
                ),
                
                ElevatedButton.icon(
                  onPressed: _isPlaying ? _stopPlayback : null,
                  icon: const Icon(Icons.stop),
                  label: const Text('Arrêter'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.red,
                    foregroundColor: Colors.white,
                  ),
                ),
                
                ElevatedButton.icon(
                  onPressed: _isUploading ? null : _uploadRecording,
                  icon: _isUploading 
                      ? const SizedBox(
                          width: 16,
                          height: 16,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Icon(Icons.cloud_upload),
                  label: Text(_isUploading ? 'Upload en cours...' : 'Upload vers Serveur'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.blue,
                    foregroundColor: Colors.white,
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildDebugCard() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Text(
                  'Messages de Debug',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const Spacer(),
                TextButton(
                  onPressed: () {
                    setState(() {
                      _debugMessages.clear();
                    });
                  },
                  child: const Text('Effacer'),
                ),
              ],
            ),
            const SizedBox(height: 8),
            
            Container(
              height: 200,
              width: double.infinity,
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: Colors.black87,
                borderRadius: BorderRadius.circular(8),
              ),
              child: _debugMessages.isEmpty
                  ? const Center(
                      child: Text(
                        'Aucun message de debug',
                        style: TextStyle(color: Colors.grey),
                      ),
                    )
                  : ListView.builder(
                      itemCount: _debugMessages.length,
                      itemBuilder: (context, index) {
                        return Padding(
                          padding: const EdgeInsets.symmetric(vertical: 1),
                          child: Text(
                            _debugMessages[index],
                            style: const TextStyle(
                              color: Colors.green,
                              fontSize: 12,
                              fontFamily: 'monospace',
                            ),
                          ),
                        );
                      },
                    ),
            ),
          ],
        ),
      ),
    );
  }

  /// Lecture de l'enregistrement audio
  Future<void> _playRecording() async {
    if (_recordedBytes == null || _recordedBytes!.isEmpty) {
      _addDebugMessage('❌ Aucun audio à lire');
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Aucun enregistrement à lire'),
          backgroundColor: Colors.red,
        ),
      );
      return;
    }

    try {
      setState(() {
        _isPlaying = true;
      });

      _addDebugMessage('🎵 Début lecture: ${_recordedBytes!.length} bytes');

      // Créer un blob audio à partir des bytes
      final blob = html.Blob([_recordedBytes!], _recordedMimeType ?? 'audio/webm');
      final url = html.Url.createObjectUrlFromBlob(blob);

      // Créer et configurer l'élément audio
      _audioPlayer = html.AudioElement(url);
      _audioPlayer!.controls = false;
      _audioPlayer!.autoplay = false;

      // Configurer les événements
      _audioPlayer!.onLoadedData.listen((_) {
        _addDebugMessage('✅ Audio chargé, durée: ${_audioPlayer!.duration?.toStringAsFixed(1)}s');
      });

      _audioPlayer!.onPlay.listen((_) {
        _addDebugMessage('▶️ Lecture démarrée');
      });

      _audioPlayer!.onPause.listen((_) {
        _addDebugMessage('⏸️ Lecture en pause');
      });

      _audioPlayer!.onEnded.listen((_) {
        _addDebugMessage('✅ Lecture terminée');
        setState(() {
          _isPlaying = false;
        });
        html.Url.revokeObjectUrl(url);
      });

      _audioPlayer!.onError.listen((error) {
        _addDebugMessage('❌ Erreur de lecture: $error');
        setState(() {
          _isPlaying = false;
        });
        html.Url.revokeObjectUrl(url);
      });

      // Démarrer la lecture
      await _audioPlayer!.play();
      _addDebugMessage('🎵 Lecture en cours...');

    } catch (e) {
      _addDebugMessage('❌ Erreur de lecture: $e');
      setState(() {
        _isPlaying = false;
      });
      
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Erreur de lecture: $e'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }

  /// Arrêter la lecture audio
  void _stopPlayback() {
    try {
      if (_audioPlayer != null) {
        _audioPlayer!.pause();
        _audioPlayer!.currentTime = 0;
        _audioPlayer = null;
      }
      
      setState(() {
        _isPlaying = false;
      });
      
      _addDebugMessage('⏹️ Lecture arrêtée');
      
    } catch (e) {
      _addDebugMessage('❌ Erreur arrêt lecture: $e');
    }
  }

  /// Upload de l'enregistrement vers le serveur
  Future<void> _uploadRecording() async {
    if (_recordedBytes == null || _recordedBytes!.isEmpty) {
      _addDebugMessage('❌ Aucun audio à uploader');
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Aucun enregistrement à uploader'),
          backgroundColor: Colors.red,
        ),
      );
      return;
    }

    setState(() {
      _isUploading = true;
    });

    try {
      _addDebugMessage('📤 Début upload: ${_recordedBytes!.length} bytes');
      
      // Créer un nom de fichier unique
      final timestamp = DateTime.now().millisecondsSinceEpoch;
      final fileName = 'flutter_test_$timestamp.webm';
      
      _addDebugMessage('📝 Nom fichier: $fileName');
      _addDebugMessage('🎵 Type MIME: $_recordedMimeType');
      
      // Upload vers le serveur
      final response = await _apiService.uploadAudio(
        audioBytes: _recordedBytes!,
        fileName: fileName,
        mimeType: _recordedMimeType ?? 'audio/webm',
      );
      
      _addDebugMessage('✅ Upload réussi: ${response.toString()}');
      
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Upload réussi !'),
            backgroundColor: Colors.green,
          ),
        );
      }
      
    } catch (e) {
      _addDebugMessage('❌ Erreur upload: $e');
      
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Erreur upload: $e'),
            backgroundColor: Colors.red,
          ),
        );
      }
    } finally {
      if (mounted) {
        setState(() {
          _isUploading = false;
        });
      }
    }
  }

  @override
  void dispose() {
    _recorder.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('🎤 Test Audio Flutter (Config HTML)'),
        backgroundColor: Colors.green,
        foregroundColor: Colors.white,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.green.shade50,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: Colors.green.shade200),
              ),
              child: Row(
                children: [
                  Icon(Icons.info, color: Colors.green.shade700),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Configuration Identique au Test HTML Réussi',
                          style: TextStyle(
                            fontWeight: FontWeight.bold,
                            color: Colors.green.shade700,
                          ),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          'Cette page utilise exactement la même configuration que votre test HTML qui fonctionne parfaitement.',
                          style: TextStyle(
                            fontSize: 12,
                            color: Colors.green.shade600,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            
            const SizedBox(height: 16),
            _buildDiagnosisCard(),
            const SizedBox(height: 16),
            _buildControlsCard(),
            const SizedBox(height: 16),
            _buildResultCard(),
            const SizedBox(height: 16),
            _buildDebugCard(),
          ],
        ),
      ),
    );
  }
}
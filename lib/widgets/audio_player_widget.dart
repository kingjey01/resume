import 'package:flutter/material.dart';
import '../services/audio_service.dart';

/// Widget de contrôle audio pour la lecture de texte
class AudioPlayerWidget extends StatefulWidget {
  final String text;
  final String? title;
  final double rate;
  final double pitch;
  final double volume;
  final String language;

  const AudioPlayerWidget({
    super.key,
    required this.text,
    this.title,
    this.rate = 0.8,
    this.pitch = 1.0,
    this.volume = 1.0,
    this.language = 'fr-FR',
  });

  @override
  State<AudioPlayerWidget> createState() => _AudioPlayerWidgetState();
}

class _AudioPlayerWidgetState extends State<AudioPlayerWidget> {
  final AudioService _audioService = AudioService();
  bool _isInitialized = false;
  bool _isPlaying = false;
  bool _isPaused = false;
  String? _errorMessage;
  bool _isStoppingManually = false;

  @override
  void initState() {
    super.initState();
    _initializeAudioService();
  }

  Future<void> _initializeAudioService() async {
    try {
      final success = await _audioService.initialize();
      if (mounted) {
        setState(() {
          _isInitialized = success;
          if (!success) {
            _errorMessage = 'Service audio non disponible';
          }
        });
      }

      // Configurer les callbacks
      _audioService.onStart = () {
        if (mounted) {
          setState(() {
            _isPlaying = true;
            _isPaused = false;
            _errorMessage = null;
          });
        }
      };

      _audioService.onComplete = () {
        if (mounted) {
          setState(() {
            _isPlaying = false;
            _isPaused = false;
          });
        }
      };

      _audioService.onPause = () {
        if (mounted) {
          setState(() {
            _isPaused = true;
          });
        }
      };

      _audioService.onResume = () {
        if (mounted) {
          setState(() {
            _isPaused = false;
          });
        }
      };

      _audioService.onError = (error) {
        if (mounted) {
          if (_isStoppingManually) {
            // Ignorer les erreurs déclenchées par l'arrêt manuel
            return;
          }
          
          final errLower = error.toString().toLowerCase();
          
          // Ignorer les erreurs d'interruption, d'annulation ou de stop provoquées par le système ou l'utilisateur
          if (errLower.contains('cancel') || 
              errLower.contains('interrupted') || 
              errLower.contains('stop') || 
              errLower.contains('status: -2') ||
              errLower.contains('error_invalid_request')) {
            return;
          }

          String userFriendlyError = error;
          if (errLower.contains('texttospeech') || 
              errLower.contains('tts') || 
              errLower.contains('speak') || 
              errLower.contains('engine')) {
            userFriendlyError = "La synthèse vocale en français n'est pas configurée sur votre appareil. "
                "Veuillez activer les services de synthèse vocale Google (Paramètres de l'appareil > Langue et saisie > Synthèse vocale > choisir Google et installer la voix française).";
          }
          setState(() {
            _isPlaying = false;
            _isPaused = false;
            _errorMessage = userFriendlyError;
          });
        }
      };
    } catch (e) {
      if (mounted) {
        setState(() {
          _isInitialized = false;
          _errorMessage = 'Erreur d\'initialisation: $e';
        });
      }
    }
  }

  Future<void> _playPause() async {
    if (!_isInitialized) return;

    try {
      setState(() {
        _isStoppingManually = false;
        _errorMessage = null;
      });
      if (_isPlaying && !_isPaused) {
        // En cours de lecture, mettre en pause
        await _audioService.pause();
      } else if (_isPlaying && _isPaused) {
        // En pause, reprendre
        await _audioService.resume();
      } else {
        // Pas de lecture, démarrer
        await _audioService.speak(
          widget.text,
          rate: widget.rate,
          pitch: widget.pitch,
          volume: widget.volume,
          language: widget.language,
        );
      }
    } catch (e) {
      setState(() {
        _errorMessage = 'Erreur de lecture: $e';
      });
    }
  }

  Future<void> _stop() async {
    if (!_isInitialized) return;

    try {
      setState(() {
        _isStoppingManually = true;
        _isPlaying = false;
        _isPaused = false;
        _errorMessage = null; // Effacer les messages d'erreur lors d'un arrêt manuel
      });
      await _audioService.stop();
      // On attend un court instant avant de désactiver le flag pour absorber tout callback d'erreur asynchrone tardif
      await Future.delayed(const Duration(milliseconds: 300));
      if (mounted) {
        setState(() {
          _isStoppingManually = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _isStoppingManually = false;
          _errorMessage = 'Erreur d\'arrêt: $e';
        });
      }
    }
  }

  @override
  void dispose() {
    _audioService.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 2,
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            // Titre
            if (widget.title != null) ...[
              Row(
                children: [
                  const Icon(Icons.headphones, color: Colors.blue),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      widget.title!,
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 12),
            ],

            // Message d'erreur
            if (_errorMessage != null) ...[
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: Colors.red.shade50,
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: Colors.red.shade200),
                ),
                child: Row(
                  children: [
                    Icon(Icons.error_outline, color: Colors.red.shade600, size: 20),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        _errorMessage!,
                        style: TextStyle(
                          color: Colors.red.shade700,
                          fontSize: 12,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 12),
            ],

            // Contrôles audio
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                // Bouton Play/Pause
                ElevatedButton.icon(
                  onPressed: _isInitialized ? _playPause : null,
                  icon: Icon(
                    _isPlaying && !_isPaused
                        ? Icons.pause
                        : Icons.play_arrow,
                  ),
                  label: Text(
                    _isPlaying && !_isPaused
                        ? 'Pause'
                        : _isPaused
                            ? 'Reprendre'
                            : 'Écouter',
                  ),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: _isPlaying && !_isPaused
                        ? Colors.orange
                        : Colors.blue,
                    foregroundColor: Colors.white,
                  ),
                ),

                const SizedBox(width: 12),

                // Bouton Stop
                if (_isPlaying || _isPaused)
                  ElevatedButton.icon(
                    onPressed: _stop,
                    icon: const Icon(Icons.stop),
                    label: const Text('Arrêter'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.red,
                      foregroundColor: Colors.white,
                    ),
                  ),
              ],
            ),

            // Indicateur d'état
            if (_isInitialized) ...[
              const SizedBox(height: 8),
              Center(
                child: Text(
                  _isPlaying && !_isPaused
                      ? '🎵 Lecture en cours...'
                      : _isPaused
                          ? '⏸️ En pause'
                          : '⏹️ Arrêté',
                  style: TextStyle(
                    fontSize: 12,
                    color: Colors.grey.shade600,
                    fontStyle: FontStyle.italic,
                  ),
                ),
              ),
            ],

            // Informations sur le service
            if (!_isInitialized) ...[
              const SizedBox(height: 8),
              Center(
                child: Text(
                  '🔄 Initialisation du service audio...',
                  style: TextStyle(
                    fontSize: 12,
                    color: Colors.grey.shade600,
                    fontStyle: FontStyle.italic,
                  ),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
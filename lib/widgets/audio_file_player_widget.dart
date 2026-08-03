import 'package:flutter/material.dart';
import '../services/audio_file_player_service.dart';

/// Widget pour lire les fichiers audio enregistrés
class AudioFilePlayerWidget extends StatefulWidget {
  final String audioUrl;
  final String? title;
  final String? subtitle;
  final bool showProgress;
  final bool autoPlay;

  const AudioFilePlayerWidget({
    super.key,
    required this.audioUrl,
    this.title,
    this.subtitle,
    this.showProgress = true,
    this.autoPlay = false,
  });

  @override
  State<AudioFilePlayerWidget> createState() => _AudioFilePlayerWidgetState();
}

class _AudioFilePlayerWidgetState extends State<AudioFilePlayerWidget> {
  final AudioFilePlayerService _playerService = AudioFilePlayerService();
  bool _isInitialized = false;
  bool _isPlaying = false;
  bool _isPaused = false;
  String? _errorMessage;
  Duration _duration = Duration.zero;
  Duration _position = Duration.zero;
  double _volume = 1.0;

  @override
  void initState() {
    super.initState();
    _initializePlayer();
  }

  Future<void> _initializePlayer() async {
    try {
      final success = await _playerService.initialize();
      if (mounted) {
        setState(() {
          _isInitialized = success;
          if (!success) {
            _errorMessage = 'Lecteur audio non disponible';
          }
        });
      }

      if (success) {
        _setupCallbacks();
        
        if (widget.autoPlay) {
          await _play();
        }
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _isInitialized = false;
          _errorMessage = 'Erreur d\'initialisation: $e';
        });
      }
    }
  }

  void _setupCallbacks() {
    _playerService.onStart = () {
      if (mounted) {
        setState(() {
          _isPlaying = true;
          _isPaused = false;
          _errorMessage = null;
        });
      }
    };

    _playerService.onComplete = () {
      if (mounted) {
        setState(() {
          _isPlaying = false;
          _isPaused = false;
          _position = Duration.zero;
        });
      }
    };

    _playerService.onPause = () {
      if (mounted) {
        setState(() {
          _isPaused = true;
        });
      }
    };

    _playerService.onResume = () {
      if (mounted) {
        setState(() {
          _isPaused = false;
        });
      }
    };

    _playerService.onError = (error) {
      if (mounted) {
        setState(() {
          _isPlaying = false;
          _isPaused = false;
          _errorMessage = error;
        });
      }
    };

    _playerService.onDurationChanged = (duration) {
      if (mounted) {
        setState(() {
          _duration = duration;
        });
      }
    };

    _playerService.onPositionChanged = (position) {
      if (mounted) {
        setState(() {
          _position = position;
        });
      }
    };
  }

  Future<void> _play() async {
    if (!_isInitialized) return;

    try {
      await _playerService.playFromUrl(widget.audioUrl);
    } catch (e) {
      setState(() {
        _errorMessage = 'Erreur de lecture: $e';
      });
    }
  }

  Future<void> _playPause() async {
    if (!_isInitialized) return;

    try {
      if (_isPlaying && !_isPaused) {
        await _playerService.pause();
      } else if (_isPlaying && _isPaused) {
        await _playerService.resume();
      } else {
        await _play();
      }
    } catch (e) {
      setState(() {
        _errorMessage = 'Erreur de contrôle: $e';
      });
    }
  }

  Future<void> _stop() async {
    if (!_isInitialized) return;

    try {
      await _playerService.stop();
    } catch (e) {
      setState(() {
        _errorMessage = 'Erreur d\'arrêt: $e';
      });
    }
  }

  Future<void> _seek(double value) async {
    if (!_isInitialized || _duration.inMilliseconds == 0) return;

    final position = Duration(
      milliseconds: (value * _duration.inMilliseconds).round(),
    );

    try {
      await _playerService.seek(position);
    } catch (e) {
      setState(() {
        _errorMessage = 'Erreur de navigation: $e';
      });
    }
  }

  Future<void> _setVolume(double volume) async {
    if (!_isInitialized) return;

    try {
      await _playerService.setVolume(volume);
      setState(() {
        _volume = volume;
      });
    } catch (e) {
      setState(() {
        _errorMessage = 'Erreur de volume: $e';
      });
    }
  }

  String _formatDuration(Duration duration) {
    String twoDigits(int n) => n.toString().padLeft(2, '0');
    final minutes = twoDigits(duration.inMinutes.remainder(60));
    final seconds = twoDigits(duration.inSeconds.remainder(60));
    return '$minutes:$seconds';
  }

  @override
  void dispose() {
    _playerService.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 3,
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            // En-tête avec titre
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: Colors.blue.shade100,
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Icon(
                    Icons.audiotrack,
                    color: Colors.blue.shade700,
                    size: 24,
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        widget.title ?? 'Enregistrement Audio',
                        style: Theme.of(context).textTheme.titleMedium?.copyWith(
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      if (widget.subtitle != null) ...[
                        const SizedBox(height: 2),
                        Text(
                          widget.subtitle!,
                          style: Theme.of(context).textTheme.bodySmall?.copyWith(
                            color: Colors.grey.shade600,
                          ),
                        ),
                      ],
                    ],
                  ),
                ),
              ],
            ),

            const SizedBox(height: 16),

            // Message d'erreur
            if (_errorMessage != null) ...[
              Container(
                padding: const EdgeInsets.all(12),
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
                          fontSize: 13,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 16),
            ],

            // Barre de progression
            if (widget.showProgress && _isInitialized) ...[
              Column(
                children: [
                  Row(
                    children: [
                      Text(
                        _formatDuration(_position),
                        style: TextStyle(
                          fontSize: 12,
                          color: Colors.grey.shade600,
                        ),
                      ),
                      Expanded(
                        child: Slider(
                          value: _duration.inMilliseconds > 0
                              ? (_position.inMilliseconds / _duration.inMilliseconds).clamp(0.0, 1.0)
                              : 0.0,
                          onChanged: _duration.inMilliseconds > 0 ? _seek : null,
                          activeColor: Colors.blue,
                          inactiveColor: Colors.grey.shade300,
                        ),
                      ),
                      Text(
                        _formatDuration(_duration),
                        style: TextStyle(
                          fontSize: 12,
                          color: Colors.grey.shade600,
                        ),
                      ),
                    ],
                  ),
                ],
              ),
              const SizedBox(height: 8),
            ],

            // Contrôles principaux
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
                    size: 28,
                  ),
                  label: Text(
                    _isPlaying && !_isPaused
                        ? 'Pause'
                        : _isPaused
                            ? 'Reprendre'
                            : 'Écouter',
                    style: const TextStyle(fontSize: 16),
                  ),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: _isPlaying && !_isPaused
                        ? Colors.orange
                        : Colors.blue,
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(25),
                    ),
                  ),
                ),

                const SizedBox(width: 16),

                // Bouton Stop
                if (_isPlaying || _isPaused)
                  ElevatedButton.icon(
                    onPressed: _stop,
                    icon: const Icon(Icons.stop, size: 24),
                    label: const Text('Arrêter'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.red,
                      foregroundColor: Colors.white,
                      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(25),
                      ),
                    ),
                  ),
              ],
            ),

            const SizedBox(height: 12),

            // Contrôle du volume
            if (_isInitialized) ...[
              Row(
                children: [
                  Icon(
                    _volume == 0 ? Icons.volume_off : Icons.volume_up,
                    color: Colors.grey.shade600,
                    size: 20,
                  ),
                  Expanded(
                    child: Slider(
                      value: _volume,
                      onChanged: _setVolume,
                      min: 0.0,
                      max: 1.0,
                      divisions: 10,
                      activeColor: Colors.blue,
                      inactiveColor: Colors.grey.shade300,
                    ),
                  ),
                  Text(
                    '${(_volume * 100).round()}%',
                    style: TextStyle(
                      fontSize: 12,
                      color: Colors.grey.shade600,
                    ),
                  ),
                ],
              ),
            ],

            // Indicateur d'état
            Center(
              child: Text(
                _isInitialized
                    ? _isPlaying && !_isPaused
                        ? '🎵 Lecture en cours...'
                        : _isPaused
                            ? '⏸️ En pause'
                            : '⏹️ Prêt à lire'
                    : '🔄 Initialisation...',
                style: TextStyle(
                  fontSize: 12,
                  color: Colors.grey.shade600,
                  fontStyle: FontStyle.italic,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
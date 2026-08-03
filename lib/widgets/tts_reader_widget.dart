import 'package:flutter/material.dart';
import 'package:resume_plus_clean/services/text_to_speech_service.dart';

/// Widget pour lire un texte à voix haute
class TtsReaderWidget extends StatefulWidget {
  final String text;
  final String? title;
  final bool showControls;
  final bool compact;

  const TtsReaderWidget({
    super.key,
    required this.text,
    this.title,
    this.showControls = true,
    this.compact = false,
  });

  @override
  State<TtsReaderWidget> createState() => _TtsReaderWidgetState();
}

class _TtsReaderWidgetState extends State<TtsReaderWidget> {
  final TextToSpeechService _tts = TextToSpeechService();
  bool _isSpeaking = false;
  bool _isPaused = false;
  bool _isInitialized = false;
  bool _isLoading = false;
  double _rate = 0.8;

  // Erreurs bénignes à ne pas montrer à l'utilisateur
  static const _benignErrors = [
    'interrupted', 'stopped', 'canceled', 'cancelled',
    'not configured', 'non configuré', '-1',
  ];

  bool _isBenignError(String error) {
    final e = error.toLowerCase();
    return _benignErrors.any((b) => e.contains(b));
  }

  @override
  void initState() {
    super.initState();
    _initTts();
  }

  Future<void> _initTts() async {
    // Tentative initiale, puis retry silencieux si échec
    bool success = await _tts.initialize();
    if (!success) {
      await Future.delayed(const Duration(milliseconds: 500));
      success = await _tts.initialize();
    }
    if (!mounted) return;
    setState(() => _isInitialized = success);

    _tts.onStart = () { if (mounted) setState(() { _isSpeaking = true; _isPaused = false; _isLoading = false; }); };
    _tts.onComplete = () { if (mounted) setState(() { _isSpeaking = false; _isPaused = false; _isLoading = false; }); };
    _tts.onPause = () { if (mounted) setState(() { _isPaused = true; _isLoading = false; }); };
    _tts.onResume = () { if (mounted) setState(() { _isPaused = false; _isSpeaking = true; _isLoading = false; }); };
    _tts.onError = (error) {
      if (!mounted) return;
      setState(() { _isSpeaking = false; _isPaused = false; _isLoading = false; });
      // Ignorer les erreurs bénignes (pause non supportée, moteur interrompu, etc.)
      if (!_isBenignError(error)) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: const Text('La lecture vocale a rencontré un problème. Réessayez.'),
            backgroundColor: Colors.orange,
            action: SnackBarAction(
              label: 'Réessayer',
              textColor: Colors.white,
              onPressed: _startSpeech,
            ),
          ),
        );
      }
    };
  }

  Future<void> _startSpeech() async {
    if (_isLoading) return;
    setState(() => _isLoading = true);
    // Si le TTS n'est pas initialisé, tenter une réinit silencieuse
    if (!_isInitialized) {
      final ok = await _tts.initialize();
      if (mounted) setState(() => _isInitialized = ok);
    }
    final textToRead = widget.title != null
        ? '${widget.title}. ${widget.text}'
        : widget.text;
    await _tts.speak(textToRead);
    if (mounted) setState(() => _isLoading = false);
  }

  Future<void> _toggleSpeech() async {
    if (_isLoading) return;
    if (_isPaused) {
      setState(() => _isLoading = true);
      await _tts.resume();
      if (mounted) setState(() => _isLoading = false);
    } else if (_isSpeaking) {
      setState(() => _isLoading = true);
      await _tts.pause();
      if (mounted) setState(() => _isLoading = false);
    } else {
      await _startSpeech();
    }
  }

  Future<void> _stopSpeech() async {
    await _tts.stop();
    if (mounted) setState(() { _isSpeaking = false; _isPaused = false; _isLoading = false; });
  }

  void _changeRate(double newRate) {
    setState(() => _rate = newRate);
    _tts.setRate(newRate);
  }

  @override
  void dispose() {
    _tts.stop();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (widget.compact) {
      return _buildCompactButton();
    }
    return _buildFullControls();
  }

  Widget _buildCompactButton() {
    if (_isLoading) {
      return const SizedBox(
        width: 36, height: 36,
        child: Padding(
          padding: EdgeInsets.all(8),
          child: CircularProgressIndicator(strokeWidth: 2),
        ),
      );
    }
    IconData icon;
    String tooltip;
    Color color = Theme.of(context).primaryColor;
    if (_isPaused) {
      icon = Icons.play_circle_outline;
      tooltip = 'Reprendre la lecture';
      color = Colors.orange;
    } else if (_isSpeaking) {
      icon = Icons.pause_circle_outline;
      tooltip = 'Mettre en pause';
      color = Colors.red;
    } else {
      icon = Icons.volume_up;
      tooltip = 'Lire à voix haute';
    }
    return IconButton(
      onPressed: _isInitialized ? _toggleSpeech : null,
      icon: Icon(icon, color: color),
      tooltip: tooltip,
    );
  }

  Widget _buildFullControls() {
    final theme = Theme.of(context);

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.record_voice_over, color: theme.primaryColor),
                const SizedBox(width: 8),
                Text(
                  'Lecture vocale',
                  style: theme.textTheme.titleSmall?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const Spacer(),
                if (!_isInitialized)
                  const SizedBox(
                    width: 16,
                    height: 16,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  ),
              ],
            ),
            const SizedBox(height: 12),
            
            // Bouton principal play/pause/stop
            Row(
              children: [
                Expanded(
                  child: ElevatedButton.icon(
                    onPressed: (_isInitialized && !_isLoading) ? _toggleSpeech : null,
                    icon: _isLoading
                        ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                        : Icon(_isPaused ? Icons.play_arrow : (_isSpeaking ? Icons.pause : Icons.play_arrow)),
                    label: Text(_isLoading ? 'Chargement...' : (_isPaused ? 'Reprendre' : (_isSpeaking ? 'Pause' : 'Lire le résumé'))),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: _isPaused ? Colors.orange : (_isSpeaking ? Colors.orange : theme.primaryColor),
                      foregroundColor: Colors.white,
                    ),
                  ),
                ),
                if (_isSpeaking || _isPaused) ...[  
                  const SizedBox(width: 8),
                  IconButton(
                    onPressed: _stopSpeech,
                    icon: const Icon(Icons.stop_circle_outlined, color: Colors.red),
                    tooltip: 'Arrêter',
                  ),
                ],
              ],
            ),
            
            if (widget.showControls) ...[
              const SizedBox(height: 12),
              
              // Contrôle de vitesse
              Row(
                children: [
                  const Icon(Icons.speed, size: 18),
                  const SizedBox(width: 8),
                  const Text('Vitesse:'),
                  Expanded(
                    child: Slider(
                      value: _rate,
                      min: 0.5,
                      max: 2.0,
                      divisions: 6,
                      label: '${_rate.toStringAsFixed(1)}x',
                      onChanged: _changeRate,
                    ),
                  ),
                  Text('${_rate.toStringAsFixed(1)}x'),
                ],
              ),
            ],
          ],
        ),
      ),
    );
  }
}

/// Bouton simple pour la lecture vocale (à utiliser dans les listes)
class TtsButton extends StatefulWidget {
  final String text;
  final double size;

  const TtsButton({
    super.key,
    required this.text,
    this.size = 24,
  });

  @override
  State<TtsButton> createState() => _TtsButtonState();
}

class _TtsButtonState extends State<TtsButton> {
  final TextToSpeechService _tts = TextToSpeechService();
  bool _isSpeaking = false;

  @override
  void initState() {
    super.initState();
    _tts.initialize();
    
    _tts.onStart = () => setState(() => _isSpeaking = true);
    _tts.onComplete = () => setState(() => _isSpeaking = false);
  }

  @override
  Widget build(BuildContext context) {
    return IconButton(
      iconSize: widget.size,
      onPressed: () async {
        if (_isSpeaking) {
          await _tts.stop();
        } else {
          await _tts.speak(widget.text);
        }
      },
      icon: Icon(
        _isSpeaking ? Icons.stop_circle : Icons.volume_up,
        color: _isSpeaking ? Colors.red : Theme.of(context).primaryColor,
      ),
      tooltip: _isSpeaking ? 'Arrêter' : 'Lire',
    );
  }

  @override
  void dispose() {
    _tts.stop();
    super.dispose();
  }
}

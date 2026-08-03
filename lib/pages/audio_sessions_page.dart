// ignore_for_file: avoid_web_libraries_in_flutter
import 'package:flutter/material.dart';
import 'package:resume_plus_clean/services/api_service.dart';
import 'package:resume_plus_clean/theme/app_theme.dart';
import 'package:intl/intl.dart';
import 'dart:html' as html;

class AudioSessionsPage extends StatefulWidget {
  const AudioSessionsPage({super.key});

  @override
  State<AudioSessionsPage> createState() => _AudioSessionsPageState();
}

class _AudioSessionsPageState extends State<AudioSessionsPage> {
  final ApiService _apiService = ApiService();
  List<dynamic> _sessions = [];
  bool _isLoading = true;
  String _error = '';
  Map<String, dynamic>? _stats;

  html.AudioElement? _audioPlayer;
  bool _isPlaying = false;
  int? _currentPlayingSessionId;

  @override
  void initState() {
    super.initState();
    _loadAudioSessions();
    _loadStats();
  }

  Future<void> _loadAudioSessions() async {
    setState(() { _isLoading = true; _error = ''; });
    try {
      final sessions = await _apiService.getAudioSessionsDetailed();
      setState(() { _sessions = sessions; _isLoading = false; });
    } catch (e) {
      setState(() { _error = e.toString(); _isLoading = false; });
    }
  }

  Future<void> _loadStats() async {
    try {
      final stats = await _apiService.getAudioProcessingStats();
      setState(() { _stats = stats['stats']; });
    } catch (e) {
      print('Erreur stats: $e');
    }
  }

  Future<void> _processAudioSession(int sessionId) async {
    try {
      showDialog(
        context: context,
        barrierDismissible: false,
        builder: (context) => const AlertDialog(
          content: Row(
            children: [CircularProgressIndicator(), SizedBox(width: 16), Text('Traitement en cours...')],
          ),
        ),
      );
      final result = await _apiService.processAudioSession(sessionId);
      if (mounted) {
        Navigator.of(context).pop();
        if (result['success'] == true) {
          ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('? ${result['message']}'), backgroundColor: Colors.green));
          _loadAudioSessions();
          _loadStats();
        } else {
          ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('? ${result['error']}'), backgroundColor: Colors.red));
        }
      }
    } catch (e) {
      if (mounted) {
        Navigator.of(context).pop();
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('? Erreur: $e'), backgroundColor: Colors.red));
      }
    }
  }

  Future<void> _autoProcessAllSessions() async {
    try {
      showDialog(
        context: context,
        barrierDismissible: false,
        builder: (context) => const AlertDialog(
          content: Row(
            children: [CircularProgressIndicator(), SizedBox(width: 16), Text('Traitement automatique en cours...')],
          ),
        ),
      );
      final result = await _apiService.autoProcessPendingSessions();
      if (mounted) {
        Navigator.of(context).pop();
        if (result['success'] == true) {
          ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('? ${result['message']}'), backgroundColor: Colors.green));
          _loadAudioSessions();
          _loadStats();
        } else {
          ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('? ${result['error']}'), backgroundColor: Colors.red));
        }
      }
    } catch (e) {
      if (mounted) {
        Navigator.of(context).pop();
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('? Erreur: $e'), backgroundColor: Colors.red));
      }
    }
  }

  Future<void> _playAudio(int sessionId, String courseName) async {
    if (_isPlaying) _stopPlayback();
    try {
      setState(() { _isPlaying = true; _currentPlayingSessionId = sessionId; });
      final result = await _apiService.getAudioFileUrl(sessionId);
      if (mounted) {
        if (result['success'] == true) {
          await _startAudioPlayback(result['audio_url'], courseName);
        } else {
          setState(() { _isPlaying = false; _currentPlayingSessionId = null; });
          ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: const Text('? Impossible de charger l\'audio'), backgroundColor: Colors.red));
        }
      }
    } catch (e) {
      if (mounted) {
        setState(() { _isPlaying = false; _currentPlayingSessionId = null; });
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('? Erreur: $e'), backgroundColor: Colors.red));
      }
    }
  }

  Future<void> _startAudioPlayback(String audioUrl, String courseName) async {
    try {
      _audioPlayer = html.AudioElement();
      _audioPlayer!.controls = false;
      _audioPlayer!.autoplay = false;
      _audioPlayer!.preload = 'metadata';
      _audioPlayer!.crossOrigin = 'anonymous';

      _audioPlayer!.onEnded.listen((_) {
        setState(() { _isPlaying = false; _currentPlayingSessionId = null; });
        _audioPlayer = null;
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('? Lecture de "$courseName" terminée'), backgroundColor: Colors.green));
      });

      _audioPlayer!.onError.listen((error) {
        setState(() { _isPlaying = false; _currentPlayingSessionId = null; });
        _audioPlayer = null;
        _tryAlternativePlayback(audioUrl, courseName);
      });

      _audioPlayer!.src = audioUrl;
      _audioPlayer!.load();
      await Future.delayed(const Duration(milliseconds: 500));
      await _audioPlayer!.play();

      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
        content: Text('?? Lecture de "$courseName" en cours...'),
        backgroundColor: Colors.blue,
        action: SnackBarAction(label: 'Arrêter', textColor: Colors.white, onPressed: _stopPlayback),
      ));
    } catch (e) {
      setState(() { _isPlaying = false; _currentPlayingSessionId = null; });
      _tryAlternativePlayback(audioUrl, courseName);
    }
  }

  void _tryAlternativePlayback(String audioUrl, String courseName) {
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(
      content: const Text('?? Format non supporté. Ouverture dans un nouvel onglet...'),
      backgroundColor: Colors.orange,
      action: SnackBarAction(label: 'Ouvrir', textColor: Colors.white, onPressed: () => html.window.open(audioUrl, '_blank')),
    ));
    html.window.open(audioUrl, '_blank');
  }

  void _stopPlayback() {
    try {
      _audioPlayer?.pause();
      _audioPlayer = null;
      setState(() { _isPlaying = false; _currentPlayingSessionId = null; });
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('?? Lecture arrêtée'), backgroundColor: Colors.orange));
    } catch (e) {
      print('? Erreur arrêt lecture: $e');
    }
  }

  @override
  void dispose() {
    _audioPlayer?.pause();
    _audioPlayer = null;
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final topPadding = MediaQuery.of(context).padding.top;

    return Scaffold(
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      body: Column(
        children: [
          Container(
            width: double.infinity,
            padding: EdgeInsets.only(top: topPadding + 8, left: 20, right: 20, bottom: 16),
            decoration: const BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
                colors: [AppTheme.primaryBlueDark, AppTheme.primaryBlue, AppTheme.primaryBlueLight],
              ),
              borderRadius: BorderRadius.only(bottomLeft: Radius.circular(24), bottomRight: Radius.circular(24)),
            ),
            child: Row(
              children: [
                GestureDetector(
                  onTap: () => Navigator.of(context).pop(),
                  child: Container(
                    width: 40, height: 40,
                    decoration: BoxDecoration(color: Colors.white.withOpacity(0.2), borderRadius: BorderRadius.circular(12)),
                    child: const Icon(Icons.arrow_back_rounded, color: Colors.white, size: 22),
                  ),
                ),
                const SizedBox(width: 14),
                Text('?? Sessions Audio', style: theme.textTheme.titleLarge?.copyWith(color: Colors.white, fontWeight: FontWeight.w700)),
                const Spacer(),
                if (_stats != null && (_stats!['pending_sessions'] ?? 0) > 0)
                  GestureDetector(
                    onTap: _autoProcessAllSessions,
                    child: Container(
                      width: 40, height: 40,
                      decoration: BoxDecoration(color: Colors.white.withOpacity(0.2), borderRadius: BorderRadius.circular(12)),
                      child: const Icon(Icons.smart_toy_rounded, color: Colors.white, size: 20),
                    ),
                  ),
                const SizedBox(width: 8),
                GestureDetector(
                  onTap: _loadAudioSessions,
                  child: Container(
                    width: 40, height: 40,
                    decoration: BoxDecoration(color: Colors.white.withOpacity(0.2), borderRadius: BorderRadius.circular(12)),
                    child: const Icon(Icons.refresh_rounded, color: Colors.white, size: 20),
                  ),
                ),
              ],
            ),
          ),
          Expanded(
            child: Column(
              children: [
                if (_stats != null)
                  Container(
                    width: double.infinity,
                    margin: const EdgeInsets.all(16),
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(16), boxShadow: AppTheme.softShadow),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Container(
                              width: 32, height: 32,
                              decoration: BoxDecoration(color: AppTheme.primaryBlue.withOpacity(0.1), borderRadius: BorderRadius.circular(10)),
                              child: const Icon(Icons.analytics_rounded, color: AppTheme.primaryBlue, size: 18),
                            ),
                            const SizedBox(width: 12),
                            const Text('Statistiques Audio', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600, color: AppTheme.textPrimary)),
                          ],
                        ),
                        const SizedBox(height: 16),
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceAround,
                          children: [
                            _buildStatCard('Total', '${_stats!['total_sessions']}', AppTheme.accentBlue),
                            _buildStatCard('Traitées', '${_stats!['processed_sessions']}', AppTheme.success),
                            _buildStatCard('En attente', '${_stats!['pending_sessions']}', AppTheme.warning),
                            _buildStatCard('Taille', '${_stats!['total_audio_size_mb']} MB', AppTheme.primaryBlue),
                          ],
                        ),
                        const SizedBox(height: 12),
                        LinearProgressIndicator(
                          value: (_stats!['processing_rate'] ?? 0) / 100,
                          backgroundColor: Theme.of(context).scaffoldBackgroundColor,
                          valueColor: AlwaysStoppedAnimation<Color>(
                            _stats!['processing_rate'] == 100 ? AppTheme.success : AppTheme.warning,
                          ),
                          borderRadius: BorderRadius.circular(4),
                        ),
                        const SizedBox(height: 6),
                        Text('Taux de traitement: ${_stats!['processing_rate']}%', style: const TextStyle(fontSize: 12, color: AppTheme.textLight)),
                      ],
                    ),
                  ),
                Expanded(
                  child: _isLoading
                      ? const Center(child: CircularProgressIndicator(color: AppTheme.primaryBlue))
                      : _error.isNotEmpty
                          ? Center(
                              child: Column(
                                mainAxisAlignment: MainAxisAlignment.center,
                                children: [
                                  Container(width: 72, height: 72, decoration: BoxDecoration(color: AppTheme.error.withOpacity(0.1), shape: BoxShape.circle), child: const Icon(Icons.error_outline_rounded, size: 36, color: AppTheme.error)),
                                  const SizedBox(height: 16),
                                  Text('Erreur: $_error', style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600, color: AppTheme.textPrimary)),
                                  const SizedBox(height: 16),
                                  ElevatedButton.icon(onPressed: _loadAudioSessions, icon: const Icon(Icons.refresh_rounded), label: const Text('Réessayer'), style: ElevatedButton.styleFrom(backgroundColor: AppTheme.primaryBlue, foregroundColor: Colors.white, shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)))),
                                ],
                              ),
                            )
                          : _sessions.isEmpty
                              ? Center(
                                  child: Column(
                                    mainAxisAlignment: MainAxisAlignment.center,
                                    children: [
                                      Container(width: 72, height: 72, decoration: BoxDecoration(color: AppTheme.primaryBlue.withOpacity(0.1), shape: BoxShape.circle), child: const Icon(Icons.mic_off_rounded, size: 36, color: AppTheme.primaryBlue)),
                                      const SizedBox(height: 16),
                                      const Text('Aucune session audio trouvée', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600, color: AppTheme.textPrimary)),
                                      const SizedBox(height: 6),
                                      const Text('Enregistrez un cours pour voir vos sessions ici', style: TextStyle(color: AppTheme.textLight, fontSize: 13)),
                                    ],
                                  ),
                                )
                              : _buildSessionsList(),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildStatCard(String label, String value, Color color) {
    return Column(
      children: [
        Container(
          padding: const EdgeInsets.all(8),
          decoration: BoxDecoration(color: color.withOpacity(0.1), borderRadius: BorderRadius.circular(8)),
          child: Icon(Icons.analytics_rounded, color: color, size: 20),
        ),
        const SizedBox(height: 4),
        Text(value, style: TextStyle(fontWeight: FontWeight.bold, color: color)),
        Text(label, style: const TextStyle(fontSize: 12)),
      ],
    );
  }

  Widget _buildSessionsList() {
    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: _sessions.length,
      itemBuilder: (context, index) {
        final session = _sessions[index];
        final audioInfo = session['audio_info'] ?? {};
        final relatedSummaries = session['related_summaries'] ?? [];
        final theme = Theme.of(context);

        return Card(
          margin: const EdgeInsets.only(bottom: 16),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.all(8),
                      decoration: BoxDecoration(color: theme.colorScheme.primary.withOpacity(0.1), borderRadius: BorderRadius.circular(8)),
                      child: Icon(Icons.mic, color: theme.colorScheme.primary),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(session['course']['nom'] ?? 'Cours inconnu', style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
                          Text('${session['course']['filiere']} - ${session['course']['university']}', style: theme.textTheme.bodySmall?.copyWith(color: Colors.grey.shade600)),
                        ],
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                Row(
                  children: [
                    Icon(Icons.person, size: 16, color: Colors.grey.shade600),
                    const SizedBox(width: 4),
                    Text(session['professeur'] ?? 'Professeur inconnu', style: theme.textTheme.bodySmall),
                    const SizedBox(width: 16),
                    Icon(Icons.calendar_today, size: 16, color: Colors.grey.shade600),
                    const SizedBox(width: 4),
                    Text(
                      session['date'] != null ? DateFormat('dd/MM/yyyy HH:mm').format(DateTime.parse(session['date'])) : 'Date inconnue',
                      style: theme.textTheme.bodySmall,
                    ),
                  ],
                ),
                if (audioInfo.isNotEmpty && audioInfo['success'] == true) ...[
                  const SizedBox(height: 8),
                  Row(
                    children: [
                      Icon(Icons.audio_file, size: 16, color: Colors.grey.shade600),
                      const SizedBox(width: 4),
                      Text('${audioInfo['file_size_mb'] ?? 0} MB', style: theme.textTheme.bodySmall),
                      const SizedBox(width: 16),
                      Icon(Icons.timer, size: 16, color: Colors.grey.shade600),
                      const SizedBox(width: 4),
                      Text('~${audioInfo['estimated_duration_minutes'] ?? 0} min', style: theme.textTheme.bodySmall),
                    ],
                  ),
                ],
                if (relatedSummaries.isNotEmpty) ...[
                  const SizedBox(height: 12),
                  Container(
                    padding: const EdgeInsets.all(8),
                    decoration: BoxDecoration(color: Colors.green.shade50, borderRadius: BorderRadius.circular(6)),
                    child: Row(
                      children: [
                        Icon(Icons.check_circle, color: Colors.green.shade700, size: 16),
                        const SizedBox(width: 6),
                        Text('${relatedSummaries.length} résumé(s) généré(s)', style: TextStyle(color: Colors.green.shade700, fontSize: 12, fontWeight: FontWeight.bold)),
                      ],
                    ),
                  ),
                ],
                const SizedBox(height: 16),
                Row(
                  children: [
                    Expanded(
                      child: _currentPlayingSessionId == session['id'] && _isPlaying
                          ? ElevatedButton.icon(
                              onPressed: _stopPlayback,
                              icon: const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2, valueColor: AlwaysStoppedAnimation<Color>(Colors.white))),
                              label: const Text('En cours...'),
                              style: ElevatedButton.styleFrom(backgroundColor: Colors.orange, foregroundColor: Colors.white),
                            )
                          : OutlinedButton.icon(
                              onPressed: _isPlaying ? null : () => _playAudio(session['id'], session['course']['nom'] ?? 'Cours'),
                              icon: const Icon(Icons.play_arrow),
                              label: const Text('Écouter'),
                            ),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: ElevatedButton.icon(
                        onPressed: relatedSummaries.isEmpty ? () => _processAudioSession(session['id']) : null,
                        icon: const Icon(Icons.smart_toy),
                        label: Text(relatedSummaries.isEmpty ? 'Générer Résumé' : 'Résumé Créé'),
                        style: ElevatedButton.styleFrom(backgroundColor: relatedSummaries.isEmpty ? theme.colorScheme.primary : Colors.grey),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        );
      },
    );
  }
}

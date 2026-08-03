import 'dart:async';
import 'package:flutter/material.dart';
import 'package:audioplayers/audioplayers.dart';
import 'package:resume_plus_clean/services/api_service.dart';
import 'package:resume_plus_clean/services/snackbar_service.dart';
import 'package:resume_plus_clean/theme/app_theme.dart';
import 'package:resume_plus_clean/features/app/screens/main_navigation_screen.dart';

class AudioSessionsScreen extends StatefulWidget {
  const AudioSessionsScreen({super.key});

  @override
  State<AudioSessionsScreen> createState() => _AudioSessionsScreenState();
}

class _AudioSessionsScreenState extends State<AudioSessionsScreen> with SingleTickerProviderStateMixin {
  final ApiService _apiService = ApiService();
  final AudioPlayer _audioPlayer = AudioPlayer();
  late TabController _tabController;
  
  List<dynamic> _sessions = [];
  Map<String, dynamic> _stats = {};
  bool _isLoading = true;
  String? _currentPlayingUrl;
  bool _isPlaying = false;
  Set<int> _processingSessionIds = {};
  String _currentFilter = 'all';
  Timer? _autoRefreshTimer;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 4, vsync: this);
    _tabController.addListener(_onTabChanged);
    _loadSessions();
    _setupAudioPlayer();
    _startAutoRefresh();
  }

  void _onTabChanged() {
    if (_tabController.indexIsChanging) return;
    final filters = ['all', 'pending', 'summarized', 'failed'];
    setState(() {
      _currentFilter = filters[_tabController.index];
    });
  }

  void _setupAudioPlayer() {
    _audioPlayer.onPlayerStateChanged.listen((PlayerState state) {
      setState(() {
        _isPlaying = state == PlayerState.playing;
      });
    });

    _audioPlayer.onPlayerComplete.listen((event) {
      setState(() {
        _isPlaying = false;
        _currentPlayingUrl = null;
      });
    });
  }

  Future<void> _loadSessions() async {
    try {
      print('🔄 Chargement de la file d\'attente...');
      final result = await _apiService.getSessionsQueue();
      
      if (result['success'] == true) {
        setState(() {
          _sessions = result['sessions'] ?? [];
          _stats = result['stats'] ?? {};
          _isLoading = false;
        });
        print('✅ ${_sessions.length} sessions trouvées');
      } else {
        throw Exception(result['error'] ?? 'Erreur inconnue');
      }
    } catch (e) {
      print('❌ Erreur chargement sessions: $e');
      setState(() {
        _isLoading = false;
      });
      SnackbarService.show('Erreur lors du chargement: $e', isError: true);
    }
  }

  Future<void> _playAudio(String audioUrl) async {
    try {
      if (_currentPlayingUrl == audioUrl && _isPlaying) {
        await _audioPlayer.pause();
      } else {
        await _audioPlayer.stop();
        
        // Construire l'URL complète en utilisant le baseUrl de production
        final baseUrl = ApiService.baseUrl.replaceAll('/api', '');
        final fullUrl = audioUrl.startsWith('http') 
            ? audioUrl 
            : '$baseUrl$audioUrl';
        
        print('Tentative de lecture: $fullUrl');
        SnackbarService.show('🎵 Lecture en cours...', isError: false);
        
        await _audioPlayer.play(UrlSource(fullUrl));
        setState(() {
          _currentPlayingUrl = audioUrl;
        });
      }
    } catch (e) {
      SnackbarService.show('❌ Erreur de lecture: $e', isError: true);
      setState(() {
        _isPlaying = false;
        _currentPlayingUrl = null;
      });
    }
  }

  /// Relancer une session en échec (traitement asynchrone en arrière-plan)
  Future<void> _retryFailedSession(int sessionId) async {
    setState(() {
      _processingSessionIds.add(sessionId);
    });

    try {
      SnackbarService.show('🔄 Relance du traitement en arrière-plan...', isError: false);
      
      final result = await _apiService.retryFailedSession(sessionId);
      
      if (result['success'] == true) {
        SnackbarService.show(
          '✅ Traitement relancé en arrière-plan. La transcription et le résumé seront générés automatiquement.',
          isError: false,
        );
        await _loadSessions();
      } else {
        SnackbarService.show('❌ Erreur: ${result['error']}', isError: true);
        await _loadSessions();
      }
    } catch (e) {
      SnackbarService.show('❌ Erreur lors de la relance: $e', isError: true);
      await _loadSessions();
    } finally {
      setState(() {
        _processingSessionIds.remove(sessionId);
      });
    }
  }

  /// Obtenir la couleur du statut
  Color _getStatusColor(String status) {
    switch (status) {
      case 'pending':
        return Colors.orange;
      case 'processing':
        return Colors.blue;
      case 'transcribed':
        return Colors.teal;
      case 'summarized':
        return Colors.green;
      case 'failed':
        return Colors.red;
      default:
        return Colors.grey;
    }
  }

  /// Obtenir l'icône du statut
  IconData _getStatusIcon(String status) {
    switch (status) {
      case 'pending':
        return Icons.hourglass_empty;
      case 'processing':
        return Icons.sync;
      case 'transcribed':
        return Icons.text_snippet;
      case 'summarized':
        return Icons.check_circle;
      case 'failed':
        return Icons.error;
      default:
        return Icons.help;
    }
  }

  /// Obtenir le libellé du statut
  String _getStatusLabel(String status) {
    switch (status) {
      case 'pending':
        return 'En attente';
      case 'processing':
        return 'En cours';
      case 'transcribed':
        return 'Transcrit';
      case 'summarized':
        return 'Résumé disponible';
      case 'failed':
        return 'Échec';
      default:
        return 'Inconnu';
    }
  }

  /// Filtrer les sessions selon l'onglet actif
  List<dynamic> get _filteredSessions {
    if (_currentFilter == 'all') {
      return _sessions;
    }
    return _sessions.where((s) => s['processing_status'] == _currentFilter).toList();
  }

  /// Afficher le résultat de la transcription
  /// [summaryId] - ID du résumé créé (optionnel)
  void _showTranscriptionResult(Map<String, dynamic> result, {int? summaryId}) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Row(
          children: [
            Icon(Icons.check_circle, color: Colors.green),
            SizedBox(width: 8),
            Text('Transcription terminée'),
          ],
        ),
        content: SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                result['message'] ?? 'Résumé créé avec succès',
                style: const TextStyle(fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 12),
              if (result['confidence'] != null && result['confidence'] > 0)
                Text('Confiance: ${(result['confidence'] * 100).toStringAsFixed(1)}%'),
              const SizedBox(height: 12),
              const Text('Aperçu de la transcription:', 
                style: TextStyle(fontWeight: FontWeight.bold)),
              const SizedBox(height: 8),
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.grey[100],
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(
                  (result['transcript'] ?? '').toString().substring(
                    0, 
                    (result['transcript']?.toString().length ?? 0) > 300 
                        ? 300 
                        : (result['transcript']?.toString().length ?? 0)
                  ) + '...',
                  style: const TextStyle(fontSize: 12),
                ),
              ),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Fermer'),
          ),
          ElevatedButton(
            onPressed: () {
              Navigator.pop(context);
              _openValidationScreen(summaryId: summaryId);
            },
            child: const Text('Voir le résumé'),
          ),
        ],
      ),
    );
  }

  /// Ouvrir la page de validation des résumés (onglet Validation dans la nav principale)
  /// [summaryId] - ID du résumé spécifique à afficher (optionnel)
  void _openValidationScreen({int? summaryId}) {
    // Revenir à la navigation principale
    Navigator.of(context).popUntil((route) => route.isFirst);
    // Basculer vers l'onglet Validation (index 2 pour CP) avec l'ID du résumé
    MainNavigationScreen.navKey.currentState?.switchToTab(2, summaryId: summaryId);
  }

  /// Polling automatique : recharge les sessions toutes les 10s
  /// tant qu'il y a des sessions en pending/processing.
  void _startAutoRefresh() {
    _autoRefreshTimer = Timer.periodic(const Duration(seconds: 10), (_) {
      final hasPending = _sessions.any((s) {
        final st = s['processing_status'] as String? ?? '';
        return st == 'pending' || st == 'processing';
      });
      if (hasPending) {
        _loadSessions();
      }
    });
  }

  @override
  void dispose() {
    _autoRefreshTimer?.cancel();
    _tabController.dispose();
    _audioPlayer.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final topPadding = MediaQuery.of(context).padding.top;
    final theme = Theme.of(context);

    return Scaffold(
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      body: Column(
        children: [
          // Header bleu courbé
          Container(
            width: double.infinity,
            padding: EdgeInsets.only(top: topPadding + 8, left: 20, right: 20, bottom: 16),
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
              children: [
                Row(
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
                    Expanded(
                      child: Text(
                        'File d\'attente Audio',
                        style: theme.textTheme.titleLarge?.copyWith(color: Colors.white, fontWeight: FontWeight.w700),
                      ),
                    ),
                    GestureDetector(
                      onTap: _isLoading ? null : _loadSessions,
                      child: Container(
                        width: 40, height: 40,
                        decoration: BoxDecoration(
                          color: Colors.white.withOpacity(0.2),
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: _isLoading
                            ? const Padding(
                                padding: EdgeInsets.all(10),
                                child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                              )
                            : const Icon(Icons.refresh_rounded, color: Colors.white, size: 22),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 16),
                // Tabs
                Container(
                  height: 38,
                  decoration: BoxDecoration(
                    color: Colors.white.withOpacity(0.15),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: TabBar(
                    controller: _tabController,
                    isScrollable: true,
                    indicator: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(10),
                    ),
                    labelColor: AppTheme.primaryBlue,
                    unselectedLabelColor: Colors.white.withOpacity(0.8),
                    labelStyle: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600),
                    unselectedLabelStyle: const TextStyle(fontSize: 12, fontWeight: FontWeight.w500),
                    dividerColor: Colors.transparent,
                    tabAlignment: TabAlignment.start,
                    padding: const EdgeInsets.all(2),
                    tabs: [
                      Tab(child: Row(mainAxisSize: MainAxisSize.min, children: [const Text('Tout'), const SizedBox(width: 4), _buildBadge(_stats['total'] ?? 0, AppTheme.textLight)])),
                      Tab(child: Row(mainAxisSize: MainAxisSize.min, children: [const Text('En attente'), const SizedBox(width: 4), _buildBadge(_stats['pending'] ?? 0, AppTheme.warning)])),
                      Tab(child: Row(mainAxisSize: MainAxisSize.min, children: [const Text('Terminé'), const SizedBox(width: 4), _buildBadge(_stats['summarized'] ?? 0, AppTheme.success)])),
                      Tab(child: Row(mainAxisSize: MainAxisSize.min, children: [const Text('Échec'), const SizedBox(width: 4), _buildBadge(_stats['failed'] ?? 0, AppTheme.error)])),
                    ],
                  ),
                ),
              ],
            ),
          ),
          // Body
          Expanded(
            child: _isLoading
                ? const Center(child: CircularProgressIndicator(color: AppTheme.primaryBlue))
                : _filteredSessions.isEmpty
                    ? Center(
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Container(
                              width: 72, height: 72,
                              decoration: BoxDecoration(
                                color: AppTheme.primaryBlue.withOpacity(0.1),
                                shape: BoxShape.circle,
                              ),
                              child: const Icon(Icons.audiotrack_rounded, size: 36, color: AppTheme.primaryBlue),
                            ),
                            const SizedBox(height: 16),
                            Text(
                              _currentFilter == 'all' 
                                  ? 'Aucune session audio trouvée'
                                  : 'Aucune session ${_getStatusLabel(_currentFilter).toLowerCase()}',
                              style: TextStyle(
                                fontSize: 16, 
                                fontWeight: FontWeight.w600, 
                                color: Theme.of(context).colorScheme.onSurface
                              ),
                            ),
                            const SizedBox(height: 6),
                            const Text('Les sessions apparaîtront ici', style: TextStyle(color: AppTheme.textLight, fontSize: 13)),
                          ],
                        ),
                      )
                    : RefreshIndicator(
                        onRefresh: _loadSessions,
                        color: AppTheme.primaryBlue,
                        child: ListView.builder(
                          padding: const EdgeInsets.all(16),
                          itemCount: _filteredSessions.length,
                          itemBuilder: (context, index) {
                            final session = _filteredSessions[index];
                            return _buildSessionCard(session);
                          },
                        ),
                      ),
          ),
        ],
      ),
    );
  }

  Widget _buildBadge(int count, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
      decoration: BoxDecoration(
        color: color.withOpacity(0.2),
        borderRadius: BorderRadius.circular(10),
      ),
      child: Text(
        '$count',
        style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: color),
      ),
    );
  }

  Widget _buildSessionCard(Map<String, dynamic> session) {
    final audioUrl = session['audio_file'] as String?;
    final sessionId = session['id'] as int?;
    final status = session['processing_status'] as String? ?? 'pending';
    final isCurrentlyPlaying = _currentPlayingUrl == audioUrl && _isPlaying;
    final isProcessing = sessionId != null && _processingSessionIds.contains(sessionId);
    final hasTranscription = session['has_ai_summary'] == true;
    final duration = session['audio_duration_formatted'] as String? ?? '00:00';
    final errorMessage = session['error_message'] as String?;
    
    final canTranscribe = (status == 'pending' || status == 'failed' || status == 'transcribed') && !hasTranscription;
    final canViewSummary = status == 'summarized';

    final cardTheme = Theme.of(context).colorScheme.surface;
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      decoration: BoxDecoration(
        color: cardTheme,
        borderRadius: BorderRadius.circular(16),
        boxShadow: AppTheme.softShadow,
      ),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  width: 40, height: 40,
                  decoration: BoxDecoration(
                    color: _getStatusColor(status).withOpacity(0.1),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Icon(_getStatusIcon(status), color: _getStatusColor(status), size: 20),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        session['course_name'] ?? 'Session audio',
                        style: TextStyle(
                          fontWeight: FontWeight.w600, 
                          fontSize: 15, 
                          color: Theme.of(context).colorScheme.onSurface
                        ),
                      ),
                      Text(
                        'Prof: ${_getProfesseurName(session)}',
                        style: TextStyle(
                          color: Theme.of(context).colorScheme.onSurface.withOpacity(0.7), 
                          fontSize: 12
                        ),
                      ),
                    ],
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: _getStatusColor(status).withOpacity(0.1),
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(_getStatusIcon(status), size: 12, color: _getStatusColor(status)),
                      const SizedBox(width: 4),
                      Text(
                        _getStatusLabel(status),
                        style: TextStyle(fontSize: 11, color: _getStatusColor(status), fontWeight: FontWeight.w600),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),

            // Barre de progression si en cours de traitement
            if (status == 'pending' || status == 'processing' || (status == 'transcribed' && !hasTranscription) || isProcessing) ...[
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    status == 'pending'
                        ? 'En attente de traitement...'
                        : status == 'processing'
                            ? 'Transcription de l\'audio en cours...'
                            : (status == 'transcribed' && !hasTranscription)
                                ? 'Génération du résumé intelligent...'
                                : 'Relance du traitement...',
                    style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.w500,
                      color: Theme.of(context).colorScheme.primary,
                    ),
                  ),
                  SizedBox(
                    width: 12,
                    height: 12,
                    child: CircularProgressIndicator(
                      strokeWidth: 1.5,
                      color: Theme.of(context).colorScheme.primary,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 6),
              ClipRRect(
                borderRadius: BorderRadius.circular(4),
                child: LinearProgressIndicator(
                  minHeight: 4,
                  backgroundColor: Theme.of(context).brightness == Brightness.dark
                      ? Colors.white10
                      : const Color(0xFFE0E0E0),
                  color: Theme.of(context).colorScheme.primary,
                ),
              ),
              const SizedBox(height: 12),
            ],

            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: Theme.of(context).scaffoldBackgroundColor,
                borderRadius: BorderRadius.circular(12),
              ),
              child: Column(
                children: [
                  if (session['summary_title'] != null && (session['summary_title'] as String).isNotEmpty) ...[
                    _buildInfoRow(Icons.title_rounded, 'Résumé', session['summary_title']),
                    const SizedBox(height: 6),
                  ],
                  _buildInfoRow(Icons.calendar_today_rounded, 'Date', session['date'] ?? 'Non spécifiée'),
                  const SizedBox(height: 6),
                  _buildInfoRow(
                    Icons.timer_rounded,
                    'Durée',
                    duration,
                  ),
                  if (session['submitted_at'] != null) ...[
                    const SizedBox(height: 6),
                    _buildInfoRow(Icons.send_rounded, 'Soumis le', _formatDate(session['submitted_at'])),
                  ],
                  if (session['processed_at'] != null) ...[
                    const SizedBox(height: 6),
                    _buildInfoRow(Icons.done_all_rounded, 'Traité le', _formatDate(session['processed_at'])),
                  ],
                ],
              ),
            ),

            if (errorMessage != null && status == 'failed') ...[
              const SizedBox(height: 8),
              Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: AppTheme.error.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Row(
                  children: [
                    const Icon(Icons.error_outline, color: AppTheme.error, size: 18),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        errorMessage!,
                        style: const TextStyle(color: AppTheme.error, fontSize: 12),
                      ),
                    ),
                  ],
                ),
              ),
            ],

            

            const SizedBox(height: 12),
            
            Row(
              children: [
                if (audioUrl != null)
                  Expanded(
                    child: OutlinedButton.icon(
                      onPressed: () => _playAudio(audioUrl),
                      icon: Icon(isCurrentlyPlaying ? Icons.pause_rounded : Icons.play_arrow_rounded, size: 18),
                      label: Text(isCurrentlyPlaying ? 'Pause' : 'Écouter'),
                      style: OutlinedButton.styleFrom(
                        foregroundColor: AppTheme.primaryBlue,
                        side: const BorderSide(color: AppTheme.primaryBlue, width: 1.2),
                        padding: const EdgeInsets.symmetric(vertical: 8),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                      ),
                    ),
                  ),
                const SizedBox(width: 8),
                
                if (status == 'pending' || status == 'processing')
                  Expanded(
                    child: ElevatedButton.icon(
                      onPressed: null,
                      icon: const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white)),
                      label: Text(status == 'processing' ? 'Traitement en cours...' : 'En attente...'),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: AppTheme.primaryBlue,
                        disabledBackgroundColor: AppTheme.primaryBlue.withOpacity(0.6),
                        disabledForegroundColor: Colors.white70,
                        elevation: 0,
                        padding: const EdgeInsets.symmetric(vertical: 8),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                      ),
                    ),
                  ),
                
                if (sessionId != null && status == 'failed' && canTranscribe)
                  Expanded(
                    child: ElevatedButton.icon(
                      onPressed: isProcessing ? null : () => _retryFailedSession(sessionId),
                      icon: isProcessing 
                          ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                          : const Icon(Icons.refresh_rounded, size: 18),
                      label: Text(isProcessing ? 'Relance...' : 'Réessayer'),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: AppTheme.warning,
                        foregroundColor: Colors.white,
                        elevation: 0,
                        padding: const EdgeInsets.symmetric(vertical: 8),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                      ),
                    ),
                  ),
                
                if (canViewSummary)
                  Expanded(
                    child: ElevatedButton.icon(
                      onPressed: () {
                        final summaryId = session['ai_summary_id'] as int?;
                        _openValidationScreen(summaryId: summaryId);
                      },
                      icon: const Icon(Icons.description_rounded, size: 18),
                      label: const Text('Voir résumé'),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: AppTheme.success,
                        foregroundColor: Colors.white,
                        elevation: 0,
                        padding: const EdgeInsets.symmetric(vertical: 8),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                      ),
                    ),
                  ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildInfoRow(IconData icon, String label, String value, {Color? valueColor, String? suffix}) {
    final defaultTextColor = Theme.of(context).colorScheme.onSurface;
    return Row(
      children: [
        Icon(icon, size: 14, color: AppTheme.textLight),
        const SizedBox(width: 8),
        Text('$label: ', style: const TextStyle(color: AppTheme.textLight, fontSize: 12)),
        Expanded(
          child: Text(
            '$value${suffix ?? ''}',
            style: TextStyle(
              fontWeight: FontWeight.w500,
              fontSize: 12,
              color: valueColor ?? defaultTextColor,
            ),
          ),
        ),
      ],
    );
  }

  String _getProfesseurName(Map<String, dynamic> session) {
    final info = session['professeur_info'] as Map<String, dynamic>?;
    if (info != null) {
      final fullName = info['user_full_name']?.toString() ?? '';
      if (fullName.trim().isNotEmpty) return fullName;
      final username = info['user_username']?.toString() ?? '';
      if (username.trim().isNotEmpty) return username;
    }
    return session['professeur']?.toString().isNotEmpty == true
        ? session['professeur']
        : 'Inconnu';
  }

  String _formatDate(String? dateStr) {
    if (dateStr == null) return 'N/A';
    try {
      final date = DateTime.parse(dateStr);
      return '${date.day.toString().padLeft(2, '0')}/${date.month.toString().padLeft(2, '0')}/${date.year} ${date.hour.toString().padLeft(2, '0')}:${date.minute.toString().padLeft(2, '0')}';
    } catch (e) {
      return dateStr;
    }
  }
}

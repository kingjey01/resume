import 'dart:async';
import 'dart:io';
import 'dart:typed_data';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
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
  // Abonnements du lecteur, annulés à la fermeture de l'écran.
  StreamSubscription<PlayerState>? _subEtat;
  StreamSubscription<void>? _subFin;
  late TabController _tabController;
  
  List<dynamic> _sessions = [];
  Map<String, dynamic> _stats = {};
  bool _isLoading = true;
  String? _currentPlayingUrl;
  bool _isPlaying = false;
  // Voir _playAudio : empêche deux préparations de lecture simultanées.
  bool _lectureEnPreparation = false;
  Set<int> _processingSessionIds = {};
  String _currentFilter = 'all';
  Timer? _autoRefreshTimer;
  bool _isRefreshing = false;

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
    // Purge du cache des lectures, faite à l'ouverture et jamais pendant une
    // lecture (tâche 41 : ne pas supprimer un fichier que le lecteur utilise).
    _purgerCacheAncien();

    // LES ABONNEMENTS SONT CONSERVÉS POUR ÊTRE ANNULÉS À LA FERMETURE.
    // Un lecteur qui émet après la disparition de l'écran appelle `setState`
    // sur un State détruit — c'est l'une des causes des erreurs « au changement
    // d'écran » signalées dans la tâche 41. Le garde `mounted` couvre en plus
    // la fenêtre où l'écran est en cours de destruction.
    _subEtat = _audioPlayer.onPlayerStateChanged.listen((PlayerState state) {
      if (!mounted) return;
      setState(() {
        _isPlaying = state == PlayerState.playing;
      });
    });

    _subFin = _audioPlayer.onPlayerComplete.listen((event) {
      if (!mounted) return;
      setState(() {
        _isPlaying = false;
        _currentPlayingUrl = null;
      });
    });
  }

  Future<void> _loadSessions({bool silent = false}) async {
    if (_isRefreshing) return; // éviter les appels simultanés
    _isRefreshing = true;
    try {
      print('🔄 Chargement de la file d\'attente...');
      final result = await _apiService.getSessionsQueue();

      if (result['success'] == true) {
        // La réponse peut arriver APRÈS la fermeture de l'écran (changement
        // d'onglet pendant un rafraîchissement) : setState sur un State détruit
        // lève une exception. On vérifie donc l'écran avant d'écrire.
        if (!mounted) return;
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
      if (!mounted) return;
      setState(() {
        _isLoading = false;
      });
      // Pas de snackbar lors du rafraîchissement automatique silencieux
      if (!silent) {
        SnackbarService.show('Erreur lors du chargement: $e', isError: true);
      }
    } finally {
      _isRefreshing = false;
    }
  }

  /// CACHE DE LECTURE — un fichier stable par enregistrement.
  ///
  /// CE QUI CAUSAIT `FileSystemException: writeFrom failed` (tâche 41) : chaque
  /// lecture téléchargeait l'audio et l'écrivait sous un NOUVEAU nom horodaté,
  /// sans jamais supprimer les précédents. Un enregistrement de 65 Mo relu
  /// quelques fois remplissait donc le dossier temporaire de l'application, et
  /// l'écriture suivante échouait — « writeFrom failed », exactement l'erreur
  /// signalée, et intermittente par nature.
  ///
  /// Avec ce cache : un seul fichier par enregistrement, réutilisé d'une lecture
  /// à l'autre. Plus d'écriture répétée, plus d'accumulation — et surtout plus
  /// de téléchargement quand le fichier est déjà là (tâche 41, §2 et §6).
  Directory get _dossierCache =>
      Directory('${Directory.systemTemp.path}/lectures_muhtasari');

  /// Clé stable, tirée du NOM DU FICHIER dans l'URL (les paramètres changent).
  String _cleDeCache(String url) {
    final nom = url.split('?').first.split('/').last;
    final propre = nom.replaceAll(RegExp(r'[^A-Za-z0-9._-]'), '_');
    return propre.isEmpty ? 'audio' : propre;
  }

  String _baseDeCle(String cle) =>
      cle.contains('.') ? cle.substring(0, cle.lastIndexOf('.')) : cle;

  /// Lecture déjà en cache, quelle que soit l'extension retenue à l'écriture.
  File? _fichierEnCache(String cle) {
    try {
      if (!_dossierCache.existsSync()) return null;
      final base = _baseDeCle(cle);
      for (final entree in _dossierCache.listSync()) {
        if (entree is! File) continue;
        final nom = entree.uri.pathSegments.last;
        final nomBase = nom.contains('.')
            ? nom.substring(0, nom.lastIndexOf('.'))
            : nom;
        if (nomBase == base && entree.lengthSync() > 0) return entree;
      }
    } catch (_) {
      // Un cache illisible n'empêche pas de retélécharger.
    }
    return null;
  }

  /// Supprime les lectures en cache depuis plus de sept jours.
  ///
  /// Appelée à l'ouverture de l'écran, jamais pendant une lecture : on ne
  /// supprime pas un fichier que le lecteur utilise (tâche 41, contraintes).
  void _purgerCacheAncien() {
    try {
      if (!_dossierCache.existsSync()) return;
      final limite = DateTime.now().subtract(const Duration(days: 7));
      for (final entree in _dossierCache.listSync()) {
        if (entree is File && entree.statSync().modified.isBefore(limite)) {
          entree.deleteSync();
        }
      }
    } catch (_) {
      // Sans conséquence : au pire, le cache reste un peu plus longtemps.
    }
  }

  /// Écrit les octets dans le cache, sous un nom STABLE, avec l'extension
  /// réelle du contenu — AVPlayer la lit pour choisir son décodeur.
  Future<File> _ecrireDansCache(
      String cle, Uint8List octets, String extension) async {
    if (!_dossierCache.existsSync()) {
      await _dossierCache.create(recursive: true);
    }
    final fichier = File('${_dossierCache.path}/${_baseDeCle(cle)}.$extension');
    // Une écriture ratée (stockage plein, sandbox) est dite clairement à
    // l'appelant, qui affichera un message compréhensible.
    await fichier.writeAsBytes(octets, flush: true);
    return fichier;
  }

  /// Extension RÉELLE, déduite des premiers octets du fichier.
  ///
  /// POURQUOI LE CONTENU ET NON L'URL (constat du 2026-10-14) : le même fichier
  /// se lit sur Android et échoue sur iOS. La différence est là — ExoPlayer
  /// inspecte le contenu pour choisir son décodeur, AVPlayer se fie à
  /// l'EXTENSION du fichier. Un nom qui ne reflète pas le format (renommé au
  /// dépôt, extension perdue, conteneur différent) passe donc sur Android et
  /// échoue sur iOS avec « Unknown error ».
  ///
  /// Renvoie `null` si la signature est inconnue : l'appelant retombe alors sur
  /// l'extension de l'URL.
  String? _extensionDepuisContenu(Uint8List octets) {
    if (octets.length < 12) return null;

    // Conteneur MP4 / M4A : « ftyp » aux octets 4 à 7.
    if (octets[4] == 0x66 && octets[5] == 0x74 &&
        octets[6] == 0x79 && octets[7] == 0x70) {
      return 'm4a';
    }
    // WAV : « RIFF ».
    if (octets[0] == 0x52 && octets[1] == 0x49 &&
        octets[2] == 0x46 && octets[3] == 0x46) {
      return 'wav';
    }
    // Ogg / Opus : « OggS ».
    if (octets[0] == 0x4F && octets[1] == 0x67 &&
        octets[2] == 0x67 && octets[3] == 0x53) {
      return 'ogg';
    }
    // AMR : « #!AMR ».
    if (octets[0] == 0x23 && octets[1] == 0x21 &&
        octets[2] == 0x41 && octets[3] == 0x4D) {
      return 'amr';
    }
    // MP3 avec étiquette ID3, ou première trame MPEG (0xFF 0xEx/0xFx).
    if (octets[0] == 0x49 && octets[1] == 0x44 && octets[2] == 0x33) {
      return 'mp3';
    }
    if (octets[0] == 0xFF && (octets[1] & 0xE0) == 0xE0) {
      return ((octets[1] & 0xF6) == 0xF0) ? 'aac' : 'mp3';
    }
    return null;
  }

  /// Extension de fichier déduite de l'URL du média — dernier recours, quand la
  /// signature du contenu n'est pas reconnue.
  String _extensionDepuisUrl(String url) {
    final sansParametres = url.split('?').first;
    final point = sansParametres.lastIndexOf('.');
    if (point == -1) return 'm4a';
    final extension = sansParametres.substring(point + 1).toLowerCase();
    return (extension.isNotEmpty && extension.length <= 5) ? extension : 'm4a';
  }

  Future<void> _playAudio(String audioUrl) async {
    // ANTI-DOUBLE-APPUI (tâche 41, §6). Deux appuis rapides lanceraient deux
    // téléchargements vers LE MÊME fichier de cache : une écriture concurrente
    // — dont « FileSystemException: writeFrom failed » était le symptôme.
    if (_lectureEnPreparation) return;
    _lectureEnPreparation = true;
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

        SnackbarService.show('🎵 Lecture en cours...', isError: false);

        // TÉLÉCHARGER PUIS LIRE, au lieu de confier l'URL à AVPlayer.
        //
        // AVPlayer n'envoie aucun en-tête et, quand la réponse ne lui convient
        // pas — fichier absent, page d'erreur HTML, absence de support des
        // requêtes « Range » —, il répond seulement
        // « AVPlayerItem.Status.failed on setSourceUrl: Unknown error, null ».
        // Via Dio, la requête porte le jeton de l'application, et un échec
        // devient un code HTTP que l'on peut afficher.
        // 1. DÉJÀ EN CACHE ? On lit, sans toucher au réseau (tâche 41, §2) :
        //    un fichier présent localement ne doit pas être retéléchargé.
        final cle = _cleDeCache(fullUrl);
        var fichier = _fichierEnCache(cle);

        if (fichier == null) {
          final octets = await _apiService.telechargerFichier(fullUrl);
          if (octets.isEmpty) {
            throw Exception('le serveur a renvoyé un fichier vide');
          }

          // LE SERVEUR PEUT RÉPONDRE 200 AVEC AUTRE CHOSE QUE L'AUDIO.
          // Une page de connexion, une page d'erreur HTML : les lire comme un
          // fichier audio fait échouer le lecteur avec « Unknown error », sans
          // jamais dire que ce n'est pas de l'audio. Un '<' en premier octet
          // est la signature d'un document HTML ou XML.
          if (octets.first == 0x3C) {
            throw Exception(
              'le serveur a renvoyé du HTML (${octets.length} octets) au lieu '
              'de l\'audio — le fichier n\'est pas accessible à cette adresse',
            );
          }

          // L'EXTENSION VIENT DU CONTENU, ET NON DE L'URL : c'est elle
          // qu'AVPlayer lit pour choisir son décodeur. Le nom stocké par le
          // serveur peut ne pas refléter le format réel — et c'est ce qui fait
          // qu'un même fichier se lit sur Android (qui inspecte le contenu) et
          // échoue sur iOS.
          final extension =
              _extensionDepuisContenu(octets) ?? _extensionDepuisUrl(fullUrl);
          try {
            fichier = await _ecrireDansCache(cle, octets, extension);
          } catch (e) {
            // L'ÉCRITURE LOCALE ÉCHOUE (stockage plein, accès refusé) : c'est
            // l'erreur « writeFrom failed » signalée. On la nomme, au lieu de
            // la laisser remonter sous la forme d'une exception inconnue.
            throw Exception(
              'Impossible d\'écrire le fichier de lecture (stockage plein ou '
              'accès refusé). Libérez de l\'espace puis réessayez. ($e)',
            );
          }
        }

        try {
          await _audioPlayer.play(DeviceFileSource(fichier.path));
        } on PlatformException {
          // LE FICHIER EST LÀ, MAIS LE LECTEUR LE REFUSE : le problème est son
          // CONTENU, pas le réseau. On nomme le fichier, qui reste vérifiable
          // même lorsqu'il venait du cache.
          throw Exception(
            'audio refusé par le lecteur '
            '(${fichier.path.split('/').last}) — format non pris en charge '
            'ou fichier incomplet',
          );
        }
        setState(() {
          _currentPlayingUrl = audioUrl;
        });
      }
    } catch (e) {
      // Le code HTTP est ce qui distingue « fichier absent » (404) de « accès
      // refusé » (403) ou d'un serveur en erreur (500). « Unknown error » ne
      // permettait aucune de ces distinctions.
      final detail = (e is DioException && e.response?.statusCode != null)
          ? 'le serveur a répondu ${e.response!.statusCode}'
          : '$e';
      SnackbarService.show('❌ Erreur de lecture : $detail', isError: true);
      if (mounted) {
        setState(() {
          _isPlaying = false;
          _currentPlayingUrl = null;
        });
      }
    } finally {
      _lectureEnPreparation = false;
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

  /// Polling automatique : recharge les sessions toutes les 5 s tant que
  /// l'écran est ouvert, pour refléter automatiquement les changements de
  /// statut (Transcription en cours → Transcrit → Résumé disponible) sans
  /// refresh manuel. Échecs silencieux.
  void _startAutoRefresh() {
    _autoRefreshTimer = Timer.periodic(const Duration(seconds: 5), (_) {
      if (mounted) _loadSessions(silent: true);
    });
  }

  @override
  void dispose() {
    _autoRefreshTimer?.cancel();
    _subEtat?.cancel();
    _subFin?.cancel();
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

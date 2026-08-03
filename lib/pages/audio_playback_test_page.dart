import 'package:flutter/material.dart';
import '../widgets/audio_file_player_widget.dart';
import '../services/api_service.dart';

/// Page de test pour la lecture des fichiers audio
class AudioPlaybackTestPage extends StatefulWidget {
  const AudioPlaybackTestPage({super.key});

  @override
  State<AudioPlaybackTestPage> createState() => _AudioPlaybackTestPageState();
}

class _AudioPlaybackTestPageState extends State<AudioPlaybackTestPage> {
  final ApiService _apiService = ApiService();
  List<Map<String, dynamic>> _audioSessions = [];
  bool _isLoading = false;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    _loadAudioSessions();
  }

  Future<void> _loadAudioSessions() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      // DEBUG: Afficher les URLs pour vérifier
      print('🔍 DEBUG: Base URL: https://resumecours.gestionhospitaliare.site/api');
      print('🔍 DEBUG: Appel: /courses/sessions/');
      print('🔍 DEBUG: URL finale attendue: https://resumecours.gestionhospitaliare.site/api/courses/sessions/');
      
      // Charger les sessions audio depuis l'API
      final response = await _apiService.get('/courses/sessions/');
      
      if (response.statusCode == 200) {
        final data = response.data;
        if (data is List) {
          setState(() {
            _audioSessions = data.cast<Map<String, dynamic>>();
            _isLoading = false;
          });
        } else if (data is Map && data.containsKey('results')) {
          setState(() {
            _audioSessions = (data['results'] as List).cast<Map<String, dynamic>>();
            _isLoading = false;
          });
        } else {
          setState(() {
            _errorMessage = 'Format de réponse inattendu';
            _isLoading = false;
          });
        }
      } else {
        setState(() {
          _errorMessage = 'Erreur ${response.statusCode}: ${response.statusMessage}';
          _isLoading = false;
        });
      }
    } catch (e) {
      setState(() {
        _errorMessage = 'Erreur de chargement: $e';
        _isLoading = false;
      });
    }
  }

  String _getAudioUrl(Map<String, dynamic> session) {
    // Construire l'URL complète du fichier audio
    final audioFile = session['audio_file'] as String?;
    if (audioFile == null || audioFile.isEmpty) {
      return '';
    }

    // Si l'URL est déjà complète, la retourner telle quelle
    if (audioFile.startsWith('http')) {
      return audioFile;
    }

    // Sinon, construire l'URL complète
    const baseUrl = 'https://resumecours.gestionhospitaliare.site';
    return '$baseUrl$audioFile';
  }

  Widget _buildSessionCard(Map<String, dynamic> session) {
    final audioUrl = _getAudioUrl(session);
    final title = session['title'] as String? ?? 'Sans titre';
    final courseName = session['course_name'] as String? ?? 'Cours inconnu';
    final createdAt = session['created_at'] as String? ?? '';
    final professor = session['professor'] as String? ?? 'Professeur inconnu';

    // Formater la date
    String formattedDate = '';
    if (createdAt.isNotEmpty) {
      try {
        final date = DateTime.parse(createdAt);
        formattedDate = '${date.day}/${date.month}/${date.year} à ${date.hour}:${date.minute.toString().padLeft(2, '0')}';
      } catch (e) {
        formattedDate = createdAt;
      }
    }

    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Informations de la session
            Row(
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        title,
                        style: Theme.of(context).textTheme.titleMedium?.copyWith(
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        courseName,
                        style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                          color: Colors.blue.shade700,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                      if (formattedDate.isNotEmpty) ...[
                        const SizedBox(height: 2),
                        Text(
                          formattedDate,
                          style: Theme.of(context).textTheme.bodySmall?.copyWith(
                            color: Colors.grey.shade600,
                          ),
                        ),
                      ],
                      if (professor.isNotEmpty) ...[
                        const SizedBox(height: 2),
                        Text(
                          'Prof: $professor',
                          style: Theme.of(context).textTheme.bodySmall?.copyWith(
                            color: Colors.grey.shade600,
                          ),
                        ),
                      ],
                    ],
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: Colors.green.shade100,
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Text(
                    'ID: ${session['id']}',
                    style: TextStyle(
                      fontSize: 12,
                      color: Colors.green.shade700,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ],
            ),

            const SizedBox(height: 16),

            // Lecteur audio
            if (audioUrl.isNotEmpty)
              AudioFilePlayerWidget(
                audioUrl: audioUrl,
                title: 'Enregistrement: $title',
                subtitle: 'Cours: $courseName • $formattedDate',
              )
            else
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: Colors.orange.shade50,
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: Colors.orange.shade200),
                ),
                child: Row(
                  children: [
                    Icon(Icons.warning_amber, color: Colors.orange.shade600),
                    const SizedBox(width: 8),
                    const Expanded(
                      child: Text(
                        'Aucun fichier audio disponible pour cette session',
                        style: TextStyle(color: Colors.orange),
                      ),
                    ),
                  ],
                ),
              ),

            const SizedBox(height: 8),

            // Informations de debug
            ExpansionTile(
              title: const Text(
                'Informations de debug',
                style: TextStyle(fontSize: 12),
              ),
              children: [
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: Colors.grey.shade100,
                    borderRadius: BorderRadius.circular(4),
                  ),
                  child: Text(
                    'URL Audio: $audioUrl\n'
                    'Données brutes: ${session.toString()}',
                    style: const TextStyle(
                      fontSize: 10,
                      fontFamily: 'monospace',
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

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Test Lecture Audio'),
        backgroundColor: Colors.blue,
        foregroundColor: Colors.white,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadAudioSessions,
          ),
        ],
      ),
      body: Column(
        children: [
          // En-tête avec informations
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: Colors.blue.shade50,
              border: Border(
                bottom: BorderSide(color: Colors.blue.shade200),
              ),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Test de Lecture des Fichiers Audio',
                  style: Theme.of(context).textTheme.titleLarge?.copyWith(
                    fontWeight: FontWeight.bold,
                    color: Colors.blue.shade800,
                  ),
                ),
                const SizedBox(height: 8),
                Text(
                  'Cette page teste la lecture des fichiers audio uploadés sur le serveur.',
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: Colors.blue.shade700,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  'Sessions trouvées: ${_audioSessions.length}',
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: Colors.blue.shade600,
                    fontWeight: FontWeight.w500,
                  ),
                ),
              ],
            ),
          ),

          // Contenu principal
          Expanded(
            child: _isLoading
                ? const Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        CircularProgressIndicator(),
                        SizedBox(height: 16),
                        Text('Chargement des sessions audio...'),
                      ],
                    ),
                  )
                : _errorMessage != null
                    ? Center(
                        child: Padding(
                          padding: const EdgeInsets.all(16),
                          child: Column(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              Icon(
                                Icons.error_outline,
                                size: 64,
                                color: Colors.red.shade400,
                              ),
                              const SizedBox(height: 16),
                              Text(
                                'Erreur de chargement',
                                style: Theme.of(context).textTheme.titleLarge?.copyWith(
                                  color: Colors.red.shade700,
                                ),
                              ),
                              const SizedBox(height: 8),
                              Text(
                                _errorMessage!,
                                textAlign: TextAlign.center,
                                style: Theme.of(context).textTheme.bodyMedium,
                              ),
                              const SizedBox(height: 16),
                              ElevatedButton.icon(
                                onPressed: _loadAudioSessions,
                                icon: const Icon(Icons.refresh),
                                label: const Text('Réessayer'),
                              ),
                            ],
                          ),
                        ),
                      )
                    : _audioSessions.isEmpty
                        ? Center(
                            child: Padding(
                              padding: const EdgeInsets.all(16),
                              child: Column(
                                mainAxisAlignment: MainAxisAlignment.center,
                                children: [
                                  Icon(
                                    Icons.audiotrack_outlined,
                                    size: 64,
                                    color: Colors.grey.shade400,
                                  ),
                                  const SizedBox(height: 16),
                                  Text(
                                    'Aucune session audio',
                                    style: Theme.of(context).textTheme.titleLarge?.copyWith(
                                      color: Colors.grey.shade600,
                                    ),
                                  ),
                                  const SizedBox(height: 8),
                                  const Text(
                                    'Aucun enregistrement audio trouvé.\nEnregistrez d\'abord un audio pour le tester ici.',
                                    textAlign: TextAlign.center,
                                  ),
                                  const SizedBox(height: 16),
                                  ElevatedButton.icon(
                                    onPressed: _loadAudioSessions,
                                    icon: const Icon(Icons.refresh),
                                    label: const Text('Actualiser'),
                                  ),
                                ],
                              ),
                            ),
                          )
                        : ListView.builder(
                            itemCount: _audioSessions.length,
                            itemBuilder: (context, index) {
                              return _buildSessionCard(_audioSessions[index]);
                            },
                          ),
          ),
        ],
      ),
    );
  }
}
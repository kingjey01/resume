import 'package:flutter/material.dart';
import 'services/api_service_debug.dart';
import 'widgets/audio_file_player_widget.dart';

/// Page de test simple pour contourner le problème de cache
class TestSimplePage extends StatefulWidget {
  const TestSimplePage({super.key});

  @override
  State<TestSimplePage> createState() => _TestSimplePageState();
}

class _TestSimplePageState extends State<TestSimplePage> {
  final ApiServiceDebug _debugService = ApiServiceDebug();
  List<Map<String, dynamic>> _audioSessions = [];
  bool _isLoading = false;
  String? _errorMessage;
  bool _isConnected = false;

  @override
  void initState() {
    super.initState();
    _testAndLoad();
  }

  Future<void> _testAndLoad() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      // Test 1: Connectivité
      print('🔍 Test de connectivité API...');
      final isConnected = await _debugService.testApiConnectivity();
      
      setState(() {
        _isConnected = isConnected;
      });
      
      if (!isConnected) {
        setState(() {
          _errorMessage = 'Impossible de se connecter à l\'API';
          _isLoading = false;
        });
        return;
      }
      
      // Test 2: Récupération des sessions
      print('🔍 Récupération des sessions audio...');
      final sessions = await _debugService.getAudioSessionsDebug();
      
      setState(() {
        _audioSessions = sessions;
        _isLoading = false;
      });
      
      print('✅ ${sessions.length} sessions audio chargées avec succès');
      
    } catch (e) {
      print('❌ Erreur: $e');
      setState(() {
        _errorMessage = 'Erreur: $e';
        _isLoading = false;
      });
    }
  }

  String _getAudioUrl(Map<String, dynamic> session) {
    final audioFile = session['audio_file'] as String?;
    if (audioFile == null || audioFile.isEmpty) {
      return '';
    }

    if (audioFile.startsWith('http')) {
      return audioFile;
    }

    return 'https://resumecours.gestionhospitaliare.site$audioFile';
  }

  Widget _buildSessionCard(Map<String, dynamic> session) {
    final audioUrl = _getAudioUrl(session);
    final title = session['title'] as String? ?? 'Sans titre';
    final courseName = session['course_name'] as String? ?? 'Cours inconnu';
    final professor = session['professeur'] as String? ?? 'Professeur inconnu';
    final sessionId = session['id']?.toString() ?? 'N/A';

    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // En-tête de la session
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: Colors.blue.shade100,
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Text(
                    'ID: $sessionId',
                    style: TextStyle(
                      fontSize: 12,
                      color: Colors.blue.shade700,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
                const Spacer(),
                Icon(
                  Icons.audiotrack,
                  color: Colors.green.shade600,
                  size: 24,
                ),
              ],
            ),
            
            const SizedBox(height: 12),
            
            // Informations de la session
            Text(
              title,
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 4),
            Text(
              'Cours: $courseName',
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                color: Colors.blue.shade700,
              ),
            ),
            const SizedBox(height: 2),
            Text(
              'Professeur: $professor',
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: Colors.grey.shade600,
              ),
            ),
            
            const SizedBox(height: 16),
            
            // Lecteur audio
            if (audioUrl.isNotEmpty)
              AudioFilePlayerWidget(
                audioUrl: audioUrl,
                title: 'Session: $title',
                subtitle: '$courseName • $professor',
              )
            else
              Container(
                padding: const EdgeInsets.all(12),
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
                        'Aucun fichier audio disponible',
                        style: TextStyle(color: Colors.orange),
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

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('🧪 Test Simple Audio'),
        backgroundColor: Colors.green,
        foregroundColor: Colors.white,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _testAndLoad,
          ),
        ],
      ),
      body: Column(
        children: [
          // Indicateur de statut
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: _isConnected ? Colors.green.shade50 : Colors.red.shade50,
              border: Border(
                bottom: BorderSide(
                  color: _isConnected ? Colors.green.shade200 : Colors.red.shade200,
                ),
              ),
            ),
            child: Row(
              children: [
                Icon(
                  _isConnected ? Icons.wifi : Icons.wifi_off,
                  color: _isConnected ? Colors.green.shade700 : Colors.red.shade700,
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        _isConnected ? 'Connecté à l\'API' : 'Déconnecté de l\'API',
                        style: TextStyle(
                          fontWeight: FontWeight.bold,
                          color: _isConnected ? Colors.green.shade700 : Colors.red.shade700,
                        ),
                      ),
                      Text(
                        'Sessions audio: ${_audioSessions.length}',
                        style: TextStyle(
                          fontSize: 12,
                          color: _isConnected ? Colors.green.shade600 : Colors.red.shade600,
                        ),
                      ),
                    ],
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
                        Text('Test de l\'API en cours...'),
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
                                'Erreur de connexion',
                                style: Theme.of(context).textTheme.titleLarge?.copyWith(
                                  color: Colors.red.shade700,
                                ),
                              ),
                              const SizedBox(height: 8),
                              Text(
                                _errorMessage!,
                                textAlign: TextAlign.center,
                              ),
                              const SizedBox(height: 16),
                              ElevatedButton.icon(
                                onPressed: _testAndLoad,
                                icon: const Icon(Icons.refresh),
                                label: const Text('Réessayer'),
                              ),
                            ],
                          ),
                        ),
                      )
                    : _audioSessions.isEmpty
                        ? const Center(
                            child: Padding(
                              padding: EdgeInsets.all(16),
                              child: Column(
                                mainAxisAlignment: MainAxisAlignment.center,
                                children: [
                                  Icon(
                                    Icons.audiotrack_outlined,
                                    size: 64,
                                    color: Colors.grey,
                                  ),
                                  SizedBox(height: 16),
                                  Text(
                                    'Aucune session audio trouvée',
                                    style: TextStyle(
                                      fontSize: 18,
                                      color: Colors.grey,
                                    ),
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
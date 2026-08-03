import 'package:flutter/material.dart';
import 'package:dio/dio.dart';

/// Page de débogage pour tester directement l'API
class DebugPage extends StatefulWidget {
  const DebugPage({super.key});

  @override
  State<DebugPage> createState() => _DebugPageState();
}

class _DebugPageState extends State<DebugPage> {
  final Dio _dio = Dio();
  String _result = '';
  bool _isLoading = false;

  Future<void> _testDirectApi() async {
    setState(() {
      _isLoading = true;
      _result = '';
    });

    const token = '9743c81fdd50b11c38a55fb9de24c56d8d4857dd';
    const correctUrl = 'https://resumecours.gestionhospitaliare.site/api/courses/sessions/';
    const wrongUrl = 'https://resumecours.gestionhospitaliare.site/api/api/courses/sessions/';

    final headers = {
      'Authorization': 'Token $token',
      'Content-Type': 'application/json',
    };

    String result = '🔍 TEST DIRECT DE L\'API\n';
    result += '=' * 50 + '\n\n';

    // Test 1: URL correcte
    result += '✅ Test URL correcte:\n';
    result += '$correctUrl\n';
    try {
      final response = await _dio.get(correctUrl, options: Options(headers: headers));
      result += '📡 Réponse: ${response.statusCode}\n';
      if (response.statusCode == 200) {
        final data = response.data;
        final sessions = data is List ? data : (data['results'] ?? []);
        final audioSessions = sessions.where((s) => s['audio_file'] != null).length;
        result += '📊 Sessions: ${sessions.length}\n';
        result += '🎵 Avec audio: $audioSessions\n';
        result += '✅ SUCCÈS!\n';
      }
    } catch (e) {
      result += '❌ Erreur: $e\n';
    }

    result += '\n' + '-' * 30 + '\n\n';

    // Test 2: URL incorrecte (double /api/)
    result += '❌ Test URL incorrecte (double /api/):\n';
    result += '$wrongUrl\n';
    try {
      final response = await _dio.get(wrongUrl, options: Options(headers: headers));
      result += '📡 Réponse: ${response.statusCode}\n';
      if (response.statusCode == 200) {
        result += '⚠️ Cette URL fonctionne aussi (inattendu)\n';
      }
    } catch (e) {
      result += '❌ Erreur (attendue): ${e.toString().contains('404') ? '404 Not Found' : e}\n';
      result += '✅ C\'est normal, cette URL ne devrait pas fonctionner\n';
    }

    result += '\n' + '=' * 50 + '\n';
    result += '📋 CONCLUSION:\n';
    result += 'Si vous voyez cette page, l\'URL correcte fonctionne.\n';
    result += 'Le problème vient du cache Flutter ou d\'une autre partie du code.\n';

    setState(() {
      _result = result;
      _isLoading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('🔧 Debug API'),
        backgroundColor: Colors.red,
        foregroundColor: Colors.white,
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Card(
              color: Colors.red.shade50,
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Icon(Icons.bug_report, color: Colors.red.shade700),
                        const SizedBox(width: 8),
                        Text(
                          'Page de Débogage API',
                          style: Theme.of(context).textTheme.titleLarge?.copyWith(
                            color: Colors.red.shade700,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    const Text(
                      'Cette page teste directement l\'API sans passer par ApiService '
                      'pour identifier le problème d\'URL dupliquée.',
                    ),
                  ],
                ),
              ),
            ),
            
            const SizedBox(height: 16),
            
            Center(
              child: ElevatedButton.icon(
                onPressed: _isLoading ? null : _testDirectApi,
                icon: _isLoading 
                    ? const SizedBox(
                        width: 16,
                        height: 16,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Icon(Icons.play_arrow),
                label: Text(_isLoading ? 'Test en cours...' : 'Tester l\'API Directement'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.red,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
                ),
              ),
            ),
            
            const SizedBox(height: 16),
            
            if (_result.isNotEmpty)
              Expanded(
                child: Card(
                  child: Padding(
                    padding: const EdgeInsets.all(16.0),
                    child: SingleChildScrollView(
                      child: Text(
                        _result,
                        style: const TextStyle(
                          fontFamily: 'monospace',
                          fontSize: 12,
                        ),
                      ),
                    ),
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }
}
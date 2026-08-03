import 'package:flutter/material.dart';
import 'package:resume_plus_clean/services/simple_login_service.dart';

class SimpleDataPage extends StatefulWidget {
  const SimpleDataPage({super.key});

  @override
  State<SimpleDataPage> createState() => _SimpleDataPageState();
}

class _SimpleDataPageState extends State<SimpleDataPage> {
  final _loginService = SimpleLoginService();
  List<dynamic> _summaries = [];
  bool _isLoading = true;
  String _error = '';

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    try {
      setState(() {
        _isLoading = true;
        _error = '';
      });

      print('🔍 DEBUG: Début getSummaries');
      final result = await _loginService.getSummaries();
      
      if (result['success'] == true) {
        setState(() {
          _summaries = result['data'] ?? [];
          _isLoading = false;
        });
        print('✅ Données chargées: ${_summaries.length} summaries');
      } else {
        setState(() {
          _error = result['message'] ?? 'Erreur inconnue';
          _isLoading = false;
        });
        print('❌ Erreur: $_error');
      }
    } catch (e) {
      setState(() {
        _error = 'Erreur: $e';
        _isLoading = false;
      });
      print('❌ Exception: $e');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      appBar: AppBar(
        title: const Text('Données Récupérées'),
        backgroundColor: Colors.green,
        foregroundColor: Colors.white,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadData,
          ),
        ],
      ),
      body: _isLoading
          ? const Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  CircularProgressIndicator(),
                  SizedBox(height: 16),
                  Text('Chargement des données...'),
                ],
              ),
            )
          : _error.isNotEmpty
              ? Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Icon(Icons.error, size: 64, color: Colors.red),
                      const SizedBox(height: 16),
                      Text(
                        'Erreur',
                        style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                      ),
                      const SizedBox(height: 8),
                      Text(_error, textAlign: TextAlign.center),
                      const SizedBox(height: 16),
                      ElevatedButton(
                        onPressed: _loadData,
                        child: const Text('Réessayer'),
                      ),
                    ],
                  ),
                )
              : Column(
                  children: [
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(16),
                      color: Colors.green.shade100,
                      child: Text(
                        '🎉 Succès ! ${_summaries.length} résumés trouvés',
                        style: TextStyle(
                          color: Colors.green.shade800,
                          fontSize: 16,
                          fontWeight: FontWeight.bold,
                        ),
                        textAlign: TextAlign.center,
                      ),
                    ),
                    Expanded(
                      child: _summaries.isEmpty
                          ? const Center(
                              child: Text('Aucun résumé trouvé'),
                            )
                          : ListView.builder(
                              padding: const EdgeInsets.all(16),
                              itemCount: _summaries.length,
                              itemBuilder: (context, index) {
                                final summary = _summaries[index];
                                return Card(
                                  margin: const EdgeInsets.only(bottom: 12),
                                  child: ListTile(
                                    leading: CircleAvatar(
                                      backgroundColor: Colors.blue,
                                      child: Text('${index + 1}'),
                                    ),
                                    title: Text(
                                      summary['title'] ?? 'Titre non disponible',
                                      style: const TextStyle(fontWeight: FontWeight.bold),
                                    ),
                                    subtitle: Column(
                                      crossAxisAlignment: CrossAxisAlignment.start,
                                      children: [
                                        if (summary['description'] != null)
                                          Text(summary['description']),
                                        const SizedBox(height: 4),
                                        Text(
                                          'ID: ${summary['id']} | Créé: ${summary['created_at'] ?? 'N/A'}',
                                          style: TextStyle(
                                            fontSize: 12,
                                            color: Colors.grey.shade600,
                                          ),
                                        ),
                                      ],
                                    ),
                                    trailing: Icon(
                                      Icons.description,
                                      color: Colors.blue.shade300,
                                    ),
                                  ),
                                );
                              },
                            ),
                    ),
                  ],
                ),
      floatingActionButton: FloatingActionButton(
        onPressed: () {
          Navigator.pushReplacementNamed(context, '/simple-login');
        },
        backgroundColor: Colors.blue,
        child: const Icon(Icons.logout, color: Colors.white),
      ),
    );
  }
}
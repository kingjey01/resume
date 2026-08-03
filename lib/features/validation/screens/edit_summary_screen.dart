import 'package:flutter/material.dart';
import 'package:resume_plus_clean/services/api_service.dart';
import 'package:resume_plus_clean/theme/app_theme.dart';

class EditSummaryScreen extends StatefulWidget {
  final Map<String, dynamic> summary;

  const EditSummaryScreen({super.key, required this.summary});

  @override
  State<EditSummaryScreen> createState() => _EditSummaryScreenState();
}

class _EditSummaryScreenState extends State<EditSummaryScreen> {
  final ApiService _apiService = ApiService();
  late TextEditingController _titreController;
  late TextEditingController _texteController;
  late TextEditingController _prixController;
  bool _isSaving = false;

  double _minimumPrice = 3000; // Valeur par défaut en attendant l'API

  @override
  void initState() {
    super.initState();
    _titreController = TextEditingController(text: widget.summary['titre'] ?? '');
    _texteController = TextEditingController(text: widget.summary['texte_resume'] ?? '');
    final currentPrice = widget.summary['prix'] ?? 0;
    _prixController = TextEditingController(text: currentPrice.toString());
    _loadPricingConfig();
  }

  Future<void> _loadPricingConfig() async {
    final minPrice = await _apiService.getMinimumResumePrice();
    if (mounted) {
      setState(() => _minimumPrice = minPrice);
    }
  }

  @override
  void dispose() {
    _titreController.dispose();
    _texteController.dispose();
    _prixController.dispose();
    super.dispose();
  }

  Future<void> _saveSummary() async {
    if (_titreController.text.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Le titre est obligatoire'), backgroundColor: AppTheme.error),
      );
      return;
    }

    final price = double.tryParse(_prixController.text) ?? 0.0;
    if (price < _minimumPrice) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Le prix minimum est ${_minimumPrice.toStringAsFixed(0)} CDF'),
          backgroundColor: AppTheme.error,
        ),
      );
      return;
    }

    setState(() => _isSaving = true);

    try {
      final data = {
        'titre': _titreController.text.trim(),
        'texte_resume': _texteController.text.trim(),
        'prix': price,
        'is_free': false,
      };

      await _apiService.editSummary(widget.summary['id'], data);

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Résumé modifié avec succès'), backgroundColor: AppTheme.success),
        );
        Navigator.of(context).pop(true);
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(ApiService.getErrorMessage(e)),
            backgroundColor: AppTheme.error,
          ),
        );
      }
    } finally {
      if (mounted) setState(() => _isSaving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final topPadding = MediaQuery.of(context).padding.top;
    final authorType = widget.summary['author_type'] ?? 'cp';
    final isAi = authorType == 'ai';
    final theme = Theme.of(context);

    return Scaffold(
      backgroundColor: theme.scaffoldBackgroundColor,
      body: Column(
        children: [
          // Header
          Container(
            padding: EdgeInsets.only(top: topPadding + 8, left: 20, right: 20, bottom: 20),
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
            child: Row(
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
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Modifier le résumé',
                        style: theme.textTheme.titleMedium?.copyWith(
                          color: Colors.white, fontWeight: FontWeight.w700,
                        ),
                      ),
                      Row(
                        children: [
                          Icon(
                            isAi ? Icons.smart_toy_rounded : Icons.person_rounded,
                            size: 12, color: Colors.white.withOpacity(0.7),
                          ),
                          const SizedBox(width: 4),
                          Text(
                            isAi ? 'Généré par IA' : 'Rédigé par CP',
                            style: TextStyle(color: Colors.white.withOpacity(0.7), fontSize: 12),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
          // Form
          Expanded(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Titre
                  const Text('Titre', style: TextStyle(fontWeight: FontWeight.w600, fontSize: 14)),
                  const SizedBox(height: 8),
                  TextField(
                    controller: _titreController,
                    decoration: InputDecoration(
                      hintText: 'Titre du résumé',
                      prefixIcon: const Icon(Icons.title_rounded, size: 20),
                      border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                    ),
                  ),
                  const SizedBox(height: 20),
                  // Contenu
                  const Text('Contenu du résumé', style: TextStyle(fontWeight: FontWeight.w600, fontSize: 14)),
                  const SizedBox(height: 8),
                  TextField(
                    controller: _texteController,
                    maxLines: 12,
                    decoration: InputDecoration(
                      hintText: 'Contenu du résumé...',
                      alignLabelWithHint: true,
                      border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                    ),
                  ),
                  const SizedBox(height: 20),
                  // Prix
                  Text('Prix (CDF) *', style: TextStyle(fontWeight: FontWeight.w600, fontSize: 14)),
                  const SizedBox(height: 8),
                  TextField(
                    controller: _prixController,
                    keyboardType: TextInputType.number,
                    decoration: InputDecoration(
                      hintText: 'Prix du résumé',
                      prefixIcon: const Icon(Icons.payments_rounded, size: 20),
                      helperText: 'Prix minimum : ${_minimumPrice.toStringAsFixed(0)} CDF',
                      helperMaxLines: 2,
                      border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                    ),
                  ),
                  const SizedBox(height: 16),
                  // Info
                  Container(
                    padding: const EdgeInsets.all(14),
                    decoration: BoxDecoration(
                      color: AppTheme.primaryBlue.withOpacity(0.05),
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: AppTheme.primaryBlue.withOpacity(0.1)),
                    ),
                    child: Row(
                      children: [
                        Icon(Icons.info_outline_rounded, size: 18, color: AppTheme.primaryBlue.withOpacity(0.7)),
                        const SizedBox(width: 10),
                        const Expanded(
                          child: Text(
                            'Les modifications par un CP sont automatiquement validées.',
                            style: TextStyle(fontSize: 12, color: AppTheme.textSecondary),
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
          // Save button
          Container(
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              color: theme.colorScheme.surface,
              boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.06), blurRadius: 10, offset: const Offset(0, -4))],
            ),
            child: SafeArea(
              child: SizedBox(
                width: double.infinity,
                child: ElevatedButton.icon(
                  onPressed: _isSaving ? null : _saveSummary,
                  icon: _isSaving
                      ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                      : const Icon(Icons.save_rounded, size: 20),
                  label: Text(_isSaving ? 'Sauvegarde...' : 'Enregistrer les modifications'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppTheme.primaryBlue,
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(vertical: 16),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:resume_plus_clean/services/api_service.dart';
import 'package:resume_plus_clean/theme/app_theme.dart';

class AssociateProfCoursScreen extends StatefulWidget {
  const AssociateProfCoursScreen({super.key});

  @override
  State<AssociateProfCoursScreen> createState() =>
      _AssociateProfCoursScreenState();
}

class _AssociateProfCoursScreenState extends State<AssociateProfCoursScreen> {
  final ApiService _apiService = ApiService();

  bool _isLoadingData = true;
  bool _isAssociating = false;
  bool _isLoadingDispenses = false;

  List<Map<String, dynamic>> _professeurs = [];
  List<Map<String, dynamic>> _cours = [];
  List<Map<String, dynamic>> _dispenses = [];

  Map<String, dynamic>? _selectedProf;
  Map<String, dynamic>? _selectedCours;

  @override
  void initState() {
    super.initState();
    _loadAll();
  }

  Future<void> _loadAll() async {
    setState(() => _isLoadingData = true);
    try {
      final results = await Future.wait([
        _apiService.getProfesseurs(),
        _apiService.getCourses(),
        _apiService.listDispenses(),
      ]);
      setState(() {
        _professeurs = results[0].cast<Map<String, dynamic>>();
        _cours = results[1].cast<Map<String, dynamic>>();
        _dispenses = results[2].cast<Map<String, dynamic>>();
        _isLoadingData = false;
      });
    } catch (_) {
      setState(() => _isLoadingData = false);
    }
  }

  Future<void> _loadDispenses() async {
    setState(() => _isLoadingDispenses = true);
    try {
      final data = await _apiService.listDispenses();
      setState(() {
        _dispenses = data.cast<Map<String, dynamic>>();
        _isLoadingDispenses = false;
      });
    } catch (_) {
      setState(() => _isLoadingDispenses = false);
    }
  }

  Future<void> _associate() async {
    if (_selectedProf == null || _selectedCours == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Veuillez sélectionner un professeur et un cours.'),
          backgroundColor: AppTheme.warning,
        ),
      );
      return;
    }
    setState(() => _isAssociating = true);
    try {
      await _apiService.createDispense(
        professeurId: _selectedProf!['id'] as int,
        coursId: _selectedCours!['id'] as int,
      );
      setState(() {
        _selectedProf = null;
        _selectedCours = null;
      });
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Association créée avec succès'),
            backgroundColor: AppTheme.success,
          ),
        );
        await _loadDispenses();
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
              content: Text('Erreur : $e'), backgroundColor: AppTheme.error),
        );
      }
    } finally {
      if (mounted) setState(() => _isAssociating = false);
    }
  }

  Future<void> _deleteDispense(int id) async {
    try {
      await _apiService.deleteDispense(id);
      await _loadDispenses();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
              content: Text('Erreur : $e'), backgroundColor: AppTheme.error),
        );
      }
    }
  }

  String _profLabel(Map<String, dynamic> p) {
    final full = p['user_full_name'] as String? ?? '';
    final username = p['user_username'] as String? ?? '';
    final spec = p['specialite'] as String? ?? '';
    final name = full.isNotEmpty ? full : username;
    return spec.isNotEmpty ? '$name ($spec)' : name;
  }

  String _coursLabel(Map<String, dynamic> c) {
    return c['nom'] as String? ?? '';
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final cs = theme.colorScheme;
    final topPadding = MediaQuery.of(context).padding.top;
    return AnnotatedRegion<SystemUiOverlayStyle>(
      value: SystemUiOverlayStyle.light,
      child: Scaffold(
        backgroundColor: cs.surface,
        body: Column(
          children: [
            // ── Header ──────────────────────────────────────────────────────
            Container(
              padding: EdgeInsets.only(
                  top: topPadding + 10, left: 20, right: 20, bottom: 24),
              decoration: const BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                  colors: [
                    AppTheme.primaryBlueDark,
                    AppTheme.primaryBlue,
                    AppTheme.primaryBlueLight,
                  ],
                ),
                borderRadius: BorderRadius.only(
                  bottomLeft: Radius.circular(28),
                  bottomRight: Radius.circular(28),
                ),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      GestureDetector(
                        onTap: () => Navigator.of(context).pop(),
                        child: Container(
                          width: 38,
                          height: 38,
                          decoration: BoxDecoration(
                            color: Colors.white.withOpacity(0.2),
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: const Icon(Icons.arrow_back_rounded,
                              color: Colors.white, size: 20),
                        ),
                      ),
                      const Spacer(),
                      const Icon(Icons.link_rounded,
                          color: Colors.white, size: 24),
                    ],
                  ),
                  const SizedBox(height: 16),
                  const Text(
                    'Association Professeur & Cours',
                    style: TextStyle(
                        color: Colors.white,
                        fontSize: 22,
                        fontWeight: FontWeight.w800),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    'Associez un professeur à un cours pour permettre le remplissage automatique lors de la création des séances.',
                    style: TextStyle(
                        color: Colors.white.withOpacity(0.8), fontSize: 13),
                  ),
                ],
              ),
            ),

            // ── Corps ───────────────────────────────────────────────────────
            Expanded(
              child: _isLoadingData
                  ? const Center(child: CircularProgressIndicator())
                  : SingleChildScrollView(
                      padding: const EdgeInsets.fromLTRB(20, 24, 20, 32),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          // Icône illustrative
                          Center(
                            child: Container(
                              width: 72,
                              height: 72,
                              decoration: BoxDecoration(
                                color: AppTheme.primaryBlue.withOpacity(0.08),
                                shape: BoxShape.circle,
                              ),
                              child: const Icon(Icons.connect_without_contact_rounded,
                                  size: 36, color: AppTheme.primaryBlue),
                            ),
                          ),
                          const SizedBox(height: 24),

                          // ── Dropdown Professeur ──────────────────────────
                          Text(
                            'Professeur',
                            style: TextStyle(
                                fontSize: 13,
                                fontWeight: FontWeight.w600,
                                color: cs.onSurfaceVariant),
                          ),
                          const SizedBox(height: 6),
                          _buildDropdown(
                            value: _selectedProf,
                            items: _professeurs,
                            label: _profLabel,
                            hint: 'Sélectionner un professeur',
                            icon: Icons.person_outline_rounded,
                            onChanged: (v) => setState(() => _selectedProf = v),
                          ),
                          const SizedBox(height: 16),

                          // ── Dropdown Cours ───────────────────────────────
                          Text(
                            'Cours',
                            style: TextStyle(
                                fontSize: 13,
                                fontWeight: FontWeight.w600,
                                color: cs.onSurfaceVariant),
                          ),
                          const SizedBox(height: 6),
                          _buildDropdown(
                            value: _selectedCours,
                            items: _cours,
                            label: _coursLabel,
                            hint: 'Sélectionner un cours',
                            icon: Icons.menu_book_outlined,
                            onChanged: (v) => setState(() => _selectedCours = v),
                          ),
                          const SizedBox(height: 24),

                          // ── Bouton Associer ──────────────────────────────
                          SizedBox(
                            width: double.infinity,
                            height: 52,
                            child: ElevatedButton.icon(
                              onPressed: _isAssociating ? null : _associate,
                              icon: _isAssociating
                                  ? const SizedBox(
                                      width: 18,
                                      height: 18,
                                      child: CircularProgressIndicator(
                                          strokeWidth: 2, color: Colors.white))
                                  : const Icon(Icons.link_rounded, size: 20),
                              label: Text(
                                _isAssociating ? 'Association...' : 'Associer',
                                style: const TextStyle(
                                    fontSize: 15, fontWeight: FontWeight.w700),
                              ),
                              style: ElevatedButton.styleFrom(
                                backgroundColor: AppTheme.primaryBlue,
                                foregroundColor: Colors.white,
                                shape: RoundedRectangleBorder(
                                    borderRadius: BorderRadius.circular(14)),
                                elevation: 0,
                              ),
                            ),
                          ),

                          const SizedBox(height: 32),

                          // ── Liste des associations ───────────────────────
                          Row(
                            children: [
                              Text(
                                'Associations existantes',
                                style: TextStyle(
                                    fontSize: 16,
                                    fontWeight: FontWeight.w700,
                                    color: cs.onSurface),
                              ),
                              const SizedBox(width: 8),
                              if (!_isLoadingDispenses)
                                Container(
                                  padding: const EdgeInsets.symmetric(
                                      horizontal: 8, vertical: 2),
                                  decoration: BoxDecoration(
                                    color:
                                        AppTheme.primaryBlue.withOpacity(0.12),
                                    borderRadius: BorderRadius.circular(20),
                                  ),
                                  child: Text(
                                    '${_dispenses.length}',
                                    style: const TextStyle(
                                        fontSize: 12,
                                        fontWeight: FontWeight.w700,
                                        color: AppTheme.primaryBlue),
                                  ),
                                ),
                              if (_isLoadingDispenses)
                                const SizedBox(
                                    width: 16,
                                    height: 16,
                                    child: CircularProgressIndicator(
                                        strokeWidth: 2)),
                            ],
                          ),
                          const SizedBox(height: 12),

                          if (!_isLoadingDispenses && _dispenses.isEmpty)
                            Container(
                              padding: const EdgeInsets.all(20),
                              decoration: BoxDecoration(
                                color: cs.surface,
                                borderRadius: BorderRadius.circular(14),
                              ),
                              child: Center(
                                child: Text(
                                  'Aucune association enregistrée.',
                                  style:
                                      TextStyle(color: cs.onSurfaceVariant),
                                ),
                              ),
                            ),

                          ...(_dispenses.map((d) => _buildDispenseCard(d))),
                        ],
                      ),
                    ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildDropdown({
    required Map<String, dynamic>? value,
    required List<Map<String, dynamic>> items,
    required String Function(Map<String, dynamic>) label,
    required String hint,
    required IconData icon,
    required void Function(Map<String, dynamic>?) onChanged,
  }) {
    final theme = Theme.of(context);
    final cs = theme.colorScheme;

    return Container(
      decoration: BoxDecoration(
        color: cs.surface,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: theme.dividerTheme.color ?? Colors.grey.shade300),
      ),
      child: DropdownButtonHideUnderline(
        child: ButtonTheme(
          alignedDropdown: true,
          child: DropdownButton<Map<String, dynamic>>(
            value: value,
            dropdownColor: cs.surface, // ← fond du menu déroulant adapté au thème
            hint: Row(
              children: [
                Icon(icon, size: 20, color: cs.onSurfaceVariant),
                const SizedBox(width: 8),
                Text(hint,
                    style: TextStyle(
                        color: cs.onSurfaceVariant, fontSize: 14.5)),
              ],
            ),
            isExpanded: true,
            borderRadius: BorderRadius.circular(14),
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
            items: items
                .map((item) => DropdownMenuItem<Map<String, dynamic>>(
                      value: item,
                      child: Text(
                        label(item),
                        overflow: TextOverflow.ellipsis,
                        style: TextStyle(
                            fontSize: 14, color: cs.onSurface), // ← s'adapte au mode
                      ),
                    ))
                .toList(),
            onChanged: onChanged,
          ),
        ),
      ),
    );
  }

  Widget _buildDispenseCard(Map<String, dynamic> d) {
    final cs = Theme.of(context).colorScheme;
    final id = d['id'] as int;
    final profName = d['professeur_name'] as String? ?? '';
    final coursNom = d['cours_nom'] as String? ?? '';

    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      decoration: BoxDecoration(
        color: cs.surface,
        borderRadius: BorderRadius.circular(14),
        boxShadow: AppTheme.softShadow,
      ),
      child: Row(
        children: [
          Container(
            width: 40,
            height: 40,
            decoration: BoxDecoration(
              color: AppTheme.primaryBlue.withOpacity(0.1),
              borderRadius: BorderRadius.circular(10),
            ),
            child: const Icon(Icons.link_rounded,
                size: 20, color: AppTheme.primaryBlue),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: RichText(
              text: TextSpan(
                style: TextStyle(
                    fontSize: 14, color: cs.onSurface),
                children: [
                  TextSpan(
                    text: profName,
                    style: const TextStyle(fontWeight: FontWeight.w600),
                  ),
                  const TextSpan(
                    text: ' → ',
                    style: TextStyle(
                        color: AppTheme.primaryBlue,
                        fontWeight: FontWeight.w700),
                  ),
                  TextSpan(
                    text: coursNom,
                    style: const TextStyle(fontWeight: FontWeight.w500),
                  ),
                ],
              ),
            ),
          ),
          IconButton(
            onPressed: () => _confirmDelete(id, profName, coursNom),
            icon: const Icon(Icons.delete_outline_rounded,
                color: AppTheme.error, size: 20),
            tooltip: 'Supprimer',
          ),
        ],
      ),
    );
  }

  void _confirmDelete(int id, String prof, String cours) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        shape:
            RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: const Text('Supprimer cette association ?'),
        content: Text('$prof → $cours'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Annuler'),
          ),
          ElevatedButton(
            onPressed: () {
              Navigator.pop(ctx);
              _deleteDispense(id);
            },
            style: ElevatedButton.styleFrom(
                backgroundColor: AppTheme.error, foregroundColor: Colors.white),
            child: const Text('Supprimer'),
          ),
        ],
      ),
    );
  }
}

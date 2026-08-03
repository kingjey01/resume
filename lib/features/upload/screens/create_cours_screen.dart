import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:resume_plus_clean/services/api_service.dart';
import 'package:resume_plus_clean/theme/app_theme.dart';

class CreateCoursScreen extends StatefulWidget {
  const CreateCoursScreen({super.key});

  @override
  State<CreateCoursScreen> createState() => _CreateCoursScreenState();
}

class _CreateCoursScreenState extends State<CreateCoursScreen> {
  final ApiService _apiService = ApiService();
  final _formKey = GlobalKey<FormState>();
  final _nomCtrl = TextEditingController();
  final _descCtrl = TextEditingController();

  bool _isCreating = false;
  bool _isLoadingList = false;
  List<Map<String, dynamic>> _cours = [];

  @override
  void initState() {
    super.initState();
    _loadCours();
  }

  @override
  void dispose() {
    _nomCtrl.dispose();
    _descCtrl.dispose();
    super.dispose();
  }

  Future<void> _loadCours() async {
    setState(() => _isLoadingList = true);
    try {
      final data = await _apiService.getCourses();
      setState(() {
        _cours = data.cast<Map<String, dynamic>>();
        _isLoadingList = false;
      });
    } catch (_) {
      setState(() => _isLoadingList = false);
    }
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _isCreating = true);
    try {
      await _apiService.createCourse(
        nom: _nomCtrl.text.trim(),
        description: _descCtrl.text.trim(),
      );
      _nomCtrl.clear();
      _descCtrl.clear();
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Cours enregistré avec succès'),
            backgroundColor: AppTheme.success,
          ),
        );
        await _loadCours();
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
              content: Text('Erreur : $e'), backgroundColor: AppTheme.error),
        );
      }
    } finally {
      if (mounted) setState(() => _isCreating = false);
    }
  }

  Future<void> _delete(int id) async {
    try {
      await _apiService.deleteCourse(id);
      await _loadCours();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
              content: Text('Erreur : $e'), backgroundColor: AppTheme.error),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final topPadding = MediaQuery.of(context).padding.top;
    return AnnotatedRegion<SystemUiOverlayStyle>(
      value: SystemUiOverlayStyle.light,
      child: Scaffold(
        backgroundColor: const Color(0xFFF5F7FA),
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
                      const Icon(Icons.menu_book_outlined,
                          color: Colors.white, size: 24),
                    ],
                  ),
                  const SizedBox(height: 16),
                  const Text(
                    'Création cours',
                    style: TextStyle(
                        color: Colors.white,
                        fontSize: 24,
                        fontWeight: FontWeight.w800),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    'Ajoutez les informations de votre cours pour pouvoir l\'associer à un professeur.',
                    style: TextStyle(
                        color: Colors.white.withOpacity(0.8), fontSize: 13),
                  ),
                ],
              ),
            ),

            // ── Corps ───────────────────────────────────────────────────────
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.fromLTRB(20, 24, 20, 32),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Illustration + formulaire
                    Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Container(
                          width: 80,
                          height: 80,
                          decoration: BoxDecoration(
                            color: AppTheme.primaryBlue.withOpacity(0.08),
                            shape: BoxShape.circle,
                          ),
                          child: ClipOval(
                            child: Image.asset(
                              'assets/cours.PNG',
                              width: 80,
                              height: 80,
                              fit: BoxFit.cover,
                            ),
                          ),
                        ),
                        const SizedBox(width: 16),
                        const Expanded(
                          child: Padding(
                            padding: EdgeInsets.only(top: 8),
                            child: Text(
                              'Renseignez les informations du cours. L\'université, la filière et la promotion sont remplies automatiquement.',
                              style: TextStyle(
                                  color: AppTheme.textSecondary,
                                  fontSize: 13.5,
                                  height: 1.5),
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 24),

                    Form(
                      key: _formKey,
                      child: Column(
                        children: [
                          _buildField(
                            ctrl: _nomCtrl,
                            hint: 'Nom du cours',
                            icon: Icons.menu_book_outlined,
                            validator: (v) => (v == null || v.trim().isEmpty)
                                ? 'Requis'
                                : null,
                            capitalization: TextCapitalization.sentences,
                          ),
                          const SizedBox(height: 12),
                          _buildField(
                            ctrl: _descCtrl,
                            hint: 'Description (optionnelle)',
                            icon: Icons.description_outlined,
                            maxLines: 3,
                            capitalization: TextCapitalization.sentences,
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 20),

                    SizedBox(
                      width: double.infinity,
                      height: 52,
                      child: ElevatedButton.icon(
                        onPressed: _isCreating ? null : _submit,
                        icon: _isCreating
                            ? const SizedBox(
                                width: 18,
                                height: 18,
                                child: CircularProgressIndicator(
                                    strokeWidth: 2, color: Colors.white))
                            : const Icon(Icons.add_rounded, size: 20),
                        label: Text(
                          _isCreating
                              ? 'Enregistrement...'
                              : 'Enregistrer le cours',
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

                    // ── Liste des cours ──────────────────────────────────────
                    Row(
                      children: [
                        const Text(
                          'Cours enregistrés',
                          style: TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.w700,
                              color: AppTheme.textPrimary),
                        ),
                        const SizedBox(width: 8),
                        if (!_isLoadingList)
                          Container(
                            padding: const EdgeInsets.symmetric(
                                horizontal: 8, vertical: 2),
                            decoration: BoxDecoration(
                              color: AppTheme.primaryBlue.withOpacity(0.12),
                              borderRadius: BorderRadius.circular(20),
                            ),
                            child: Text(
                              '${_cours.length}',
                              style: const TextStyle(
                                  fontSize: 12,
                                  fontWeight: FontWeight.w700,
                                  color: AppTheme.primaryBlue),
                            ),
                          ),
                        if (_isLoadingList)
                          const SizedBox(
                              width: 16,
                              height: 16,
                              child: CircularProgressIndicator(strokeWidth: 2)),
                      ],
                    ),
                    const SizedBox(height: 12),

                    if (!_isLoadingList && _cours.isEmpty)
                      Container(
                        padding: const EdgeInsets.all(20),
                        decoration: BoxDecoration(
                          color: Colors.white,
                          borderRadius: BorderRadius.circular(14),
                          boxShadow: AppTheme.softShadow,
                        ),
                        child: const Center(
                          child: Text(
                            'Aucun cours enregistré.',
                            style: TextStyle(color: AppTheme.textLight),
                          ),
                        ),
                      ),

                    ...(_cours.map((c) => _buildCourseCard(c))),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildCourseCard(Map<String, dynamic> c) {
    final id = c['id'] as int;
    final nom = c['nom'] as String? ?? '';
    final desc = c['description'] as String? ?? '';

    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(14),
        boxShadow: AppTheme.softShadow,
      ),
      child: Row(
        children: [
          Container(
            width: 44,
            height: 44,
            decoration: BoxDecoration(
              color: AppTheme.primaryBlue.withOpacity(0.1),
              borderRadius: BorderRadius.circular(12),
            ),
            child: const Icon(Icons.menu_book_rounded,
                size: 22, color: AppTheme.primaryBlue),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  nom,
                  style: const TextStyle(
                      fontWeight: FontWeight.w600,
                      fontSize: 14,
                      color: AppTheme.textPrimary),
                ),
                if (desc.isNotEmpty) ...[
                  const SizedBox(height: 2),
                  Text(
                    desc,
                    style:
                        const TextStyle(fontSize: 12, color: AppTheme.textLight),
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                  ),
                ],
              ],
            ),
          ),
          IconButton(
            onPressed: () => _confirmDelete(id, nom),
            icon: const Icon(Icons.delete_outline_rounded,
                color: AppTheme.error, size: 20),
            tooltip: 'Supprimer',
          ),
        ],
      ),
    );
  }

  void _confirmDelete(int id, String nom) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: const Text('Supprimer ce cours ?'),
        content: Text('Voulez-vous supprimer "$nom" ?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Annuler'),
          ),
          ElevatedButton(
            onPressed: () {
              Navigator.pop(ctx);
              _delete(id);
            },
            style: ElevatedButton.styleFrom(
                backgroundColor: AppTheme.error, foregroundColor: Colors.white),
            child: const Text('Supprimer'),
          ),
        ],
      ),
    );
  }

  Widget _buildField({
    required TextEditingController ctrl,
    required String hint,
    required IconData icon,
    String? Function(String?)? validator,
    TextInputType? keyboard,
    int maxLines = 1,
    TextCapitalization capitalization = TextCapitalization.none,
  }) {
    return TextFormField(
      controller: ctrl,
      validator: validator,
      keyboardType: keyboard,
      maxLines: maxLines,
      textCapitalization: capitalization,
      style: const TextStyle(fontSize: 15, color: AppTheme.textPrimary),
      decoration: InputDecoration(
        hintText: hint,
        hintStyle:
            const TextStyle(color: AppTheme.textLight, fontSize: 14.5),
        prefixIcon: Icon(icon, size: 20, color: AppTheme.textLight),
        filled: true,
        fillColor: Colors.white,
        contentPadding:
            const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
          borderSide: BorderSide(color: Colors.grey.shade200),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
          borderSide: BorderSide(color: Colors.grey.shade200),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
          borderSide:
              const BorderSide(color: AppTheme.primaryBlue, width: 1.5),
        ),
        errorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
          borderSide: const BorderSide(color: AppTheme.error),
        ),
      ),
    );
  }
}

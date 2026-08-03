import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:resume_plus_clean/services/api_service.dart';
import 'package:resume_plus_clean/theme/app_theme.dart';

class CPOnboardingFlow extends StatefulWidget {
  const CPOnboardingFlow({super.key});

  @override
  State<CPOnboardingFlow> createState() => _CPOnboardingFlowState();
}

class _CPOnboardingFlowState extends State<CPOnboardingFlow> {
  int _step = 0; // 0 = Prof, 1 = Cours, 2 = Félicitations
  final ApiService _apiService = ApiService();

  // État professeur
  final _profFormKey = GlobalKey<FormState>();
  final _nomCompletCtrl = TextEditingController();
  final _telephoneCtrl = TextEditingController();
  final _specialiteCtrl = TextEditingController();
  bool _isCreatingProf = false;
  int? _createdProfId;

  // État cours
  final _courseFormKey = GlobalKey<FormState>();
  final _nomCoursCtrl = TextEditingController();
  final _descCoursCtrl = TextEditingController();
  bool _isCreatingCourse = false;
  int? _createdCourseId;

  @override
  void dispose() {
    _nomCompletCtrl.dispose();
    _telephoneCtrl.dispose();
    _specialiteCtrl.dispose();
    _nomCoursCtrl.dispose();
    _descCoursCtrl.dispose();
    super.dispose();
  }

  // ─── Step indicator ─────────────────────────────────────────────────────────
  Widget _buildStepIndicator() {
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: List.generate(3, (i) {
        final isActive = i == _step;
        final isDone = i < _step;
        return AnimatedContainer(
          duration: const Duration(milliseconds: 300),
          margin: const EdgeInsets.symmetric(horizontal: 6),
          width: isActive ? 32 : 10,
          height: 10,
          decoration: BoxDecoration(
            color: isDone || isActive
                ? Colors.white
                : Colors.white.withOpacity(0.35),
            borderRadius: BorderRadius.circular(5),
          ),
        );
      }),
    );
  }

  // ─── Header commun ─────────────────────────────────────────────────────────
  Widget _buildHeader({required String stepLabel, VoidCallback? onBack}) {
    final topPadding = MediaQuery.of(context).padding.top;
    return Container(
      padding: EdgeInsets.only(
        top: topPadding + 10,
        left: 20,
        right: 20,
        bottom: 28,
      ),
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
          bottomLeft: Radius.circular(32),
          bottomRight: Radius.circular(32),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          Row(
            children: [
              if (onBack != null)
                GestureDetector(
                  onTap: onBack,
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
                )
              else
                const SizedBox(width: 38),
              Expanded(
                child: Text(
                  stepLabel,
                  textAlign: TextAlign.center,
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 14,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
              const SizedBox(width: 38),
            ],
          ),
          const SizedBox(height: 16),
          _buildStepIndicator(),
        ],
      ),
    );
  }

  // ─── Écran 1 : Créer un professeur ─────────────────────────────────────────
  Widget _buildStep1() {
    return Column(
      children: [
        _buildHeader(stepLabel: 'Étape 1 sur 3'),
        Expanded(
          child: SingleChildScrollView(
            padding: const EdgeInsets.fromLTRB(24, 28, 24, 24),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Illustration + titre
                Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          RichText(
                            text: const TextSpan(
                              style: TextStyle(
                                fontSize: 24,
                                fontWeight: FontWeight.w800,
                                color: AppTheme.textPrimary,
                                height: 1.3,
                              ),
                              children: [
                                TextSpan(text: 'Créez votre\npremier '),
                                TextSpan(
                                  text: 'professeur',
                                  style: TextStyle(color: AppTheme.primaryBlue),
                                ),
                              ],
                            ),
                          ),
                          const SizedBox(height: 10),
                          const Text(
                            'Avant d\'ajouter des cours, commencez par enregistrer le professeur qui les dispense.',
                            style: TextStyle(
                              color: AppTheme.textSecondary,
                              fontSize: 13.5,
                              height: 1.5,
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(width: 12),
                    Container(
                      width: 90,
                      height: 90,
                      decoration: BoxDecoration(
                        color: AppTheme.primaryBlue.withOpacity(0.08),
                        shape: BoxShape.circle,
                      ),
                      child: ClipOval(
                        child: Image.asset(
                          'assets/professeur.PNG',
                          width: 90,
                          height: 90,
                          fit: BoxFit.cover,
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 28),

                // Formulaire
                Form(
                  key: _profFormKey,
                  child: Column(
                    children: [
                      _buildTextField(
                        controller: _nomCompletCtrl,
                        hint: 'Nom complet du professeur',
                        icon: Icons.person_outline_rounded,
                        validator: (v) => (v == null || v.trim().isEmpty)
                            ? 'Champ requis'
                            : null,
                        textCapitalization: TextCapitalization.words,
                      ),
                      const SizedBox(height: 14),
                      _buildTextField(
                        controller: _telephoneCtrl,
                        hint: 'Téléphone',
                        icon: Icons.phone_outlined,
                        keyboardType: TextInputType.phone,
                      ),
                      const SizedBox(height: 14),
                      _buildTextField(
                        controller: _specialiteCtrl,
                        hint: 'Spécialité / Matière enseignée',
                        icon: Icons.school_outlined,
                        textCapitalization: TextCapitalization.sentences,
                      ),
                    ],
                  ),
                ),

                const SizedBox(height: 20),
                // Note d'information
                _buildInfoBanner(
                  icon: Icons.lightbulb_outline_rounded,
                  color: const Color(0xFFFFF8E1),
                  borderColor: const Color(0xFFFFE082),
                  iconColor: const Color(0xFFF59E0B),
                  text: 'Ces informations seront utilisées pour associer le professeur aux cours que vous allez créer.',
                ),
              ],
            ),
          ),
        ),

        // Bouton Continuer
        _buildBottomButton(
          label: 'Continuer',
          isLoading: _isCreatingProf,
          onTap: _submitProfesseur,
        ),
      ],
    );
  }

  // ─── Écran 2 : Créer un cours ───────────────────────────────────────────────
  Widget _buildStep2() {
    return Column(
      children: [
        _buildHeader(
          stepLabel: 'Étape 2 sur 3',
          onBack: () => setState(() => _step = 0),
        ),
        Expanded(
          child: SingleChildScrollView(
            padding: const EdgeInsets.fromLTRB(24, 28, 24, 24),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Illustration + titre
                Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          RichText(
                            text: const TextSpan(
                              style: TextStyle(
                                fontSize: 24,
                                fontWeight: FontWeight.w800,
                                color: AppTheme.textPrimary,
                                height: 1.3,
                              ),
                              children: [
                                TextSpan(text: 'Créez votre\npremier '),
                                TextSpan(
                                  text: 'cours',
                                  style: TextStyle(color: AppTheme.primaryBlue),
                                ),
                              ],
                            ),
                          ),
                          const SizedBox(height: 10),
                          const Text(
                            'Ajoutez maintenant le premier cours que vous allez suivre et résumer.',
                            style: TextStyle(
                              color: AppTheme.textSecondary,
                              fontSize: 13.5,
                              height: 1.5,
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(width: 12),
                    Container(
                      width: 90,
                      height: 90,
                      decoration: BoxDecoration(
                        color: AppTheme.primaryBlue.withOpacity(0.08),
                        shape: BoxShape.circle,
                      ),
                      child: ClipOval(
                        child: Image.asset(
                          'assets/cours.PNG',
                          width: 90,
                          height: 90,
                          fit: BoxFit.cover,
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 28),

                // Formulaire
                Form(
                  key: _courseFormKey,
                  child: Column(
                    children: [
                      _buildTextField(
                        controller: _nomCoursCtrl,
                        hint: 'Nom du cours',
                        icon: Icons.menu_book_outlined,
                        validator: (v) => (v == null || v.trim().isEmpty)
                            ? 'Champ requis'
                            : null,
                        textCapitalization: TextCapitalization.sentences,
                      ),
                      const SizedBox(height: 14),
                      _buildTextField(
                        controller: _descCoursCtrl,
                        hint: 'Description du cours (optionnel)',
                        icon: Icons.description_outlined,
                        maxLines: 4,
                        maxLength: 250,
                        textCapitalization: TextCapitalization.sentences,
                      ),
                    ],
                  ),
                ),

                const SizedBox(height: 16),
                // Note info professeur
                _buildInfoBanner(
                  icon: Icons.info_outline_rounded,
                  color: const Color(0xFFE3F2FD),
                  borderColor: const Color(0xFF90CAF9),
                  iconColor: AppTheme.primaryBlue,
                  text: 'Le professeur créé à l\'étape précédente sera automatiquement associé à ce cours.',
                ),
              ],
            ),
          ),
        ),

        // Bouton Continuer
        _buildBottomButton(
          label: 'Continuer',
          isLoading: _isCreatingCourse,
          onTap: _submitCourse,
        ),
      ],
    );
  }

  // ─── Écran 3 : Félicitations ────────────────────────────────────────────────
  Widget _buildStep3() {
    final topPadding = MediaQuery.of(context).padding.top;
    final bottomPadding = MediaQuery.of(context).padding.bottom;

    return Column(
      children: [
        // Header simplifié
        Container(
          padding: EdgeInsets.only(
            top: topPadding + 10,
            left: 20,
            right: 20,
            bottom: 28,
          ),
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
              bottomLeft: Radius.circular(32),
              bottomRight: Radius.circular(32),
            ),
          ),
          child: Column(
            children: [
              Text(
                'Étape 3 sur 3',
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 14,
                  fontWeight: FontWeight.w600,
                ),
              ),
              const SizedBox(height: 16),
              _buildStepIndicator(),
            ],
          ),
        ),

        Expanded(
          child: SingleChildScrollView(
            padding: const EdgeInsets.fromLTRB(24, 32, 24, 24),
            child: Column(
              children: [
                // Icône succès
                Container(
                  width: 100,
                  height: 100,
                  decoration: BoxDecoration(
                    color: AppTheme.primaryBlue,
                    shape: BoxShape.circle,
                    boxShadow: [
                      BoxShadow(
                        color: AppTheme.primaryBlue.withOpacity(0.35),
                        blurRadius: 24,
                        offset: const Offset(0, 8),
                      ),
                    ],
                  ),
                  child: const Icon(Icons.check_rounded,
                      color: Colors.white, size: 52),
                ),
                const SizedBox(height: 28),

                const Text(
                  'Félicitations ! 🎉',
                  style: TextStyle(
                    fontSize: 26,
                    fontWeight: FontWeight.w800,
                    color: AppTheme.textPrimary,
                  ),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 12),
                const Text(
                  'Votre premier professeur et votre premier cours sont prêts.\nVous pouvez maintenant enregistrer votre première séance.',
                  style: TextStyle(
                    color: AppTheme.textSecondary,
                    fontSize: 14.5,
                    height: 1.6,
                  ),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 32),

                // Checklist
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(20),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(16),
                    boxShadow: AppTheme.softShadow,
                  ),
                  child: Column(
                    children: [
                      _buildCheckItem('Professeur créé avec succès'),
                      const SizedBox(height: 12),
                      _buildCheckItem('Cours créé avec succès'),
                      const SizedBox(height: 12),
                      _buildCheckItem('Association effectuée automatiquement'),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),

        // Boutons
        Container(
          padding: EdgeInsets.fromLTRB(24, 16, 24, bottomPadding + 24),
          child: Column(
            children: [
              SizedBox(
                width: double.infinity,
                height: 54,
                child: ElevatedButton.icon(
                  onPressed: _goToCreateSession,
                  icon: const Icon(Icons.fiber_manual_record_rounded, size: 18),
                  label: const Text(
                    'Créer ma première séance',
                    style: TextStyle(fontSize: 16, fontWeight: FontWeight.w700),
                  ),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppTheme.primaryBlue,
                    foregroundColor: Colors.white,
                    shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(16)),
                    elevation: 0,
                  ),
                ),
              ),
              const SizedBox(height: 12),
              SizedBox(
                width: double.infinity,
                height: 54,
                child: OutlinedButton.icon(
                  onPressed: _goToHome,
                  icon: const Icon(Icons.home_rounded, size: 20),
                  label: const Text(
                    'Aller à l\'accueil',
                    style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
                  ),
                  style: OutlinedButton.styleFrom(
                    foregroundColor: AppTheme.primaryBlue,
                    side: const BorderSide(color: AppTheme.primaryBlue, width: 1.5),
                    shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(16)),
                  ),
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  // ─── Helpers UI ─────────────────────────────────────────────────────────────
  Widget _buildTextField({
    required TextEditingController controller,
    required String hint,
    required IconData icon,
    String? Function(String?)? validator,
    TextInputType? keyboardType,
    int maxLines = 1,
    int? maxLength,
    TextCapitalization textCapitalization = TextCapitalization.none,
  }) {
    return TextFormField(
      controller: controller,
      validator: validator,
      keyboardType: keyboardType,
      maxLines: maxLines,
      maxLength: maxLength,
      textCapitalization: textCapitalization,
      style: const TextStyle(fontSize: 15, color: AppTheme.textPrimary),
      decoration: InputDecoration(
        hintText: hint,
        hintStyle: const TextStyle(color: AppTheme.textLight, fontSize: 14.5),
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

  Widget _buildInfoBanner({
    required IconData icon,
    required Color color,
    required Color borderColor,
    required Color iconColor,
    required String text,
  }) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: color,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: borderColor),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, size: 20, color: iconColor),
          const SizedBox(width: 10),
          Expanded(
            child: Text(
              text,
              style: TextStyle(
                color: iconColor.withOpacity(0.85),
                fontSize: 13,
                height: 1.5,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildCheckItem(String text) {
    return Row(
      children: [
        Container(
          width: 24,
          height: 24,
          decoration: BoxDecoration(
            color: AppTheme.primaryBlue,
            shape: BoxShape.circle,
          ),
          child: const Icon(Icons.check_rounded, color: Colors.white, size: 14),
        ),
        const SizedBox(width: 12),
        Expanded( // ← Permet au texte de passer à la ligne
          child: Text(
            text,
            style: const TextStyle(
              fontSize: 14,
              fontWeight: FontWeight.w500,
              color: AppTheme.textPrimary,
            ),
            softWrap: true,
          ),
        ),
      ],
    );
  }

  Widget _buildBottomButton({
    required String label,
    required bool isLoading,
    required VoidCallback onTap,
  }) {
    final bottomPadding = MediaQuery.of(context).padding.bottom;
    return Container(
      padding: EdgeInsets.fromLTRB(24, 12, 24, bottomPadding + 20),
      decoration: BoxDecoration(
        color: Theme.of(context).scaffoldBackgroundColor,
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 10,
            offset: const Offset(0, -4),
          ),
        ],
      ),
      child: SizedBox(
        width: double.infinity,
        height: 54,
        child: ElevatedButton(
          onPressed: isLoading ? null : onTap,
          style: ElevatedButton.styleFrom(
            backgroundColor: AppTheme.primaryBlue,
            foregroundColor: Colors.white,
            shape:
                RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
            elevation: 0,
          ),
          child: isLoading
              ? const SizedBox(
                  width: 22,
                  height: 22,
                  child: CircularProgressIndicator(
                      strokeWidth: 2.5, color: Colors.white),
                )
              : Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Text(
                      label,
                      style: const TextStyle(
                          fontSize: 16, fontWeight: FontWeight.w700),
                    ),
                    const SizedBox(width: 8),
                    const Icon(Icons.arrow_forward_rounded, size: 18),
                  ],
                ),
        ),
      ),
    );
  }

  // ─── Actions ────────────────────────────────────────────────────────────────
  Future<void> _submitProfesseur() async {
    if (!_profFormKey.currentState!.validate()) return;
    setState(() => _isCreatingProf = true);

    try {
      final data = await _apiService.createProfesseurSimple(
        nomComplet: _nomCompletCtrl.text.trim(),
        telephone: _telephoneCtrl.text.trim(),
        specialite: _specialiteCtrl.text.trim(),
      );
      _createdProfId = data['professeur']?['id'];
      if (mounted) setState(() => _step = 1);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Erreur: $e'), backgroundColor: AppTheme.error),
        );
      }
    } finally {
      if (mounted) setState(() => _isCreatingProf = false);
    }
  }

  Future<void> _submitCourse() async {
    if (!_courseFormKey.currentState!.validate()) return;
    setState(() => _isCreatingCourse = true);

    try {
      final data = await _apiService.createCourse(
        nom: _nomCoursCtrl.text.trim(),
        description: _descCoursCtrl.text.trim(),
      );
      _createdCourseId = data['id'];

      // Auto-créer la dispense si on a les deux IDs
      if (_createdProfId != null && _createdCourseId != null) {
        try {
          await _apiService.createDispense(
            professeurId: _createdProfId!,
            coursId: _createdCourseId!,
          );
        } catch (_) {
          // La dispense est souvent créée automatiquement côté backend
        }
      }

      if (mounted) setState(() => _step = 2);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Erreur: $e'), backgroundColor: AppTheme.error),
        );
      }
    } finally {
      if (mounted) setState(() => _isCreatingCourse = false);
    }
  }

  void _goToHome() {
    Navigator.of(context).pop();
  }

  void _goToCreateSession() {
    Navigator.of(context).pop();
    // TODO: naviguer vers l'écran de création de séance
  }

  // ─── Build ──────────────────────────────────────────────────────────────────
  @override
  Widget build(BuildContext context) {
    return AnnotatedRegion<SystemUiOverlayStyle>(
      value: SystemUiOverlayStyle.light,
      child: Scaffold(
        backgroundColor: const Color(0xFFF5F7FA),
        body: AnimatedSwitcher(
          duration: const Duration(milliseconds: 350),
          transitionBuilder: (child, animation) => SlideTransition(
            position: Tween<Offset>(
              begin: const Offset(1, 0),
              end: Offset.zero,
            ).animate(CurvedAnimation(parent: animation, curve: Curves.easeOut)),
            child: child,
          ),
          child: _step == 0
              ? _buildStep1().let((w) => KeyedSubtree(key: const ValueKey(0), child: w))
              : _step == 1
                  ? _buildStep2().let((w) => KeyedSubtree(key: const ValueKey(1), child: w))
                  : _buildStep3().let((w) => KeyedSubtree(key: const ValueKey(2), child: w)),
        ),
      ),
    );
  }
}

extension _WidgetExt on Widget {
  Widget let(Widget Function(Widget) f) => f(this);
}

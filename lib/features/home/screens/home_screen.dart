import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:resume_plus_clean/features/auth/providers/auth_provider.dart';
import 'package:resume_plus_clean/models/user.dart';
import 'package:resume_plus_clean/features/home/providers/summary_provider.dart';
import 'package:resume_plus_clean/providers/tab_refresh_provider.dart';
import 'package:resume_plus_clean/features/home/widgets/summary_card.dart';
import 'package:resume_plus_clean/features/home/widgets/course_tile.dart';
import 'package:resume_plus_clean/features/upload/screens/upload_choice_screen.dart';
import 'package:resume_plus_clean/features/upload/screens/audio_sessions_screen.dart';
import 'package:resume_plus_clean/features/settings/screens/settings_screen.dart';
import 'package:resume_plus_clean/services/api_service.dart';
import 'package:resume_plus_clean/features/auth/screens/profile_completion_screen.dart';
import 'package:resume_plus_clean/theme/app_theme.dart';
import 'package:resume_plus_clean/features/notifications/providers/notification_provider.dart';
import 'package:resume_plus_clean/features/notifications/screens/notifications_screen.dart';
import 'package:resume_plus_clean/services/notification_service.dart';

class HomeScreen extends ConsumerStatefulWidget {
  const HomeScreen({super.key});

  @override
  ConsumerState<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends ConsumerState<HomeScreen> with AutomaticKeepAliveClientMixin {
  final TextEditingController _searchController = TextEditingController();
  final FocusNode _searchFocusNode = FocusNode();
  final ApiService _apiService = ApiService();
  Timer? _debounceTimer;
  String _userRole = 'ETUDIANT';
  bool _isLoadingProfile = true;
  List<Map<String, dynamic>> _courses = [];
  bool _isLoadingCourses = true;
  bool _showAllCourses = false;
  bool _isRefreshing = false;

  // Demande CP
  bool _cpRequestPending = false;
  String? _cpRequestStatus; // pending / approved / rejected

  @override
  bool get wantKeepAlive => true;

  @override
  void initState() {
    super.initState();
    _loadUserProfile();
    NotificationService().startPolling();
  }

  Future<void> _loadUserProfile() async {
    try {
      final profile = await _apiService.getUserProfile();
      print('👤 Profil utilisateur: $profile');
      
      final userProfile = profile['profile'];
      if (userProfile != null) {
        final universite = userProfile['universite'];
        final promotion = userProfile['promotion']; 
        final filiere = userProfile['filiere'];
        
        print('🎓 Université: $universite');
        print('📚 Promotion: $promotion');
        print('📖 Filière: $filiere');
        
        if (universite == null || promotion == null || filiere == null) {
          print('⚠️ Profil incomplet - redirection vers complétion');
          // Rediriger vers la complétion de profil
          if (mounted) {
            Navigator.of(context).pushReplacement(
              MaterialPageRoute(
                builder: (_) => const ProfileCompletionScreen(),
              ),
            );
            return;
          }
        }
      }
      
      setState(() {
        _userRole = profile['profile']?['groupe'] ?? 'ETUDIANT';
        _isLoadingProfile = false;
      });
      // Charger les cours seulement après le profil
      _loadCourses();
      // Charger le statut de la demande CP (si étudiant)
      _loadCPRequestStatus();
    } catch (e) {
      print('❌ Erreur chargement profil: $e');
      setState(() {
        _isLoadingProfile = false;
        _isLoadingCourses = false;
      });
    }
  }

  /// Charge le statut de la demande CP de l'utilisateur (étudiant).
  Future<void> _loadCPRequestStatus() async {
    try {
      final result = await _apiService.getCPRequestStatus();
      if (!mounted) return;
      final request = result['request'];
      if (request != null) {
        setState(() {
          _cpRequestStatus = request['status'];
          _cpRequestPending = request['status'] == 'pending';
        });
      }
    } catch (e) {
      // Non bloquant : le bouton reste actif
      print('⚠️ Erreur chargement statut demande CP: $e');
    }
  }

  /// Bannière "Demander à devenir CP" affichée pour les étudiants.
  /// Si une demande est en attente, le bouton est remplacé par un message.
  Widget _buildCPRequestBanner(BuildContext context) {
    final theme = Theme.of(context);

    return Container(
      margin: const EdgeInsets.fromLTRB(20, 16, 20, 0),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            AppTheme.primaryBlue.withOpacity(0.08),
            AppTheme.primaryBlueLight.withOpacity(0.05),
          ],
        ),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: AppTheme.primaryBlue.withOpacity(0.15),
        ),
      ),
      child: Row(
        children: [
          Container(
            width: 44,
            height: 44,
            decoration: BoxDecoration(
              gradient: const LinearGradient(
                colors: [AppTheme.primaryBlue, AppTheme.primaryBlueLight],
              ),
              shape: BoxShape.circle,
            ),
            child: Icon(
              _cpRequestPending
                  ? Icons.hourglass_top_rounded
                  : Icons.workspace_premium_rounded,
              color: Colors.white,
              size: 22,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  _cpRequestPending
                      ? 'Demande en cours de traitement'
                      : 'Devenez Chef de Promotion',
                  style: theme.textTheme.titleSmall?.copyWith(
                    fontWeight: FontWeight.w700,
                    color: AppTheme.primaryBlue,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  _cpRequestPending
                      ? 'Votre demande a été envoyée. Un administrateur la traitera prochainement.'
                      : 'Créez des cours, enregistrez des séances et publiez des résumés pour les étudiants.',
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: theme.colorScheme.onSurface.withOpacity(0.6),
                    height: 1.4,
                  ),
                ),
              ],
            ),
          ),
          if (!_cpRequestPending) ...[
            const SizedBox(width: 8),
            InkWell(
              onTap: _showCPRequestDialog,
              borderRadius: BorderRadius.circular(10),
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                decoration: BoxDecoration(
                  color: AppTheme.primaryBlue,
                  borderRadius: BorderRadius.circular(10),
                  boxShadow: [
                    BoxShadow(
                      color: AppTheme.primaryBlue.withOpacity(0.3),
                      blurRadius: 8,
                      offset: const Offset(0, 3),
                    ),
                  ],
                ),
                child: const Text(
                  'Demander',
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 13,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
            ),
          ],
        ],
      ),
    );
  }

  /// Affiche le formulaire de demande pour devenir CP.
  Future<void> _showCPRequestDialog() async {
    if (_cpRequestPending) return;

    final TextEditingController motivationCtrl = TextEditingController();
    final TextEditingController emailCtrl = TextEditingController(
      text: ref.read(currentUserProvider)?.email ?? '',
    );
    bool isSubmitting = false;

    await showDialog(
      context: context,
      barrierDismissible: false,
      builder: (dialogContext) => StatefulBuilder(
        builder: (context, setDialogState) => AlertDialog(
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
          title: const Row(
            children: [
              Icon(Icons.workspace_premium_rounded, color: AppTheme.primaryBlue),
              SizedBox(width: 10),
              Expanded(
                child: Text(
                  'Demander à devenir CP',
                  style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                ),
              ),
            ],
          ),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Text(
                'En devenant Chef de Promotion (CP), vous pourrez créer des cours, '
                'enregistrer des séances et publier des résumés pour les étudiants.',
                style: const TextStyle(fontSize: 14, height: 1.5),
              ),
              const SizedBox(height: 16),
              // Champ email TOUJOURS visible (hors zone de défilement)
              TextField(
                controller: emailCtrl,
                keyboardType: TextInputType.emailAddress,
                decoration: InputDecoration(
                  labelText: 'Email (pour les notifications)',
                  hintText: 'Vous recevrez la réponse de l\'administrateur ici',
                  prefixIcon: const Icon(Icons.mail_outline_rounded),
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                  filled: true,
                ),
              ),
              const SizedBox(height: 12),
              // Motivation seule dans une zone scrollable (écrans petits)
              Flexible(
                child: SingleChildScrollView(
                  child: TextField(
                    controller: motivationCtrl,
                    maxLines: 4,
                    maxLength: 500,
                    decoration: InputDecoration(
                      labelText: 'Motivation (optionnel)',
                      hintText: 'Pourquoi souhaitez-vous devenir CP ?',
                      border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                      filled: true,
                    ),
                  ),
                ),
              ),
              const SizedBox(height: 20),
              // Boutons TOUJOURS côte à côte (Row + Expanded)
              Row(
                children: [
                  Expanded(
                    child: SizedBox(
                      height: 48,
                      child: TextButton(
                        onPressed: isSubmitting
                            ? null
                            : () => Navigator.pop(dialogContext),
                        child: const Text('Annuler'),
                      ),
                    ),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: SizedBox(
                      height: 48,
                      child: ElevatedButton(
                        onPressed: isSubmitting
                            ? null
                            : () async {
                                setDialogState(() => isSubmitting = true);
                                try {
                                  await _apiService.createCPRequest(
                                    motivation: motivationCtrl.text.trim(),
                                    email: emailCtrl.text.trim(),
                                  );
                                  if (!dialogContext.mounted) return;
                                  Navigator.pop(dialogContext);
                                  if (mounted) {
                                    setState(() {
                                      _cpRequestStatus = 'pending';
                                      _cpRequestPending = true;
                                    });
                                    ScaffoldMessenger.of(context).showSnackBar(
                                      const SnackBar(
                                        content: Text('Demande envoyée. Elle sera traitée par un administrateur.'),
                                        backgroundColor: AppTheme.success,
                                      ),
                                    );
                                  }
                                } catch (e) {
                                  if (!dialogContext.mounted) return;
                                  setDialogState(() => isSubmitting = false);
                                  ScaffoldMessenger.of(dialogContext).showSnackBar(
                                    SnackBar(
                                      content: Text(ApiService.getErrorMessage(e)),
                                      backgroundColor: AppTheme.error,
                                    ),
                                  );
                                }
                              },
                        style: ElevatedButton.styleFrom(
                          backgroundColor: AppTheme.primaryBlue,
                          foregroundColor: Colors.white,
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                        ),
                        child: isSubmitting
                            ? const SizedBox(
                                width: 20, height: 20,
                                child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                              )
                            : const Text('Envoyer la demande'),
                      ),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  Future<void> _loadCourses() async {
    try {
      print('🔄 Chargement des cours...');
      final coursesData = await _apiService.getCourses();
      print('✅ Cours chargés: ${coursesData.length} cours');
      setState(() {
        _courses = coursesData.map((c) => {
          'id': c['id'] ?? 0,
          'title': c['nom'] ?? 'Cours sans nom',
          'filiere': c['filiere_nom'] ?? c['filiere'] ?? 'Non définie',
        }).toList();
        _isLoadingCourses = false;
      });
    } catch (e) {
      print('❌ Erreur chargement cours: $e');
      setState(() {
        _isLoadingCourses = false;
      });
    }
  }

  Future<void> _refreshAll() async {
    print('🔄 Pull-to-refresh déclenché');
    await ref.refresh(summariesProvider.future);
    await _loadCourses();
  }

  void _onSearchChanged(String query) {
    _debounceTimer?.cancel();
    final cursorPosition = _searchController.selection;
    _debounceTimer = Timer(const Duration(seconds: 3), () {
      if (mounted) {
        ref.read(searchQueryProvider.notifier).state = query;
        WidgetsBinding.instance.addPostFrameCallback((_) {
          if (mounted && _searchFocusNode.canRequestFocus) {
            _searchFocusNode.requestFocus();
            _searchController.selection = cursorPosition;
          }
        });
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    super.build(context);
    final summariesAsync = ref.watch(summariesProvider);
    final theme = Theme.of(context);
    final topPadding = MediaQuery.of(context).padding.top;

    // Recharger les données quand la session utilisateur change (login d'un autre compte)
    ref.listen<int>(userSessionVersionProvider, (prev, next) {
      if (prev != next) {
        print('🔄 [Home] Changement de session détecté ($prev → $next) — rechargement des données');
        _apiService.clearSession();
        _loadUserProfile();
        ref.invalidate(summariesProvider);
      }
    });

    // Écouter les changements d'état auth pour détecter un nouvel utilisateur
    ref.listen<AsyncValue<User?>>(authProvider, (prev, next) {
      if (prev?.value?.id != next.value?.id && next.value != null) {
        print('🔄 [Home] Nouvel utilisateur détecté (id=${next.value!.id}) — rechargement des données');
        _apiService.clearSession();
        _loadUserProfile();
        ref.invalidate(summariesProvider);
      }
    });

    // Rafraîchir les données à chaque fois qu'on arrive sur l'onglet Accueil
    ref.listen<int>(homeRefreshProvider, (prev, next) {
      if (prev != next) {
        print('🔄 [Home] Onglet Accueil sélectionné — rafraîchissement');
        _loadCourses();
        ref.invalidate(summariesProvider);
      }
    });

    return Scaffold(
      backgroundColor: theme.scaffoldBackgroundColor,
      floatingActionButton: _isLoadingProfile
          ? null
          : (_userRole == 'CP' || _userRole == 'ADMIN'
              ? FloatingActionButton(
                  onPressed: () {
                    Navigator.of(context).push(
                      MaterialPageRoute(builder: (_) => const UploadChoiceScreen()),
                    );
                  },
                  backgroundColor: AppTheme.primaryBlue,
                  child: const Icon(Icons.add, color: Colors.white, size: 28),
                )
              : null),
      floatingActionButtonLocation: FloatingActionButtonLocation.endFloat,
      body: summariesAsync.when(
        loading: () => const Center(
          child: CircularProgressIndicator(color: AppTheme.primaryBlue),
        ),
        error: (err, stack) => Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.error_outline, size: 48, color: AppTheme.error),
              const SizedBox(height: 16),
              Text('Erreur de chargement', style: theme.textTheme.titleMedium),
              const SizedBox(height: 8),
              TextButton(
                onPressed: () => ref.invalidate(summariesProvider),
                child: const Text('Réessayer'),
              ),
            ],
          ),
        ),
        data: (summaries) => RefreshIndicator(
          onRefresh: _refreshAll,
          color: AppTheme.primaryBlue,
          displacement: 40,
          child: SingleChildScrollView(
            physics: const AlwaysScrollableScrollPhysics(),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Header bleu courbé
                _buildCurvedHeader(context, topPadding),

                // Bannière "Demander à devenir CP" (uniquement étudiants)
                if (!_isLoadingProfile && _userRole != 'CP' && _userRole != 'ADMIN')
                  _buildCPRequestBanner(context),

              const SizedBox(height: 20),

              // Section résumés récents
              if (summaries.isEmpty)
                _buildEmptyState(context)
              else ...[
                _buildSectionHeader(context, 'Résumés récents', Icons.access_time_rounded, showViewAll: summaries.length > 4),
                const SizedBox(height: 12),
                SizedBox(
                  height: 230,
                  child: ListView.builder(
                    scrollDirection: Axis.horizontal,
                    padding: const EdgeInsets.symmetric(horizontal: 20),
                    itemCount: summaries.length > 4 ? 4 : summaries.length,
                    itemBuilder: (context, index) {
                      return Container(
                        width: 260,
                        margin: const EdgeInsets.only(right: 14),
                        child: SummaryCard(summary: summaries[index], showAuthorBadge: _userRole == 'CP' || _userRole == 'ADMIN'),
                      );
                    },
                  ),
                ),
                const SizedBox(height: 24),
                _buildSectionHeader(context, 'Parcourir les cours', Icons.school_rounded, showViewAll: _courses.length > 4, onViewAll: () => setState(() => _showAllCourses = !_showAllCourses)),
                const SizedBox(height: 12),
                if (_isLoadingCourses)
                  const Center(
                    child: Padding(
                      padding: EdgeInsets.all(24),
                      child: CircularProgressIndicator(color: AppTheme.primaryBlue),
                    ),
                  )
                else if (_courses.isEmpty)
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
                    child: Text(
                      'Aucun cours disponible',
                      style: theme.textTheme.bodyMedium,
                    ),
                  )
                else
                  ListView.builder(
                    shrinkWrap: true,
                    physics: const NeverScrollableScrollPhysics(),
                    padding: const EdgeInsets.symmetric(horizontal: 20),
                    itemCount: _showAllCourses ? _courses.length : (_courses.length > 4 ? 4 : _courses.length),
                    itemBuilder: (context, index) {
                      final course = _courses[index];
                      return Padding(
                        padding: const EdgeInsets.only(bottom: 10),
                        child: CourseTile(
                          courseId: course['id'] as int,
                          title: course['title'] as String,
                          filiere: course['filiere'] as String,
                        ),
                      );
                    },
                  ),
              ],
              const SizedBox(height: 100),
            ],
          ),
        ),
      ),
    ),
  );
  }

  Widget _buildCurvedHeader(BuildContext context, double topPadding) {
    return Stack(
      children: [
        // Fond courbé bleu
        ClipPath(
          clipper: _HeaderClipper(),
          child: Container(
            height: 260 + topPadding,
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
            ),
          ),
        ),
        // Contenu du header
        Padding(
          padding: EdgeInsets.only(top: topPadding + 16, left: 20, right: 20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Top row: titre + actions
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Résumé+',
                          style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                            color: Colors.white,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                        if (_userRole == 'ETUDIANT') ...[
                          const SizedBox(height: 4),
                          Text(
                            'Trouvez vos résumés de cours',
                            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                              color: Colors.white.withOpacity(0.8),
                            ),
                          ),
                        ],
                      ],
                    ),
                  ),
                  Row(
                    children: [
                      _buildHeaderIconButton(
                        Icons.refresh_rounded,
                        () async {
                          if (_isRefreshing) return;
                          setState(() => _isRefreshing = true);
                          await ref.refresh(summariesProvider.future);
                          await _loadCourses();
                          if (mounted) setState(() => _isRefreshing = false);
                        },
                        isLoading: _isRefreshing,
                      ),
                      const SizedBox(width: 8),
                      if (_userRole != 'ETUDIANT')
                        _buildHeaderIconButton(
                          Icons.mic_rounded,
                          () => Navigator.of(context).push(
                            MaterialPageRoute(builder: (_) => const AudioSessionsScreen()),
                          ),
                        ),
                      if (_userRole != 'ETUDIANT') const SizedBox(width: 8),
                      _buildHeaderIconButton(
                        Icons.settings_rounded,
                        () => Navigator.of(context).push(
                          MaterialPageRoute(builder: (_) => const SettingsScreen()),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
              const SizedBox(height: 24),
              // Search bar (85%) + notification bell (15%)
              Row(
                children: [
                  Expanded(
                    flex: 85,
                    child: Container(
                      height: 50,
                      decoration: BoxDecoration(
                        color: Colors.white,
                        borderRadius: BorderRadius.circular(25),
                        boxShadow: [
                          BoxShadow(
                            color: AppTheme.primaryBlueDark.withOpacity(0.15),
                            blurRadius: 20,
                            offset: const Offset(0, 8),
                          ),
                        ],
                      ),
                      child: TextField(
                        controller: _searchController,
                        focusNode: _searchFocusNode,
                        onChanged: _onSearchChanged,
                        style: const TextStyle(color: Colors.black87),
                        decoration: InputDecoration(
                          hintText: 'Rechercher un résumé...',
                          hintStyle: const TextStyle(color: Colors.black54),
                          prefixIcon: const Icon(Icons.search_rounded, color: Colors.black54),
                          suffixIcon: _searchController.text.isNotEmpty
                              ? IconButton(
                                  icon: const Icon(Icons.close_rounded, color: Colors.black54, size: 20),
                                  onPressed: () {
                                    _searchController.clear();
                                    _debounceTimer?.cancel();
                                    ref.read(searchQueryProvider.notifier).state = '';
                                    _searchFocusNode.requestFocus();
                                    setState(() {});
                                  },
                                )
                              : null,
                          border: InputBorder.none,
                          enabledBorder: InputBorder.none,
                          focusedBorder: InputBorder.none,
                          contentPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
                          filled: false,
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    flex: 15,
                    child: _buildSearchRowNotificationButton(context),
                  ),
                ],
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildHeaderIconButton(IconData icon, VoidCallback onTap, {bool isLoading = false}) {
    return GestureDetector(
      onTap: isLoading ? null : onTap,
      child: Container(
        width: 42,
        height: 42,
        decoration: BoxDecoration(
          color: Colors.white.withOpacity(0.2),
          shape: BoxShape.circle,
        ),
        child: isLoading
            ? const Padding(
                padding: EdgeInsets.all(10),
                child: CircularProgressIndicator(
                  strokeWidth: 2,
                  valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                ),
              )
            : Icon(icon, color: Colors.white, size: 22),
      ),
    );
  }

  Widget _buildSearchRowNotificationButton(BuildContext context) {
    final unread = ref.watch(unreadCountProvider);
    return GestureDetector(
      onTap: () => Navigator.of(context).push(
        MaterialPageRoute(builder: (_) => const NotificationsScreen()),
      ),
      child: Container(
        height: 50,
        decoration: BoxDecoration(
          color: Colors.white.withOpacity(0.2),
          shape: BoxShape.circle,
        ),
        child: Stack(
          children: [
            const Center(
              child: Icon(Icons.notifications_rounded, color: Colors.white, size: 24),
            ),
            if (unread > 0)
              Positioned(
                top: 8,
                right: 8,
                child: Container(
                  width: 17,
                  height: 17,
                  decoration: const BoxDecoration(
                    color: Color(0xFFEF4444),
                    shape: BoxShape.circle,
                  ),
                  child: Center(
                    child: Text(
                      unread > 99 ? '99' : '$unread',
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 9,
                        fontWeight: FontWeight.w700,
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

  Widget _buildSectionHeader(BuildContext context, String title, IconData icon, {bool showViewAll = false, VoidCallback? onViewAll}) {
    final theme = Theme.of(context);
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20),
      child: Row(
        children: [
          Container(
            width: 36,
            height: 36,
            decoration: BoxDecoration(
              color: AppTheme.primaryBlue.withOpacity(0.1),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Icon(icon, color: AppTheme.primaryBlue, size: 20),
          ),
          const SizedBox(width: 10),
          Text(
            title,
            style: theme.textTheme.titleLarge?.copyWith(
              fontWeight: FontWeight.w700,
              color: theme.colorScheme.onSurface,
            ),
          ),
          const Spacer(),
          if (showViewAll)
            TextButton(
              onPressed: onViewAll,
              child: Text(
                'Voir tout',
                style: theme.textTheme.bodySmall?.copyWith(
                  color: AppTheme.primaryBlue,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildEmptyState(BuildContext context) {
    // Message personnalisé selon le niveau de l'utilisateur
    final isCP = _userRole == 'CP';
    final title = isCP ? 'Aucun résumé pour le moment' : 'Aucun résumé disponible';
    final message = isCP 
        ? 'Créez votre premier résumé en cliquant sur le bouton +'
        : 'Retrouvez les résumés réels de votre promotion à partir des scéances de cours';
    
    final theme = Theme.of(context);
    
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(40),
        child: Column(
          children: [
            Container(
              width: 100,
              height: 100,
              decoration: BoxDecoration(
                color: AppTheme.primaryBlue.withOpacity(0.1),
                shape: BoxShape.circle,
              ),
              child: const Icon(
                Icons.menu_book_rounded,
                size: 48,
                color: AppTheme.primaryBlue,
              ),
            ),
            const SizedBox(height: 24),
            Text(
              title,
              style: theme.textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.w600,
                color: theme.colorScheme.onSurface,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              message,
              textAlign: TextAlign.center,
              style: theme.textTheme.bodyMedium?.copyWith(
                color: theme.colorScheme.onSurface.withOpacity(0.7),
              ),
            ),
          ],
        ),
      ),
    );
  }

  @override
  void dispose() {
    _searchController.dispose();
    _searchFocusNode.dispose();
    _debounceTimer?.cancel();
    super.dispose();
  }
}

class _HeaderClipper extends CustomClipper<Path> {
  @override
  Path getClip(Size size) {
    final path = Path();
    path.lineTo(0, size.height - 50);
    path.quadraticBezierTo(
      size.width / 2,
      size.height + 10,
      size.width,
      size.height - 50,
    );
    path.lineTo(size.width, 0);
    path.close();
    return path;
  }

  @override
  bool shouldReclip(covariant CustomClipper<Path> oldClipper) => false;
}

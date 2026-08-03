import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:resume_plus_clean/models/exercise.dart';
import 'package:resume_plus_clean/models/personalized_exercise.dart' as pe;
import 'package:resume_plus_clean/services/api_service.dart';
import 'package:resume_plus_clean/theme/app_theme.dart';
import 'package:resume_plus_clean/providers/tab_refresh_provider.dart';
import 'package:resume_plus_clean/features/exercises/screens/exercise_subscription_screen.dart';
import 'package:resume_plus_clean/features/exercises/screens/exercise_result_screen.dart';
import 'package:resume_plus_clean/features/exercises/screens/quiz_result_screen.dart';
import 'package:resume_plus_clean/features/exercises/screens/personalized_quiz_screen.dart';

/// Tentative unifiée : agrège les tentatives de l'ancien système d'exercices
/// et celles du quiz QCM personnalisé pour les afficher avec la même logique.
class _UnifiedAttempt {
  final int id;
  final String title;
  final String summaryTitle;
  final double score;
  final DateTime completedAt;
  final bool isPersonalized;
  final int summaryId;

  const _UnifiedAttempt({
    required this.id,
    required this.title,
    required this.summaryTitle,
    required this.score,
    required this.completedAt,
    required this.isPersonalized,
    this.summaryId = 0,
  });

  String get scoreFormatted => '${score.toStringAsFixed(0)}%';
  bool get isPassed => score >= 50;
}

class ExercisesScreen extends ConsumerStatefulWidget {
  const ExercisesScreen({super.key});

  @override
  ConsumerState<ExercisesScreen> createState() => _ExercisesScreenState();
}

class _ExercisesScreenState extends ConsumerState<ExercisesScreen> with SingleTickerProviderStateMixin {
  final ApiService _apiService = ApiService();
  List<_UnifiedAttempt> _attempts = [];
  bool _isLoading = true;
  bool _hasSubscription = false;
  bool _isExpired = false;
  String? _error;
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    _loadData();
  }

  Future<void> _loadData() async {
    if (!mounted) return;
    setState(() {
      _isLoading = true;
      _error = null;
    });

    // Charger abonnement et tentatives indépendamment
    // pour éviter qu'un échec de l'un bloque l'autre
    bool subLoaded = false;
    bool attemptsLoaded = false;

    try {
      final subData = await _apiService.checkExerciseSubscription();
      if (!mounted) return;
      _hasSubscription = subData['has_subscription'] == true;
      _isExpired = subData['is_expired'] == true;
      subLoaded = true;
    } catch (e) {
      debugPrint('⚠️ Erreur chargement abonnement exercices: $e');
      _hasSubscription = false;
      _isExpired = false;
    }

    final List<_UnifiedAttempt> merged = [];

    // 1. Anciennes tentatives (système d'exercices classique)
    try {
      final attemptsData = await _apiService.getExerciseAttempts();
      if (!mounted) return;
      for (final a in attemptsData) {
        final att = ExerciseAttempt.fromJson(a as Map<String, dynamic>);
        merged.add(_UnifiedAttempt(
          id: att.id,
          title: att.exerciseTitle,
          summaryTitle: att.summaryTitle,
          score: att.score,
          completedAt: att.completedAt,
          isPersonalized: false,
        ));
      }
      attemptsLoaded = true;
    } catch (e) {
      debugPrint('⚠️ Erreur chargement tentatives classiques: $e');
    }

    // 2. Tentatives du quiz QCM personnalisé
    try {
      final data = await _apiService.getPersonalizedExerciseAttempts();
      if (!mounted) return;
      final list = data['attempts'] as List<dynamic>? ?? [];
      for (final a in list) {
        final att = pe.ExerciseAttempt.fromJson(a as Map<String, dynamic>);
        merged.add(_UnifiedAttempt(
          id: att.id,
          title: 'Exercice QCM • ${att.difficultyLabel}',
          summaryTitle: att.summaryTitle,
          score: att.score,
          completedAt: att.completedAt ?? att.startedAt,
          isPersonalized: true,
          summaryId: att.summaryId,
        ));
      }
      attemptsLoaded = true;
    } catch (e) {
      debugPrint('⚠️ Erreur chargement tentatives personnalisées: $e');
    }

    // Trier par date décroissante (plus récentes en premier)
    merged.sort((a, b) => b.completedAt.compareTo(a.completedAt));
    _attempts = merged;
    debugPrint('✅ ${_attempts.length} tentatives chargées (toutes sources)');

    if (!mounted) return;
    setState(() {
      if (!subLoaded && !attemptsLoaded) {
        _error = 'Impossible de charger les données. Vérifiez votre connexion.';
      }
      _isLoading = false;
    });
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final topPadding = MediaQuery.of(context).padding.top;

    // Rafraîchir les données à chaque fois qu'on arrive sur l'onglet Exercices
    ref.listen<int>(exercisesRefreshProvider, (prev, next) {
      if (prev != next) {
        _loadData();
      }
    });

    return Scaffold(
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      body: Column(
        children: [
          // Header
          Container(
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
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Container(
                      width: 44, height: 44,
                      decoration: BoxDecoration(
                        color: Colors.white.withValues(alpha: 0.15),
                        borderRadius: BorderRadius.circular(14),
                      ),
                      child: const Icon(Icons.quiz_rounded, color: Colors.white, size: 24),
                    ),
                    const SizedBox(width: 14),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Exercices QCM',
                            style: Theme.of(context).textTheme.titleLarge?.copyWith(
                              color: Colors.white, fontWeight: FontWeight.w700,
                            ),
                          ),
                          Text(
                            _hasSubscription
                                ? 'Abonnement actif'
                                : _isExpired
                                    ? 'Abonnement expiré'
                                    : 'Abonnement requis',
                            style: TextStyle(
                              color: Colors.white.withValues(alpha: 0.7), fontSize: 12,
                            ),
                          ),
                        ],
                      ),
                    ),
                    // Subscription badge
                    GestureDetector(
                      onTap: _hasSubscription ? null : _navigateToSubscription,
                      child: Container(
                        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                        decoration: BoxDecoration(
                          color: _hasSubscription
                              ? AppTheme.success.withValues(alpha: 0.2)
                              : _isExpired
                                  ? AppTheme.error.withValues(alpha: 0.2)
                                  : AppTheme.warning.withValues(alpha: 0.2),
                          borderRadius: BorderRadius.circular(20),
                        ),
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Icon(
                              _hasSubscription
                                  ? Icons.check_circle_rounded
                                  : _isExpired
                                      ? Icons.history_rounded
                                      : Icons.lock_rounded,
                              color: _hasSubscription
                                  ? AppTheme.success
                                  : _isExpired
                                      ? AppTheme.error
                                      : AppTheme.warning,
                              size: 14,
                            ),
                            const SizedBox(width: 4),
                            Text(
                              _hasSubscription
                                  ? 'Actif'
                                  : _isExpired
                                      ? 'Expiré'
                                      : "S'abonner",
                              style: TextStyle(
                                color: _hasSubscription
                                    ? AppTheme.success
                                    : _isExpired
                                        ? AppTheme.error
                                        : AppTheme.warning,
                                fontSize: 11, fontWeight: FontWeight.w600,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 16),
                // Tabs
                TabBar(
                  controller: _tabController,
                  labelColor: Colors.white,
                  unselectedLabelColor: Colors.white.withValues(alpha: 0.5),
                  indicatorColor: Colors.white,
                  indicatorWeight: 3,
                  tabs: const [
                    Tab(text: 'Mes tentatives'),
                    Tab(text: 'Statistiques'),
                  ],
                ),
              ],
            ),
          ),
          // Content
          Expanded(
            child: _isLoading
                ? const Center(child: CircularProgressIndicator(color: AppTheme.primaryBlue))
                : _error != null
                    ? _buildError()
                    : TabBarView(
                        controller: _tabController,
                        children: [
                          _buildAttemptsList(),
                          _buildStats(),
                        ],
                      ),
          ),
        ],
      ),
    );
  }

  Widget _buildAttemptsList() {
    if (_attempts.isEmpty) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(32),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Container(
                width: 80, height: 80,
                decoration: BoxDecoration(
                  color: AppTheme.primaryBlue.withValues(alpha: 0.1),
                  shape: BoxShape.circle,
                ),
                child: const Icon(Icons.quiz_outlined, size: 36, color: AppTheme.primaryBlue),
              ),
              const SizedBox(height: 20),
              Text(
                'Aucune tentative',
                style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w600),
              ),
              const SizedBox(height: 8),
              const Text(
                'Accédez à un résumé et lancez un exercice QCM pour commencer.',
                textAlign: TextAlign.center,
                style: TextStyle(color: AppTheme.textLight, fontSize: 13),
              ),
            ],
          ),
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: _loadData,
      child: ListView.builder(
        padding: const EdgeInsets.all(20),
        itemCount: _attempts.length,
        itemBuilder: (context, index) {
          final attempt = _attempts[index];
          return _buildAttemptCard(attempt);
        },
      ),
    );
  }

  Widget _buildAttemptCard(_UnifiedAttempt attempt) {
    final theme = Theme.of(context);
    return GestureDetector(
      onTap: () => _openAttemptResult(attempt),
      child: Container(
        margin: const EdgeInsets.only(bottom: 14),
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: theme.colorScheme.surface,
          borderRadius: BorderRadius.circular(16),
          boxShadow: AppTheme.softShadow,
        ),
        child: Row(
          children: [
            // Score circle
            Container(
              width: 54, height: 54,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: attempt.isPassed
                    ? AppTheme.success.withValues(alpha: 0.1)
                    : AppTheme.error.withValues(alpha: 0.1),
              ),
              child: Center(
                child: Text(
                  attempt.scoreFormatted,
                  style: TextStyle(
                    color: attempt.isPassed ? AppTheme.success : AppTheme.error,
                    fontWeight: FontWeight.w800, fontSize: 14,
                  ),
                ),
              ),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Expanded(
                        child: Text(
                          attempt.title,
                          style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w600),
                          maxLines: 1, overflow: TextOverflow.ellipsis,
                        ),
                      ),
                      if (attempt.isPersonalized)
                        Container(
                          margin: const EdgeInsets.only(left: 8),
                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                          decoration: BoxDecoration(
                            color: AppTheme.primaryBlue.withValues(alpha: 0.1),
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: const Text(
                            'Perso',
                            style: TextStyle(
                              color: AppTheme.primaryBlue,
                              fontSize: 10,
                              fontWeight: FontWeight.w700,
                            ),
                          ),
                        ),
                    ],
                  ),
                  const SizedBox(height: 4),
                  Text(
                    attempt.summaryTitle,
                    style: const TextStyle(color: AppTheme.textLight, fontSize: 12),
                    maxLines: 1, overflow: TextOverflow.ellipsis,
                  ),
                  const SizedBox(height: 4),
                  Text(
                    _formatDate(attempt.completedAt),
                    style: const TextStyle(color: AppTheme.textLight, fontSize: 11),
                  ),
                ],
              ),
            ),
            Icon(
              Icons.chevron_right_rounded,
              color: theme.colorScheme.onSurface.withValues(alpha: 0.4),
              size: 22,
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _openAttemptResult(_UnifiedAttempt attempt) async {
    try {
      showDialog(
        context: context,
        barrierDismissible: false,
        builder: (_) => const Center(child: CircularProgressIndicator()),
      );

      if (attempt.isPersonalized) {
        // Détail d'une tentative du quiz QCM personnalisé
        final data = await _apiService.getPersonalizedAttemptDetail(attempt.id);
        if (!mounted) return;
        Navigator.of(context).pop(); // fermer le loader

        final result = pe.AttemptResult.fromJson(data);
        final exercise = pe.PersonalizedExercise.fromJson(
          data['exercise'] as Map<String, dynamic>? ?? {},
        );

        Navigator.of(context).push(
          MaterialPageRoute(
            builder: (_) => QuizResultScreen(
              result: result,
              exercise: exercise,
              onRetry: () {
                Navigator.of(context).pop(); // ferme le résultat
                Navigator.of(context).push(
                  MaterialPageRoute(
                    builder: (_) => PersonalizedQuizScreen(
                      summaryId: attempt.summaryId,
                      summaryTitle: attempt.summaryTitle,
                    ),
                  ),
                );
              },
              onBack: () => Navigator.of(context).pop(),
            ),
          ),
        );
      } else {
        // Détail d'une tentative du système d'exercices classique
        final data = await _apiService.getAttemptResult(attempt.id);
        if (!mounted) return;
        Navigator.of(context).pop(); // fermer le loader
        final result = ExerciseResult.fromJson(data);
        Navigator.of(context).push(
          MaterialPageRoute(builder: (_) => ExerciseResultScreen(result: result)),
        );
      }
    } catch (e) {
      if (mounted) {
        Navigator.of(context).pop(); // fermer le loader
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Impossible de charger les détails: $e')),
        );
      }
    }
  }

  Widget _buildStats() {
    final totalAttempts = _attempts.length;
    final passed = _attempts.where((a) => a.isPassed).length;
    final avgScore = totalAttempts > 0
        ? _attempts.map((a) => a.score).reduce((a, b) => a + b) / totalAttempts
        : 0.0;

    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        children: [
          Row(
            children: [
              _buildStatCard('Total', totalAttempts.toString(), Icons.assignment_rounded, AppTheme.primaryBlue),
              const SizedBox(width: 12),
              _buildStatCard('Réussis', passed.toString(), Icons.check_circle_rounded, AppTheme.success),
            ],
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              _buildStatCard('Moyenne', '${avgScore.toStringAsFixed(0)}%', Icons.analytics_rounded, AppTheme.warning),
              const SizedBox(width: 12),
              _buildStatCard('Échoués', '${totalAttempts - passed}', Icons.cancel_rounded, AppTheme.error),
            ],
          ),
          if (!_hasSubscription) ...[
            const SizedBox(height: 24),
            Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: (_isExpired ? AppTheme.error : AppTheme.warning).withValues(alpha: 0.1),
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: (_isExpired ? AppTheme.error : AppTheme.warning).withValues(alpha: 0.3)),
              ),
              child: Column(
                children: [
                  Icon(
                    _isExpired ? Icons.history_rounded : Icons.lock_outline_rounded,
                    size: 40,
                    color: _isExpired ? AppTheme.error : AppTheme.warning,
                  ),
                  const SizedBox(height: 12),
                  Text(
                    _isExpired ? 'Abonnement expiré' : 'Abonnement requis',
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w600),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    _isExpired
                        ? 'Votre abonnement a expiré. Veuillez le renouveler pour continuer à générer des QCM.'
                        : 'Souscrivez au service Exercices pour générer des QCM sur tous vos résumés.',
                    textAlign: TextAlign.center,
                    style: TextStyle(color: AppTheme.textSecondary, fontSize: 13),
                  ),
                  const SizedBox(height: 14),
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton.icon(
                      onPressed: () => _navigateToSubscription(),
                      icon: const Icon(Icons.diamond_rounded, size: 18, color: Colors.white),
                      label: Text(
                        _isExpired ? "Renouveler" : "S'abonner",
                        style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w600),
                      ),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: _isExpired ? AppTheme.error : AppTheme.primaryBlue,
                        padding: const EdgeInsets.symmetric(vertical: 12),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                        elevation: 0,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildStatCard(String label, String value, IconData icon, Color color) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.all(18),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(16),
          boxShadow: AppTheme.softShadow,
        ),
        child: Column(
          children: [
            Container(
              width: 44, height: 44,
              decoration: BoxDecoration(
                color: color.withValues(alpha: 0.1), shape: BoxShape.circle,
              ),
              child: Icon(icon, color: color, size: 22),
            ),
            const SizedBox(height: 12),
            Text(value, style: TextStyle(color: color, fontSize: 24, fontWeight: FontWeight.w800)),
            const SizedBox(height: 4),
            Text(label, style: const TextStyle(color: AppTheme.textLight, fontSize: 12)),
          ],
        ),
      ),
    );
  }

  Widget _buildError() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.error_outline_rounded, size: 48, color: AppTheme.error),
            const SizedBox(height: 16),
            Text(_error!, textAlign: TextAlign.center),
            const SizedBox(height: 16),
            ElevatedButton(onPressed: _loadData, child: const Text('Réessayer')),
          ],
        ),
      ),
    );
  }

  Future<void> _navigateToSubscription() async {
    final result = await Navigator.of(context).push<bool>(
      MaterialPageRoute(builder: (_) => const ExerciseSubscriptionScreen()),
    );
    if (result == true) {
      _loadData();
    }
  }

  String _formatDate(DateTime date) {
    return '${date.day.toString().padLeft(2, '0')}/${date.month.toString().padLeft(2, '0')}/${date.year} à ${date.hour.toString().padLeft(2, '0')}:${date.minute.toString().padLeft(2, '0')}';
  }
}

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:resume_plus_clean/features/home/screens/home_screen.dart';
import 'package:resume_plus_clean/features/onboarding/cp_onboarding_flow.dart';
import 'package:resume_plus_clean/features/summaries/screens/all_summaries_screen.dart';
import 'package:resume_plus_clean/features/purchases/screens/purchases_screen.dart';
import 'package:resume_plus_clean/features/exercises/screens/exercises_screen.dart';
import 'package:resume_plus_clean/features/validation/screens/validation_screen.dart';
import 'package:resume_plus_clean/services/api_service.dart';
import 'package:resume_plus_clean/services/notification_service.dart';
import 'package:resume_plus_clean/features/auth/providers/auth_provider.dart';
import 'package:resume_plus_clean/theme/app_theme.dart';
import 'package:resume_plus_clean/providers/purchase_badge_provider.dart';
import 'package:resume_plus_clean/features/home/providers/summary_provider.dart';
import 'package:resume_plus_clean/features/summaries/providers/purchased_summaries_provider.dart';
import 'package:resume_plus_clean/widgets/badge_icon.dart';
import 'package:resume_plus_clean/providers/tab_refresh_provider.dart';

class MainNavigationScreen extends ConsumerStatefulWidget {
  const MainNavigationScreen({super.key});

  /// Clé globale pour accéder à l'état depuis d'autres écrans
  static final GlobalKey<_MainNavigationScreenState> navKey = GlobalKey<_MainNavigationScreenState>();

  @override
  ConsumerState<MainNavigationScreen> createState() => _MainNavigationScreenState();
}

class _MainNavigationScreenState extends ConsumerState<MainNavigationScreen> {
  int _currentIndex = 0;
  int? _validationSummaryId; // ID du résumé à afficher dans l'onglet validation
  late int _purchasesTabIndex; // Index de l'onglet "Mes Achats"

  /// Permet de changer d'onglet depuis l'extérieur
  /// [summaryId] - ID du résumé à afficher dans l'onglet validation (optionnel)
  void switchToTab(int index, {int? summaryId}) {
    if (index >= 0 && index < _destinations.length) {
      setState(() {
        _currentIndex = index;
        if (index == 2 && summaryId != null) {
          _validationSummaryId = summaryId;
        }
      });
    }
  }
  String _userRole = 'ETUDIANT';
  bool _isLoadingProfile = true;
  final ApiService _apiService = ApiService();

  /// Garde-fou anti-doublon : un seul flux d'onboarding CP à la fois. Tant que
  /// le flux est affiché (route ouverte), toute tentative concurrente est
  /// ignorée → jamais deux CPOnboardingFlow empilés.
  bool _cpCheckInFlight = false;

  // CP:      Accueil(0), Résumés(1), Validation(2), Mes achats(3), Exercices(4)
  // Étudiant: Accueil(0), Résumés(1), Mes achats(2), Exercices(3)
  List<Widget> get _screens {
    if (_userRole == 'CP') {
      return [
        const HomeScreen(),
        const AllSummariesScreen(),
        ValidationScreen(key: ValueKey('validation_$_validationSummaryId'), initialSummaryId: _validationSummaryId),
        const PurchasesScreen(),
        const ExercisesScreen(),
      ];
    }
    return [
      const HomeScreen(),
      const AllSummariesScreen(),
      const PurchasesScreen(),
      const ExercisesScreen(),
    ];
  }

  List<NavigationDestination> get _destinations {
    if (_userRole == 'CP') {
      return const [
        NavigationDestination(
          icon: Icon(Icons.home_rounded),
          selectedIcon: Icon(Icons.home_rounded),
          label: 'Accueil',
        ),
        NavigationDestination(
          icon: Icon(Icons.auto_stories_rounded),
          selectedIcon: Icon(Icons.auto_stories_rounded),
          label: 'Résumés',
        ),
        NavigationDestination(
          icon: Icon(Icons.verified_rounded),
          selectedIcon: Icon(Icons.verified_rounded),
          label: 'Validation',
        ),
        NavigationDestination(
          icon: Icon(Icons.shopping_bag_rounded),
          selectedIcon: Icon(Icons.shopping_bag_rounded),
          label: 'Mes Achats',
        ),
        NavigationDestination(
          icon: Icon(Icons.quiz_rounded),
          selectedIcon: Icon(Icons.quiz_rounded),
          label: 'Exercices',
        ),
      ];
    }
    return const [
      NavigationDestination(
        icon: Icon(Icons.home_rounded),
        selectedIcon: Icon(Icons.home_rounded),
        label: 'Accueil',
      ),
      NavigationDestination(
        icon: Icon(Icons.auto_stories_rounded),
        selectedIcon: Icon(Icons.auto_stories_rounded),
        label: 'Résumés',
      ),
      NavigationDestination(
        icon: Icon(Icons.shopping_bag_rounded),
        selectedIcon: Icon(Icons.shopping_bag_rounded),
        label: 'Mes Achats',
      ),
      NavigationDestination(
        icon: Icon(Icons.quiz_rounded),
        selectedIcon: Icon(Icons.quiz_rounded),
        label: 'Exercices',
      ),
    ];
  }

  int get _exercisesIndex => _userRole == 'CP' ? 4 : 3;

  /// Construit les destinations avec les badges
  List<NavigationDestination> _buildDestinations(WidgetRef ref) {
    final purchaseBadgeCount = ref.watch(purchaseBadgeCountProvider);
    final validatedSummariesBadgeCount = ref.watch(validatedSummariesBadgeProvider);
    final createdSummariesBadgeCount = ref.watch(createdSummariesBadgeProvider);
    
    if (_userRole == 'CP') {
      return [
        const NavigationDestination(
          icon: Icon(Icons.home_rounded),
          selectedIcon: Icon(Icons.home_rounded),
          label: 'Accueil',
        ),
        NavigationDestination(
          icon: BadgeIcon(
            icon: Icons.auto_stories_rounded,
            badgeCount: validatedSummariesBadgeCount,
            badgeColor: Colors.red,
            badgeTextColor: Colors.white,
          ),
          selectedIcon: BadgeIcon(
            icon: Icons.auto_stories_rounded,
            badgeCount: validatedSummariesBadgeCount,
            badgeColor: Colors.red,
            badgeTextColor: Colors.white,
          ),
          label: 'Résumés',
        ),
        NavigationDestination(
          icon: BadgeIcon(
            icon: Icons.verified_rounded,
            badgeCount: createdSummariesBadgeCount,
            badgeColor: Colors.orange,
            badgeTextColor: Colors.white,
          ),
          selectedIcon: BadgeIcon(
            icon: Icons.verified_rounded,
            badgeCount: createdSummariesBadgeCount,
            badgeColor: Colors.orange,
            badgeTextColor: Colors.white,
          ),
          label: 'Validation',
        ),
        NavigationDestination(
          icon: BadgeIcon(
            icon: Icons.shopping_bag_rounded,
            badgeCount: purchaseBadgeCount,
            badgeColor: Colors.red,
            badgeTextColor: Colors.white,
          ),
          selectedIcon: BadgeIcon(
            icon: Icons.shopping_bag_rounded,
            badgeCount: purchaseBadgeCount,
            badgeColor: Colors.red,
            badgeTextColor: Colors.white,
          ),
          label: 'Mes Achats',
        ),
        const NavigationDestination(
          icon: Icon(Icons.quiz_rounded),
          selectedIcon: Icon(Icons.quiz_rounded),
          label: 'Exercices',
        ),
      ];
    }
    
    return [
      const NavigationDestination(
        icon: Icon(Icons.home_rounded),
        selectedIcon: Icon(Icons.home_rounded),
        label: 'Accueil',
      ),
      NavigationDestination(
        icon: BadgeIcon(
          icon: Icons.auto_stories_rounded,
          badgeCount: validatedSummariesBadgeCount,
          badgeColor: Colors.red,
          badgeTextColor: Colors.white,
        ),
        selectedIcon: BadgeIcon(
          icon: Icons.auto_stories_rounded,
          badgeCount: validatedSummariesBadgeCount,
          badgeColor: Colors.red,
          badgeTextColor: Colors.white,
        ),
        label: 'Résumés',
      ),
      NavigationDestination(
        icon: BadgeIcon(
          icon: Icons.shopping_bag_rounded,
          badgeCount: purchaseBadgeCount,
          badgeColor: Colors.red,
          badgeTextColor: Colors.white,
        ),
        selectedIcon: BadgeIcon(
          icon: Icons.shopping_bag_rounded,
          badgeCount: purchaseBadgeCount,
          badgeColor: Colors.red,
          badgeTextColor: Colors.white,
        ),
        label: 'Mes Achats',
      ),
      const NavigationDestination(
        icon: Icon(Icons.quiz_rounded),
        selectedIcon: Icon(Icons.quiz_rounded),
        label: 'Exercices',
      ),
    ];
  }

  @override
  void initState() {
    super.initState();
    _loadUserProfile();
    // Invalider les providers de données pour garantir des données fraîches après login
    Future.microtask(() {
      ref.invalidate(summariesProvider);
      ref.read(purchasedSummariesProvider.notifier).refresh();
      ref.read(purchaseBadgeCountProvider.notifier).loadBadgeCount();
      ref.read(validatedSummariesBadgeProvider.notifier).refreshBadge();
      ref.read(createdSummariesBadgeProvider.notifier).refreshBadge();
    });
    // Écouter les nouvelles notifications pour rafraîchir les badges
    NotificationService().addNewNotifListener(_onNewNotification);
  }

  @override
  void dispose() {
    NotificationService().removeNewNotifListener(_onNewNotification);
    super.dispose();
  }

  /// Appelé quand une nouvelle notification arrive (FCM ou polling)
  void _onNewNotification() {
    debugPrint('🔔 [Nav] Nouvelle notification → rafraîchir les badges');
    // Rafraîchir tous les badges (ils comptent les items après lastViewed)
    ref.read(validatedSummariesBadgeProvider.notifier).refreshBadge();
    ref.read(createdSummariesBadgeProvider.notifier).refreshBadge();
    ref.read(purchaseBadgeCountProvider.notifier).loadBadgeCount();
  }

  Future<void> _loadUserProfile() async {
    try {
      final profile = await _apiService.getUserProfile();
      final role = profile['profile']?['groupe'] ?? 'ETUDIANT';
      final cpOnboardingCompleted =
          profile['profile']?['cp_onboarding_completed'] == true;
      setState(() {
        _userRole = role;
        _isLoadingProfile = false;
        _purchasesTabIndex = _userRole == 'CP' ? 3 : 2;
      });
      // Première utilisation du CP (non encore finalisée) : lancer l'onboarding.
      // Décision SYNCHRONE depuis le profil déjà chargé — on évite un second
      // appel asynchrone différé dont la réponse, datant d'avant la
      // finalisation, pourrait réafficher le flux après coup.
      if (role == 'CP' && !cpOnboardingCompleted) {
        _openCPOnboarding();
      }
    } catch (e) {
      setState(() {
        _userRole = 'ETUDIANT';
        _isLoadingProfile = false;
        _purchasesTabIndex = 2;
      });
    }
  }

  /// Ouvre le flux d'onboarding CP — une seule instance à la fois.
  ///
  /// [Navigator.push] ne se termine qu'au pop de la route : tant que le flux
  /// est affiché, [_cpCheckInFlight] reste vrai et toute tentative concurrente
  /// est ignorée → jamais deux CPOnboardingFlow empilés dans la pile.
  Future<void> _openCPOnboarding() async {
    if (_cpCheckInFlight || !mounted) return;
    _cpCheckInFlight = true;
    try {
      await Navigator.of(context).push(
        MaterialPageRoute(
          fullscreenDialog: true,
          builder: (_) => const CPOnboardingFlow(),
        ),
      );
    } catch (_) {
      // Silencieux : si la navigation échoue on n'interrompt pas l'utilisateur
    } finally {
      _cpCheckInFlight = false;
    }
  }

  /// Re-vérifie (serveur) si l'onboarding CP doit s'afficher et le lance.
  /// Public : appelé après acceptation d'une demande CP (rafraîchissement) pour
  /// afficher l'onboarding sans redémarrer l'app.
  Future<void> checkCPOnboarding() async {
    try {
      final status = await _apiService.getOnboardingStatus();
      // Si le backend dit « déjà finalisé » (réponse en vol obtenue APRÈS une
      // finalisation), on ne pousse plus rien — l'auto-garde du flow fait le
      // reste pour tout flux déjà ouvert par erreur.
      if (status['is_first_use'] != true || !mounted) return;
      await _openCPOnboarding();
    } catch (_) {
      // Silencieux : si l'API échoue on n'interrompt pas l'utilisateur
    }
  }

  @override
  Widget build(BuildContext context) {
    // Source de vérité RÉACTIVE du rôle : on écoute authProvider (chaque
    // rafraîchissement global crée un nouvel état → ce build se rejoue) et on
    // resynchronise _userRole. Un CP accepté voit donc immédiatement ses
    // 5 onglets (4 → 5) sans déconnexion ni redémarrage.
    final authState = ref.watch(authProvider);
    // `valueOrNull` : en chargement ou en erreur le rôle est simplement
    // « inconnu » (null) — on garde le rôle déjà connu au lieu de faire
    // planter le build (contrairement à `value`, qui relance l'erreur).
    final authRole = authState.valueOrNull?.groupe;
    if (authRole != null && authRole != _userRole) {
      _userRole = authRole;
    }
    // Sécurité d'index : si le rôle a réduit le nombre d'onglets, ramener
    // l'onglet courant dans les bornes (après la frame, hors build).
    final tabCount = _userRole == 'CP' ? 5 : 4;
    if (_currentIndex >= tabCount) {
      final maxIndex = tabCount - 1;
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (mounted && _currentIndex >= tabCount) {
          setState(() => _currentIndex = maxIndex);
        }
      });
    }

    if (_isLoadingProfile) {
      return const Scaffold(
        body: Center(child: CircularProgressIndicator()),
      );
    }

    return Scaffold(
      body: IndexedStack(
        index: _currentIndex,
        children: _screens,
      ),
      bottomNavigationBar: Container(
        decoration: BoxDecoration(
          color: Theme.of(context).navigationBarTheme.backgroundColor,
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.06),
              blurRadius: 20,
              offset: const Offset(0, -4),
            ),
          ],
        ),
        child: SafeArea(
          child: NavigationBar(
            selectedIndex: _currentIndex,
            onDestinationSelected: (index) async {
              debugPrint('📍 [Nav] Onglet sélectionné: $index (role: $_userRole)');
              // Rafraîchir les données de l'onglet sélectionné
              switch (index) {
                case 0:
                  ref.read(homeRefreshProvider.notifier).state++;
                  break;
                case 1:
                  ref.read(summariesRefreshProvider.notifier).state++;
                  break;
                case 2:
                  if (_userRole == 'CP') {
                    ref.read(summariesRefreshProvider.notifier).state++;
                  } else {
                    ref.read(purchasesRefreshProvider.notifier).state++;
                  }
                  break;
                case 3:
                  if (_userRole == 'CP') {
                    ref.read(purchasesRefreshProvider.notifier).state++;
                  } else {
                    ref.read(exercisesRefreshProvider.notifier).state++;
                  }
                  break;
                case 4:
                  ref.read(exercisesRefreshProvider.notifier).state++;
                  break;
              }
              // Réinitialiser les badges à la consultation de l'onglet
              // IMPORTANT: NE PAS appeler refreshBadge() juste après resetBadge()
              // car cela annulerait le reset. resetBadge() enregistre maintenant
              // un timestamp → refreshBadge() futur ne comptera que les NOUVEAUX items.
              if (_userRole == 'CP') {
                // CP: index 1 = Résumés, index 2 = Validation, index 3 = Mes Achats
                if (index == 1) {
                  debugPrint('🔵 [Nav] Reset badge Résumés (CP)');
                  await ref.read(validatedSummariesBadgeProvider.notifier).resetBadge();
                } else if (index == 2) {
                  debugPrint('🟠 [Nav] Reset badge Validation (CP)');
                  await ref.read(createdSummariesBadgeProvider.notifier).resetBadge();
                } else if (index == 3) {
                  debugPrint('🔴 [Nav] Reset badge Achats (CP)');
                  await ref.read(purchaseBadgeCountProvider.notifier).resetBadge();
                }
              } else {
                // Étudiant: index 1 = Résumés, index 2 = Mes Achats
                if (index == 1) {
                  debugPrint('🔵 [Nav] Reset badge Résumés (Étudiant)');
                  await ref.read(validatedSummariesBadgeProvider.notifier).resetBadge();
                } else if (index == 2) {
                  debugPrint('🔴 [Nav] Reset badge Achats (Étudiant)');
                  await ref.read(purchaseBadgeCountProvider.notifier).resetBadge();
                }
              }
              setState(() {
                _currentIndex = index;
              });
            },
            destinations: _buildDestinations(ref),
            elevation: 0,
          ),
        ),
      ),
    );
  }
}

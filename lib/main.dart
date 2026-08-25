import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:resume_plus_clean/features/splash/screens/splash_screen.dart';
import 'package:resume_plus_clean/features/app/screens/main_navigation_screen.dart';
import 'package:resume_plus_clean/features/auth/screens/phone_login_screen.dart';
import 'package:resume_plus_clean/features/auth/screens/profile_completion_screen.dart';
import 'package:resume_plus_clean/features/settings/providers/theme_provider.dart';
import 'package:resume_plus_clean/services/screen_security_service.dart';
import 'package:resume_plus_clean/services/snackbar_service.dart';
import 'package:resume_plus_clean/theme/app_theme.dart';
import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:intl/intl.dart';
import 'package:intl/date_symbol_data_local.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:resume_plus_clean/services/fcm_service.dart';
import 'package:resume_plus_clean/services/badge_service.dart';
import 'package:resume_plus_clean/features/auth/providers/auth_provider.dart' hide apiServiceProvider;
import 'package:resume_plus_clean/features/home/providers/summary_provider.dart';
import 'package:resume_plus_clean/features/notifications/providers/notification_provider.dart';
import 'package:resume_plus_clean/features/summaries/providers/purchased_summaries_provider.dart' hide apiServiceProvider;
import 'package:resume_plus_clean/providers/purchase_badge_provider.dart';
import 'package:resume_plus_clean/features/subscriptions/providers/subscription_provider.dart';
import 'package:resume_plus_clean/features/subscriptions/providers/service_provider.dart';
import 'package:resume_plus_clean/features/exercises/providers/personalized_exercise_provider.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  Intl.defaultLocale = 'fr_FR';
  await initializeDateFormatting('fr_FR', null);

  // 🔥 Initialiser Firebase
  try {
    await Firebase.initializeApp();
    // Initialiser FCM uniquement sur mobile (pas web)
    if (!kIsWeb) {
      await FcmService().initialize();
      // 🔴 Initialiser le badge d'icône (compteur de notifications)
      await BadgeService().initialize();
    }
  } catch (e) {
    print('⚠️ Firebase init error (non bloquant): $e');
  }

  // Les restrictions d'orientation ont été retirées (exigence Google Play
  // Android 16 / grands écrans) : l'app s'adapte à toutes les orientations.
  if (!kIsWeb) {
    // 🔒 Initialiser la protection contre les captures d'écran globalement
    try {
      await ScreenSecurityService.enableGlobalScreenSecurity();
      print('🔒 Protection contre les captures d\'écran activée globalement');
    } catch (e) {
      print('⚠️ Erreur lors de l\'initialisation de la protection d\'écran: $e');
    }
  }

  runApp(const ProviderScope(child: MyApp()));
}

class MyApp extends ConsumerWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final themeMode = ref.watch(themeModeProvider);

    // Isolation des données entre utilisateurs : quand l'utilisateur
    // authentifié change (login, logout, changement de compte sur le même
    // téléphone), on invalide TOUS les providers dépendants de l'utilisateur
    // pour que l'utilisateur suivant ne voie JAMAIS les données du précédent.
    ref.listen(authProvider, (prev, next) {
      final prevId = prev?.value?.id;
      final nextId = next.value?.id;
      if (prevId != nextId) {
        debugPrint('🔄 [Root] Utilisateur changé ($prevId → $nextId) — invalidation des données');
        // Vider la session API en mémoire (token + caches universités/filières)
        ref.read(apiServiceProvider).clearSession();
        ref.invalidate(summariesProvider);
        ref.invalidate(validatedSummariesBadgeProvider);
        ref.invalidate(createdSummariesBadgeProvider);
        ref.invalidate(unreadCountProvider);
        ref.invalidate(notificationsProvider);
        ref.invalidate(purchasedSummariesProvider);
        ref.invalidate(purchaseHistoryProvider);
        ref.invalidate(purchaseBadgeCountProvider);
        ref.invalidate(subscriptionsProvider);
        ref.invalidate(servicesProvider);
        ref.invalidate(personalizedExerciseProvider);
        ref.invalidate(personalizedExerciseAttemptsProvider);
        ref.read(searchQueryProvider.notifier).state = '';
        // Incrémenter le compteur de session pour les écrans existants
        ref.read(userSessionVersionProvider.notifier).state++;
      }
    });

    return MaterialApp(
      title: 'Résumé+',
      theme: AppTheme.lightTheme,
      darkTheme: AppTheme.darkTheme,
      themeMode: themeMode,
      debugShowCheckedModeBanner: false,
      scaffoldMessengerKey: SnackbarService.scaffoldMessengerKey,
      locale: const Locale('fr', 'FR'),
      supportedLocales: const [
        Locale('fr', 'FR'),
        Locale('en', 'US'),
      ],
      localizationsDelegates: const [
        GlobalMaterialLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
      ],
      home: const SplashScreen(),
      routes: {
        '/login': (context) => const PhoneLoginScreen(),
        '/main': (context) => MainNavigationScreen(key: MainNavigationScreen.navKey),
        '/profile-completion': (context) => const ProfileCompletionScreen(),
      },
    );
  }
}

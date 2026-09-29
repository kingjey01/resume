import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:resume_plus_clean/features/auth/providers/auth_provider.dart';

/// Résumés déjà consultés par l'utilisateur connecté (tache34, point 1).
///
/// Choix d'implémentation :
/// - **100 % Flutter** : aucun champ « vu » n'existe côté backend (ni sur
///   `Summary`, ni via un modèle de jonction `user × summary`), et le besoin
///   est explicitement front-end.
/// - **Clé propre à l'utilisateur** (`seen_summaries_user_<id>`) : sur un même
///   téléphone, un second compte ne doit pas hériter des résumés déjà vus par
///   le premier (même précaution que `StorageService.resetGeneralOnboarding`).
/// - **Pas d'état parallèle aux données** : on ne stocke que des identifiants.
///   La liste, le cache et les badges continuent de venir de `summariesProvider`
///   / `purchasedSummariesProvider` — rien n'est invalidé ni rechargé.
///
/// L'état est réactif : la carte qui affiche un résumé se met à jour d'elle-même
/// au retour de l'écran de détail, sans rechargement réseau.
class SeenSummariesNotifier extends StateNotifier<Set<int>> {
  SeenSummariesNotifier({required this.userId}) : super(const <int>{}) {
    initialLoad = _load();
  }

  /// Se termine quand l'état initial a été relu depuis le stockage.
  /// Exposé pour que les tests puissent attendre le chargement sans `delay`
  /// arbitraire (l'UI, elle, n'en dépend pas : l'ensemble vide est un état
  /// valide qui affiche simplement l'indicateur « non vu »).
  late final Future<void> initialLoad;

  /// Identifiant de l'utilisateur connecté, `null` s'il n'y en a pas.
  /// Dans ce cas rien n'est persisté : l'indicateur reste purement local à la
  /// session en cours.
  final int? userId;

  static const String _keyPrefix = 'seen_summaries_user_';

  String? get _storageKey => userId == null ? null : '$_keyPrefix$userId';

  Future<void> _load() async {
    final key = _storageKey;
    if (key == null) return;
    try {
      final prefs = await SharedPreferences.getInstance();
      final raw = prefs.getStringList(key) ?? const <String>[];
      if (!mounted) return;
      state = raw.map(int.tryParse).whereType<int>().toSet();
    } catch (_) {
      // Stockage indisponible (web privé, quota…) : on garde l'ensemble vide,
      // l'indicateur « non vu » reste affiché. Aucune fonctionnalité bloquée.
    }
  }

  /// Marque un résumé comme consulté. Idempotent.
  Future<void> markSeen(int summaryId) async {
    if (state.contains(summaryId)) return;

    // Mise à jour immédiate de l'UI, la persistance suit.
    final updated = {...state, summaryId};
    state = updated;

    final key = _storageKey;
    if (key == null) return;
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setStringList(key, updated.map((id) => '$id').toList());
    } catch (_) {
      // Échec d'écriture : l'indicateur restera « non vu » au prochain
      // démarrage. Sans conséquence fonctionnelle.
    }
  }
}

/// Source unique du statut « déjà vu » pour toutes les cartes de résumé.
///
/// `watch` sur [currentUserProvider] : au changement de compte, un nouveau
/// notifier est créé avec la bonne clé de stockage — le statut suit donc
/// l'utilisateur connecté. (`User` compare par `id`, donc un simple
/// rafraîchissement du profil ne recrée pas le notifier.)
final seenSummariesProvider =
    StateNotifierProvider<SeenSummariesNotifier, Set<int>>((ref) {
  final userId = ref.watch(currentUserProvider)?.id;
  return SeenSummariesNotifier(userId: userId);
});

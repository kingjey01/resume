import 'package:flutter_riverpod/flutter_riverpod.dart';

/// Providers de rafraîchissement pour chaque onglet de navigation.
/// Incrémentés à chaque sélection d'onglet pour forcer le rechargement des données.

final homeRefreshProvider = StateProvider<int>((ref) => 0);
final summariesRefreshProvider = StateProvider<int>((ref) => 0);
final purchasesRefreshProvider = StateProvider<int>((ref) => 0);
final exercisesRefreshProvider = StateProvider<int>((ref) => 0);

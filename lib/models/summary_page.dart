import 'package:resume_plus_clean/models/summary.dart';

/// Page paginée de résumés (tâche 60, axe 2).
class SummariesPage {
  final List<Summary> items;
  final int? count;
  final bool hasMore;

  const SummariesPage({
    required this.items,
    this.count,
    required this.hasMore,
  });
}

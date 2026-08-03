import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import 'package:resume_plus_clean/features/home/providers/summary_provider.dart';
import 'package:resume_plus_clean/providers/tab_refresh_provider.dart';
import 'package:resume_plus_clean/features/home/widgets/summary_card.dart';
import 'package:resume_plus_clean/features/summaries/providers/purchased_summaries_provider.dart';
import 'package:resume_plus_clean/features/summaries/widgets/purchased_summary_card.dart';
import 'package:resume_plus_clean/theme/app_theme.dart';
import 'package:resume_plus_clean/widgets/api_error_view.dart';

class AllSummariesScreen extends ConsumerStatefulWidget {
  const AllSummariesScreen({super.key});

  @override
  ConsumerState<AllSummariesScreen> createState() => _AllSummariesScreenState();
}

class _AllSummariesScreenState extends ConsumerState<AllSummariesScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;
  String _searchQuery = '';
  String _filterProfessor = '';
  DateTimeRange? _filterDateRange;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 4, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final topPadding = MediaQuery.of(context).padding.top;

    // Rafraîchir les données à chaque fois qu'on arrive sur l'onglet Résumés
    ref.listen<int>(summariesRefreshProvider, (prev, next) {
      if (prev != next) {
        ref.invalidate(summariesProvider);
        ref.invalidate(purchasedSummariesProvider);
      }
    });

    return Scaffold(
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      body: Column(
        children: [
          // Header avec gradient bleu
          Container(
            padding: EdgeInsets.only(top: topPadding + 16, left: 20, right: 20, bottom: 0),
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
                bottomLeft: Radius.circular(24),
                bottomRight: Radius.circular(24),
              ),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Expanded(
                      child: Text(
                        'Résumés',
                        style: theme.textTheme.headlineMedium?.copyWith(
                          color: Colors.white,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                    ),
                    IconButton(
                      onPressed: () {
                        ref.invalidate(summariesProvider);
                        ref.invalidate(purchasedSummariesProvider);
                      },
                      icon: const Icon(Icons.refresh_rounded, color: Colors.white),
                      tooltip: 'Rafraîchir',
                    ),
                  ],
                ),
                const SizedBox(height: 14),
                // Barre de recherche + bouton filtre
                Row(
                  children: [
                    Expanded(
                      child: Container(
                        height: 46,
                        decoration: BoxDecoration(
                          color: Colors.white.withOpacity(0.2),
                          borderRadius: BorderRadius.circular(23),
                        ),
                        child: TextField(
                          style: const TextStyle(color: Colors.white, fontSize: 14),
                          decoration: InputDecoration(
                            hintText: 'Rechercher des résumés...',
                            hintStyle: TextStyle(color: Colors.white.withOpacity(0.7), fontSize: 14),
                            prefixIcon: Icon(Icons.search_rounded, color: Colors.white.withOpacity(0.8)),
                            suffixIcon: _searchQuery.isNotEmpty
                                ? IconButton(
                                    icon: Icon(Icons.close_rounded, color: Colors.white.withOpacity(0.8), size: 20),
                                    onPressed: () => setState(() => _searchQuery = ''),
                                  )
                                : null,
                            border: InputBorder.none,
                            enabledBorder: InputBorder.none,
                            focusedBorder: InputBorder.none,
                            contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                            filled: false,
                          ),
                          onChanged: (value) => setState(() => _searchQuery = value),
                        ),
                      ),
                    ),
                    const SizedBox(width: 8),
                    // Bouton filtres avancés
                    GestureDetector(
                      onTap: () => _showFilterSheet(context),
                      child: Container(
                        width: 46,
                        height: 46,
                        decoration: BoxDecoration(
                          color: _hasActiveFilters
                              ? Colors.white
                              : Colors.white.withOpacity(0.2),
                          borderRadius: BorderRadius.circular(23),
                        ),
                        child: Icon(
                          Icons.tune_rounded,
                          size: 20,
                          color: _hasActiveFilters
                              ? AppTheme.primaryBlue
                              : Colors.white,
                        ),
                      ),
                    ),
                  ],
                ),
                // Chips filtres actifs
                if (_hasActiveFilters) ...[  
                  const SizedBox(height: 8),
                  SizedBox(
                    height: 28,
                    child: ListView(
                      scrollDirection: Axis.horizontal,
                      children: [
                        if (_filterProfessor.isNotEmpty)
                          _buildFilterChip(
                            label: _filterProfessor,
                            icon: Icons.school_rounded,
                            onRemove: () => setState(() => _filterProfessor = ''),
                          ),
                        if (_filterDateRange != null)
                          _buildFilterChip(
                            label:
                                '${DateFormat('dd/MM').format(_filterDateRange!.start)} – ${DateFormat('dd/MM/yy').format(_filterDateRange!.end)}',
                            icon: Icons.calendar_today_rounded,
                            onRemove: () => setState(() => _filterDateRange = null),
                          ),
                      ],
                    ),
                  ),
                ],
                const SizedBox(height: 14),
                // Tabs
                TabBar(
                  controller: _tabController,
                  isScrollable: true,
                  labelColor: Colors.white,
                  unselectedLabelColor: Colors.white.withOpacity(0.6),
                  indicatorColor: Colors.white,
                  indicatorWeight: 3,
                  indicatorSize: TabBarIndicatorSize.label,
                  dividerColor: Colors.transparent,
                  tabAlignment: TabAlignment.start,
                  labelStyle: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600),
                  unselectedLabelStyle: const TextStyle(fontSize: 13, fontWeight: FontWeight.w500),
                  tabs: const [
                    Tab(text: 'Tous'),
                    Tab(text: 'Gratuits'),
                    Tab(text: 'Payants'),
                    Tab(text: 'Récents'),
                  ],
                ),
              ],
            ),
          ),

          // Contenu des onglets
          Expanded(
            child: TabBarView(
              controller: _tabController,
              children: [
                _buildAllSummariesTab(),
                _buildFreeSummariesTab(),
                _buildPaidSummariesTab(),
                _buildRecentSummariesTab(),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildAllSummariesTab() {
    final summariesAsync = ref.watch(summariesProvider);

    return RefreshIndicator(
      onRefresh: () async {
        ref.invalidate(summariesProvider);
      },
      child: summariesAsync.when(
        data: (summaries) {
          final filteredSummaries = _filterSummaries(summaries);
          
          if (filteredSummaries.isEmpty) {
            return _buildEmptyState(
              icon: Icons.description_outlined,
              title: _searchQuery.isNotEmpty 
                  ? 'Aucun résumé trouvé'
                  : 'Aucun résumé disponible',
              subtitle: _searchQuery.isNotEmpty
                  ? 'Essayez avec d\'autres mots-clés'
                  : 'Les résumés apparaîtront ici',
            );
          }

          return ListView.builder(
            padding: const EdgeInsets.fromLTRB(20, 16, 20, 20),
            itemCount: filteredSummaries.length,
            itemBuilder: (context, index) {
              return Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: SummaryCard(summary: filteredSummaries[index]),
              );
            },
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, stack) => ApiErrorView(
          error: error,
          onRetry: () => ref.invalidate(summariesProvider),
        ),
      ),
    );
  }

  Widget _buildFreeSummariesTab() {
    final summariesAsync = ref.watch(summariesProvider);

    return RefreshIndicator(
      onRefresh: () async {
        ref.invalidate(summariesProvider);
      },
      child: summariesAsync.when(
        data: (summaries) {
          final freeSummaries = _filterSummaries(
            summaries.where((s) => s.isFree).toList()
          );
          
          if (freeSummaries.isEmpty) {
            return _buildEmptyState(
              icon: Icons.free_breakfast,
              title: 'Aucun résumé gratuit',
              subtitle: 'Les résumés gratuits apparaîtront ici',
            );
          }

          return ListView.builder(
            padding: const EdgeInsets.fromLTRB(20, 16, 20, 20),
            itemCount: freeSummaries.length,
            itemBuilder: (context, index) {
              return Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: SummaryCard(summary: freeSummaries[index]),
              );
            },
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, stack) => ApiErrorView(
          error: error,
          onRetry: () => ref.invalidate(summariesProvider),
        ),
      ),
    );
  }

  Widget _buildPaidSummariesTab() {
    final summariesAsync = ref.watch(summariesProvider);

    return RefreshIndicator(
      onRefresh: () async {
        ref.invalidate(summariesProvider);
      },
      child: summariesAsync.when(
        data: (summaries) {
          final paidSummaries = _filterSummaries(
            summaries.where((s) => !s.isFree).toList()
          );
          
          if (paidSummaries.isEmpty) {
            return _buildEmptyState(
              icon: Icons.attach_money,
              title: 'Aucun résumé payant',
              subtitle: 'Les résumés payants apparaîtront ici',
            );
          }

          return ListView.builder(
            padding: const EdgeInsets.fromLTRB(20, 16, 20, 20),
            itemCount: paidSummaries.length,
            itemBuilder: (context, index) {
              return Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: SummaryCard(summary: paidSummaries[index]),
              );
            },
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, stack) => ApiErrorView(
          error: error,
          onRetry: () => ref.invalidate(summariesProvider),
        ),
      ),
    );
  }

  Widget _buildRecentSummariesTab() {
    final summariesAsync = ref.watch(summariesProvider);

    return RefreshIndicator(
      onRefresh: () async {
        ref.invalidate(summariesProvider);
      },
      child: summariesAsync.when(
        data: (summaries) {
          final recentSummaries = _filterSummaries(summaries)
            ..sort((a, b) => b.createdAt.compareTo(a.createdAt));
          
          if (recentSummaries.isEmpty) {
            return _buildEmptyState(
              icon: Icons.access_time,
              title: 'Aucun résumé récent',
              subtitle: 'Les résumés récents apparaîtront ici',
            );
          }

          return ListView.builder(
            padding: const EdgeInsets.fromLTRB(20, 16, 20, 20),
            itemCount: recentSummaries.length,
            itemBuilder: (context, index) {
              return Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: SummaryCard(summary: recentSummaries[index]),
              );
            },
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, stack) => ApiErrorView(
          error: error,
          onRetry: () => ref.invalidate(summariesProvider),
        ),
      ),
    );
  }

  bool get _hasActiveFilters => _filterProfessor.isNotEmpty || _filterDateRange != null;

  List<dynamic> _filterSummaries(List<dynamic> summaries) {
    return summaries.where((summary) {
      // Filtre texte (titre + contenu)
      if (_searchQuery.isNotEmpty) {
        final query = _searchQuery.toLowerCase();
        final title = (summary.title ?? '').toLowerCase();
        final content = (summary.content ?? '').toLowerCase();
        final subject = (summary.subject ?? '').toLowerCase();
        if (!title.contains(query) && !content.contains(query) && !subject.contains(query)) {
          return false;
        }
      }
      // Filtre professeur
      if (_filterProfessor.isNotEmpty) {
        final prof = (summary.professorName ?? '').toLowerCase();
        if (!prof.contains(_filterProfessor.toLowerCase())) return false;
      }
      // Filtre date
      if (_filterDateRange != null) {
        final date = summary.createdAt as DateTime;
        final start = _filterDateRange!.start;
        final end = _filterDateRange!.end.add(const Duration(days: 1));
        if (date.isBefore(start) || date.isAfter(end)) return false;
      }
      return true;
    }).toList();
  }

  Widget _buildFilterChip({
    required String label,
    required IconData icon,
    required VoidCallback onRemove,
  }) {
    return Container(
      margin: const EdgeInsets.only(right: 6),
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.25),
        borderRadius: BorderRadius.circular(14),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 12, color: Colors.white),
          const SizedBox(width: 4),
          Text(label, style: const TextStyle(color: Colors.white, fontSize: 11, fontWeight: FontWeight.w600)),
          const SizedBox(width: 4),
          GestureDetector(
            onTap: onRemove,
            child: const Icon(Icons.close_rounded, size: 12, color: Colors.white),
          ),
        ],
      ),
    );
  }

  void _showFilterSheet(BuildContext context) {
    final theme = Theme.of(context);
    String tempProfessor = _filterProfessor;
    DateTimeRange? tempDateRange = _filterDateRange;
    final profController = TextEditingController(text: tempProfessor);

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setSheetState) => Container(
          padding: EdgeInsets.only(
            left: 20, right: 20, top: 20,
            bottom: MediaQuery.of(ctx).viewInsets.bottom + 24,
          ),
          decoration: BoxDecoration(
            color: theme.colorScheme.surface,
            borderRadius: const BorderRadius.vertical(top: Radius.circular(24)),
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Poignée
              Center(
                child: Container(
                  width: 40, height: 4,
                  decoration: BoxDecoration(
                    color: theme.colorScheme.onSurface.withOpacity(0.15),
                    borderRadius: BorderRadius.circular(2),
                  ),
                ),
              ),
              const SizedBox(height: 16),
              Row(
                children: [
                  Text('Filtres avancés', style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700)),
                  const Spacer(),
                  if (tempProfessor.isNotEmpty || tempDateRange != null)
                    TextButton(
                      onPressed: () {
                        setSheetState(() { tempProfessor = ''; tempDateRange = null; profController.clear(); });
                      },
                      child: const Text('Effacer tout', style: TextStyle(fontSize: 12)),
                    ),
                ],
              ),
              const SizedBox(height: 16),
              // Filtre professeur
              Text('Professeur', style: theme.textTheme.labelLarge?.copyWith(fontWeight: FontWeight.w600)),
              const SizedBox(height: 8),
              TextField(
                controller: profController,
                decoration: InputDecoration(
                  hintText: 'Nom du professeur...',
                  prefixIcon: const Icon(Icons.school_rounded, size: 18),
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                  contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                  isDense: true,
                ),
                onChanged: (v) => setSheetState(() => tempProfessor = v),
              ),
              const SizedBox(height: 16),
              // Filtre date
              Text('Période', style: theme.textTheme.labelLarge?.copyWith(fontWeight: FontWeight.w600)),
              const SizedBox(height: 8),
              GestureDetector(
                onTap: () async {
                  final picked = await showDateRangePicker(
                    context: ctx,
                    firstDate: DateTime(2020),
                    lastDate: DateTime.now(),
                    initialDateRange: tempDateRange,
                    builder: (context, child) => Theme(
                      data: Theme.of(context).copyWith(
                        colorScheme: Theme.of(context).colorScheme.copyWith(primary: AppTheme.primaryBlue),
                      ),
                      child: child!,
                    ),
                  );
                  if (picked != null) setSheetState(() => tempDateRange = picked);
                },
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
                  decoration: BoxDecoration(
                    border: Border.all(color: theme.colorScheme.outline),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Row(
                    children: [
                      Icon(Icons.calendar_today_rounded, size: 18, color: AppTheme.primaryBlue),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Text(
                          tempDateRange == null
                              ? 'Choisir une période...'
                              : '${DateFormat('dd/MM/yyyy').format(tempDateRange!.start)}  →  ${DateFormat('dd/MM/yyyy').format(tempDateRange!.end)}',
                          style: theme.textTheme.bodyMedium?.copyWith(
                            color: tempDateRange == null
                                ? theme.colorScheme.onSurface.withOpacity(0.5)
                                : theme.colorScheme.onSurface,
                          ),
                        ),
                      ),
                      if (tempDateRange != null)
                        GestureDetector(
                          onTap: () => setSheetState(() => tempDateRange = null),
                          child: Icon(Icons.close_rounded, size: 16, color: theme.colorScheme.onSurface.withOpacity(0.5)),
                        ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 24),
              // Bouton Appliquer
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: () {
                    setState(() {
                      _filterProfessor = tempProfessor.trim();
                      _filterDateRange = tempDateRange;
                    });
                    Navigator.of(ctx).pop();
                  },
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppTheme.primaryBlue,
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(vertical: 14),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                    elevation: 0,
                  ),
                  child: const Text('Appliquer les filtres', style: TextStyle(fontWeight: FontWeight.w600)),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildEmptyState({
    required IconData icon,
    required String title,
    required String subtitle,
  }) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              width: 80,
              height: 80,
              decoration: BoxDecoration(
                color: AppTheme.primaryBlue.withOpacity(0.1),
                shape: BoxShape.circle,
              ),
              child: Icon(icon, size: 36, color: AppTheme.primaryBlue),
            ),
            const SizedBox(height: 20),
            Text(
              title,
              style: const TextStyle(
                fontSize: 17,
                fontWeight: FontWeight.w600,
                color: AppTheme.textPrimary,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              subtitle,
              style: const TextStyle(color: AppTheme.textLight, fontSize: 14),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildPurchasedSummariesTab() {
    final purchasedSummariesAsync = ref.watch(purchasedSummariesProvider);

    return RefreshIndicator(
      onRefresh: () async {
        ref.invalidate(purchasedSummariesProvider);
      },
      child: purchasedSummariesAsync.when(
        data: (purchasedSummaries) {
          final filteredPurchased = _filterPurchasedSummaries(purchasedSummaries);
          
          if (filteredPurchased.isEmpty) {
            return _buildEmptyState(
              icon: Icons.shopping_bag_outlined,
              title: _searchQuery.isNotEmpty 
                  ? 'Aucun achat trouvé'
                  : 'Aucun résumé acheté',
              subtitle: _searchQuery.isNotEmpty
                  ? 'Essayez avec d\'autres mots-clés'
                  : 'Vos résumés achetés apparaîtront ici',
            );
          }

          return ListView.builder(
            padding: const EdgeInsets.all(16),
            itemCount: filteredPurchased.length,
            itemBuilder: (context, index) {
              final purchase = filteredPurchased[index];
              return PurchasedSummaryCard(purchase: purchase);
            },
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, stack) => ApiErrorView(
          error: error,
          onRetry: () => ref.invalidate(purchasedSummariesProvider),
        ),
      ),
    );
  }

  List<dynamic> _filterPurchasedSummaries(List<dynamic> purchases) {
    if (_searchQuery.isEmpty) return purchases;
    
    return purchases.where((purchase) {
      final title = purchase.summaryTitle?.toLowerCase() ?? '';
      final query = _searchQuery.toLowerCase();
      
      return title.contains(query);
    }).toList();
  }

  @override
  void setState(VoidCallback fn) {
    if (mounted) super.setState(fn);
  }
}

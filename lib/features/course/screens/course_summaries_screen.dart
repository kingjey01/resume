import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:resume_plus_clean/models/summary.dart' as model;
import 'package:resume_plus_clean/services/api_service.dart';
import 'package:resume_plus_clean/features/home/widgets/summary_card.dart';
import 'package:resume_plus_clean/theme/app_theme.dart';

class CourseSummariesScreen extends ConsumerStatefulWidget {
  final int courseId;
  final String courseTitle;
  final String filiere;

  const CourseSummariesScreen({
    super.key,
    required this.courseId,
    required this.courseTitle,
    required this.filiere,
  });

  @override
  ConsumerState<CourseSummariesScreen> createState() => _CourseSummariesScreenState();
}

class _CourseSummariesScreenState extends ConsumerState<CourseSummariesScreen> {
  final ApiService _api = ApiService();
  List<model.Summary> _summaries = [];
  bool _isLoading = true;
  bool _isLoadingMore = false;
  bool _hasMore = false;
  int _page = 1;
  int? _totalCount;
  int _generation = 0;
  Timer? _searchDebounce;
  String? _error;
  String _searchQuery = '';

  @override
  void initState() {
    super.initState();
    _loadSummariesByCourse(reset: true);
  }

  @override
  void dispose() {
    _searchDebounce?.cancel();
    super.dispose();
  }

  Future<void> _loadSummariesByCourse({bool reset = true}) async {
    final generation = ++_generation;
    final targetPage = reset ? 1 : _page + 1;

    setState(() {
      if (reset) {
        _isLoading = true;
        _summaries = [];
        _page = 1;
        _hasMore = false;
      } else {
        _isLoadingMore = true;
      }
      _error = null;
    });

    try {
      final page = await _api.getSummariesPage(
        page: targetPage,
        pageSize: 20,
        courseId: widget.courseId,
        search: _searchQuery.isEmpty ? null : _searchQuery,
      );

      if (!mounted || generation != _generation) return;
      setState(() {
        _summaries = reset ? page.items : [..._summaries, ...page.items];
        _page = targetPage;
        _hasMore = page.hasMore;
        _totalCount = page.count;
        _isLoading = false;
        _isLoadingMore = false;
      });
    } catch (e) {
      if (!mounted || generation != _generation) return;
      setState(() {
        _error = ApiService.getErrorMessage(e);
        _isLoading = false;
        _isLoadingMore = false;
      });
    }
  }

  void _onSearchChanged(String value) {
    setState(() => _searchQuery = value);
    _searchDebounce?.cancel();
    _searchDebounce = Timer(const Duration(milliseconds: 400), () {
      if (mounted) _loadSummariesByCourse(reset: true);
    });
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final topPadding = MediaQuery.of(context).padding.top;

    return Scaffold(
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      body: Column(
        children: [
          // Header bleu courbé
          Container(
            padding: EdgeInsets.only(top: topPadding + 8, left: 20, right: 20, bottom: 20),
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
                    GestureDetector(
                      onTap: () => Navigator.of(context).pop(),
                      child: Container(
                        width: 40, height: 40,
                        decoration: BoxDecoration(
                          color: Colors.white.withOpacity(0.2),
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: const Icon(Icons.arrow_back_rounded, color: Colors.white, size: 22),
                      ),
                    ),
                    const SizedBox(width: 14),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            widget.courseTitle,
                            style: theme.textTheme.titleLarge?.copyWith(color: Colors.white, fontWeight: FontWeight.w700),
                            maxLines: 1, overflow: TextOverflow.ellipsis,
                          ),
                          const SizedBox(height: 2),
                          Text(
                            'Filière ${widget.filiere}',
                            style: TextStyle(color: Colors.white.withOpacity(0.8), fontSize: 13),
                          ),
                        ],
                      ),
                    ),
                    GestureDetector(
                      onTap: () => _loadSummariesByCourse(reset: true),
                      child: Container(
                        width: 40, height: 40,
                        decoration: BoxDecoration(
                          color: Colors.white.withOpacity(0.2),
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: const Icon(Icons.refresh_rounded, color: Colors.white, size: 22),
                      ),
                    ),
                  ],
                ),
                // Barre de recherche pill
                if (!_isLoading &&
                    _error == null &&
                    ((_totalCount ?? 0) > 0 || _searchQuery.isNotEmpty)) ...[
                  const SizedBox(height: 12),
                  Container(
                    height: 44,
                    decoration: BoxDecoration(
                      color: Colors.white.withOpacity(0.2),
                      borderRadius: BorderRadius.circular(22),
                    ),
                    child: TextField(
                      style: const TextStyle(color: Colors.white, fontSize: 14),
                      decoration: InputDecoration(
                        hintText: 'Rechercher un résumé...',
                        hintStyle: TextStyle(color: Colors.white.withOpacity(0.7), fontSize: 14),
                        prefixIcon: Icon(Icons.search_rounded, color: Colors.white.withOpacity(0.8)),
                        suffixIcon: _searchQuery.isNotEmpty
                            ? IconButton(
                                icon: Icon(Icons.close_rounded, color: Colors.white.withOpacity(0.8), size: 20),
                                onPressed: () {
                                  setState(() => _searchQuery = '');
                                  _loadSummariesByCourse(reset: true);
                                },
                              )
                            : null,
                        border: InputBorder.none,
                        enabledBorder: InputBorder.none,
                        focusedBorder: InputBorder.none,
                        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 11),
                        filled: false,
                      ),
                      onChanged: _onSearchChanged,
                    ),
                  ),
                ],
                if (!_isLoading &&
                    _error == null &&
                    ((_totalCount ?? 0) > 0 || _searchQuery.isNotEmpty)) ...[
                  const SizedBox(height: 12),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                    decoration: BoxDecoration(
                      color: Colors.white.withOpacity(0.2),
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: Text(
                      '${_totalCount ?? _summaries.length} résumé${(_totalCount ?? _summaries.length) > 1 ? 's' : ''} trouvé${(_totalCount ?? _summaries.length) > 1 ? 's' : ''}',
                      style: const TextStyle(color: Colors.white, fontSize: 13, fontWeight: FontWeight.w500),
                    ),
                  ),
                ],
              ],
            ),
          ),

          // Contenu
          Expanded(
            child: _isLoading
                ? const Center(
                    child: CircularProgressIndicator(color: AppTheme.primaryBlue))
                : _error != null
                    ? _buildErrorState()
                    : _summaries.isEmpty
                        ? (_searchQuery.isEmpty
                            ? _buildEmptyState()
                            : _buildSearchEmptyState())
                        : Column(
                            children: [
                              Expanded(
                                child: RefreshIndicator(
                                  onRefresh: () =>
                                      _loadSummariesByCourse(reset: true),
                                  child: LayoutBuilder(
                                    builder: (context, constraints) {
                                      int crossAxisCount;
                                      double childAspectRatio;

                                      if (constraints.maxWidth < 600) {
                                        crossAxisCount = 2;
                                        childAspectRatio = 0.72;
                                      } else if (constraints.maxWidth < 900) {
                                        crossAxisCount = 3;
                                        childAspectRatio = 0.78;
                                      } else if (constraints.maxWidth < 1200) {
                                        crossAxisCount = 4;
                                        childAspectRatio = 0.82;
                                      } else {
                                        crossAxisCount = 5;
                                        childAspectRatio = 0.85;
                                      }

                                      return GridView.builder(
                                        physics:
                                            const AlwaysScrollableScrollPhysics(),
                                        padding: EdgeInsets.fromLTRB(
                                          constraints.maxWidth < 600 ? 16 : 20,
                                          16,
                                          constraints.maxWidth < 600 ? 16 : 20,
                                          20,
                                        ),
                                        gridDelegate:
                                            SliverGridDelegateWithFixedCrossAxisCount(
                                          crossAxisCount: crossAxisCount,
                                          childAspectRatio: childAspectRatio,
                                          crossAxisSpacing:
                                              constraints.maxWidth < 600 ? 8 : 12,
                                          mainAxisSpacing:
                                              constraints.maxWidth < 600 ? 8 : 12,
                                        ),
                                        itemCount: _summaries.length,
                                        itemBuilder: (context, index) {
                                          return SummaryCard(
                                              summary: _summaries[index]);
                                        },
                                      );
                                    },
                                  ),
                                ),
                              ),
                              if (_hasMore) _buildLoadMoreButton(),
                            ],
                          ),
          ),
        ],
      ),
    );
  }

  Widget _buildLoadMoreButton() {
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 0, 20, 20),
      child: SizedBox(
        width: double.infinity,
        child: OutlinedButton.icon(
          onPressed: _isLoadingMore
              ? null
              : () => _loadSummariesByCourse(reset: false),
          icon: _isLoadingMore
              ? const SizedBox(
                  width: 16,
                  height: 16,
                  child: CircularProgressIndicator(strokeWidth: 2),
                )
              : const Icon(Icons.expand_more_rounded),
          label: Text(_isLoadingMore ? 'Chargement...' : 'Charger plus'),
        ),
      ),
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              width: 80, height: 80,
              decoration: BoxDecoration(
                color: AppTheme.primaryBlue.withOpacity(0.1),
                shape: BoxShape.circle,
              ),
              child: const Icon(Icons.book_outlined, size: 36, color: AppTheme.primaryBlue),
            ),
            const SizedBox(height: 20),
            const Text('Aucun résumé disponible', style: TextStyle(fontSize: 17, fontWeight: FontWeight.w600, color: AppTheme.textPrimary)),
            const SizedBox(height: 8),
            Text(
              'Il n\'y a pas encore de résumés pour le cours "${widget.courseTitle}".',
              textAlign: TextAlign.center,
              style: const TextStyle(color: AppTheme.textLight, fontSize: 14),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSearchEmptyState() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              width: 80, height: 80,
              decoration: BoxDecoration(
                color: AppTheme.primaryBlue.withOpacity(0.1),
                shape: BoxShape.circle,
              ),
              child: const Icon(Icons.search_off_rounded, size: 36, color: AppTheme.primaryBlue),
            ),
            const SizedBox(height: 20),
            const Text('Aucun résumé trouvé', style: TextStyle(fontSize: 17, fontWeight: FontWeight.w600, color: AppTheme.textPrimary)),
            const SizedBox(height: 8),
            const Text(
              'Essayez de rechercher avec d\'autres mots-clés.',
              textAlign: TextAlign.center,
              style: TextStyle(color: AppTheme.textLight, fontSize: 14),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildErrorState() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              width: 80, height: 80,
              decoration: BoxDecoration(
                color: AppTheme.error.withOpacity(0.1),
                shape: BoxShape.circle,
              ),
              child: const Icon(Icons.error_outline_rounded, size: 36, color: AppTheme.error),
            ),
            const SizedBox(height: 20),
            Text(_error!, textAlign: TextAlign.center, style: const TextStyle(color: AppTheme.textLight, fontSize: 13)),
            const SizedBox(height: 20),
            ElevatedButton(
              onPressed: () => _loadSummariesByCourse(reset: true),
              child: const Text('Réessayer'),
            ),
          ],
        ),
      ),
    );
  }
}

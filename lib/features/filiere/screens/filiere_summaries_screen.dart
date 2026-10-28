import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:resume_plus_clean/models/summary.dart';
import 'package:resume_plus_clean/services/api_service.dart';
import 'package:resume_plus_clean/features/home/widgets/summary_card.dart';
import 'package:resume_plus_clean/theme/app_theme.dart';

class FiliereSummariesScreen extends ConsumerStatefulWidget {
  final String filiere;
  final String? filiereId;

  const FiliereSummariesScreen({
    super.key, 
    required this.filiere,
    this.filiereId,
  });

  @override
  ConsumerState<FiliereSummariesScreen> createState() => _FiliereSummariesScreenState();
}

class _FiliereSummariesScreenState extends ConsumerState<FiliereSummariesScreen> {
  final ApiService _api = ApiService();
  List<Summary> _summaries = [];
  bool _isLoading = true;
  bool _isLoadingMore = false;
  bool _hasMore = false;
  int _page = 1;
  int? _totalCount;
  int _generation = 0;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadSummariesByFiliere(reset: true);
  }

  Future<void> _loadSummariesByFiliere({bool reset = true}) async {
    final generation = ++_generation;
    final targetPage = reset ? 1 : _page + 1;
    final filiereId = int.tryParse(widget.filiereId ?? '');

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
        filiereId: filiereId,
        filiereNom: filiereId == null ? widget.filiere : null,
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
                      child: Text(
                        'Filière ${widget.filiere}',
                        style: theme.textTheme.titleLarge?.copyWith(color: Colors.white, fontWeight: FontWeight.w700),
                        maxLines: 1, overflow: TextOverflow.ellipsis,
                      ),
                    ),
                    GestureDetector(
                      onTap: () => _loadSummariesByFiliere(reset: true),
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
                if (!_isLoading && _error == null && _summaries.isNotEmpty) ...[
                  const SizedBox(height: 14),
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
                    ? Center(
                        child: Padding(
                          padding: const EdgeInsets.all(32),
                          child: Column(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              Container(
                                width: 80,
                                height: 80,
                                decoration: BoxDecoration(
                                  color: AppTheme.error.withOpacity(0.1),
                                  shape: BoxShape.circle,
                                ),
                                child: const Icon(Icons.error_outline_rounded,
                                    size: 36, color: AppTheme.error),
                              ),
                              const SizedBox(height: 20),
                              Text(
                                _error!,
                                textAlign: TextAlign.center,
                                style: const TextStyle(
                                    color: AppTheme.textLight, fontSize: 13),
                              ),
                              const SizedBox(height: 20),
                              ElevatedButton(
                                onPressed: () =>
                                    _loadSummariesByFiliere(reset: true),
                                child: const Text('Réessayer'),
                              ),
                            ],
                          ),
                        ),
                      )
                    : _summaries.isEmpty
                        ? Center(
                            child: Padding(
                              padding: const EdgeInsets.all(32),
                              child: Column(
                                mainAxisAlignment: MainAxisAlignment.center,
                                children: [
                                  Container(
                                    width: 80,
                                    height: 80,
                                    decoration: BoxDecoration(
                                      color: AppTheme.primaryBlue
                                          .withOpacity(0.1),
                                      shape: BoxShape.circle,
                                    ),
                                    child: const Icon(Icons.school_outlined,
                                        size: 36, color: AppTheme.primaryBlue),
                                  ),
                                  const SizedBox(height: 20),
                                  const Text(
                                    'Aucun résumé disponible',
                                    style: TextStyle(
                                      fontSize: 17,
                                      fontWeight: FontWeight.w600,
                                      color: AppTheme.textPrimary,
                                    ),
                                  ),
                                  const SizedBox(height: 8),
                                  Text(
                                    "Il n'y a pas encore de résumés pour la filière ${widget.filiere}.",
                                    textAlign: TextAlign.center,
                                    style: const TextStyle(
                                        color: AppTheme.textLight,
                                        fontSize: 14),
                                  ),
                                ],
                              ),
                            ),
                          )
                        : Column(
                            children: [
                              Expanded(
                                child: RefreshIndicator(
                                  onRefresh: () =>
                                      _loadSummariesByFiliere(reset: true),
                                  child: GridView.builder(
                                    physics:
                                        const AlwaysScrollableScrollPhysics(),
                                    padding: const EdgeInsets.fromLTRB(
                                        20, 16, 20, 20),
                                    gridDelegate:
                                        const SliverGridDelegateWithFixedCrossAxisCount(
                                      crossAxisCount: 2,
                                      childAspectRatio: 0.75,
                                      crossAxisSpacing: 12,
                                      mainAxisSpacing: 12,
                                    ),
                                    itemCount: _summaries.length,
                                    itemBuilder: (context, index) {
                                      return SummaryCard(
                                          summary: _summaries[index]);
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
              : () => _loadSummariesByFiliere(reset: false),
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
}

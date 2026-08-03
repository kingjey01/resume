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
  List<model.Summary> _summaries = [];
  bool _isLoading = true;
  String? _error;
  String _searchQuery = '';

  @override
  void initState() {
    super.initState();
    _loadSummariesByCourse();
  }

  List<model.Summary> get _filteredSummaries {
    if (_searchQuery.isEmpty) return _summaries;
    return _summaries.where((summary) {
      final title = summary.title?.toLowerCase() ?? '';
      final content = summary.content?.toLowerCase() ?? '';
      final query = _searchQuery.toLowerCase();
      return title.contains(query) || content.contains(query);
    }).toList();
  }

  Future<void> _loadSummariesByCourse() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final apiService = ApiService();
      final allSummaries = await apiService.getSummaries();
      
      final filteredSummaries = allSummaries.where((summary) {
        return summary.courseId == widget.courseId;
      }).toList();

      setState(() {
        _summaries = filteredSummaries;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _error = 'Erreur lors du chargement des résumés: $e';
        _isLoading = false;
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
                      onTap: _loadSummariesByCourse,
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
                if (!_isLoading && _error == null && _summaries.isNotEmpty) ...[
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
                                onPressed: () => setState(() => _searchQuery = ''),
                              )
                            : null,
                        border: InputBorder.none,
                        enabledBorder: InputBorder.none,
                        focusedBorder: InputBorder.none,
                        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 11),
                        filled: false,
                      ),
                      onChanged: (value) => setState(() => _searchQuery = value),
                    ),
                  ),
                ],
                if (!_isLoading && _error == null && _summaries.isNotEmpty) ...[
                  const SizedBox(height: 12),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                    decoration: BoxDecoration(
                      color: Colors.white.withOpacity(0.2),
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: Text(
                      '${_filteredSummaries.length} résumé${_filteredSummaries.length > 1 ? 's' : ''} trouvé${_filteredSummaries.length > 1 ? 's' : ''}',
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
                ? const Center(child: CircularProgressIndicator(color: AppTheme.primaryBlue))
                : _error != null
                    ? _buildErrorState()
                    : _summaries.isEmpty
                        ? _buildEmptyState()
                        : _filteredSummaries.isEmpty
                            ? _buildSearchEmptyState()
                            : LayoutBuilder(
                                builder: (context, constraints) {
                                  // Responsive grid based on screen width
                                  int crossAxisCount;
                                  double childAspectRatio;
                                  
                                  if (constraints.maxWidth < 600) {
                                    // Mobile: 2 columns
                                    crossAxisCount = 2;
                                    childAspectRatio = 0.72;
                                  } else if (constraints.maxWidth < 900) {
                                    // Tablet: 3 columns
                                    crossAxisCount = 3;
                                    childAspectRatio = 0.78;
                                  } else if (constraints.maxWidth < 1200) {
                                    // Small desktop: 4 columns
                                    crossAxisCount = 4;
                                    childAspectRatio = 0.82;
                                  } else {
                                    // Large desktop: 5 columns
                                    crossAxisCount = 5;
                                    childAspectRatio = 0.85;
                                  }
                                  
                                  return GridView.builder(
                                    padding: EdgeInsets.fromLTRB(
                                      constraints.maxWidth < 600 ? 16 : 20,
                                      16,
                                      constraints.maxWidth < 600 ? 16 : 20,
                                      20,
                                    ),
                                    gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
                                      crossAxisCount: crossAxisCount,
                                      childAspectRatio: childAspectRatio,
                                      crossAxisSpacing: constraints.maxWidth < 600 ? 8 : 12,
                                      mainAxisSpacing: constraints.maxWidth < 600 ? 8 : 12,
                                    ),
                                    itemCount: _filteredSummaries.length,
                                    itemBuilder: (context, index) {
                                      return SummaryCard(summary: _filteredSummaries[index]);
                                    },
                                  );
                                },
                              ),
          ),
        ],
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
              onPressed: _loadSummariesByCourse,
              child: const Text('Réessayer'),
            ),
          ],
        ),
      ),
    );
  }
}

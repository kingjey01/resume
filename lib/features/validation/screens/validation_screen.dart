import 'dart:async';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:resume_plus_clean/services/api_service.dart';
import 'package:resume_plus_clean/providers/tab_refresh_provider.dart';
import 'package:resume_plus_clean/features/validation/screens/edit_summary_screen.dart';
import 'package:resume_plus_clean/theme/app_theme.dart';
import 'package:resume_plus_clean/widgets/api_error_view.dart';
import 'package:resume_plus_clean/mixins/error_handler_mixin.dart';

class ValidationScreen extends ConsumerStatefulWidget {
  final int? initialSummaryId;

  const ValidationScreen({super.key, this.initialSummaryId});

  @override
  ConsumerState<ValidationScreen> createState() => _ValidationScreenState();
}

class _ValidationScreenState extends ConsumerState<ValidationScreen> with ErrorHandlerMixin {
  final ApiService _apiService = ApiService();
  final TextEditingController _searchController = TextEditingController();
  List<Map<String, dynamic>> _summaries = [];
  bool _isLoading = true;
  dynamic _error;
  String _filter = 'all'; // 'all', 'validated', 'pending'
  String _searchQuery = '';
  Map<String, dynamic>? _selectedSummary;
  Timer? _debounce;

  @override
  void initState() {
    super.initState();
    _loadSummaries();
  }

  @override
  void dispose() {
    _searchController.dispose();
    _debounce?.cancel();
    super.dispose();
  }

  void _onSearchChanged(String query) {
    // Mettre à jour immédiatement l'UI pour l'icône "clear"
    setState(() {});
    
    if (_debounce?.isActive ?? false) _debounce!.cancel();
    _debounce = Timer(const Duration(milliseconds: 500), () {
      if (mounted) {
        setState(() {
          _searchQuery = query;
        });
        _loadSummaries();
      }
    });
  }

  Future<void> _loadSummaries() async {
    setState(() {
      _isLoading = true;
      _error = null;
      _selectedSummary = null;
    });

    try {
      final data = await _apiService.getSummariesForValidation(
        search: _searchQuery.isNotEmpty ? _searchQuery : null,
      );
      final summariesRaw = data['summaries'] as List<dynamic>? ?? [];
      _summaries = summariesRaw.map((s) => Map<String, dynamic>.from(s as Map)).toList();

      // If initialSummaryId is provided, find and select that summary
      if (widget.initialSummaryId != null) {
        final summary = _summaries.firstWhere(
          (s) => s['id'] == widget.initialSummaryId,
          orElse: () => <String, dynamic>{},
        );
        if (summary.isNotEmpty) {
          setState(() => _selectedSummary = summary);
        }
      }

      setState(() => _isLoading = false);
    } catch (e) {
      setState(() {
        _error = e;
        _isLoading = false;
      });
    }
  }

  Future<void> _loadSummaryById(int summaryId) async {
    setState(() => _isLoading = true);

    try {
      final summary = await _apiService.getSummaryById(summaryId);
      setState(() {
        _selectedSummary = summary.toJson();
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _error = e;
        _isLoading = false;
      });
    }
  }

  List<Map<String, dynamic>> get _filteredSummaries {
    List<Map<String, dynamic>> filtered = _summaries;
    
    // Filtrage local par recherche (pour une réactivité instantanée)
    if (_searchController.text.isNotEmpty) {
      final query = _searchController.text.toLowerCase();
      filtered = filtered.where((s) {
        final titre = (s['titre'] ?? '').toString().toLowerCase();
        final course = (s['course_name'] ?? '').toString().toLowerCase();
        final author = (s['author_name'] ?? '').toString().toLowerCase();
        return titre.contains(query) || course.contains(query) || author.contains(query);
      }).toList();
    }

    // Filtrage par statut
    if (_filter == 'validated') {
      return filtered.where((s) => s['is_validated'] == true).toList();
    } else if (_filter == 'pending') {
      return filtered.where((s) => s['is_validated'] != true).toList();
    }
    return filtered;
  }

  Future<void> _toggleValidation(Map<String, dynamic> summary) async {
    final currentlyValidated = summary['is_validated'] == true;
    final newState = !currentlyValidated;

    try {
      await _apiService.validateSummary(summary['id'], newState);

      setState(() {
        summary['is_validated'] = newState;
      });

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(newState ? 'Résumé validé' : 'Résumé invalidé'),
            backgroundColor: newState ? AppTheme.success : AppTheme.error,
            duration: const Duration(seconds: 2),
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        handleError(e);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final topPadding = MediaQuery.of(context).padding.top;

    // Rafraîchir les données à chaque fois qu'on arrive sur l'onglet Validation
    ref.listen<int>(summariesRefreshProvider, (prev, next) {
      if (prev != next) {
        _loadSummaries();
      }
    });

    // Appliquer le filtre de recherche pour les compteurs
    List<Map<String, dynamic>> searchFiltered = _summaries;
    if (_searchController.text.isNotEmpty) {
      final query = _searchController.text.toLowerCase();
      searchFiltered = _summaries.where((s) {
        final titre = (s['titre'] ?? '').toString().toLowerCase();
        final course = (s['course_name'] ?? '').toString().toLowerCase();
        final author = (s['author_name'] ?? '').toString().toLowerCase();
        return titre.contains(query) || course.contains(query) || author.contains(query);
      }).toList();
    }

    final validatedCount = searchFiltered.where((s) => s['is_validated'] == true).length;
    final pendingCount = searchFiltered.where((s) => s['is_validated'] != true).length;

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
                        color: Colors.white.withOpacity(0.15),
                        borderRadius: BorderRadius.circular(14),
                      ),
                      child: const Icon(Icons.verified_rounded, color: Colors.white, size: 24),
                    ),
                    const SizedBox(width: 14),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Validation',
                            style: Theme.of(context).textTheme.titleLarge?.copyWith(
                              color: Colors.white, fontWeight: FontWeight.w700,
                            ),
                          ),
                          Text(
                            '${searchFiltered.length} résumés',
                            style: TextStyle(color: Colors.white.withOpacity(0.7), fontSize: 12),
                          ),
                        ],
                      ),
                    ),
                    // Refresh button
                    IconButton(
                      onPressed: _isLoading ? null : _loadSummaries,
                      icon: _isLoading
                          ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                          : const Icon(Icons.refresh_rounded, color: Colors.white),
                      tooltip: 'Rafraîchir',
                    ),
                  ],
                ),
                const SizedBox(height: 16),
                // Search Bar (Design cohérent avec la page Résumé)
                Container(
                  height: 48,
                  decoration: BoxDecoration(
                    color: Colors.white.withOpacity(0.2),
                    borderRadius: BorderRadius.circular(24),
                  ),
                  child: TextField(
                    controller: _searchController,
                    onChanged: _onSearchChanged,
                    style: const TextStyle(color: Colors.white, fontSize: 14),
                    cursorColor: Colors.white,
                    decoration: InputDecoration(
                      hintText: 'Rechercher par titre, professeur, matière...',
                      hintStyle: TextStyle(color: Colors.white.withOpacity(0.7), fontSize: 14),
                      prefixIcon: Icon(Icons.search_rounded, color: Colors.white.withOpacity(0.8), size: 20),
                      suffixIcon: _searchController.text.isNotEmpty
                          ? IconButton(
                              icon: Icon(Icons.close_rounded, color: Colors.white.withOpacity(0.8), size: 20),
                              onPressed: () {
                                _searchController.clear();
                                _onSearchChanged('');
                              },
                            )
                          : null,
                      border: InputBorder.none,
                      enabledBorder: InputBorder.none,
                      focusedBorder: InputBorder.none,
                      filled: false,
                      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                    ),
                  ),
                ),
                const SizedBox(height: 16),
                // Stats bar
                Row(
                  children: [
                    _buildStatBadge('Tous', searchFiltered.length, 'all'),
                    const SizedBox(width: 8),
                    _buildStatBadge('Validés', validatedCount, 'validated'),
                    const SizedBox(width: 8),
                    _buildStatBadge('En attente', pendingCount, 'pending'),
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
                    ? ApiErrorView(
                        error: _error,
                        onRetry: _loadSummaries,
                      )
                    : _filteredSummaries.isEmpty
                        ? _buildEmpty()
                        : RefreshIndicator(
                            onRefresh: _loadSummaries,
                            child: ListView.builder(
                              padding: const EdgeInsets.all(20),
                              itemCount: _filteredSummaries.length,
                              itemBuilder: (context, index) {
                                return _buildSummaryCard(_filteredSummaries[index]);
                              },
                            ),
                          ),
          ),
        ],
      ),
    );
  }

  Widget _buildStatBadge(String label, int count, String filterValue) {
    final isActive = _filter == filterValue;
    return GestureDetector(
      onTap: () => setState(() => _filter = filterValue),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
        decoration: BoxDecoration(
          color: isActive ? Colors.white : Colors.white.withOpacity(0.15),
          borderRadius: BorderRadius.circular(20),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              '$count',
              style: TextStyle(
                color: isActive ? AppTheme.primaryBlue : Colors.white,
                fontWeight: FontWeight.w700, fontSize: 13,
              ),
            ),
            const SizedBox(width: 4),
            Text(
              label,
              style: TextStyle(
                color: isActive ? AppTheme.primaryBlue : Colors.white.withOpacity(0.8),
                fontSize: 12, fontWeight: FontWeight.w500,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSummaryCard(Map<String, dynamic> summary) {
    final isValidated = summary['is_validated'] == true;
    final authorType = summary['author_type'] ?? 'cp';
    final isAi = authorType == 'ai';

    final cardColor = Theme.of(context).colorScheme.surface;
    return Container(
      margin: const EdgeInsets.only(bottom: 14),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: cardColor,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: isValidated 
              ? AppTheme.success.withOpacity(0.3) 
              : Theme.of(context).dividerColor.withOpacity(0.1),
          width: isValidated ? 1.5 : 1,
        ),
        boxShadow: AppTheme.softShadow,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              // Author badge
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: isAi
                      ? const Color(0xFF7C3AED).withOpacity(0.1)
                      : AppTheme.primaryBlue.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(
                      isAi ? Icons.smart_toy_rounded : Icons.person_rounded,
                      size: 14,
                      color: isAi ? const Color(0xFF7C3AED) : AppTheme.primaryBlue,
                    ),
                    const SizedBox(width: 4),
                    Text(
                      isAi ? 'IA' : 'CP',
                      style: TextStyle(
                        color: isAi ? const Color(0xFF7C3AED) : AppTheme.primaryBlue,
                        fontSize: 11, fontWeight: FontWeight.w700,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 8),
              // Validation status
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: isValidated ? AppTheme.success.withOpacity(0.1) : AppTheme.error.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(
                      isValidated ? Icons.check_circle_rounded : Icons.pending_rounded,
                      size: 14,
                      color: isValidated ? AppTheme.success : AppTheme.error,
                    ),
                    const SizedBox(width: 4),
                    Text(
                      isValidated ? 'Validé' : 'En attente',
                      style: TextStyle(
                        color: isValidated ? AppTheme.success : AppTheme.error,
                        fontSize: 11, fontWeight: FontWeight.w600,
                      ),
                    ),
                  ],
                ),
              ),
              const Spacer(),
              Text(
                '${(summary['prix'] ?? 0).toString()} FC',
                style: const TextStyle(
                  color: AppTheme.primaryBlue, fontWeight: FontWeight.w700, fontSize: 13,
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Text(
            summary['titre'] ?? 'Sans titre',
            style: TextStyle(
              fontWeight: FontWeight.w600, 
              fontSize: 15,
              color: Theme.of(context).colorScheme.onSurface
            ),
            maxLines: 2, overflow: TextOverflow.ellipsis,
          ),
          const SizedBox(height: 4),
          Text(
            summary['course_name'] ?? '',
            style: TextStyle(
              color: Theme.of(context).colorScheme.onSurface.withOpacity(0.6), 
              fontSize: 12
            ),
          ),
          const SizedBox(height: 4),
          Text(
            'Par ${summary['author_name'] ?? 'Inconnu'}',
            style: TextStyle(
              color: Theme.of(context).colorScheme.onSurface.withOpacity(0.7), 
              fontSize: 12
            ),
          ),
          const SizedBox(height: 14),
          // Action buttons
          Row(
            children: [
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: () {
                    Navigator.of(context).push(
                      MaterialPageRoute(
                        builder: (_) => EditSummaryScreen(summary: summary),
                      ),
                    ).then((_) => _loadSummaries());
                  },
                  icon: const Icon(Icons.edit_rounded, size: 16),
                  label: const Text('Modifier'),
                  style: OutlinedButton.styleFrom(
                    foregroundColor: AppTheme.primaryBlue,
                    side: const BorderSide(color: AppTheme.primaryBlue),
                    padding: const EdgeInsets.symmetric(vertical: 10),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                    textStyle: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600),
                  ),
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: ElevatedButton.icon(
                  onPressed: () => _toggleValidation(summary),
                  icon: Icon(
                    isValidated ? Icons.cancel_rounded : Icons.check_circle_rounded,
                    size: 16,
                  ),
                  label: Text(isValidated ? 'Invalider' : 'Valider'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: isValidated ? AppTheme.error : AppTheme.success,
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(vertical: 10),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                    textStyle: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600),
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildEmpty() {
    final isSearching = _searchQuery.isNotEmpty;
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              width: 80, height: 80,
              decoration: BoxDecoration(
                color: isSearching ? Colors.grey.withOpacity(0.1) : AppTheme.success.withOpacity(0.1),
                shape: BoxShape.circle,
              ),
              child: Icon(
                isSearching ? Icons.search_off_rounded : Icons.verified_rounded,
                size: 36,
                color: isSearching ? Colors.grey : AppTheme.success,
              ),
            ),
            const SizedBox(height: 20),
            Text(
              isSearching ? 'Aucun résultat' : 'Aucun résumé trouvé',
              style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 16),
            ),
            const SizedBox(height: 8),
            Text(
              isSearching
                  ? 'Aucun résumé ne correspond à votre recherche "$_searchQuery".'
                  : 'Il n\'y a aucun résumé correspondant au filtre sélectionné.',
              textAlign: TextAlign.center,
              style: const TextStyle(color: AppTheme.textLight, fontSize: 13),
            ),
            if (isSearching)
              TextButton(
                onPressed: () {
                  _searchController.clear();
                  _onSearchChanged('');
                },
                child: const Text('Effacer la recherche'),
              ),
          ],
        ),
      ),
    );
  }

  @override
  void setState(VoidCallback fn) {
    if (mounted) super.setState(fn);
  }
}

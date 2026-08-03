import 'package:flutter/material.dart';
import 'package:resume_plus_clean/services/api_service.dart';
import 'package:resume_plus_clean/models/course.dart';
import 'package:resume_plus_clean/services/snackbar_service.dart';
import 'package:resume_plus_clean/theme/app_theme.dart';

class CourseSelectionScreen extends StatefulWidget {
  final Function(Course) onCourseSelected;
  
  const CourseSelectionScreen({
    super.key,
    required this.onCourseSelected,
  });

  @override
  State<CourseSelectionScreen> createState() => _CourseSelectionScreenState();
}

class _CourseSelectionScreenState extends State<CourseSelectionScreen> {
  final _apiService = ApiService();
  List<Course> _courses = [];
  bool _isLoading = false;
  String _searchQuery = '';

  @override
  void initState() {
    super.initState();
    _loadCourses();
  }

  Future<void> _loadCourses() async {
    setState(() => _isLoading = true);
    
    try {
      final coursesData = await _apiService.getCourses();
      setState(() {
        _courses = coursesData.map((json) => Course.fromJson(json)).toList();
        _isLoading = false;
      });
    } catch (e) {
      setState(() => _isLoading = false);
      SnackbarService.show('Erreur lors du chargement des cours: $e', isError: true);
    }
  }

  List<Course> get _filteredCourses {
    if (_searchQuery.isEmpty) return _courses;
    return _courses.where((course) =>
      course.nom.toLowerCase().contains(_searchQuery.toLowerCase())
    ).toList();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final topPadding = MediaQuery.of(context).padding.top;
    
    return Scaffold(
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      body: Column(
        children: [
          // Header bleu avec recherche
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
                    Text(
                      'Choisir un cours',
                      style: theme.textTheme.titleLarge?.copyWith(color: Colors.white, fontWeight: FontWeight.w700),
                    ),
                  ],
                ),
                const SizedBox(height: 14),
                // Barre de recherche pill
                Container(
                  height: 44,
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(22),
                  ),
                  child: TextField(
                    decoration: const InputDecoration(
                      hintText: 'Rechercher un cours...',
                      hintStyle: TextStyle(color: AppTheme.textLight, fontSize: 14),
                      prefixIcon: Icon(Icons.search_rounded, color: AppTheme.textLight, size: 20),
                      border: InputBorder.none,
                      contentPadding: EdgeInsets.symmetric(vertical: 12),
                    ),
                    style: const TextStyle(fontSize: 14),
                    onChanged: (value) {
                      setState(() => _searchQuery = value);
                    },
                  ),
                ),
              ],
            ),
          ),
          
          // Liste des cours
          Expanded(
            child: _isLoading
                ? const Center(child: CircularProgressIndicator(color: AppTheme.primaryBlue))
                : _filteredCourses.isEmpty
                    ? Center(
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
                                child: const Icon(Icons.school_outlined, size: 36, color: AppTheme.primaryBlue),
                              ),
                              const SizedBox(height: 20),
                              Text(
                                _searchQuery.isEmpty ? 'Aucun cours disponible' : 'Aucun cours trouvé',
                                style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w600, color: AppTheme.textPrimary),
                              ),
                            ],
                          ),
                        ),
                      )
                    : ListView.builder(
                        padding: const EdgeInsets.fromLTRB(20, 16, 20, 20),
                        itemCount: _filteredCourses.length,
                        itemBuilder: (context, index) {
                          final course = _filteredCourses[index];
                          return Container(
                            margin: const EdgeInsets.only(bottom: 10),
                            decoration: BoxDecoration(
                              color: Colors.white,
                              borderRadius: BorderRadius.circular(14),
                              boxShadow: AppTheme.softShadow,
                            ),
                            child: ListTile(
                              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                              contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 4),
                              leading: Container(
                                width: 42, height: 42,
                                decoration: BoxDecoration(
                                  color: AppTheme.primaryBlue.withOpacity(0.1),
                                  borderRadius: BorderRadius.circular(12),
                                ),
                                child: const Icon(Icons.book_rounded, color: AppTheme.primaryBlue, size: 20),
                              ),
                              title: Text(
                                course.nom,
                                style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14, color: AppTheme.textPrimary),
                              ),
                              subtitle: course.description.isNotEmpty
                                  ? Text(course.description, maxLines: 2, overflow: TextOverflow.ellipsis, style: const TextStyle(color: AppTheme.textLight, fontSize: 12))
                                  : null,
                              trailing: Container(
                                width: 28, height: 28,
                                decoration: BoxDecoration(
                                  color: AppTheme.primaryBlue.withOpacity(0.1),
                                  borderRadius: BorderRadius.circular(8),
                                ),
                                child: const Icon(Icons.arrow_forward_ios_rounded, color: AppTheme.primaryBlue, size: 12),
                              ),
                              onTap: () {
                                widget.onCourseSelected(course);
                              },
                            ),
                          );
                        },
                      ),
          ),
        ],
      ),
    );
  }
}

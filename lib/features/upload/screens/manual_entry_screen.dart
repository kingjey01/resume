import 'package:flutter/material.dart';
import 'package:resume_plus_clean/services/api_service.dart';
import 'package:resume_plus_clean/models/course.dart';
import 'package:resume_plus_clean/models/professeur.dart';
import 'package:resume_plus_clean/services/snackbar_service.dart';
import 'package:resume_plus_clean/theme/app_theme.dart';

class ManualEntryScreen extends StatefulWidget {
  const ManualEntryScreen({super.key});

  @override
  State<ManualEntryScreen> createState() => _ManualEntryScreenState();
}

class _ManualEntryScreenState extends State<ManualEntryScreen> {
  final _formKey = GlobalKey<FormState>();
  final _titleController = TextEditingController();
  final _subjectController = TextEditingController();
  final _contentController = TextEditingController();
  final _priceController = TextEditingController();
  final _apiService = ApiService();

  List<Course> _courses = [];
  Course? _selectedCourse;
  bool _isLoadingCourses = false;
  bool _isSubmitting = false;

  List<Professeur> _professeurs = [];
  Professeur? _selectedProfesseur;
  bool _isLoadingProfesseurs = false;

  double _minimumPrice = 3000; // Valeur par défaut en attendant l'API

  @override
  void initState() {
    super.initState();
    _loadCourses();
    _loadProfesseurs();
    _loadPricingConfig();
  }

  @override
  void dispose() {
    _titleController.dispose();
    _subjectController.dispose();
    _contentController.dispose();
    _priceController.dispose();
    super.dispose();
  }

  Future<void> _loadPricingConfig() async {
    final minPrice = await _apiService.getMinimumResumePrice();
    if (mounted) {
      setState(() => _minimumPrice = minPrice);
      _priceController.text = minPrice.toStringAsFixed(0);
    }
  }

  Future<void> _loadProfesseurs() async {
    setState(() => _isLoadingProfesseurs = true);
    try {
      final data = await _apiService.getProfesseurs();
      setState(() {
        _professeurs = data
            .map((json) => Professeur.fromJson(json as Map<String, dynamic>))
            .toList();
        _isLoadingProfesseurs = false;
      });
    } catch (e) {
      setState(() => _isLoadingProfesseurs = false);
    }
  }

  Future<void> _loadCourses() async {
    setState(() => _isLoadingCourses = true);
    try {
      final coursesData = await _apiService.getCourses();
      setState(() {
        _courses = coursesData.map((json) => Course.fromJson(json)).toList();
        _isLoadingCourses = false;
      });
    } catch (e) {
      setState(() => _isLoadingCourses = false);
      SnackbarService.show('Erreur lors du chargement des cours: $e', isError: true);
    }
  }

  Future<void> _submitSummary() async {
    if (!_formKey.currentState!.validate() || _selectedCourse == null) {
      if (_selectedCourse == null) {
        SnackbarService.show('Veuillez sélectionner un cours', isError: true);
      }
      return;
    }

    final price = double.tryParse(_priceController.text.trim());
    if (price == null) {
      SnackbarService.show('Veuillez entrer un prix valide.', isError: true);
      return;
    }

    setState(() {
      _isSubmitting = true;
    });

    try {
      await _apiService.createSummary(
        titre: _titleController.text.trim(),
        texteResume: _contentController.text.trim(),
        courseId: _selectedCourse!.id,
        prix: price,
        professeurId: _selectedProfesseur?.id,
      );

      SnackbarService.show('Résumé créé avec succès !', isError: false);
      Navigator.of(context).pop();
    } catch (e) {
      SnackbarService.show('Erreur : ${ApiService.getErrorMessage(e)}', isError: true);
    } finally {
      setState(() {
        _isSubmitting = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final topPadding = MediaQuery.of(context).padding.top;

    return Scaffold(
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      body: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Header bleu - pleine largeur
            Container(
              width: double.infinity,
              padding: EdgeInsets.only(top: topPadding + 8, left: 20, right: 20, bottom: 24),
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
                  const SizedBox(height: 16),
                  Text(
                    'Saisir un résumé',
                    style: theme.textTheme.headlineMedium?.copyWith(color: Colors.white, fontWeight: FontWeight.w700),
                  ),
                  const SizedBox(height: 6),
                  Text(
                    'Rédigez votre résumé manuellement',
                    style: TextStyle(color: Colors.white.withOpacity(0.8), fontSize: 14),
                  ),
                ],
              ),
            ),

            const SizedBox(height: 20),

            // Formulaire dans carte blanche
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20),
              child: Container(
                padding: const EdgeInsets.all(20),
                decoration: BoxDecoration(
                  color: theme.colorScheme.surface,
                  borderRadius: BorderRadius.circular(16),
                  boxShadow: AppTheme.softShadow,
                ),
                child: Form(
                  key: _formKey,
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      TextFormField(
                        controller: _titleController,
                        decoration: const InputDecoration(
                          labelText: 'Titre du résumé',
                          prefixIcon: Icon(Icons.title_rounded),
                        ),
                        validator: (value) {
                          if (value == null || value.isEmpty) {
                            return 'Veuillez entrer un titre.';
                          }
                          return null;
                        },
                      ),
                      const SizedBox(height: 16),
                      _isLoadingCourses
                          ? const Center(child: CircularProgressIndicator(color: AppTheme.primaryBlue))
                          : DropdownButtonFormField<Course>(
                              value: _selectedCourse,
                              isExpanded: true,
                              decoration: const InputDecoration(
                                labelText: 'Sélectionner un cours',
                                prefixIcon: Icon(Icons.school_rounded),
                                border: OutlineInputBorder(),
                              ),
                              items: _courses.map((course) {
                                return DropdownMenuItem<Course>(
                                  value: course,
                                  child: Text(
                                    '${course.nom} - ${course.filiereDisplay}',
                                    overflow: TextOverflow.ellipsis,
                                  ),
                                );
                              }).toList(),
                              onChanged: (Course? newValue) {
                                setState(() {
                                  _selectedCourse = newValue;
                                });
                              },
                              validator: (value) {
                                if (value == null) {
                                  return 'Veuillez sélectionner un cours.';
                                }
                                return null;
                              },
                            ),
                      const SizedBox(height: 16),
                      _isLoadingProfesseurs
                          ? const Center(child: CircularProgressIndicator())
                          : DropdownButtonFormField<Professeur>(
                              value: _selectedProfesseur,
                              isExpanded: true,
                              decoration: const InputDecoration(
                                labelText: 'Professeur (optionnel)',
                                prefixIcon: Icon(Icons.person_rounded),
                                border: OutlineInputBorder(),
                              ),
                              hint: const Text('Sélectionner un professeur'),
                              items: _professeurs.map((prof) {
                                return DropdownMenuItem<Professeur>(
                                  value: prof,
                                  child: Text(
                                    prof.displayName,
                                    overflow: TextOverflow.ellipsis,
                                  ),
                                );
                              }).toList(),
                              onChanged: (value) => setState(() => _selectedProfesseur = value),
                            ),
                      const SizedBox(height: 16),

                      // ── Prix du résumé ──────────────────────────────────
                      TextFormField(
                        controller: _priceController,
                        keyboardType: const TextInputType.numberWithOptions(decimal: false),
                        decoration: InputDecoration(
                          labelText: 'Prix (CDF) *',
                          prefixIcon: const Icon(Icons.payments_rounded),
                          helperText: 'Prix minimum : ${_minimumPrice.toStringAsFixed(0)} CDF',
                          helperMaxLines: 2,
                          border: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(12),
                          ),
                        ),
                        validator: (value) {
                          if (value == null || value.trim().isEmpty) {
                            return 'Le prix est obligatoire';
                          }
                          final p = double.tryParse(value);
                          if (p == null) {
                            return 'Entrez un nombre valide.';
                          }
                          if (p < _minimumPrice) {
                            return 'Le prix minimum est ${_minimumPrice.toStringAsFixed(0)} CDF';
                          }
                          return null;
                        },
                      ),
                      const SizedBox(height: 16),
                      TextFormField(
                        controller: _contentController,
                        decoration: const InputDecoration(
                          labelText: 'Contenu du résumé',
                          alignLabelWithHint: true,
                          border: OutlineInputBorder(),
                        ),
                        maxLines: 15,
                        validator: (value) {
                          if (value == null || value.isEmpty) {
                            return 'Veuillez entrer le contenu.';
                          }
                          if (value.length < 50) {
                            return 'Le contenu doit contenir au moins 50 caractères.';
                          }
                          return null;
                        },
                      ),
                      const SizedBox(height: 24),
                      SizedBox(
                        height: 50,
                        child: ElevatedButton.icon(
                          style: ElevatedButton.styleFrom(
                            backgroundColor: AppTheme.primaryBlue,
                            foregroundColor: Colors.white,
                            elevation: 0,
                            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                          ),
                          icon: _isSubmitting
                              ? const SizedBox(
                                  width: 20, height: 20,
                                  child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                                )
                              : const Icon(Icons.cloud_upload_outlined, color: Colors.white),
                          label: Text(
                            _isSubmitting ? 'Création en cours...' : 'Soumettre le résumé',
                            style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w600),
                          ),
                          onPressed: _isSubmitting ? null : _submitSummary,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
            const SizedBox(height: 40),
          ],
        ),
      ),
    );
  }
}

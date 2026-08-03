import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:image_picker/image_picker.dart';
import 'package:resume_plus_clean/services/api_service.dart';
import 'package:resume_plus_clean/services/snackbar_service.dart';
import 'package:resume_plus_clean/theme/app_theme.dart';
import 'package:dio/dio.dart';

class EditProfileScreen extends StatefulWidget {
  final Map<String, dynamic> userProfile;

  const EditProfileScreen({
    super.key,
    required this.userProfile,
  });

  @override
  State<EditProfileScreen> createState() => _EditProfileScreenState();
}

class _EditProfileScreenState extends State<EditProfileScreen> {
  final _formKey = GlobalKey<FormState>();
  final _firstNameController = TextEditingController();
  final _lastNameController = TextEditingController();
  final _emailController = TextEditingController();
  final _phoneController = TextEditingController();
  final ApiService _apiService = ApiService();
  final ImagePicker _picker = ImagePicker();
  
  XFile? _profileImage;
  String? _currentProfileImageUrl;
  bool _isLoading = false;
  bool _isLoadingData = false;
  bool _isFieldsLocked = true;
  
  List<Map<String, dynamic>> _universites = [];
  List<Map<String, dynamic>> _promotions = [];
  List<Map<String, dynamic>> _filieres = [];
  
  int? _selectedUniversiteId;
  int? _selectedPromotionId;
  int? _selectedFiliereId;

  @override
  void initState() {
    super.initState();
    _initializeFields();
    _loadInitialData();
  }

  void _initializeFields() {
    final profile = widget.userProfile['profile'];
    _firstNameController.text = widget.userProfile['first_name'] ?? '';
    _lastNameController.text = widget.userProfile['last_name'] ?? '';
    _emailController.text = widget.userProfile['email'] ?? '';
    _phoneController.text = widget.userProfile['username'] ?? '';

    if (profile != null) {
      _selectedUniversiteId = profile['universite'];
      _selectedPromotionId = profile['promotion'];
      _selectedFiliereId = profile['filiere'];
      final groupe = profile['groupe']?.toString().toUpperCase() ?? 'ETUDIANT';
      _isFieldsLocked = groupe == 'ETUDIANT' || groupe == 'CP';
      final rawPic = profile['profile_picture'];
      if (rawPic != null && rawPic.isNotEmpty) {
        _currentProfileImageUrl = rawPic.startsWith('http')
            ? rawPic
            : '${ApiService.baseUrl.replaceAll('/api', '')}$rawPic';
      }
    }
  }

  Future<void> _loadInitialData() async {
    setState(() => _isLoadingData = true);
    
    try {
      final dio = Dio();
      dio.options.headers['Authorization'] = 'Bearer ${await _apiService.getAccessToken()}';
      
      final responses = await Future.wait([
        dio.get('${ApiService.baseUrl}/courses/universites/'),
        dio.get('${ApiService.baseUrl}/courses/promotions/'),
        dio.get('${ApiService.baseUrl}/courses/filieres/'),
      ]);

      setState(() {
        _universites = _parseListResponse(responses[0].data);
        _promotions = _parseListResponse(responses[1].data);
        _filieres = _parseListResponse(responses[2].data);
        _isLoadingData = false;
      });
    } catch (e) {
      setState(() => _isLoadingData = false);
      SnackbarService.showError('Erreur lors du chargement des données');
    }
  }

  List<Map<String, dynamic>> _parseListResponse(dynamic data) {
    if (data is List) {
      return List<Map<String, dynamic>>.from(data);
    } else if (data is Map && data.containsKey('results')) {
      return List<Map<String, dynamic>>.from(data['results']);
    }
    return [];
  }

  Future<void> _pickImage() async {
    try {
      final XFile? image = await _picker.pickImage(
        source: ImageSource.gallery,
        maxWidth: 512,
        maxHeight: 512,
        imageQuality: 85,
      );
      
      if (image != null) {
        setState(() {
          _profileImage = image;
        });
      }
    } catch (e) {
      SnackbarService.showError('Erreur lors de la sélection de l\'image');
    }
  }

  Future<void> _saveProfile() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() => _isLoading = true);

    try {
      final formData = FormData.fromMap({
        'first_name': _firstNameController.text.trim(),
        'last_name': _lastNameController.text.trim(),
        'email': _emailController.text.trim(),
        if (_selectedUniversiteId != null) 'universite_id': _selectedUniversiteId,
        if (_selectedPromotionId != null) 'promotion_id': _selectedPromotionId,
        if (_selectedFiliereId != null) 'filiere_id': _selectedFiliereId,
      });

      // Ajouter la photo de profil si sélectionnée
      if (_profileImage != null) {
        if (kIsWeb) {
          final bytes = await _profileImage!.readAsBytes();
          formData.files.add(MapEntry(
            'profile_picture',
            MultipartFile.fromBytes(bytes, filename: 'profile.jpg'),
          ));
        } else {
          formData.files.add(MapEntry(
            'profile_picture',
            await MultipartFile.fromFile(_profileImage!.path, filename: 'profile.jpg'),
          ));
        }
      }

      final dio = Dio();
      dio.options.headers['Authorization'] = 'Bearer ${await _apiService.getAccessToken()}';
      
      final response = await dio.put(
        '${ApiService.baseUrl}/auth/profile/update/',
        data: formData,
      );

      if (response.statusCode == 200) {
        SnackbarService.showSuccess('Profil mis à jour avec succès');
        if (mounted) Navigator.of(context).pop(true);
      }
    } catch (e) {
      SnackbarService.showError('Erreur lors de la mise à jour: $e');
    } finally {
      setState(() => _isLoading = false);
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
          children: [
            // Header bleu
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
                      width: 40,
                      height: 40,
                      decoration: BoxDecoration(
                        color: Colors.white.withOpacity(0.2),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: const Icon(Icons.arrow_back_rounded, color: Colors.white, size: 22),
                    ),
                  ),
                  const SizedBox(height: 16),
                  Text(
                    'Modifier le profil',
                    style: theme.textTheme.headlineMedium?.copyWith(
                      color: Colors.white,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                  const SizedBox(height: 6),
                  Text(
                    'Mettez à jour vos informations personnelles',
                    style: TextStyle(color: Colors.white.withOpacity(0.8), fontSize: 14),
                  ),
                ],
              ),
            ),

            const SizedBox(height: 20),

            // Photo de profil
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20),
              child: Container(
                padding: const EdgeInsets.all(20),
                decoration: BoxDecoration(
                  color: theme.colorScheme.surface,
                  borderRadius: BorderRadius.circular(16),
                  boxShadow: AppTheme.softShadow,
                ),
                child: Column(
                  children: [
                    Stack(
                      children: [
                        CircleAvatar(
                          radius: 60,
                          backgroundColor: AppTheme.primaryBlue.withOpacity(0.1),
                          backgroundImage: _profileImage != null
                              ? (kIsWeb
                                  ? NetworkImage(_profileImage!.path)
                                  : FileImage(File(_profileImage!.path)) as ImageProvider)
                              : (_currentProfileImageUrl != null
                                  ? NetworkImage(_currentProfileImageUrl!)
                                  : null),
                          child: _profileImage == null && _currentProfileImageUrl == null
                              ? const Icon(Icons.person, size: 60, color: AppTheme.primaryBlue)
                              : null,
                        ),
                        Positioned(
                          bottom: 0,
                          right: 0,
                          child: GestureDetector(
                            onTap: _pickImage,
                            child: Container(
                              padding: const EdgeInsets.all(8),
                              decoration: BoxDecoration(
                                color: AppTheme.primaryBlue,
                                shape: BoxShape.circle,
                                border: Border.all(color: Colors.white, width: 3),
                              ),
                              child: const Icon(Icons.camera_alt, color: Colors.white, size: 20),
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),
                    Text(
                      'Appuyez sur l\'icône pour changer la photo',
                      style: theme.textTheme.bodySmall?.copyWith(color: Colors.grey),
                    ),
                  ],
                ),
              ),
            ),

            const SizedBox(height: 16),

            // Formulaire
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
                        controller: _firstNameController,
                        decoration: const InputDecoration(
                          labelText: 'Prénom *',
                          prefixIcon: Icon(Icons.person_outline),
                        ),
                        validator: (value) {
                          if (value == null || value.trim().isEmpty) {
                            return 'Le prénom est obligatoire';
                          }
                          return null;
                        },
                      ),
                      const SizedBox(height: 16),
                      TextFormField(
                        controller: _lastNameController,
                        decoration: const InputDecoration(
                          labelText: 'Nom *',
                          prefixIcon: Icon(Icons.person_outline),
                        ),
                        validator: (value) {
                          if (value == null || value.trim().isEmpty) {
                            return 'Le nom est obligatoire';
                          }
                          return null;
                        },
                      ),
                      const SizedBox(height: 16),
                      TextFormField(
                        controller: _emailController,
                        decoration: const InputDecoration(
                          labelText: 'Email *',
                          prefixIcon: Icon(Icons.email_outlined),
                        ),
                        keyboardType: TextInputType.emailAddress,
                        validator: (value) {
                          if (value == null || value.trim().isEmpty) {
                            return 'L\'email est obligatoire';
                          }
                          return null;
                        },
                      ),
                      const SizedBox(height: 16),
                      if (_isLoadingData)
                        const Center(child: CircularProgressIndicator())
                      else ...[
                        // 🧩7: champs lecture seule pour ETUDIANT
                        if (_isFieldsLocked)
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                            decoration: BoxDecoration(
                              color: Colors.amber.withOpacity(0.1),
                              borderRadius: BorderRadius.circular(8),
                              border: Border.all(color: Colors.amber.withOpacity(0.4)),
                            ),
                            child: const Row(
                              children: [
                                Icon(Icons.lock_outline, size: 16, color: Colors.amber),
                                SizedBox(width: 8),
                                Expanded(
                                  child: Text(
                                    'Université, promotion et filière ne peuvent être modifiés que par un administrateur.',
                                    style: TextStyle(fontSize: 12, color: Colors.amber),
                                  ),
                                ),
                              ],
                            ),
                          ),
                        if (_isFieldsLocked) const SizedBox(height: 12),
                        DropdownButtonFormField<int>(
                          value: _selectedUniversiteId,
                          isExpanded: true,
                          decoration: InputDecoration(
                            labelText: 'Université *',
                            prefixIcon: const Icon(Icons.school_outlined),
                            suffixIcon: _isFieldsLocked ? const Icon(Icons.lock, size: 18) : null,
                          ),
                          items: _universites.map((u) {
                            return DropdownMenuItem<int>(
                              value: u['id'],
                              child: Text(u['nom'], overflow: TextOverflow.ellipsis),
                            );
                          }).toList(),
                          onChanged: _isFieldsLocked ? null : (value) => setState(() => _selectedUniversiteId = value),
                        ),
                        const SizedBox(height: 16),
                        DropdownButtonFormField<int>(
                          value: _selectedPromotionId,
                          isExpanded: true,
                          decoration: InputDecoration(
                            labelText: 'Promotion *',
                            prefixIcon: const Icon(Icons.calendar_today_outlined),
                            suffixIcon: _isFieldsLocked ? const Icon(Icons.lock, size: 18) : null,
                          ),
                          items: _promotions.map((p) {
                            return DropdownMenuItem<int>(
                              value: p['id'],
                              child: Text(p['nom'], overflow: TextOverflow.ellipsis),
                            );
                          }).toList(),
                          onChanged: _isFieldsLocked ? null : (value) => setState(() => _selectedPromotionId = value),
                        ),
                        const SizedBox(height: 16),
                        DropdownButtonFormField<int>(
                          value: _selectedFiliereId,
                          isExpanded: true,
                          decoration: InputDecoration(
                            labelText: 'Filière *',
                            prefixIcon: const Icon(Icons.class_outlined),
                            suffixIcon: _isFieldsLocked ? const Icon(Icons.lock, size: 18) : null,
                          ),
                          items: _filieres.map((f) {
                            return DropdownMenuItem<int>(
                              value: f['id'],
                              child: Text(f['nom'], overflow: TextOverflow.ellipsis),
                            );
                          }).toList(),
                          onChanged: _isFieldsLocked ? null : (value) => setState(() => _selectedFiliereId = value),
                        ),
                      ],
                      const SizedBox(height: 24),
                      SizedBox(
                        height: 50,
                        child: ElevatedButton.icon(
                          onPressed: _isLoading ? null : _saveProfile,
                          style: ElevatedButton.styleFrom(
                            backgroundColor: AppTheme.primaryBlue,
                            foregroundColor: Colors.white,
                            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                          ),
                          icon: _isLoading
                              ? const SizedBox(
                                  width: 20,
                                  height: 20,
                                  child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                                )
                              : const Icon(Icons.save),
                          label: Text(_isLoading ? 'Enregistrement...' : 'Enregistrer'),
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

  @override
  void dispose() {
    _firstNameController.dispose();
    _lastNameController.dispose();
    _emailController.dispose();
    _phoneController.dispose();
    super.dispose();
  }
}

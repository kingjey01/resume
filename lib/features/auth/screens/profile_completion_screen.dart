import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart';
import 'package:dio/dio.dart';
import 'package:resume_plus_clean/theme/app_theme.dart';
import 'package:resume_plus_clean/features/app/screens/main_navigation_screen.dart';
import 'package:resume_plus_clean/services/api_service.dart';
import 'package:resume_plus_clean/services/storage_service.dart';

class ProfileCompletionScreen extends StatefulWidget {
  const ProfileCompletionScreen({
    super.key,
  });

  @override
  State<ProfileCompletionScreen> createState() => _ProfileCompletionScreenState();
}

class _ProfileCompletionScreenState extends State<ProfileCompletionScreen> {
  final _formKey = GlobalKey<FormState>();
  final _firstNameController = TextEditingController();
  final _lastNameController = TextEditingController();
  
  bool _isLoading = false;
  bool _isLoadingData = true;
  
  List<Map<String, dynamic>> _universites = [];
  List<Map<String, dynamic>> _promotions = [];
  List<Map<String, dynamic>> _filieres = [];
  
  int? _selectedUniversiteId;
  int? _selectedPromotionId;
  int? _selectedFiliereId;
  
  late Dio _dio;

  @override
  void initState() {
    super.initState();
    _dio = Dio();
    _loadInitialData();
  }

  @override
  void dispose() {
    _firstNameController.dispose();
    _lastNameController.dispose();
    super.dispose();
  }

  List<Map<String, dynamic>> _parseListResponse(dynamic data) {
    if (data is List) {
      return List<Map<String, dynamic>>.from(data);
    } else if (data is Map && data.containsKey('results')) {
      return List<Map<String, dynamic>>.from(data['results']);
    }
    return [];
  }

  Future<void> _loadInitialData() async {
    try {
      // Charger les universités, promotions et filières
      final responses = await Future.wait([
        _dio.get('${ApiService.baseUrl}/courses/universites/'),
        _dio.get('${ApiService.baseUrl}/courses/promotions/'),
        _dio.get('${ApiService.baseUrl}/courses/filieres/'),
      ]);

      if (mounted) {
        setState(() {
          _universites = _parseListResponse(responses[0].data);
          _promotions = _parseListResponse(responses[1].data);
          _filieres = _parseListResponse(responses[2].data);
          _isLoadingData = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _isLoadingData = false;
        });
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Erreur lors du chargement des données'),
            backgroundColor: AppTheme.error,
          ),
        );
      }
    }
  }

  // Récupérer le token d'accès depuis le storage
  Future<String?> _getAccessToken() async {
    try {
      final storageService = StorageService();
      return await storageService.accessToken;
    } catch (e) {
      print('❌ Erreur récupération token: $e');
      return null;
    }
  }

  Future<void> _completeProfile() async {
    if (_formKey.currentState?.validate() ?? false) {
      FocusScope.of(context).unfocus();
      
      setState(() {
        _isLoading = true;
      });

      try {
        // Récupérer le token d'accès depuis le storage
        final accessToken = await _getAccessToken();
        
        if (accessToken == null) {
          throw Exception('Token non disponible');
        }
        
        if (kDebugMode) {
          print('Profile completion - Access token: ${accessToken.isNotEmpty ? "Present" : "Missing"}');
          print('Profile completion - Token length: ${accessToken.length}');
        }
        
        final response = await _dio.post(
          '${ApiService.baseUrl}/auth/profile/complete/',
          data: {
            'first_name': _firstNameController.text.trim(),
            'last_name': _lastNameController.text.trim(),
            'universite_id': _selectedUniversiteId,
            'promotion_id': _selectedPromotionId,
            'filiere_id': _selectedFiliereId,
          },
          options: Options(
            headers: {'Authorization': 'Bearer $accessToken'},
          ),
        );

        if (kDebugMode) {
          print('Profile completion - Response status: ${response.statusCode}');
          print('Profile completion - Response data: ${response.data}');
        }

        if (response.statusCode == 200) {
          if (mounted) {
            // Profil complété avec succès, aller à l'espace principal
            Navigator.of(context).pushAndRemoveUntil(
              MaterialPageRoute(builder: (_) => MainNavigationScreen(key: MainNavigationScreen.navKey)),
              (route) => false,
            );
          }
        }
      } catch (e) {
        if (kDebugMode) {
          print('Profile completion - Error: $e');
          if (e is DioException) {
            print('Profile completion - Dio error: ${e.response?.statusCode}');
            print('Profile completion - Dio response: ${e.response?.data}');
            print('Profile completion - Dio headers: ${e.response?.headers}');
          }
        }
        
        if (mounted) {
          String errorMessage = 'Erreur lors de la complétion du profil';
          
          if (e is DioException && e.response?.data != null) {
            errorMessage = e.response?.data['error'] ?? e.response?.data['message'] ?? errorMessage;
          }
          
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text(errorMessage),
              backgroundColor: AppTheme.error,
            ),
          );
        }
      } finally {
        if (mounted) {
          setState(() {
            _isLoading = false;
          });
        }
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    if (_isLoadingData) {
      return Scaffold(
        backgroundColor: theme.scaffoldBackgroundColor,
        body: const Center(
          child: CircularProgressIndicator(),
        ),
      );
    }

    return Scaffold(
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      body: SingleChildScrollView(
        child: Column(
          children: [
            // Header
            Container(
              width: double.infinity,
              padding: EdgeInsets.only(
                top: MediaQuery.of(context).padding.top + 40,
                bottom: 40,
                left: 24,
                right: 24,
              ),
              decoration: const BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                  colors: [AppTheme.primaryBlueDark, AppTheme.primaryBlue, AppTheme.primaryBlueLight],
                ),
                borderRadius: BorderRadius.only(
                  bottomLeft: Radius.circular(32),
                  bottomRight: Radius.circular(32),
                ),
              ),
              child: Column(
                children: [
                  Container(
                    width: 70, height: 70,
                    decoration: BoxDecoration(
                      color: Colors.white.withOpacity(0.2),
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: const Icon(Icons.person_add_rounded, color: Colors.white, size: 36),
                  ),
                  const SizedBox(height: 16),
                  Text(
                    'Complétez votre profil',
                    style: theme.textTheme.headlineSmall?.copyWith(color: Colors.white, fontWeight: FontWeight.w700),
                  ),
                  const SizedBox(height: 6),
                  Text(
                    'Quelques informations pour personnaliser votre expérience',
                    style: TextStyle(color: Colors.white.withOpacity(0.8), fontSize: 14),
                    textAlign: TextAlign.center,
                  ),
                ],
              ),
            ),

            const SizedBox(height: 28),

            // Formulaire
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 24),
              child: Container(
                padding: const EdgeInsets.all(24),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(20),
                  boxShadow: AppTheme.softShadow,
                ),
                child: Form(
                  key: _formKey,
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      // Prénom
                      TextFormField(
                        controller: _firstNameController,
                        style: TextStyle(color: Theme.of(context).brightness == Brightness.dark ? Colors.white : Colors.black87),
                        decoration: InputDecoration(
                          labelText: 'Prénom *',
                          labelStyle: TextStyle(color: Theme.of(context).brightness == Brightness.dark ? Colors.white70 : AppTheme.primaryBlue),
                          floatingLabelStyle: TextStyle(color: Theme.of(context).brightness == Brightness.dark ? Colors.white : AppTheme.primaryBlue),
                          hintText: 'Votre prénom',
                          hintStyle: TextStyle(color: Theme.of(context).brightness == Brightness.dark ? Colors.white38 : Colors.grey),
                          prefixIcon: const Icon(Icons.person_outline_rounded),
                          border: OutlineInputBorder(borderRadius: BorderRadius.circular(14)),
                        ),
                        textInputAction: TextInputAction.next,
                        validator: (value) {
                          if (value == null || value.trim().isEmpty) {
                            return 'Le prénom est obligatoire';
                          }
                          return null;
                        },
                      ),
                      
                      const SizedBox(height: 16),
                      
                      // Nom
                      TextFormField(
                        controller: _lastNameController,
                        style: TextStyle(color: Theme.of(context).brightness == Brightness.dark ? Colors.white : Colors.black87),
                        decoration: InputDecoration(
                          labelText: 'Nom *',
                          labelStyle: TextStyle(color: Theme.of(context).brightness == Brightness.dark ? Colors.white70 : AppTheme.primaryBlue),
                          floatingLabelStyle: TextStyle(color: Theme.of(context).brightness == Brightness.dark ? Colors.white : AppTheme.primaryBlue),
                          hintText: 'Votre nom de famille',
                          hintStyle: TextStyle(color: Theme.of(context).brightness == Brightness.dark ? Colors.white38 : Colors.grey),
                          prefixIcon: const Icon(Icons.person_outline_rounded),
                          border: OutlineInputBorder(borderRadius: BorderRadius.circular(14)),
                        ),
                        textInputAction: TextInputAction.next,
                        validator: (value) {
                          if (value == null || value.trim().isEmpty) {
                            return 'Le nom est obligatoire';
                          }
                          return null;
                        },
                      ),
                      
                      const SizedBox(height: 16),
                      
                      // Université
                      DropdownButtonFormField<int>(
                        value: _selectedUniversiteId,
                        isExpanded: true,
                        dropdownColor: Theme.of(context).brightness == Brightness.dark ? const Color(0xFF1A1D2E) : Colors.white,
                        style: TextStyle(color: Theme.of(context).brightness == Brightness.dark ? Colors.white : Colors.black87),
                        decoration: InputDecoration(
                          labelText: 'Université *',
                          labelStyle: TextStyle(color: Theme.of(context).brightness == Brightness.dark ? Colors.white70 : AppTheme.primaryBlue),
                          floatingLabelStyle: TextStyle(color: Theme.of(context).brightness == Brightness.dark ? Colors.white : AppTheme.primaryBlue),
                          prefixIcon: const Icon(Icons.school_outlined),
                          border: OutlineInputBorder(borderRadius: BorderRadius.circular(14)),
                        ),
                        items: _universites.map((universite) {
                          return DropdownMenuItem<int>(
                            value: universite['id'],
                            child: Text(
                              universite['nom'],
                              overflow: TextOverflow.ellipsis,
                              maxLines: 1,
                            ),
                          );
                        }).toList(),
                        onChanged: (value) {
                          setState(() {
                            _selectedUniversiteId = value;
                          });
                        },
                        validator: (value) {
                          if (value == null) {
                            return 'Veuillez sélectionner une université';
                          }
                          return null;
                        },
                      ),
                      
                      const SizedBox(height: 16),
                      
                      // Promotion
                      DropdownButtonFormField<int>(
                        value: _selectedPromotionId,
                        isExpanded: true,
                        dropdownColor: Theme.of(context).brightness == Brightness.dark ? const Color(0xFF1A1D2E) : Colors.white,
                        style: TextStyle(color: Theme.of(context).brightness == Brightness.dark ? Colors.white : Colors.black87),
                        decoration: InputDecoration(
                          labelText: 'Promotion *',
                          labelStyle: TextStyle(color: Theme.of(context).brightness == Brightness.dark ? Colors.white70 : AppTheme.primaryBlue),
                          floatingLabelStyle: TextStyle(color: Theme.of(context).brightness == Brightness.dark ? Colors.white : AppTheme.primaryBlue),
                          prefixIcon: const Icon(Icons.calendar_today_outlined),
                          border: OutlineInputBorder(borderRadius: BorderRadius.circular(14)),
                        ),
                        items: _promotions.map((promotion) {
                          return DropdownMenuItem<int>(
                            value: promotion['id'],
                            child: Text(
                              promotion['nom'],
                              overflow: TextOverflow.ellipsis,
                              maxLines: 1,
                            ),
                          );
                        }).toList(),
                        onChanged: (value) {
                          setState(() {
                            _selectedPromotionId = value;
                          });
                        },
                        validator: (value) {
                          if (value == null) {
                            return 'Veuillez sélectionner une promotion';
                          }
                          return null;
                        },
                      ),
                      
                      const SizedBox(height: 16),
                      
                      // Filière
                      DropdownButtonFormField<int>(
                        value: _selectedFiliereId,
                        isExpanded: true,
                        dropdownColor: Theme.of(context).brightness == Brightness.dark ? const Color(0xFF1A1D2E) : Colors.white,
                        style: TextStyle(color: Theme.of(context).brightness == Brightness.dark ? Colors.white : Colors.black87),
                        decoration: InputDecoration(
                          labelText: 'Filière *',
                          labelStyle: TextStyle(color: Theme.of(context).brightness == Brightness.dark ? Colors.white70 : AppTheme.primaryBlue),
                          floatingLabelStyle: TextStyle(color: Theme.of(context).brightness == Brightness.dark ? Colors.white : AppTheme.primaryBlue),
                          prefixIcon: const Icon(Icons.subject_outlined),
                          border: OutlineInputBorder(borderRadius: BorderRadius.circular(14)),
                        ),
                        items: _filieres.map((filiere) {
                          return DropdownMenuItem<int>(
                            value: filiere['id'],
                            child: Text(
                              filiere['nom'],
                              overflow: TextOverflow.ellipsis,
                              maxLines: 1,
                            ),
                          );
                        }).toList(),
                        onChanged: (value) {
                          setState(() {
                            _selectedFiliereId = value;
                          });
                        },
                        validator: (value) {
                          if (value == null) {
                            return 'Veuillez sélectionner une filière';
                          }
                          return null;
                        },
                      ),
                      
                      const SizedBox(height: 24),
                      
                      // Information
                      Container(
                        padding: const EdgeInsets.all(16),
                        decoration: BoxDecoration(
                          color: AppTheme.primaryBlue.withOpacity(0.1),
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: Row(
                          children: [
                            Icon(Icons.info_outline, color: AppTheme.primaryBlue, size: 20),
                            const SizedBox(width: 12),
                            Expanded(
                              child: Text(
                                'Ces informations nous permettent de vous proposer du contenu adapté à votre parcours.',
                                style: TextStyle(
                                  color: AppTheme.primaryBlue,
                                  fontSize: 13,
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                      
                      const SizedBox(height: 24),
                      
                      // Bouton de validation
                      SizedBox(
                        height: 50,
                        child: ElevatedButton(
                          onPressed: _isLoading ? null : _completeProfile,
                          style: ElevatedButton.styleFrom(
                            backgroundColor: AppTheme.primaryBlue,
                            foregroundColor: Colors.white,
                            elevation: 0,
                            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                          ),
                          child: _isLoading
                              ? const SizedBox(
                                  width: 22, height: 22,
                                  child: CircularProgressIndicator(strokeWidth: 2.5, color: Colors.white),
                                )
                              : const Text('Terminer l\'inscription', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
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

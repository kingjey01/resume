import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:resume_plus_clean/features/auth/providers/auth_provider.dart';
import 'package:resume_plus_clean/services/snackbar_service.dart';
import 'package:resume_plus_clean/services/api_service.dart';
import 'package:resume_plus_clean/features/settings/screens/edit_profile_screen.dart';
import 'package:resume_plus_clean/theme/app_theme.dart';

class ProfileSection extends ConsumerStatefulWidget {
  const ProfileSection({super.key});

  @override
  ConsumerState<ProfileSection> createState() => _ProfileSectionState();
}

class _ProfileSectionState extends ConsumerState<ProfileSection> {
  final ApiService _apiService = ApiService();
  Map<String, dynamic>? _userProfile;
  bool _isLoading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadUserProfile();
  }

  Future<void> _loadUserProfile() async {
    try {
      setState(() {
        _isLoading = true;
        _error = null;
      });
      
      final profile = await _apiService.getUserProfile();
      
      if (mounted) {
        setState(() {
          _userProfile = profile;
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _error = e.toString();
          _isLoading = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    if (_isLoading) {
      return const Center(
        child: Column(
          children: [
            CircularProgressIndicator(),
            SizedBox(height: 8),
            Text('Chargement du profil...'),
          ],
        ),
      );
    }

    if (_error != null) {
      return Column(
        children: [
          Icon(Icons.error_outline, color: Colors.red, size: 48),
          const SizedBox(height: 8),
          Text('Erreur: $_error'),
          const SizedBox(height: 8),
          ElevatedButton(
            onPressed: _loadUserProfile,
            child: const Text('Réessayer'),
          ),
        ],
      );
    }

    if (_userProfile == null) {
      return const Text('Aucune information de profil disponible');
    }

    final username = _userProfile!['username'] ?? 'Utilisateur';
    final email = _userProfile!['email'] ?? 'email@example.com';
    final role = _userProfile!['profile']?['groupe'] ?? 'ETUDIANT';
    final rawPicture = _userProfile!['profile']?['profile_picture'];
    final profilePicture = rawPicture != null && rawPicture.isNotEmpty
        ? (rawPicture.startsWith('http') ? rawPicture : '${ApiService.baseUrl.replaceAll('/api', '')}$rawPicture')
        : null;
    final firstName = _userProfile!['first_name'] ?? '';
    final lastName = _userProfile!['last_name'] ?? '';
    final displayName = firstName.isNotEmpty || lastName.isNotEmpty
        ? '$firstName $lastName'.trim()
        : username;

    return Column(
      children: [
        // Avatar et nom d'utilisateur
        Row(
          children: [
            CircleAvatar(
              radius: 30,
              backgroundColor: AppTheme.primaryBlue.withOpacity(0.1),
              backgroundImage: profilePicture != null ? NetworkImage(profilePicture) : null,
              child: profilePicture == null
                  ? Text(
                      displayName.isNotEmpty ? displayName[0].toUpperCase() : 'U',
                      style: theme.textTheme.headlineSmall?.copyWith(
                        color: AppTheme.primaryBlue,
                        fontWeight: FontWeight.bold,
                      ),
                    )
                  : null,
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    displayName,
                    style: theme.textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.bold,
                      color: theme.colorScheme.onSurface,
                    ),
                  ),
                  Text(
                    email,
                    style: theme.textTheme.bodyMedium?.copyWith(
                      color: theme.colorScheme.onSurface.withOpacity(0.7),
                    ),
                  ),
                  Container(
                    margin: const EdgeInsets.only(top: 4),
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                    decoration: BoxDecoration(
                      color: theme.colorScheme.secondaryContainer,
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Text(
                      role,
                      style: theme.textTheme.bodySmall?.copyWith(
                        color: theme.colorScheme.onSecondaryContainer,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
        
        const SizedBox(height: 16),
        
        // Bouton modifier le profil
        SizedBox(
          width: double.infinity,
          child: OutlinedButton.icon(
            onPressed: () => _navigateToEditProfile(context),
            icon: const Icon(Icons.edit),
            label: const Text('Modifier le profil'),
          ),
        ),
      ],
    );
  }

  Future<void> _navigateToEditProfile(BuildContext context) async {
    if (_userProfile == null) return;
    
    final result = await Navigator.of(context).push(
      MaterialPageRoute(
        builder: (context) => EditProfileScreen(userProfile: _userProfile!),
      ),
    );
    
    // Recharger le profil si des modifications ont été faites
    if (result == true) {
      _loadUserProfile();
    }
  }
}
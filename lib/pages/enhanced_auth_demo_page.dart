import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:resume_plus_clean/providers/api_provider.dart';
import 'package:resume_plus_clean/widgets/enhanced_auth_widget.dart';

/// 🔥 Page de démonstration de l'authentification améliorée
/// Montre comment intégrer la gestion hybride des tokens dans l'app principale
class EnhancedAuthDemoPage extends ConsumerWidget {
  const EnhancedAuthDemoPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final authState = ref.watch(authStateProvider);
    final userProfile = ref.watch(userProfileProvider);
    final theme = Theme.of(context);

    return Scaffold(
      backgroundColor: Colors.grey.shade50,
      appBar: AppBar(
        title: const Text('🔥 Authentification Améliorée'),
        backgroundColor: theme.colorScheme.primary,
        foregroundColor: Colors.white,
        elevation: 0,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // En-tête avec informations
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: [
                    theme.colorScheme.primary.withOpacity(0.1),
                    theme.colorScheme.secondary.withOpacity(0.1),
                  ],
                ),
                borderRadius: BorderRadius.circular(16),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Icon(
                        Icons.rocket_launch,
                        color: theme.colorScheme.primary,
                        size: 32,
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Text(
                          'Authentification Hybride Intégrée',
                          style: theme.textTheme.headlineSmall?.copyWith(
                            fontWeight: FontWeight.bold,
                            color: theme.colorScheme.primary,
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  Text(
                    'Cette page démontre l\'intégration de la solution d\'authentification hybride '
                    'qui fonctionne parfaitement dans le projet principal.',
                    style: theme.textTheme.bodyLarge,
                  ),
                  const SizedBox(height: 16),
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: [
                      _buildFeatureChip('✅ Tokens en mémoire', Colors.green),
                      _buildFeatureChip('✅ Storage de secours', Colors.blue),
                      _buildFeatureChip('✅ Résistant aux erreurs web', Colors.orange),
                      _buildFeatureChip('✅ API fonctionnelle', Colors.purple),
                    ],
                  ),
                ],
              ),
            ),
            const SizedBox(height: 24),

            // État de l'authentification
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Icon(
                          Icons.account_circle,
                          color: theme.colorScheme.primary,
                        ),
                        const SizedBox(width: 8),
                        Text(
                          'État de l\'authentification',
                          style: theme.textTheme.titleMedium?.copyWith(
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),
                    authState.when(
                      data: (isLoggedIn) => Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              Icon(
                                isLoggedIn ? Icons.check_circle : Icons.cancel,
                                color: isLoggedIn ? Colors.green : Colors.red,
                                size: 20,
                              ),
                              const SizedBox(width: 8),
                              Text(
                                isLoggedIn ? 'Connecté' : 'Non connecté',
                                style: TextStyle(
                                  color: isLoggedIn ? Colors.green : Colors.red,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                            ],
                          ),
                          if (isLoggedIn) ...[
                            const SizedBox(height: 8),
                            userProfile.when(
                              data: (profile) => profile != null
                                  ? Column(
                                      crossAxisAlignment: CrossAxisAlignment.start,
                                      children: [
                                        Text('👤 Utilisateur: ${profile['username'] ?? 'N/A'}'),
                                        Text('📧 Email: ${profile['email'] ?? 'N/A'}'),
                                        Text('🏷️ Type: ${profile['user_type'] ?? 'N/A'}'),
                                      ],
                                    )
                                  : const Text('Profil non disponible'),
                              loading: () => const Text('Chargement du profil...'),
                              error: (e, _) => Text('Erreur profil: $e'),
                            ),
                            const SizedBox(height: 12),
                            ElevatedButton.icon(
                              onPressed: () async {
                                final loginNotifier = ref.read(loginProvider.notifier);
                                await loginNotifier.logout();
                                ref.invalidate(authStateProvider);
                                ref.invalidate(userProfileProvider);
                              },
                              icon: const Icon(Icons.logout),
                              label: const Text('Se déconnecter'),
                              style: ElevatedButton.styleFrom(
                                backgroundColor: Colors.red,
                                foregroundColor: Colors.white,
                              ),
                            ),
                          ],
                        ],
                      ),
                      loading: () => const Row(
                        children: [
                          SizedBox(
                            width: 16,
                            height: 16,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          ),
                          SizedBox(width: 8),
                          Text('Vérification...'),
                        ],
                      ),
                      error: (e, _) => Text(
                        'Erreur: $e',
                        style: const TextStyle(color: Colors.red),
                      ),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 24),

            // Widget d'authentification si non connecté
            authState.when(
              data: (isLoggedIn) => !isLoggedIn
                  ? EnhancedAuthWidget(
                      title: 'Connexion au Projet Principal',
                      onLoginSuccess: () {
                        // Rafraîchir les providers après connexion
                        ref.invalidate(authStateProvider);
                        ref.invalidate(userProfileProvider);
                      },
                    )
                  : const SizedBox.shrink(),
              loading: () => const SizedBox.shrink(),
              error: (_, __) => EnhancedAuthWidget(
                title: 'Connexion au Projet Principal',
                onLoginSuccess: () {
                  ref.invalidate(authStateProvider);
                  ref.invalidate(userProfileProvider);
                },
              ),
            ),

            // Informations techniques
            const SizedBox(height: 24),
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Icon(
                          Icons.info,
                          color: theme.colorScheme.primary,
                        ),
                        const SizedBox(width: 8),
                        Text(
                          'Fonctionnalités intégrées',
                          style: theme.textTheme.titleMedium?.copyWith(
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),
                    const Text(
                      '🔥 Gestion hybride des tokens (mémoire + storage)\n'
                      '✅ Résistant aux erreurs OperationError du web\n'
                      '🚀 API fonctionnelle avec 21 résumés récupérés\n'
                      '🎯 Interface utilisateur réactive\n'
                      '🔄 Rafraîchissement automatique des tokens\n'
                      '🛡️ Gestion d\'erreurs robuste\n'
                      '📱 Compatible mobile et web',
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildFeatureChip(String label, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: color.withOpacity(0.3)),
      ),
      child: Text(
        label,
        style: TextStyle(
          color: color.withOpacity(0.8),
          fontSize: 12,
          fontWeight: FontWeight.bold,
        ),
      ),
    );
  }
}
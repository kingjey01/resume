import 'package:flutter/material.dart';
import 'package:resume_plus_clean/theme/app_theme.dart';

class TermsOfServiceScreen extends StatelessWidget {
  const TermsOfServiceScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final topPadding = MediaQuery.of(context).padding.top;

    return Scaffold(
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      body: CustomScrollView(
        slivers: [
          // Header
          SliverAppBar(
            expandedHeight: 120,
            pinned: true,
            backgroundColor: AppTheme.primaryBlue,
            foregroundColor: Colors.white,
            flexibleSpace: FlexibleSpaceBar(
              title: const Text(
                "Conditions d'Utilisation",
                style: TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.w600,
                  fontSize: 16,
                ),
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
              titlePadding: const EdgeInsets.only(left: 72, bottom: 16, right: 16),
              background: Container(
                decoration: const BoxDecoration(
                  gradient: LinearGradient(
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                    colors: [
                      AppTheme.primaryBlueDark,
                      AppTheme.primaryBlue,
                      AppTheme.primaryBlueLight,
                    ],
                  ),
                ),
              ),
            ),
          ),
          
          // Contenu
          SliverPadding(
            padding: const EdgeInsets.all(20),
            sliver: SliverList(
              delegate: SliverChildListDelegate([
                _buildSection(
                  textColor: theme.colorScheme.onSurface,
                  title: '1. Acceptation des Conditions',
                  content: '''
En utilisant l'application Résumé+, vous acceptez les présentes conditions d'utilisation. Si vous n'acceptez pas ces conditions, n'utilisez pas notre application.

Ces conditions s'appliquent à tous les utilisateurs de Résumé+.
                  ''',
                ),
                
                _buildSection(
                  textColor: theme.colorScheme.onSurface,
                  title: '2. Description du Service',
                  content: '''
Résumé+ est une application mobile qui permet :
• D'accéder à des résumés de cours académiques
• D'acheter des résumés collectifs
• De souscrire à des abonnements pour accéder à du contenu premium
• De bénéficier d'exercices et corrections

Notre service est destiné aux étudiants et enseignants.
                  ''',
                ),
                
                _buildSection(
                  textColor: theme.colorScheme.onSurface,
                  title: '3. Compte Utilisateur',
                  content: '''
Pour utiliser Résumé+, vous devez :
• Créer un compte avec des informations exactes
• Maintenir vos informations à jour
• Ne pas partager votre compte avec des tiers

Vous êtes responsable de toutes les activités effectuées depuis votre compte.
                  ''',
                ),
                
                _buildSection(
                  textColor: theme.colorScheme.onSurface,
                  title: '4. Abonnements et Paiements',
                  content: '''
Nos abonnements offrent :
• Accès aux exercices et corrections
• Support prioritaire

Paiements :
• Traitement sécurisé via Mobile Money
• Renouvellement automatique (optionnel)
• Annulation possible à tout moment
• Pas de remboursement pour les services utilisés
                  ''',
                ),
                
                _buildSection(
                  textColor: theme.colorScheme.onSurface,
                  title: '5. Contenu et Propriété Intellectuelle',
                  content: '''
Les résumés disponibles sur Résumé+ sont :
• Créés par des Chefs de Promotion qualifiés
• Validés par notre équipe éditoriale
• Protégés par le droit d'auteur

Vous pouvez :
• Consulter les résumés pour usage personnel

Vous ne pouvez pas :
• Revendre ou redistribuer les résumés
• Publier les résumés sur d'autres plateformes
• Utiliser les résumés à des fins commerciales
• Télécharger ou exporter les résumés (fonction désactivée)
• Partager votre compte ou les résumés achetés avec d'autres utilisateurs

Téléchargement désactivé :
La fonctionnalité de téléchargement est intentionnellement désactivée pour protéger les contenus achetés et prévenir le partage non autorisé entre utilisateurs. Vous pouvez consulter vos résumés achetés en ligne uniquement via l'application.
                  ''',
                ),
                
                _buildSection(
                  textColor: theme.colorScheme.onSurface,
                  title: '6. Comportement de l\'Utilisateur',
                  content: '''
Vous vous engagez à ne pas :
• Publier de contenu offensant ou inapproprié
• Harceler d'autres utilisateurs
• Tenter de pirater notre système
• Utiliser l'application à des fins illégales
• Perturber le fonctionnement normal du service

Tout non-respect peut entraîner la suspension de votre compte.
                  ''',
                ),
                
                _buildSection(
                  textColor: theme.colorScheme.onSurface,
                  title: '7. Confidentialité',
                  content: '''
Nous respectons votre vie privée conformément à notre politique de confidentialité.

Nous collectons et utilisons vos données pour :
• Fournir nos services
• Améliorer votre expérience
• Communiquer avec vous
• Assurer la sécurité de notre plateforme

Consultez notre politique de confidentialité pour plus de détails.
                  ''',
                ),
                
                _buildSection(
                  textColor: theme.colorScheme.onSurface,
                  title: '8. Disponibilité du Service',
                  content: '''
Nous nous efforçons de maintenir Résumé+ disponible en permanence, mais :
• Le service peut être indisponible pour maintenance
• Des interruptions peuvent survenir pour des raisons techniques
• Nous ne garantissons pas une disponibilité à 100%

Nous ne sommes pas responsables des pertes dues à des interruptions de service.
                  ''',
                ),
                
                _buildSection(
                  textColor: theme.colorScheme.onSurface,
                  title: '9. Limitation de Responsabilité',
                  content: '''
Résumé+ est fourni "en l'état". Nous ne garantissons pas :
• L'exactitude de tous les résumés
• L'absence d'erreurs dans le contenu
• La compatibilité avec tous les appareils

Notre responsabilité est limitée au montant payé pour le service concerné.
                  ''',
                ),
                
                _buildSection(
                  textColor: theme.colorScheme.onSurface,
                  title: '10. Résiliation',
                  content: '''
Nous pouvons résilier votre compte si :
• Vous violez ces conditions d'utilisation
• Vous utilisez l'application de manière frauduleuse
• Vous ne respectez pas les droits d'auteur
• Votre comportement nuit à d'autres utilisateurs

Vous pouvez résilier votre compte à tout moment depuis les paramètres.
                  ''',
                ),
                
                _buildSection(
                  textColor: theme.colorScheme.onSurface,
                  title: '11. Modifications des Conditions',
                  content: '''
Nous pouvons modifier ces conditions d'utilisation. Les modifications vous seront notifiées par :
• E-mail
• Notification dans l'application
• Publication sur notre site web

Les modifications prennent effet 7 jours après notification.
                  ''',
                ),
                
                _buildSection(
                  textColor: theme.colorScheme.onSurface,
                  title: '12. Droit Applicable',
                  content: '''
Ces conditions sont régies par le droit congolais. Tout litige sera soumis aux tribunaux compétents de la République Démocratique du Congo.

En cas de litige, nous privilégions une résolution à l'amiable.
                  ''',
                ),
                
                _buildSection(
                  textColor: theme.colorScheme.onSurface,
                  title: '13. Contact',
                  content: '''
Pour toute question concernant ces conditions :
• E-mail : jeyyeta01@gmail.com
• Téléphone : 0996816806

Nous sommes à votre disposition pour clarifier ces conditions.
                  ''',
                ),
                
                const SizedBox(height: 40),
                
                // Date de mise à jour
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: theme.colorScheme.surface,
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: theme.colorScheme.outline.withOpacity(0.2)),
                  ),
                  child: Row(
                    children: [
                      Icon(Icons.info_outline, color: theme.colorScheme.primary),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Text(
                          'Dernière mise à jour : 29 Mars 2026',
                          style: theme.textTheme.bodySmall?.copyWith(
                            color: theme.colorScheme.onSurface.withOpacity(0.7),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
                
                const SizedBox(height: 40),
              ]),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSection({
    required String title,
    required String content,
    required Color textColor,
  }) {
    return Container(
      margin: const EdgeInsets.only(bottom: 24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            title,
            style: const TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.w700,
              color: AppTheme.primaryBlue,
            ),
          ),
          const SizedBox(height: 12),
          Text(
            content.trim(),
            style: TextStyle(
              fontSize: 15,
              height: 1.6,
              color: textColor,
            ),
          ),
        ],
      ),
    );
  }
}

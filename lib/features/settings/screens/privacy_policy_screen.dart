import 'package:flutter/material.dart';
import 'package:resume_plus_clean/theme/app_theme.dart';

class PrivacyPolicyScreen extends StatelessWidget {
  const PrivacyPolicyScreen({super.key});

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
                'Politique de Confidentialité',
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
                  title: '1. Collecte des Informations',
                  content: '''
Nous collectons les informations suivantes :
• Informations personnelles : nom, prénom, adresse e-mail, numéro de téléphone
• Informations académiques : université, filière, promotion
• Informations d'utilisation : historique des achats, préférences
• Données techniques : adresse IP, type d'appareil, système d'exploitation

Ces informations sont collectées lors de :
• Création de votre compte
• Utilisation de l'application
• Achats de résumés et abonnements
                  ''',
                ),
                
                _buildSection(
                  textColor: theme.colorScheme.onSurface,
                  title: '2. Utilisation des Données',
                  content: '''
Vos données sont utilisées pour :
• Fournir et améliorer nos services
• Traiter vos achats et abonnements
• Personnaliser votre expérience
• Communiquer avec vous
• Assurer la sécurité de notre plateforme
• Prévenir le partage non autorisé de contenu acheté

Protection des contenus achetés :
Nous désactivons intentionnellement la fonction de téléchargement pour protéger les résumés achetés et empêcher leur partage entre utilisateurs. Cette mesure assure que chaque utilisateur achète individuellement son accès aux contenus, respectant ainsi les droits des créateurs et notre modèle économique.
                  ''',
                ),
                
                _buildSection(
                  textColor: theme.colorScheme.onSurface,
                  title: '3. Partage des Données',
                  content: '''
Nous ne partageons vos données personnelles avec des tiers que dans les cas suivants :
• Fournisseurs de paiement (pour traiter vos transactions)
• Autorités légales (si requis par la loi)
• Partenaires techniques (pour le fonctionnement de l'application)
• Avec votre consentement explicite
                  ''',
                ),
                
                _buildSection(
                  textColor: theme.colorScheme.onSurface,
                  title: '4. Sécurité des Données',
                  content: '''
Nous mettons en œuvre des mesures de sécurité appropriées :
• Chiffrement des données sensibles
• Accès limité aux données personnelles
• Surveillance régulière de notre système
• Mises à jour régulières de nos protocoles de sécurité
                  ''',
                ),
                
                _buildSection(
                  textColor: theme.colorScheme.onSurface,
                  title: '5. Vos Droits',
                  content: '''
Vous avez le droit de :
• Accéder à vos données personnelles
• Modifier vos informations
• Supprimer votre compte
• Vous opposer au traitement de vos données
• Demander la portabilité de vos données
                  ''',
                ),
                
                _buildSection(
                  textColor: theme.colorScheme.onSurface,
                  title: '6. Conservation des Données',
                  content: '''
Nous conservons vos données pendant :
• La durée de votre compte actif
• 5 ans après suppression du compte (pour obligations légales)
• Périodes plus longues si requis par la loi

Les données financières sont conservées 7 ans pour raisons fiscales.
                  ''',
                ),
                
                _buildSection(
                  textColor: theme.colorScheme.onSurface,
                  title: '7. Cookies et Technologies Similaires',
                  content: '''
Nous utilisons des cookies pour :
• Maintenir votre session active
• Mémoriser vos préférences
• Analyser l'utilisation de notre application
• Améliorer nos services

Vous pouvez gérer les cookies dans les paramètres de votre navigateur.
                  ''',
                ),
                
                _buildSection(
                  textColor: theme.colorScheme.onSurface,
                  title: '8. Modifications de cette Politique',
                  content: '''
Nous pouvons modifier cette politique de confidentialité. Les modifications vous seront notifiées par :
• E-mail
• Notification dans l'application
• Publication sur notre site web

Les modifications prennent effet 30 jours après notification.
                  ''',
                ),
                
                _buildSection(
                  textColor: theme.colorScheme.onSurface,
                  title: '9. Contact',
                  content: '''
Pour toute question concernant cette politique de confidentialité :
• E-mail : jeyyeta01@gmail.com
• Téléphone : 0996816806

Nous répondrons à votre demande dans un délai de 30 jours.
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

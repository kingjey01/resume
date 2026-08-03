import 'package:flutter/material.dart';
import 'package:resume_plus_clean/theme/app_theme.dart';

class AboutScreen extends StatelessWidget {
  const AboutScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      backgroundColor: theme.scaffoldBackgroundColor,
      body: CustomScrollView(
        slivers: [
          // ─── Header fixe ────────────────────────────────────────────────────
          SliverAppBar(
            pinned: true,
            floating: false,
            snap: false,
            elevation: 0,
            backgroundColor: AppTheme.primaryBlueDark,
            foregroundColor: Colors.white,
            title: const Text(
              'À propos',
              style: TextStyle(fontWeight: FontWeight.w700, fontSize: 18),
            ),
            centerTitle: true,
            leading: IconButton(
              icon: const Icon(Icons.arrow_back_rounded),
              onPressed: () => Navigator.of(context).pop(),
            ),
          ),

          // ─── Contenu ──────────────────────────────────────────────────────
          // ─── Bannière Résumé+ (scrollable) ─────────────────────────────────
          SliverToBoxAdapter(
            child: Container(
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
              child: SafeArea(
                top: false,
                bottom: false,
                child: Padding(
                  padding: const EdgeInsets.symmetric(vertical: 24),
                  child: Column(
                    children: [
                      Container(
                        width: 72,
                        height: 72,
                        decoration: BoxDecoration(
                          color: Colors.white.withOpacity(0.2),
                          shape: BoxShape.circle,
                        ),
                        child: const Icon(Icons.menu_book_rounded, size: 38, color: Colors.white),
                      ),
                      const SizedBox(height: 10),
                      const Text(
                        'Résumé+',
                        style: TextStyle(
                          color: Colors.white,
                          fontSize: 22,
                          fontWeight: FontWeight.w800,
                          letterSpacing: 0.5,
                        ),
                      ),
                      const Text(
                        'v1.0.0',
                        style: TextStyle(color: Colors.white70, fontSize: 12),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),

          // ─── Contenu ──────────────────────────────────────────────────────
          SliverList(
            delegate: SliverChildListDelegate([
              const SizedBox(height: 24),

              // ── Objectif de l'application ─────────────────────────────────
              _buildSection(
                theme: theme,
                icon: Icons.lightbulb_rounded,
                iconColor: const Color(0xFFFFC107),
                title: "Objectif de l'application",
                child: _buildParagraph(
                  theme,
                  "Résumé+ est une application mobile intelligente conçue pour les étudiants et les chargés de promotion. "
                  "Elle exploite l'intelligence artificielle pour transformer automatiquement vos enregistrements audio de cours en résumés textuels clairs, "
                  "accessibles à tous et enrichis de quiz interactifs.",
                ),
              ),

              // ── Comment ça fonctionne ──────────────────────────────────────
              _buildSection(
                theme: theme,
                icon: Icons.bolt_rounded,
                iconColor: AppTheme.primaryBlue,
                title: 'Comment ça fonctionne',
                child: Column(
                  children: [
                    _buildStep(theme, '1', Icons.mic_rounded, 'Enregistrement audio',
                        'Un cours est enregistré en audio sur le terrain.'),
                    _buildStep(theme, '2', Icons.graphic_eq_rounded, 'Transcription par l\'IA',
                        'L\'intelligence artificielle transcrit l\'audio en texte et génère un résumé structuré et concis.'),
                    _buildStep(theme, '3', Icons.verified_rounded, 'Validation par le CP',
                        'Le Chargé de Promotion vérifie et valide le résumé avant sa publication.'),
                    _buildStep(theme, '4', Icons.auto_stories_rounded, 'Lecture & Quiz',
                        'Les étudiants lisent ou écoutent les résumés via la synthèse vocale et s\'évaluent avec des quiz générés par l\'IA.',
                        isLast: true),
                  ],
                ),
              ),

              // ── Fonctionnalités clés ───────────────────────────────────────
              _buildSection(
                theme: theme,
                icon: Icons.stars_rounded,
                iconColor: const Color(0xFF9C27B0),
                title: 'Fonctionnalités clés',
                child: Wrap(
                  spacing: 10,
                  runSpacing: 10,
                  children: [
                    _buildFeatureChip(theme, Icons.graphic_eq_rounded, 'Audio → Résumé IA'),
                    _buildFeatureChip(theme, Icons.volume_up_rounded, 'Lecture vocale (TTS)'),
                    _buildFeatureChip(theme, Icons.shopping_cart_rounded, 'Marketplace résumés'),
                    _buildFeatureChip(theme, Icons.quiz_rounded, 'Quiz interactifs'),
                    _buildFeatureChip(theme, Icons.notifications_rounded, 'Notifications push'),
                    _buildFeatureChip(theme, Icons.card_membership_rounded, 'Abonnements'),
                    _buildFeatureChip(theme, Icons.dark_mode_rounded, 'Mode sombre'),
                    _buildFeatureChip(theme, Icons.lock_rounded, 'Sécurité des données'),
                  ],
                ),
              ),

              // ── Guide CP ──────────────────────────────────────────────────
              _buildSection(
                theme: theme,
                icon: Icons.admin_panel_settings_rounded,
                iconColor: const Color(0xFF2196F3),
                title: 'Guide — Chargé de Promotion (CP)',
                child: Column(
                  children: [
                    _buildRoleBanner(
                      theme,
                      color: const Color(0xFF2196F3),
                      label: 'Rôle : Chargé de Promotion',
                      subtitle: 'Vous gérez et publiez les résumés de votre promotion.',
                    ),
                    const SizedBox(height: 14),
                    _buildGuideItem(theme, Icons.upload_file_rounded,
                        'Soumettre un enregistrement',
                        'Depuis l\'accueil, appuyez sur le bouton d\'enregistrement, importez votre fichier audio et soumettez-le. '
                        'L\'IA génère automatiquement un résumé en quelques instants.'),
                    _buildGuideItem(theme, Icons.rule_rounded,
                        'Valider les résumés',
                        'Dans l\'onglet "Validation" de la barre de navigation, retrouvez tous les résumés en attente. '
                        'Lisez-les, corrigez si nécessaire, puis validez pour les rendre accessibles aux étudiants.'),
                    _buildGuideItem(theme, Icons.notifications_active_rounded,
                        'Recevoir des notifications',
                        'Vous êtes notifié automatiquement lorsqu\'un nouveau résumé est généré pour votre promotion et lorsqu\'un étudiant achète un résumé.'),
                    _buildGuideItem(theme, Icons.bar_chart_rounded,
                        'Suivre votre tableau de bord',
                        'Consultez les badges de la barre de navigation pour suivre le nombre de résumés en attente de validation.',
                        isLast: true),
                  ],
                ),
              ),

              // ── Guide Étudiant ─────────────────────────────────────────────
              _buildSection(
                theme: theme,
                icon: Icons.school_rounded,
                iconColor: const Color(0xFF4CAF50),
                title: 'Guide — Étudiant',
                child: Column(
                  children: [
                    _buildRoleBanner(
                      theme,
                      color: const Color(0xFF4CAF50),
                      label: 'Rôle : Utilisateur / Étudiant',
                      subtitle: 'Vous accédez aux résumés validés et vous évaluez avec des quiz.',
                    ),
                    const SizedBox(height: 14),
                    _buildGuideItem(theme, Icons.home_rounded,
                        'Parcourir les résumés',
                        'Depuis l\'onglet "Accueil", consultez tous les résumés validés de votre promotion, '
                        'filtrables par matière et triés par date.'),
                    _buildGuideItem(theme, Icons.volume_up_rounded,
                        'Écouter un résumé (TTS)',
                        'Ouvrez un résumé et appuyez sur le bouton de lecture pour l\'écouter grâce à la synthèse vocale. '
                        'Vous pouvez mettre en pause, reprendre et ajuster la vitesse de lecture.'),
                    _buildGuideItem(theme, Icons.shopping_cart_rounded,
                        'Acheter un résumé',
                        'Dans l\'onglet "Découvrir", retrouvez des résumés supplémentaires disponibles à l\'achat. '
                        'Payez via Mobile Money ou vos points accumulés.'),
                    _buildGuideItem(theme, Icons.quiz_rounded,
                        'Faire des exercices & quiz',
                        'Dans l\'onglet "Exercices", accédez aux quiz générés par l\'IA pour tester vos connaissances '
                        'sur les cours déjà résumés.'),
                    _buildGuideItem(theme, Icons.card_membership_rounded,
                        'Gérer son abonnement',
                        'Dans "Paramètres → Abonnement", souscrivez à un plan pour débloquer l\'accès illimité '
                        'aux résumés premium et à tous les quiz.',
                        isLast: true),
                  ],
                ),
              ),

              // ── Contact ───────────────────────────────────────────────────
              _buildSection(
                theme: theme,
                icon: Icons.contact_support_rounded,
                iconColor: const Color(0xFFFF5722),
                title: 'Contact & Support',
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    _buildContactRow(theme, Icons.email_rounded, 'Email', 'jeyyeta01@gmail.com'),
                    const SizedBox(height: 8),
                    _buildContactRow(theme, Icons.phone_rounded, 'WhatsApp', '+243 996 816 806'),
                    const SizedBox(height: 8),
                    _buildContactRow(theme, Icons.access_time_rounded, 'Disponibilité',
                        'Lun–Ven : 8h00–17h00 · Sam : 9h00–13h00'),
                  ],
                ),
              ),

              // ── Footer ────────────────────────────────────────────────────
              const SizedBox(height: 8),
              Center(
                child: Padding(
                  padding: const EdgeInsets.only(bottom: 40),
                  child: Text(
                    '© 2024 Résumé+ · Tous droits réservés',
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: theme.colorScheme.onSurface.withOpacity(0.4),
                    ),
                  ),
                ),
              ),
            ]),
          ),
        ],
      ),
    );
  }

  // ─── Helpers ──────────────────────────────────────────────────────────────

  Widget _buildSection({
    required ThemeData theme,
    required IconData icon,
    required Color iconColor,
    required String title,
    required Widget child,
  }) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
      child: Container(
        padding: const EdgeInsets.all(18),
        decoration: BoxDecoration(
          color: theme.colorScheme.surface,
          borderRadius: BorderRadius.circular(18),
          boxShadow: AppTheme.softShadow,
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  width: 38,
                  height: 38,
                  decoration: BoxDecoration(
                    color: iconColor.withOpacity(0.12),
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: Icon(icon, color: iconColor, size: 20),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(
                    title,
                    style: theme.textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.w700,
                      color: theme.colorScheme.onSurface,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            child,
          ],
        ),
      ),
    );
  }

  Widget _buildParagraph(ThemeData theme, String text) {
    return Text(
      text,
      style: theme.textTheme.bodyMedium?.copyWith(
        color: theme.colorScheme.onSurface.withOpacity(0.75),
        height: 1.6,
      ),
    );
  }

  Widget _buildStep(
    ThemeData theme,
    String number,
    IconData icon,
    String title,
    String description, {
    bool isLast = false,
  }) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Column(
          children: [
            Container(
              width: 36,
              height: 36,
              decoration: BoxDecoration(
                color: AppTheme.primaryBlue.withOpacity(0.12),
                shape: BoxShape.circle,
              ),
              child: Center(
                child: Text(
                  number,
                  style: const TextStyle(
                    color: AppTheme.primaryBlue,
                    fontWeight: FontWeight.w800,
                    fontSize: 14,
                  ),
                ),
              ),
            ),
            if (!isLast)
              Container(
                width: 2,
                height: 36,
                color: AppTheme.primaryBlue.withOpacity(0.15),
              ),
          ],
        ),
        const SizedBox(width: 12),
        Expanded(
          child: Padding(
            padding: EdgeInsets.only(bottom: isLast ? 0 : 12),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Icon(icon, size: 16, color: AppTheme.primaryBlue),
                    const SizedBox(width: 6),
                    Text(title,
                        style: theme.textTheme.titleSmall
                            ?.copyWith(fontWeight: FontWeight.w600, color: theme.colorScheme.onSurface)),
                  ],
                ),
                const SizedBox(height: 4),
                Text(
                  description,
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: theme.colorScheme.onSurface.withOpacity(0.65),
                    height: 1.5,
                  ),
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildFeatureChip(ThemeData theme, IconData icon, String label) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 7),
      decoration: BoxDecoration(
        color: AppTheme.primaryBlue.withOpacity(0.08),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: AppTheme.primaryBlue.withOpacity(0.2)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 14, color: AppTheme.primaryBlue),
          const SizedBox(width: 6),
          Text(
            label,
            style: theme.textTheme.bodySmall?.copyWith(
              color: AppTheme.primaryBlue,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildRoleBanner(
    ThemeData theme, {
    required Color color,
    required String label,
    required String subtitle,
  }) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
      decoration: BoxDecoration(
        color: color.withOpacity(0.08),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: color.withOpacity(0.25)),
      ),
      child: Row(
        children: [
          Icon(Icons.badge_rounded, color: color, size: 22),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(label,
                    style: theme.textTheme.titleSmall
                        ?.copyWith(fontWeight: FontWeight.w700, color: color)),
                const SizedBox(height: 2),
                Text(subtitle,
                    style: theme.textTheme.bodySmall?.copyWith(
                        color: theme.colorScheme.onSurface.withOpacity(0.6))),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildGuideItem(
    ThemeData theme,
    IconData icon,
    String title,
    String description, {
    bool isLast = false,
  }) {
    return Padding(
      padding: EdgeInsets.only(bottom: isLast ? 0 : 14),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 34,
            height: 34,
            margin: const EdgeInsets.only(top: 1),
            decoration: BoxDecoration(
              color: theme.colorScheme.primary.withOpacity(0.08),
              borderRadius: BorderRadius.circular(9),
            ),
            child: Icon(icon, size: 17, color: theme.colorScheme.primary),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title,
                    style: theme.textTheme.titleSmall?.copyWith(
                        fontWeight: FontWeight.w600,
                        color: theme.colorScheme.onSurface)),
                const SizedBox(height: 3),
                Text(description,
                    style: theme.textTheme.bodySmall?.copyWith(
                        color: theme.colorScheme.onSurface.withOpacity(0.62),
                        height: 1.5)),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildContactRow(ThemeData theme, IconData icon, String label, String value) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Icon(icon, size: 17, color: theme.colorScheme.primary),
        const SizedBox(width: 10),
        Expanded(
          child: RichText(
            text: TextSpan(
              children: [
                TextSpan(
                  text: '$label : ',
                  style: theme.textTheme.bodySmall?.copyWith(
                    fontWeight: FontWeight.w700,
                    color: theme.colorScheme.onSurface,
                  ),
                ),
                TextSpan(
                  text: value,
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: theme.colorScheme.onSurface.withOpacity(0.7),
                  ),
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }
}

import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:resume_plus_clean/features/upload/screens/associate_prof_cours_screen.dart';
import 'package:resume_plus_clean/features/upload/screens/create_cours_screen.dart';
import 'package:resume_plus_clean/features/upload/screens/create_professeur_screen.dart';
import 'package:resume_plus_clean/features/upload/screens/manual_entry_screen.dart';
import 'package:resume_plus_clean/features/upload/screens/record_audio_screen.dart';
import 'package:resume_plus_clean/features/upload/screens/record_audio_screen_web_safe.dart';
import 'package:resume_plus_clean/theme/app_theme.dart';

class UploadChoiceScreen extends StatelessWidget {
  const UploadChoiceScreen({super.key});

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
            // Header bleu
            Container(
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
                    'Menu Créer',
                    style: theme.textTheme.headlineMedium?.copyWith(color: Colors.white, fontWeight: FontWeight.w700),
                  ),
                  const SizedBox(height: 6),
                  Text(
                    'Que souhaitez-vous faire ?',
                    style: TextStyle(color: Colors.white.withOpacity(0.8), fontSize: 14),
                  ),
                ],
              ),
            ),

            const SizedBox(height: 24),

            // Option 1: Saisie manuelle
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20),
              child: _buildOptionCard(
                context: context,
                icon: Icons.edit_note_rounded,
                title: 'Saisie manuelle',
                description: 'Rédigez votre résumé directement dans l\'application',
                color: AppTheme.primaryBlue,
                onTap: () {
                  Navigator.of(context).push(
                    MaterialPageRoute(builder: (context) => const ManualEntryScreen()),
                  );
                },
              ),
            ),
            
            const SizedBox(height: 16),
            
            // Option 2: Enregistrement audio
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20),
              child: _buildOptionCard(
                context: context,
                icon: Icons.mic_rounded,
                title: kIsWeb ? 'IA Résumé (Web)' : 'Enregistrement audio',
                description: kIsWeb 
                    ? 'Générez un résumé IA simulé pour le cours sélectionné'
                    : 'Enregistrez votre cours et créez un résumé automatiquement',
                color: kIsWeb ? const Color(0xFF7C3AED) : AppTheme.error,
                onTap: () {
                  Navigator.of(context).push(
                    MaterialPageRoute(
                      builder: (context) => kIsWeb 
                          ? const RecordAudioScreenWebSafe()
                          : const RecordAudioScreen(),
                    ),
                  );
                },
              ),
            ),
            
            const SizedBox(height: 16),

            // Option 3: Créer un professeur
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20),
              child: _buildOptionCard(
                context: context,
                icon: Icons.person_add_rounded,
                title: 'Créer un professeur',
                description: 'Enregistrez un professeur et gérez la liste existante',
                color: const Color(0xFF10B981),
                onTap: () {
                  Navigator.of(context).push(
                    MaterialPageRoute(
                        builder: (context) => const CreateProfesseurScreen()),
                  );
                },
              ),
            ),

            const SizedBox(height: 16),

            // Option 4: Créer un cours
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20),
              child: _buildOptionCard(
                context: context,
                icon: Icons.menu_book_rounded,
                title: 'Créer un cours',
                description: 'Enregistrez un cours et gérez la liste existante',
                color: const Color(0xFFF59E0B),
                onTap: () {
                  Navigator.of(context).push(
                    MaterialPageRoute(
                        builder: (context) => const CreateCoursScreen()),
                  );
                },
              ),
            ),

            const SizedBox(height: 16),

            // Option 5: Associer professeur à cours
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20),
              child: _buildOptionCard(
                context: context,
                icon: Icons.link_rounded,
                title: 'Associer prof. à cours',
                description: 'Liez un professeur à un cours pour le remplissage automatique',
                color: const Color(0xFF8B5CF6),
                onTap: () {
                  Navigator.of(context).push(
                    MaterialPageRoute(
                        builder: (context) =>
                            const AssociateProfCoursScreen()),
                  );
                },
              ),
            ),

            const SizedBox(height: 24),

            const SizedBox(height: 40),
          ],
        ),
      ),
    );
  }

  Widget _buildOptionCard({
    required BuildContext context,
    required IconData icon,
    required String title,
    required String description,
    required Color color,
    required VoidCallback onTap,
  }) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: AppTheme.softShadow,
      ),
      child: Material(
        color: Colors.transparent,
        borderRadius: BorderRadius.circular(16),
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(16),
          child: Padding(
            padding: const EdgeInsets.all(20),
            child: Row(
              children: [
                Container(
                  width: 56, height: 56,
                  decoration: BoxDecoration(
                    color: color.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(16),
                  ),
                  child: Icon(icon, size: 28, color: color),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        title,
                        style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600, color: AppTheme.textPrimary),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        description,
                        style: const TextStyle(color: AppTheme.textLight, fontSize: 13),
                        maxLines: 2, overflow: TextOverflow.ellipsis,
                      ),
                    ],
                  ),
                ),
                const SizedBox(width: 8),
                Container(
                  width: 32, height: 32,
                  decoration: BoxDecoration(
                    color: color.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Icon(Icons.arrow_forward_ios_rounded, color: color, size: 14),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

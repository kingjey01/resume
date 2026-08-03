import 'package:flutter/material.dart';
import 'package:resume_plus_clean/features/auth/screens/phone_login_screen.dart';
import 'package:resume_plus_clean/services/storage_service.dart';
import 'package:resume_plus_clean/theme/app_theme.dart';

class OnboardingScreen extends StatefulWidget {
  const OnboardingScreen({super.key});

  @override
  State<OnboardingScreen> createState() => _OnboardingScreenState();
}

class _OnboardingScreenState extends State<OnboardingScreen> {
  final PageController _pageController = PageController();
  int _currentPage = 0;

  final List<Map<String, dynamic>> _onboardingData = [
    {
      'icon': Icons.graphic_eq_rounded,
      'title': 'Audio en Texte, par l\'IA',
      'description': 'Importez vos enregistrements de cours. Notre intelligence artificielle les transforme en résumés textuels clairs et concis.',
    },
    {
      'icon': Icons.shopping_cart_rounded,
      'title': 'Achetez des Résumés',
      'description': 'Explorez notre marketplace pour trouver et acheter des résumés de haute qualité, créés par d\'autres membres de la communauté.',
    },
    {
      'icon': Icons.quiz_rounded,
      'title': 'Quiz & Exercices Premium',
      'description': 'Évaluez vos acquis en temps réel grâce à des quiz et exercices générés par l\'intelligence artificielle, conçus pour renforcer votre apprentissage de manière ciblée et efficace.',
    },
  ];

  @override
  Widget build(BuildContext context) {
    final topPadding = MediaQuery.of(context).padding.top;

    return Scaffold(
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      body: Column(
        children: [
          // Top bar avec bouton Passer
          Padding(
            padding: EdgeInsets.only(top: topPadding + 12, right: 20),
            child: Align(
              alignment: Alignment.topRight,
              child: TextButton(
                onPressed: _skipOnboarding,
                child: Text('Passer', style: TextStyle(color: Theme.of(context).colorScheme.onSurface.withOpacity(0.5), fontWeight: FontWeight.w600, fontSize: 14)),
              ),
            ),
          ),
          // Contenu des pages
          Expanded(
            child: PageView.builder(
              controller: _pageController,
              itemCount: _onboardingData.length,
              onPageChanged: (index) {
                setState(() {
                  _currentPage = index;
                });
              },
              itemBuilder: (context, index) {
                return OnboardingPageContent(data: _onboardingData[index]);
              },
            ),
          ),
          // Indicateurs et bouton
          Padding(
            padding: const EdgeInsets.fromLTRB(24, 0, 24, 40),
            child: Column(
              children: [
                // Dots
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: List.generate(
                    _onboardingData.length,
                    (index) => _buildDot(index),
                  ),
                ),
                const SizedBox(height: 32),
                // Bouton
                SizedBox(
                  width: double.infinity,
                  height: 52,
                  child: ElevatedButton(
                    onPressed: _nextPage,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppTheme.primaryBlue,
                      foregroundColor: Colors.white,
                      elevation: 0,
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                    ),
                    child: Text(
                      _currentPage == _onboardingData.length - 1 ? 'Commencer' : 'Suivant',
                      style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildDot(int index) {
    final isActive = _currentPage == index;
    return AnimatedContainer(
      duration: const Duration(milliseconds: 250),
      margin: const EdgeInsets.symmetric(horizontal: 4),
      height: 8,
      width: isActive ? 28 : 8,
      decoration: BoxDecoration(
        color: isActive ? AppTheme.primaryBlue : AppTheme.primaryBlue.withOpacity(0.2),
        borderRadius: BorderRadius.circular(4),
      ),
    );
  }

  void _nextPage() {
    if (_currentPage == _onboardingData.length - 1) {
      _skipOnboarding();
    } else {
      _pageController.nextPage(
        duration: const Duration(milliseconds: 300),
        curve: Curves.ease,
      );
    }
  }

  void _skipOnboarding() async {
    // Marquer l'onboarding comme terminé pour ne plus le réafficher
    await StorageService().setOnboardingComplete();
    if (mounted) {
      Navigator.of(context).pushReplacement(
        MaterialPageRoute(builder: (context) => const PhoneLoginScreen()),
      );
    }
  }
}

class OnboardingPageContent extends StatelessWidget {
  final Map<String, dynamic> data;

  const OnboardingPageContent({super.key, required this.data});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final cs = theme.colorScheme;

    return SingleChildScrollView(
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 36, vertical: 20),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const SizedBox(height: 40),
            // Icône dans un cercle bleu
            Container(
              width: 120, height: 120,
              decoration: BoxDecoration(
                color: AppTheme.primaryBlue.withOpacity(0.1),
                shape: BoxShape.circle,
              ),
              child: Icon(
                data['icon'] as IconData? ?? Icons.error,
                size: 56,
                color: AppTheme.primaryBlue,
              ),
            ),
            const SizedBox(height: 40),
            Text(
              data['title']!,
              style: theme.textTheme.headlineSmall?.copyWith(
                fontWeight: FontWeight.w700,
                color: cs.onSurface, // ← s'adapte au mode clair/sombre
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 16),
            Text(
              data['description']!,
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: 15,
                color: cs.onSurface.withOpacity(0.7), // ← s'adapte au mode clair/sombre
                height: 1.5,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

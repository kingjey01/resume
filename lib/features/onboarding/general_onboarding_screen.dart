import 'package:flutter/material.dart';
import 'package:resume_plus_clean/features/app/screens/main_navigation_screen.dart';
import 'package:resume_plus_clean/services/storage_service.dart';
import 'package:resume_plus_clean/theme/app_theme.dart';

/// Onboarding général (2 pages) affiché APRÈS la complétion du profil, pour les
/// utilisateurs standards (étudiants), avant l'accueil.
///
/// Page 1 — « Découvrez des résumés générés par IA » (résumés gratuits du domaine).
/// Page 2 — « Commencez dès maintenant ! » (bouton Continuer).
///
/// À la fin, on persiste un flag pour ne plus le réafficher aux connexions suivantes.
class GeneralOnboardingScreen extends StatefulWidget {
  const GeneralOnboardingScreen({super.key});

  @override
  State<GeneralOnboardingScreen> createState() => _GeneralOnboardingScreenState();
}

class _GeneralOnboardingScreenState extends State<GeneralOnboardingScreen> {
  final PageController _pageController = PageController();
  int _currentPage = 0;
  bool _isFinishing = false;

  /// Termine l'onboarding : persiste le flag puis va à l'Accueil existant.
  Future<void> _finish() async {
    if (_isFinishing) return;
    _isFinishing = true;
    await StorageService().setGeneralOnboardingComplete();
    if (!mounted) return;
    Navigator.of(context).pushAndRemoveUntil(
      MaterialPageRoute(
        builder: (_) => MainNavigationScreen(key: MainNavigationScreen.navKey),
      ),
      (route) => false,
    );
  }

  void _nextPage() {
    if (_currentPage == 0) {
      _pageController.nextPage(
        duration: const Duration(milliseconds: 350),
        curve: Curves.easeOut,
      );
    } else {
      _finish();
    }
  }

  @override
  void dispose() {
    _pageController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final topPadding = MediaQuery.of(context).padding.top;

    return Scaffold(
      backgroundColor: Colors.white,
      body: Stack(
        children: [
          // ── Éléments décoratifs triangulaires bleu / bleu ciel ──────────
          // Maquette : fond blanc + triangles bleu ciel en haut-gauche,
          // bas-gauche et bas-droit (haut-droit laissé blanc).
          const Positioned(
            top: -70,
            left: -60,
            child: _DecorativeTriangle(size: 190, color: Color(0xFF9ABBF7)),
          ),
          const Positioned(
            bottom: -60,
            left: -70,
            child: _DecorativeTriangle(size: 200, color: Color(0xFFAFCBFA)),
          ),
          const Positioned(
            bottom: -80,
            right: -70,
            child: _DecorativeTriangle(size: 220, color: Color(0xFFDBE7FB)),
          ),
          Column(
            children: [
              // Bouton « Passer » (disponible dès la page 1)
              Padding(
                padding: EdgeInsets.only(top: topPadding + 8, right: 20),
                child: Align(
                  alignment: Alignment.topRight,
                  child: TextButton(
                    onPressed: _finish,
                    child: const Text(
                      'Passer',
                      style: TextStyle(
                        color: AppTheme.textLight,
                        fontWeight: FontWeight.w600,
                        fontSize: 14,
                      ),
                    ),
                  ),
                ),
              ),
              // Pages
              Expanded(
                child: PageView.builder(
                  controller: _pageController,
                  itemCount: 2,
                  onPageChanged: (index) => setState(() => _currentPage = index),
                  itemBuilder: (context, index) {
                    return index == 0 ? _buildPage1() : _buildPage2();
                  },
                ),
              ),
              // Indicateurs + bouton
              Padding(
                padding: const EdgeInsets.fromLTRB(24, 0, 24, 40),
                child: Column(
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: List.generate(2, (i) => _buildDot(i)),
                    ),
                    const SizedBox(height: 28),
                    SizedBox(
                      width: double.infinity,
                      height: 54,
                      child: ElevatedButton(
                        onPressed: _nextPage,
                        style: ElevatedButton.styleFrom(
                          backgroundColor: AppTheme.primaryBlue,
                          foregroundColor: Colors.white,
                          elevation: 0,
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(16),
                          ),
                        ),
                        child: Text(
                          _currentPage == 0 ? 'Suivant' : 'Continuer',
                          style: const TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ],
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
        color: isActive ? AppTheme.primaryBlue : AppTheme.primaryBlue.withOpacity(0.25),
        borderRadius: BorderRadius.circular(4),
      ),
    );
  }

  // ─── PAGE 1 : Découvrir les résumés gratuits ────────────────────────────────
  Widget _buildPage1() {
    return SingleChildScrollView(
      padding: const EdgeInsets.symmetric(horizontal: 28, vertical: 16),
      child: Column(
        children: [
          const SizedBox(height: 20),
          // Illustration
          Container(
            width: 140,
            height: 140,
            decoration: BoxDecoration(
              gradient: const LinearGradient(
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
                colors: [AppTheme.primaryBlueLight, AppTheme.primaryBlue],
              ),
              shape: BoxShape.circle,
              boxShadow: [
                BoxShadow(
                  color: AppTheme.primaryBlue.withOpacity(0.25),
                  blurRadius: 24,
                  offset: const Offset(0, 8),
                ),
              ],
            ),
            child: const Icon(
              Icons.auto_stories_rounded,
              color: Colors.white,
              size: 60,
            ),
          ),
          const SizedBox(height: 32),
          const Text(
            'Découvrez des résumés générés par IA',
            textAlign: TextAlign.center,
            style: TextStyle(
              fontSize: 24,
              fontWeight: FontWeight.w800,
              color: AppTheme.primaryBlueDark,
              height: 1.3,
            ),
          ),
          const SizedBox(height: 12),
          const Text(
            'Accédez à des résumés complets générés par intelligence artificielle, spécialement adaptés à votre domaine d\'étude.',
            textAlign: TextAlign.center,
            style: TextStyle(
              fontSize: 15,
              color: AppTheme.textSecondary,
              height: 1.5,
            ),
          ),
          const SizedBox(height: 28),
          // Cartes d'avantages
          _buildBenefitCard(
            icon: Icons.article_rounded,
            title: 'Résumés clairs et complets',
            subtitle: 'L\'essentiel du cours, structuré et lisible.',
            color: AppTheme.primaryBlue,
          ),
          const SizedBox(height: 12),
          _buildBenefitCard(
            icon: Icons.psychology_rounded,
            title: 'Approfondissez vos connaissances',
            subtitle: 'Comprenez mieux chaque notion de votre domaine.',
            color: const Color(0xFF8B5CF6),
          ),
          const SizedBox(height: 12),
          _buildBenefitCard(
            icon: Icons.explore_rounded,
            title: 'Mieux vous orienter dans vos études',
            subtitle: 'Retrouvez les concepts clés de vos matières.',
            color: const Color(0xFF10B981),
          ),
        ],
      ),
    );
  }

  Widget _buildBenefitCard({
    required IconData icon,
    required String title,
    required String subtitle,
    required Color color,
  }) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: color.withOpacity(0.06),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: color.withOpacity(0.2)),
      ),
      child: Row(
        children: [
          Container(
            width: 46,
            height: 46,
            decoration: BoxDecoration(
              color: color.withOpacity(0.12),
              shape: BoxShape.circle,
            ),
            child: Icon(icon, color: color, size: 24),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: const TextStyle(
                    fontSize: 15,
                    fontWeight: FontWeight.w700,
                    color: AppTheme.textPrimary,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  subtitle,
                  style: const TextStyle(
                    fontSize: 12.5,
                    color: AppTheme.textLight,
                    height: 1.4,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  // ─── PAGE 2 : Continuer vers l'application ──────────────────────────────────
  Widget _buildPage2() {
    return SingleChildScrollView(
      padding: const EdgeInsets.symmetric(horizontal: 28, vertical: 16),
      child: Column(
        children: [
          const SizedBox(height: 24),
          // Illustration
          Container(
            width: 140,
            height: 140,
            decoration: BoxDecoration(
              color: AppTheme.primaryBlue.withOpacity(0.08),
              shape: BoxShape.circle,
            ),
            child: const Icon(
              Icons.menu_book_rounded,
              color: AppTheme.primaryBlue,
              size: 64,
            ),
          ),
          const SizedBox(height: 32),
          const Text(
            'Commencez dès maintenant !',
            textAlign: TextAlign.center,
            style: TextStyle(
              fontSize: 24,
              fontWeight: FontWeight.w800,
              color: AppTheme.primaryBlueDark,
              height: 1.3,
            ),
          ),
          const SizedBox(height: 12),
          const Text(
            'Explorez les résumés gratuits disponibles et profitez pleinement de Résumé Plus pour exceller dans vos études.',
            textAlign: TextAlign.center,
            style: TextStyle(
              fontSize: 15,
              color: AppTheme.textSecondary,
              height: 1.5,
            ),
          ),
          const SizedBox(height: 28),
          // Zone informative : résumés gratuits du domaine d'étude
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(18),
            decoration: BoxDecoration(
              gradient: const LinearGradient(
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
                colors: [AppTheme.primaryBlueLight, AppTheme.primaryBlue],
              ),
              borderRadius: BorderRadius.circular(18),
              boxShadow: [
                BoxShadow(
                  color: AppTheme.primaryBlue.withOpacity(0.25),
                  blurRadius: 16,
                  offset: const Offset(0, 6),
                ),
              ],
            ),
            child: const Row(
              children: [
                Icon(Icons.recommend_rounded, color: Colors.white, size: 30),
                SizedBox(width: 14),
                Expanded(
                  child: Text(
                    'Des résumés gratuits correspondant à votre domaine d\'étude sont disponibles pour vous.',
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 14,
                      height: 1.4,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
          const Text(
            'Bonne découverte ! 👋',
            style: TextStyle(
              fontSize: 14,
              color: AppTheme.textLight,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }
}

/// Triangle décoratif bleu (élément visuel de la maquette).
class _DecorativeTriangle extends StatelessWidget {
  final double size;
  final Color color;

  const _DecorativeTriangle({required this.size, required this.color});

  @override
  Widget build(BuildContext context) {
    return IgnorePointer(
      child: CustomPaint(
        size: Size(size, size),
        painter: _TrianglePainter(color),
      ),
    );
  }
}

class _TrianglePainter extends CustomPainter {
  final Color color;
  _TrianglePainter(this.color);

  @override
  void paint(Canvas canvas, Size size) {
    final path = Path()
      ..moveTo(0, size.height)
      ..lineTo(size.width, size.height)
      ..lineTo(size.width, 0)
      ..close();
    canvas.drawPath(path, Paint()..color = color);
  }

  @override
  bool shouldRepaint(_TrianglePainter oldDelegate) => oldDelegate.color != color;
}

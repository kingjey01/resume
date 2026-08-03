import 'dart:async';
import 'package:flutter/material.dart';
import 'package:lottie/lottie.dart';
import 'package:resume_plus_clean/features/onboarding/onboarding_screen.dart';
import 'package:resume_plus_clean/theme/app_theme.dart';

class SplashScreenAlt extends StatefulWidget {
  const SplashScreenAlt({super.key});

  @override
  State<SplashScreenAlt> createState() => _SplashScreenAltState();
}

class _SplashScreenAltState extends State<SplashScreenAlt> {
  @override
  void initState() {
    super.initState();
    Timer(
      const Duration(seconds: 3),
      () {
        if (mounted) {
          Navigator.of(context).pushReplacement(
            MaterialPageRoute(builder: (context) => const OnboardingScreen()),
          );
        }
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        width: double.infinity,
        height: double.infinity,
        alignment: Alignment.center,
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [AppTheme.primaryBlueDark, AppTheme.primaryBlue, AppTheme.primaryBlueLight],
          ),
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Lottie.asset(
              'assets/animations/loading_animation.json',
              width: 200,
              height: 200,
              errorBuilder: (context, error, stackTrace) {
                return Container(
                  width: 100, height: 100,
                  decoration: BoxDecoration(
                    color: Colors.white.withOpacity(0.15),
                    borderRadius: BorderRadius.circular(28),
                  ),
                  child: const Icon(Icons.school_rounded, color: Colors.white, size: 52),
                );
              },
            ),
            const SizedBox(height: 24),
            const Text(
              'Résumé+',
              style: TextStyle(fontSize: 32, fontWeight: FontWeight.w700, color: Colors.white, letterSpacing: -0.5),
            ),
            const SizedBox(height: 8),
            Text(
              'Vos cours, simplifiés',
              style: TextStyle(fontSize: 14, color: Colors.white.withOpacity(0.7)),
            ),
          ],
        ),
      ),
    );
  }
}

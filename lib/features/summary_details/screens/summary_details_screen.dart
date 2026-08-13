import 'dart:io';
import 'dart:math';

import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:intl/intl.dart';
import 'package:resume_plus_clean/models/summary.dart' as models;
import 'package:resume_plus_clean/services/api_service.dart';
import 'package:resume_plus_clean/services/storage_service.dart';
import 'package:resume_plus_clean/widgets/secure_screen_wrapper.dart';
import 'package:resume_plus_clean/widgets/audio_player_widget.dart';
import 'package:resume_plus_clean/theme/app_theme.dart';
import 'package:resume_plus_clean/features/exercises/screens/exercise_quiz_screen.dart';
import 'package:resume_plus_clean/features/exercises/screens/exercise_subscription_screen.dart';
import 'package:resume_plus_clean/features/exercises/screens/personalized_quiz_screen.dart';
import 'package:resume_plus_clean/features/exercises/widgets/difficulty_selector_modal.dart';
import 'package:resume_plus_clean/features/exercises/widgets/exercise_generation_progress.dart';
import 'package:resume_plus_clean/features/purchases/screens/payment_status_screen.dart';
import 'package:resume_plus_clean/widgets/ai_content_view.dart';
import 'package:resume_plus_clean/widgets/api_error_view.dart';
import 'package:resume_plus_clean/mixins/error_handler_mixin.dart';

class SummaryDetailsScreen extends StatefulWidget {
  final models.Summary summary;

  const SummaryDetailsScreen({super.key, required this.summary});

  @override
  State<SummaryDetailsScreen> createState() => _SummaryDetailsScreenState();
}

class _SummaryDetailsScreenState extends State<SummaryDetailsScreen> with ErrorHandlerMixin {
  final ApiService _apiService = ApiService();
  final StorageService _storageService = StorageService();
  
  bool _isActuallyPurchased = false;
  String _userRole = 'ETUDIANT'; // Par défaut étudiant
  bool _isLoadingProfile = true;
  bool _hasExerciseSubscription = false;
  bool _isGeneratingExercise = false;
  bool _isFetchingFullSummary = false;
  dynamic _error;
  // Données complètes du résumé lorsqu'elles sont chargées depuis l'API
  String? _fetchedContent;
  String? _fetchedAuthor;
  
  // Détermine si le résumé est accessible selon le rôle et l'achat
  bool get _hasAccess {
    // CP et ADMIN ont accès gratuit à tout
    if (_userRole == 'CP' || _userRole == 'ADMIN') {
      return true;
    }
    
    // Pour les étudiants : seulement si gratuit OU acheté
    return widget.summary.isFree || _isActuallyPurchased;
  }

  @override
  void initState() {
    super.initState();
    // Si le summary vient de Mes Achats, on sait déjà qu'il est acheté
    if (widget.summary.isPurchased) {
      _isActuallyPurchased = true;
    }
    _loadUserProfile();
    _secureScreen();
    // Charger le contenu réel si besoin :
    // 1) Le contenu est un placeholder spécial __FETCH_REQUIRED__
    // 2) OU le contenu semble tronqué (< 500 caractères) alors qu'on a accès
    //    (la sérialisation liste tronque à 150 car. pour les non-acheteurs)
    // widget.summary.isPurchased est fiable car vient du modèle Summary (is_purchased API)
    if (widget.summary.content == '__FETCH_REQUIRED__' ||
        (widget.summary.isPurchased && widget.summary.content.length < 500)) {
      _fetchFullSummary();
    }
  }

  Future<void> _fetchFullSummary() async {
    setState(() => _isFetchingFullSummary = true);
    try {
      final full = await _apiService.getSummaryById(widget.summary.id);
      if (mounted) {
        setState(() {
          _fetchedContent = full.content;
          _fetchedAuthor = full.authorName.isNotEmpty ? full.authorName : null;
          _isFetchingFullSummary = false;
          _error = null;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _isFetchingFullSummary = false;
          _error = e;
        });
      }
    }
  }

  Future<void> _loadUserProfile() async {
    try {
      final profile = await _apiService.getUserProfile();
      if (!mounted) return;
      setState(() {
        _userRole = profile['profile']?['groupe'] ?? 'ETUDIANT';
        _isLoadingProfile = false;
      });
      
      // Vérifier si l'étudiant a acheté ce résumé (sauf si déjà connu)
      if (_userRole == 'ETUDIANT' && !widget.summary.isFree && !widget.summary.isPurchased) {
        await _checkPurchaseStatus();
      }
      
      // Vérifier abonnement exercices
      _checkExerciseSubscription();
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _isLoadingProfile = false;
      });
    }
  }

  Future<void> _checkPurchaseStatus() async {
    try {
      final isPurchased = await _apiService.hasPurchasedSummary(widget.summary.id);
      if (!mounted) return;
      setState(() {
        _isActuallyPurchased = isPurchased;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _isActuallyPurchased = false;
      });
    }
  }

  Future<void> _checkExerciseSubscription() async {
    try {
      final data = await _apiService.checkExerciseSubscription();
      if (mounted) {
        setState(() {
          _hasExerciseSubscription = data['has_subscription'] == true;
        });
      }
    } catch (e) {
      // Silently fail
    }
  }

  // Champs pour la progression de la génération personnalisée
  double _exerciseGenerationProgress = 0.0;
  String _exerciseGenerationStatus = 'Préparation...';

  /// Affiche le modal de sélection de difficulté
  Future<void> _showDifficultySelector() async {
    final difficulty = await context.showDifficultySelector();
    if (difficulty != null && mounted) {
      _generatePersonalizedExercise(difficulty);
    }
  }

  /// Génère un exercice QCM personnalisé avec la difficulté choisie.
  /// Règle TACHE3 : Utilisateur + Résumé + Niveau = un exercice unique.
  /// 1. Vérifier l'exercice de CE niveau → s'il existe, le réutiliser.
  /// 2. S'il n'existe pas → le créer. Jamais de régénération automatique.
  Future<void> _generatePersonalizedExercise(String difficulty) async {
    if (!mounted) return;
    setState(() {
      _isGeneratingExercise = true;
      _exerciseGenerationProgress = 0.1;
      _exerciseGenerationStatus = 'Préparation...';
    });

    try {
      // Vérifier UNIQUEMENT ce niveau (et non n'importe quel exercice du résumé)
      final checkData = await _apiService.checkPersonalizedExercise(
        widget.summary.id,
        difficulty: difficulty,
      );
      final exists = checkData['exists'] as bool? ?? false;
      final existingStatus = checkData['status'] as String? ?? '';
      final existingExerciseId = checkData['exercise_id'] as int?;

      if (exists && existingStatus == 'completed') {
        // Exercice de ce niveau déjà prêt → réutiliser, ne rien régénérer
        if (mounted) _navigateToPersonalizedQuiz(difficulty: difficulty);
        return;
      }

      if (exists && existingStatus == 'generating' && existingExerciseId != null) {
        // Génération de ce niveau déjà en cours → suivre cette génération
        _pollPersonalizedExercise(existingExerciseId, difficulty: difficulty);
        return;
      }

      if (mounted) setState(() {
        _exerciseGenerationProgress = 0.3;
        _exerciseGenerationStatus = 'Génération des questions...';
      });

      final data = await _apiService.generatePersonalizedExercise(
        summaryId: widget.summary.id,
        difficulty: difficulty,
        regenerate: false, // jamais de régénération automatique (règle TACHE3)
      );

      final exerciseId = data['exercise_id'] as int?;
      final status = data['status'] as String? ?? 'generating';

      if (exerciseId == null) {
        throw Exception('Erreur lors du démarrage de la génération');
      }

      if (status == 'completed') {
        if (mounted) _navigateToPersonalizedQuiz(difficulty: difficulty);
      } else {
        _pollPersonalizedExercise(exerciseId, difficulty: difficulty);
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _isGeneratingExercise = false;
          _exerciseGenerationProgress = 0.0;
        });
        handleError(e);
      }
    }
  }

  /// Polling pour suivre la progression de la génération
  void _pollPersonalizedExercise(int exerciseId, {String? difficulty}) {
    const maxAttempts = 30;
    int attempt = 0;

    Future.doWhile(() async {
      await Future.delayed(const Duration(seconds: 3));
      if (!mounted) return false;
      attempt++;

      try {
        final data = await _apiService.getPersonalizedExercise(exerciseId);
        final s = data['status'] as String? ?? '';

        if (s == 'completed') {
          if (mounted) _navigateToPersonalizedQuiz(difficulty: difficulty);
          return false;
        } else if (s == 'failed' || attempt >= maxAttempts) {
          if (mounted) {
            setState(() {
              _isGeneratingExercise = false;
              _exerciseGenerationProgress = 0.0;
            });
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(
                content: const Text('La génération a échoué. Réessayez.'),
                backgroundColor: AppTheme.error,
                action: SnackBarAction(
                  label: 'Réessayer',
                  textColor: Colors.white,
                  onPressed: _showDifficultySelector,
                ),
              ),
            );
          }
          return false;
        }

        // Avancer la barre de progression
        if (mounted) setState(() {
          _exerciseGenerationProgress = (_exerciseGenerationProgress + 0.08).clamp(0.3, 0.92);
          _exerciseGenerationStatus = attempt < 5
              ? 'Analyse du contenu...'
              : attempt < 15
                  ? 'Génération des questions...'
                  : 'Finalisation...';
        });
        return true;
      } catch (e) {
        if (mounted) {
          setState(() {
            _isGeneratingExercise = false;
            _exerciseGenerationProgress = 0.0;
          });
          handleError(e);
        }
        return false;
      }
    });
  }

  /// Navigation vers l'écran du quiz personnalisé
  void _navigateToPersonalizedQuiz({String? difficulty}) {
    setState(() {
      _isGeneratingExercise = false;
      _exerciseGenerationProgress = 1.0;
    });

    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) => PersonalizedQuizScreen(
          summaryId: widget.summary.id,
          summaryTitle: widget.summary.title,
          difficulty: difficulty,
        ),
      ),
    ).then((_) {
      if (mounted) setState(() {
        _isGeneratingExercise = false;
        _exerciseGenerationProgress = 0.0;
      });
    });
  }

  Future<void> _pollExerciseStatus(int exerciseId, String difficulty) async {
    const maxAttempts = 30; // 30 * 3s = 90s max (DeepSeek peut prendre jusqu'à 60s)
    for (int i = 0; i < maxAttempts; i++) {
      await Future.delayed(const Duration(seconds: 3));
      if (!mounted) return;

      try {
        final exercise = await _apiService.getExercise(exerciseId);
        final s = exercise['status'] ?? '';
        if (s == 'completed') {
          _navigateToQuiz(exerciseId, difficulty: difficulty);
          return;
        } else if (s == 'failed') {
          throw Exception('La génération a échoué. Veuillez réessayer.');
        }
        // still generating — continue polling
      } catch (e) {
        if (e.toString().contains('génération')) rethrow;
        // network hiccup — continue polling
      }
    }
    throw Exception('Délai dépassé. La génération prend trop de temps.');
  }

  void _navigateToQuiz(int exerciseId, {String difficulty = 'medium'}) {
    if (!mounted) return;
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => ExerciseQuizScreen(
          exerciseId: exerciseId,
          exerciseTitle: 'QCM - ${widget.summary.title}',
          summaryId: widget.summary.id,
          difficulty: difficulty,
        ),
      ),
    );
  }

  Future<void> _showDifficultyBottomSheet() async {
    final theme = Theme.of(context);
    final result = await showModalBottomSheet<String>(
      context: context,
      backgroundColor: Colors.transparent,
      isScrollControlled: true,
      builder: (context) {
        return Container(
          decoration: BoxDecoration(
            color: theme.colorScheme.surface,
            borderRadius: const BorderRadius.vertical(top: Radius.circular(24)),
          ),
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Center(
                child: Container(
                  width: 40,
                  height: 4,
                  decoration: BoxDecoration(
                    color: theme.colorScheme.onSurface.withOpacity(0.2),
                    borderRadius: BorderRadius.circular(2),
                  ),
                ),
              ),
              const SizedBox(height: 20),
              Text(
                'Niveau de difficulté',
                style: theme.textTheme.titleLarge?.copyWith(
                  fontWeight: FontWeight.w700,
                ),
              ),
              const SizedBox(height: 6),
              Text(
                'Choisissez le niveau du QCM pour adapter les questions à votre niveau',
                style: theme.textTheme.bodyMedium?.copyWith(
                  color: theme.colorScheme.onSurface.withOpacity(0.6),
                ),
              ),
              const SizedBox(height: 20),
              _buildDifficultyOption(
                context,
                'Facile',
                'Questions simples pour réviser les bases',
                Icons.sentiment_satisfied_rounded,
                Colors.green,
                'easy',
              ),
              const SizedBox(height: 10),
              _buildDifficultyOption(
                context,
                'Moyen',
                'Questions intermédiaires pour tester vos connaissances',
                Icons.sentiment_neutral_rounded,
                Colors.orange,
                'medium',
              ),
              const SizedBox(height: 10),
              _buildDifficultyOption(
                context,
                'Difficile',
                'Questions avancées pour approfondir votre maîtrise',
                Icons.sentiment_dissatisfied_rounded,
                Colors.red,
                'hard',
              ),
              const SizedBox(height: 24),
            ],
          ),
        );
      },
    );

    if (result != null && mounted) {
      _generatePersonalizedExercise(result);
    }
  }

  Widget _buildDifficultyOption(
    BuildContext context,
    String title,
    String subtitle,
    IconData icon,
    Color color,
    String difficulty,
  ) {
    final theme = Theme.of(context);
    return InkWell(
      onTap: () => Navigator.of(context).pop(difficulty),
      borderRadius: BorderRadius.circular(14),
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: color.withOpacity(0.08),
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: color.withOpacity(0.3)),
        ),
        child: Row(
          children: [
            Container(
              width: 44,
              height: 44,
              decoration: BoxDecoration(
                color: color.withOpacity(0.15),
                shape: BoxShape.circle,
              ),
              child: Icon(icon, color: color, size: 22),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    title,
                    style: theme.textTheme.titleSmall?.copyWith(
                      fontWeight: FontWeight.w700,
                      color: color,
                    ),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    subtitle,
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: theme.colorScheme.onSurface.withOpacity(0.6),
                    ),
                  ),
                ],
              ),
            ),
            Icon(Icons.chevron_right_rounded, color: color.withOpacity(0.6)),
          ],
        ),
      ),
    );
  }

  Future<void> _navigateToSubscription() async {
    final result = await Navigator.of(context).push<bool>(
      MaterialPageRoute(builder: (_) => const ExerciseSubscriptionScreen()),
    );
    if (result == true) {
      _checkExerciseSubscription();
    }
  }

  Future<void> _secureScreen() async {
    // 🔒 PROTECTION CONTRE LES CAPTURES D'ÉCRAN
    if (!kIsWeb && Platform.isAndroid) {
      try {
        // API moderne : masquer les overlays système (statut + navigation)
        // setEnabledSystemUIOverlays est obsolète et supprimée des moteurs récents.
        await SystemChrome.setEnabledSystemUIMode(
          SystemUiMode.immersiveSticky,
          overlays: [],
        );
        // Bloquer les captures d'écran
        await SystemChannels.platform.invokeMethod('SystemChrome.setApplicationSwitcherDescription', {
          'label': 'Résumé sécurisé',
          'primaryColor': 0xFF000000,
        });
      } catch (e) {
        print('Erreur lors de la sécurisation de l\'écran: $e');
      }
    }
  }

  Future<void> _initiatePurchase() async {
    final TextEditingController phoneController = TextEditingController();
    bool isLoading = false;

    await showDialog(
      context: context,
      barrierDismissible: false,
      builder: (BuildContext dialogContext) {
        return StatefulBuilder(
          builder: (context, setState) {
            return AlertDialog(
              title: const Text('Acheter le résumé'),
              content: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(
                    'Prix: ${widget.summary.price.toStringAsFixed(0)} FC',
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.bold,
                      color: Colors.green,
                    ),
                  ),
                  const SizedBox(height: 16),
                  TextField(
                    controller: phoneController,
                    decoration: const InputDecoration(
                      labelText: 'Numéro de téléphone',
                      hintText: 'Ex: 0973123456',
                      border: OutlineInputBorder(),
                      prefixText: '+243 ',
                    ),
                    keyboardType: TextInputType.phone,
                    maxLength: 10,
                    onChanged: (value) {
                      // Nettoyer le numéro
                      if (value.startsWith('+243')) {
                        phoneController.text = value.substring(4);
                      } else if (value.startsWith('243')) {
                        phoneController.text = value.substring(3);
                      }
                      phoneController.selection = TextSelection.fromPosition(
                        TextPosition(offset: phoneController.text.length),
                      );
                    },
                  ),
                  const SizedBox(height: 16),
                  const Text(
                    'Vous recevrez une demande de paiement sur votre téléphone.',
                    style: TextStyle(fontSize: 12, color: Colors.grey),
                    textAlign: TextAlign.center,
                  ),
                ],
              ),
              actions: [
                TextButton(
                  onPressed: isLoading ? null : () => Navigator.of(dialogContext).pop(),
                  child: const Text('Annuler'),
                ),
                ElevatedButton(
                  onPressed: isLoading ? null : () async {
                    final phoneNumber = phoneController.text.trim();
                    if (phoneNumber.isEmpty || phoneNumber.length < 9) {
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(
                          content: Text('Veuillez saisir un numéro de téléphone valide'),
                          backgroundColor: Colors.red,
                        ),
                      );
                      return;
                    }

                    setState(() => isLoading = true);

                    try {
                      final result = await _apiService.initiateSummaryPurchase(
                        summaryId: widget.summary.id,
                        phoneNumber: phoneNumber,
                      );

                      if (result['success'] == true) {
                        Navigator.of(dialogContext).pop();
                        await _navigateToPaymentStatus(result);
                      } else {
                        ScaffoldMessenger.of(context).showSnackBar(
                          SnackBar(
                            content: Text(result['error'] ?? 'Erreur lors de l\'initiation du paiement'),
                            backgroundColor: Colors.red,
                          ),
                        );
                      }
                    } catch (e) {
                      ScaffoldMessenger.of(context).showSnackBar(
                        SnackBar(
                          content: Text('Erreur: ${e.toString()}'),
                          backgroundColor: Colors.red,
                        ),
                      );
                    } finally {
                      setState(() => isLoading = false);
                    }
                  },
                  child: isLoading
                      ? const SizedBox(
                          width: 20,
                          height: 20,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Text('Payer'),
                ),
              ],
            );
          },
        );
      },
    );
  }

  Future<void> _navigateToPaymentStatus(Map<String, dynamic> paymentData) async {
    final reference = paymentData['reference']?.toString() ?? '';
    final summaryTitle = paymentData['summary_title']?.toString() ?? widget.summary.title;
    final amount = paymentData['amount']?.toString() ?? widget.summary.price.toStringAsFixed(0);
    final currency = paymentData['currency']?.toString() ?? 'CDF';
    final isSimulated = paymentData['simulated'] == true;

    if (isSimulated) {
      // Mode simulation → succès direct, rafraîchir l'état
      _checkPurchaseStatus();
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Paiement réussi !'),
          backgroundColor: Colors.green,
        ),
      );
      return;
    }

    if (reference.isNotEmpty) {
      // Envoyer vers l'écran de statut et attendre le retour
      // PaymentStatusScreen fait pop(true) si succès, pop(false) sinon
      final paid = await Navigator.of(context).push<bool>(
        MaterialPageRoute(
          builder: (_) => PaymentStatusScreen(
            transactionRef: reference,
            summaryTitle: summaryTitle,
            amount: amount,
            currency: currency,
          ),
        ),
      );

      // Revenu de PaymentStatusScreen → rafraîchir immédiatement
      if (mounted && paid == true) {
        _checkPurchaseStatus();
        // Forcer le rechargement du contenu complet (la liste renvoie du texte tronqué)
        _fetchFullSummary();
        setState(() {});
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_error != null) {
      return Scaffold(
        appBar: AppBar(
          title: Text(widget.summary.title),
          backgroundColor: AppTheme.primaryBlue,
        ),
        body: ApiErrorView(
          error: _error,
          onRetry: _fetchFullSummary,
        ),
      );
    }

    final theme = Theme.of(context);
    final topPadding = MediaQuery.of(context).padding.top;

    return SecureScreenWrapper(
      screenName: 'Résumé: ${widget.summary.title}',
      enableSecurity: _hasAccess,
      child: Scaffold(
        backgroundColor: Theme.of(context).scaffoldBackgroundColor,
        body: SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Header bleu cohérent avec ValidationScreen / SummariesScreen
              _buildDetailHeader(context, topPadding),

              // Contenu principal
              Padding(
                  padding: const EdgeInsets.fromLTRB(20, 16, 20, 0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // Carte info rapide
                      Container(
                        padding: const EdgeInsets.all(16),
                        decoration: BoxDecoration(
                          color: theme.colorScheme.surface,
                          borderRadius: BorderRadius.circular(16),
                          boxShadow: AppTheme.mediumShadow,
                        ),
                        child: Row(
                          children: [
                            _buildInfoChip(context, Icons.person_outline_rounded, _fetchedAuthor ?? widget.summary.authorName),
                            const SizedBox(width: 12),
                            _buildInfoChip(context, Icons.calendar_today_rounded, DateFormat('dd/MM/yyyy').format(widget.summary.createdAt)),
                            const Spacer(),
                            // Badge prix
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                              decoration: BoxDecoration(
                                color: widget.summary.isFree
                                    ? AppTheme.success.withOpacity(0.1)
                                    : theme.colorScheme.primaryContainer,
                                borderRadius: BorderRadius.circular(20),
                              ),
                              child: Text(
                                widget.summary.isFree ? 'Gratuit' : '${widget.summary.price.toStringAsFixed(0)} FC',
                                style: TextStyle(
                                  color: widget.summary.isFree ? AppTheme.success : theme.colorScheme.primary,
                                  fontSize: 13,
                                  fontWeight: FontWeight.w700,
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(height: 16),

                      // Badges auteur IA/CP (visible uniquement CP/Admin)
                      if (_userRole == 'CP' || _userRole == 'ADMIN') ...[
                        _buildAuthorBadge(),
                        const SizedBox(height: 16),
                      ],

                      // Widget de lecture audio
                      if (_hasAccess) ...[
                        Container(
                          decoration: BoxDecoration(
                            color: theme.colorScheme.surface,
                            borderRadius: BorderRadius.circular(16),
                            boxShadow: AppTheme.softShadow,
                          ),
                          padding: const EdgeInsets.all(16),
                          child: AudioPlayerWidget(
                            text: _fetchedContent ?? widget.summary.content,
                            title: 'Écouter le résumé',
                            rate: 0.5,
                            pitch: 1.0,
                            volume: 1.0,
                            language: 'fr-FR',
                          ),
                        ),
                        const SizedBox(height: 16),
                      ],

                      // Contenu du résumé
                      _hasAccess
                          ? Container(
                              padding: const EdgeInsets.all(20),
                              decoration: BoxDecoration(
                                color: theme.colorScheme.surface,
                                borderRadius: BorderRadius.circular(16),
                                boxShadow: AppTheme.softShadow,
                              ),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Row(
                                    children: [
                                      Container(
                                        width: 32,
                                        height: 32,
                                        decoration: BoxDecoration(
                                          color: theme.colorScheme.primaryContainer,
                                          borderRadius: BorderRadius.circular(8),
                                        ),
                                        child: Icon(Icons.article_rounded, color: theme.colorScheme.primary, size: 18),
                                      ),
                                      const SizedBox(width: 10),
                                      Text(
                                        'Contenu du résumé',
                                        style: theme.textTheme.titleMedium?.copyWith(
                                          fontWeight: FontWeight.w600,
                                        ),
                                      ),
                                    ],
                                  ),
                                  const SizedBox(height: 16),
                                  if (_isFetchingFullSummary)
                                    const Center(child: Padding(
                                      padding: EdgeInsets.symmetric(vertical: 20),
                                      child: CircularProgressIndicator(),
                                    ))
                                  else
                                    AiContentView(
                                      content: _fetchedContent ?? widget.summary.content,
                                    ),
                                ],
                              ),
                            )
                          : _buildLockedContent(theme),
                      // Bouton exercice QCM
                      if (_hasAccess && widget.summary.isValidated) ...[                        
                        const SizedBox(height: 16),
                        _buildExerciseButton(),
                      ],
                      const SizedBox(height: 40),
                    ],
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildDetailHeader(BuildContext context, double topPadding) {
    return Container(
      width: double.infinity,
      padding: EdgeInsets.only(top: topPadding + 8, left: 20, right: 20, bottom: 18),
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
          // Ligne supérieure : back + icône + matière (compact)
          Row(
            children: [
              GestureDetector(
                onTap: () => Navigator.of(context).pop(),
                child: Container(
                  width: 44,
                  height: 44,
                  decoration: BoxDecoration(
                    color: Colors.white.withOpacity(0.15),
                    borderRadius: BorderRadius.circular(14),
                  ),
                  child: const Icon(Icons.arrow_back_rounded, color: Colors.white, size: 22),
                ),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Détail du résumé',
                      style: TextStyle(
                        color: Colors.white.withOpacity(0.7),
                        fontSize: 12,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      widget.summary.subject,
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 16,
                        fontWeight: FontWeight.w700,
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ],
                ),
              ),
              Container(
                width: 44,
                height: 44,
                decoration: BoxDecoration(
                  color: Colors.white.withOpacity(0.15),
                  borderRadius: BorderRadius.circular(14),
                ),
                child: const Icon(Icons.menu_book_rounded, color: Colors.white, size: 22),
              ),
            ],
          ),
          const SizedBox(height: 14),
          // Titre du résumé
          Text(
            widget.summary.title,
            style: const TextStyle(
              color: Colors.white,
              fontSize: 20,
              fontWeight: FontWeight.w700,
              height: 1.25,
            ),
            maxLines: 3,
            overflow: TextOverflow.ellipsis,
          ),
        ],
      ),
    );
  }

  Widget _buildInfoChip(BuildContext context, IconData icon, String text) {
    final theme = Theme.of(context);
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(icon, size: 14, color: theme.colorScheme.onSurface.withOpacity(0.5)),
        const SizedBox(width: 4),
        Text(
          text,
          style: TextStyle(
            color: theme.colorScheme.onSurface.withOpacity(0.7),
            fontSize: 12,
            fontWeight: FontWeight.w500,
          ),
          maxLines: 1,
          overflow: TextOverflow.ellipsis,
        ),
      ],
    );
  }

  Widget _buildLockedContent(ThemeData theme) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Aperçu limité
        Container(
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            color: theme.colorScheme.surface,
            borderRadius: BorderRadius.circular(16),
            boxShadow: AppTheme.softShadow,
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Stack(
                children: [
                  Text(
                    widget.summary.content.substring(0, min(widget.summary.content.length, 150)),
                    style: theme.textTheme.bodyLarge?.copyWith(
                      color: theme.colorScheme.onSurface.withOpacity(0.7),
                      height: 1.7,
                    ),
                  ),
                  Positioned(
                    bottom: 0,
                    left: 0,
                    right: 0,
                    height: 50,
                    child: Container(
                      decoration: BoxDecoration(
                        gradient: LinearGradient(
                          begin: Alignment.topCenter,
                          end: Alignment.bottomCenter,
                          colors: [Colors.transparent, theme.colorScheme.surface],
                        ),
                      ),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
        const SizedBox(height: 16),

        // Carte d'achat moderne
        Container(
          width: double.infinity,
          padding: const EdgeInsets.all(24),
          decoration: BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: [
                theme.colorScheme.primary,
                theme.colorScheme.primaryContainer,
                theme.colorScheme.primaryContainer,
              ],
            ),
            borderRadius: BorderRadius.circular(20),
            boxShadow: [
              BoxShadow(
                color: theme.colorScheme.primary.withOpacity(0.3),
                blurRadius: 20,
                offset: const Offset(0, 8),
              ),
            ],
          ),
          child: Column(
            children: [
              Container(
                width: 60,
                height: 60,
                decoration: BoxDecoration(
                  color: theme.colorScheme.surface,
                  shape: BoxShape.circle,
                ),
                child: Icon(Icons.lock_rounded, color: theme.colorScheme.onSurface, size: 28),
              ),
              const SizedBox(height: 16),
              Text(
                'Contenu Premium',
                style: TextStyle(
                  color: theme.colorScheme.onSurface,
                  fontSize: 20,
                  fontWeight: FontWeight.w700,
                ),
              ),
              const SizedBox(height: 8),
              Text(
                'Achetez ce résumé pour accéder au contenu complet et à la lecture audio.',
                textAlign: TextAlign.center,
                style: TextStyle(
                  color: theme.colorScheme.onSurface.withOpacity(0.85),
                  fontSize: 14,
                ),
              ),
              const SizedBox(height: 20),
              if (!widget.summary.isFree) ...[
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
                  decoration: BoxDecoration(
                    color: theme.colorScheme.surface,
                    borderRadius: BorderRadius.circular(30),
                  ),
                  child: Text(
                    '${widget.summary.price.toStringAsFixed(0)} FC',
                    style: TextStyle(
                      color: theme.colorScheme.onSurface,
                      fontSize: 22,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ),
                const SizedBox(height: 16),
              ],
              SizedBox(
                width: double.infinity,
                child: ElevatedButton.icon(
                  icon: Icon(
                    widget.summary.isFree ? Icons.download_rounded : Icons.shopping_cart_rounded,
                    color: theme.colorScheme.onPrimary,
                  ),
                  label: Text(
                    widget.summary.isFree ? 'Télécharger gratuitement' : 'Acheter maintenant',
                    style: TextStyle(
                      color: theme.colorScheme.onPrimary,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: theme.colorScheme.primary,
                    foregroundColor: theme.colorScheme.onPrimary,
                    padding: const EdgeInsets.symmetric(vertical: 14),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                    elevation: 0,
                  ),
                  onPressed: () async {
                    if (widget.summary.isFree) {
                      ScaffoldMessenger.of(context).showSnackBar(
                        SnackBar(
                          content: Text('Téléchargement gratuit bientôt disponible'),
                          backgroundColor: AppTheme.success,
                        ),
                      );
                    } else {
                      await _initiatePurchase();
                    }
                  },
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildAuthorBadge() {
    final theme = Theme.of(context);
    final isAi = widget.summary.isAiGenerated;
    final isValidated = widget.summary.isValidated;

    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: theme.colorScheme.surface,
        borderRadius: BorderRadius.circular(14),
        boxShadow: AppTheme.softShadow,
      ),
      child: Row(
        children: [
          // Author type badge
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
            decoration: BoxDecoration(
              color: isAi
                  ? theme.colorScheme.primaryContainer
                  : theme.colorScheme.primaryContainer,
              borderRadius: BorderRadius.circular(10),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(
                  isAi ? Icons.smart_toy_rounded : Icons.person_rounded,
                  size: 16,
                  color: isAi ? theme.colorScheme.primary : theme.colorScheme.primary,
                ),
                const SizedBox(width: 6),
                Text(
                  isAi ? 'Généré par IA' : 'Rédigé par CP',
                  style: TextStyle(
                    color: isAi ? theme.colorScheme.primary : theme.colorScheme.primary,
                    fontSize: 12, fontWeight: FontWeight.w700,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(width: 10),
          // Validation badge
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
            decoration: BoxDecoration(
              color: isValidated
                  ? AppTheme.success.withOpacity(0.1)
                  : theme.colorScheme.errorContainer,
              borderRadius: BorderRadius.circular(10),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(
                  isValidated ? Icons.check_circle_rounded : Icons.pending_rounded,
                  size: 16,
                  color: isValidated ? AppTheme.success : theme.colorScheme.error,
                ),
                const SizedBox(width: 6),
                Text(
                  isValidated ? 'Validé' : 'Non validé',
                  style: TextStyle(
                    color: isValidated ? AppTheme.success : theme.colorScheme.error,
                    fontSize: 12, fontWeight: FontWeight.w600,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildExerciseButton() {
    final theme = Theme.of(context);
    final hasAccess = _hasExerciseSubscription;

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        // Gradient riche bleu foncé pour garantir un excellent contraste avec le texte blanc
        gradient: hasAccess
            ? const LinearGradient(
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
                colors: [
                  AppTheme.primaryBlueDark,
                  AppTheme.primaryBlue,
                  AppTheme.primaryBlueLight,
                ],
              )
            : null,
        color: hasAccess ? null : theme.colorScheme.surface,
        borderRadius: BorderRadius.circular(18),
        boxShadow: hasAccess
            ? [BoxShadow(color: AppTheme.primaryBlue.withOpacity(0.35), blurRadius: 16, offset: const Offset(0, 6))]
            : AppTheme.softShadow,
      ),
      child: Column(
        children: [
          Icon(
            hasAccess ? Icons.quiz_rounded : Icons.lock_rounded,
            size: 32,
            color: hasAccess ? Colors.white : theme.colorScheme.onSurface.withOpacity(0.5),
          ),
          const SizedBox(height: 10),
          Text(
            'Exercice QCM',
            style: TextStyle(
              color: hasAccess ? Colors.white : theme.colorScheme.onSurface,
              fontSize: 16,
              fontWeight: FontWeight.w700,
            ),
          ),
          const SizedBox(height: 6),
          Text(
            hasAccess
                ? 'Testez vos connaissances avec un QCM généré par IA'
                : 'Abonnez-vous au service Exercices pour accéder aux QCM',
            textAlign: TextAlign.center,
            style: TextStyle(
              color: hasAccess
                  ? Colors.white.withOpacity(0.92)
                  : theme.colorScheme.onSurface.withOpacity(0.6),
              fontSize: 12,
            ),
          ),
          if (_isGeneratingExercise) ...[  
            const SizedBox(height: 12),
            ExerciseGenerationProgress(
              progress: _exerciseGenerationProgress,
              status: _exerciseGenerationStatus,
              onCancel: () {
                setState(() {
                  _isGeneratingExercise = false;
                  _exerciseGenerationProgress = 0.0;
                });
              },
            ),
          ] else ...[  
          const SizedBox(height: 14),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton.icon(
              onPressed: hasAccess
                  ? (_isGeneratingExercise ? null : _showDifficultySelector)
                  : null,
              icon: _isGeneratingExercise
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(strokeWidth: 2, color: AppTheme.primaryBlue),
                    )
                  : Icon(
                      hasAccess ? Icons.play_arrow_rounded : Icons.lock_rounded,
                      size: 20,
                      color: hasAccess ? AppTheme.primaryBlue : theme.colorScheme.onSurface,
                    ),
              label: Text(
                        hasAccess
                        ? 'Lancer le QCM'
                        : 'Abonnement requis',
                style: TextStyle(
                  color: hasAccess ? AppTheme.primaryBlue : theme.colorScheme.onSurface,
                  fontWeight: FontWeight.w700,
                ),
              ),
              style: ElevatedButton.styleFrom(
                // Bouton BLANC à l'intérieur du gradient bleu → texte bleu lisible
                backgroundColor: hasAccess
                    ? Colors.white
                    : theme.brightness == Brightness.dark
                        ? Colors.white10
                        : Colors.grey.shade100,
                foregroundColor: hasAccess ? AppTheme.primaryBlue : theme.colorScheme.onSurface,
                padding: const EdgeInsets.symmetric(vertical: 14),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                elevation: 0,
              ),
            ),
          ),
          ], // fermeture bloc else (bouton)
          if (!hasAccess) ...[          
            const SizedBox(height: 10),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: () => _navigateToSubscription(),
                icon: const Icon(Icons.diamond_rounded, size: 18, color: Colors.white),
                label: const Text(
                  "S'abonner maintenant",
                  style: TextStyle(color: Colors.white, fontWeight: FontWeight.w600),
                ),
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF7C3AED),
                  padding: const EdgeInsets.symmetric(vertical: 14),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                  elevation: 0,
                ),
              ),
            ),
          ],
        ],
      ),
    );
  }
}
import 'package:flutter/material.dart';
import 'package:resume_plus_clean/services/api_service.dart';
import 'package:resume_plus_clean/theme/app_theme.dart';
import 'package:resume_plus_clean/features/purchases/screens/payment_status_screen.dart';

class ExerciseSubscriptionScreen extends StatefulWidget {
  const ExerciseSubscriptionScreen({super.key});

  @override
  State<ExerciseSubscriptionScreen> createState() => _ExerciseSubscriptionScreenState();
}

class _ExerciseSubscriptionScreenState extends State<ExerciseSubscriptionScreen> {
  final ApiService _apiService = ApiService();
  final TextEditingController _phoneController = TextEditingController();

  bool _isLoadingServices = true;
  bool _isProcessingPayment = false;
  List<dynamic> _services = [];
  Map<String, dynamic>? _selectedService;

  @override
  void initState() {
    super.initState();
    _loadServices();
  }

  @override
  void dispose() {
    _phoneController.dispose();
    super.dispose();
  }

  Future<void> _loadServices() async {
    try {
      final services = await _apiService.getServices();
      if (!mounted) return;
      setState(() {
        _services = services.where((s) {
          final nom = (s['nom'] ?? '').toString().toLowerCase();
          return nom.contains('exercice') || nom.contains('qcm');
        }).toList();
        // If no exercise-specific services, show all
        if (_services.isEmpty) {
          _services = services;
        }
        _isLoadingServices = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() => _isLoadingServices = false);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Erreur: ${e.toString()}')),
      );
    }
  }

  Future<void> _initiatePayment() async {
    if (_selectedService == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Veuillez sélectionner un service')),
      );
      return;
    }

    final phone = _phoneController.text.trim();
    if (phone.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Veuillez entrer votre numéro de téléphone')),
      );
      return;
    }

    setState(() => _isProcessingPayment = true);

    try {
      final serviceId = _selectedService!['id'] as int;
      final result = await _apiService.initiateSubscriptionPayment(serviceId, phone);

      if (!mounted) return;

      if (result['success'] == true) {
        final isSimulated = result['simulated'] == true;
        final reference = result['reference']?.toString() ?? '';
        final amount = result['amount']?.toString() ?? _selectedService!['price']?.toString() ?? '0';
        final currency = result['currency']?.toString() ?? 'CDF';

        setState(() => _isProcessingPayment = false);

        if (isSimulated) {
          _showSuccessDialog();
        } else if (reference.isNotEmpty) {
          if (!mounted) return;
          final subscribed = await Navigator.of(context).push<bool>(
            MaterialPageRoute(
              builder: (_) => PaymentStatusScreen(
                transactionRef: reference,
                summaryTitle: _selectedService!['name']?.toString() ?? 'Exercices QCM',
                amount: amount,
                currency: currency,
                successMessage: 'Abonnement activé !',
                successSubtitle: 'Votre abonnement au service d\'exercices\nest maintenant actif.',
                onPaymentConfirmed: () async {
                  await _apiService.createSubscriptionAfterPayment(
                    reference,
                    serviceId,
                  );
                },
              ),
            ),
          );
          if (mounted && subscribed == true) {
            Navigator.of(context).pop(true);
          }
        }
      } else {
        setState(() => _isProcessingPayment = false);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(result['error'] ?? 'Erreur lors du paiement')),
        );
      }
    } catch (e) {
      if (!mounted) return;
      setState(() => _isProcessingPayment = false);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Erreur: ${e.toString()}')),
      );
    }
  }

  void _showSuccessDialog() {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (ctx) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: const Row(
          children: [
            Icon(Icons.check_circle_rounded, color: AppTheme.success, size: 28),
            SizedBox(width: 10),
            Expanded(child: Text('Abonnement activé !', style: TextStyle(fontSize: 18))),
          ],
        ),
        content: const Text(
          'Votre abonnement au service d\'exercices est maintenant actif. '
          'Vous pouvez générer des QCM sur tous les résumés validés.',
        ),
        actions: [
          ElevatedButton(
            onPressed: () {
              Navigator.of(ctx).pop();
              Navigator.of(context).pop(true); // return true = subscribed
            },
            style: ElevatedButton.styleFrom(
              backgroundColor: AppTheme.primaryBlue,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
            ),
            child: const Text('Commencer', style: TextStyle(color: Colors.white)),
          ),
        ],
      ),
    );
  }


  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      backgroundColor: theme.scaffoldBackgroundColor,
      appBar: AppBar(
        title: Text(
          'Abonnement Exercices',
          style: TextStyle(
            fontWeight: FontWeight.w700,
            color: theme.colorScheme.onSurface,
          ),
        ),
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: Icon(Icons.arrow_back_ios_rounded, color: theme.colorScheme.onSurface),
          onPressed: () => Navigator.of(context).pop(),
        ),
      ),
      body: _isLoadingServices
          ? const Center(child: CircularProgressIndicator(color: AppTheme.primaryBlue))
          : SingleChildScrollView(
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Hero section
                  _buildHeroSection(theme),
                  const SizedBox(height: 24),

                  // Features
                  _buildFeaturesSection(theme),
                  const SizedBox(height: 24),

                  // Service plans
                  Text(
                    'Choisir un plan',
                    style: theme.textTheme.titleLarge?.copyWith(
                      fontWeight: FontWeight.w700,
                      color: theme.colorScheme.onSurface,
                    ),
                  ),
                  const SizedBox(height: 12),
                  if (_services.isEmpty)
                    _buildNoServicesCard(theme)
                  else
                    ..._services.map((s) => _buildServiceCard(s, theme)),

                  const SizedBox(height: 24),

                  // Phone number input
                  if (_selectedService != null) ...[
                    Text(
                      'Numéro Mobile Money',
                      style: theme.textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.w600,
                        color: theme.colorScheme.onSurface,
                      ),
                    ),
                    const SizedBox(height: 8),
                    TextField(
                      controller: _phoneController,
                      keyboardType: TextInputType.phone,
                      decoration: InputDecoration(
                        hintText: '0990000000',
                        prefixIcon: const Icon(Icons.phone_rounded, color: AppTheme.primaryBlue),
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(12),
                          borderSide: BorderSide(color: Colors.grey[300]!),
                        ),
                        enabledBorder: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(12),
                          borderSide: BorderSide(color: Colors.grey[300]!),
                        ),
                        focusedBorder: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(12),
                          borderSide: const BorderSide(color: AppTheme.primaryBlue, width: 1.5),
                        ),
                      ),
                    ),
                    const SizedBox(height: 20),

                    // Pay button
                    SizedBox(
                      width: double.infinity,
                      height: 52,
                      child: ElevatedButton(
                        onPressed: _isProcessingPayment ? null : _initiatePayment,
                        style: ElevatedButton.styleFrom(
                          backgroundColor: AppTheme.primaryBlue,
                          disabledBackgroundColor: AppTheme.primaryBlue.withOpacity(0.5),
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                          elevation: 0,
                        ),
                        child: _isProcessingPayment
                            ? const SizedBox(
                                width: 24,
                                height: 24,
                                child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2.5),
                              )
                            : Text(
                                'Payer ${_selectedService!['price']} ${_selectedService!['currency'] ?? 'CDF'}',
                                style: const TextStyle(
                                  color: Colors.white,
                                  fontSize: 16,
                                  fontWeight: FontWeight.w700,
                                ),
                              ),
                      ),
                    ),
                    const SizedBox(height: 40),
                  ],
                ],
              ),
            ),
    );
  }

  Widget _buildHeroSection(ThemeData theme) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [AppTheme.primaryBlueDark, AppTheme.primaryBlue],
        ),
        borderRadius: BorderRadius.circular(20),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: Colors.white.withOpacity(0.2),
              borderRadius: BorderRadius.circular(14),
            ),
            child: const Icon(Icons.quiz_rounded, color: Colors.white, size: 32),
          ),
          const SizedBox(height: 16),
          const Text(
            'Exercices QCM',
            style: TextStyle(
              color: Colors.white,
              fontSize: 24,
              fontWeight: FontWeight.w800,
            ),
          ),
          const SizedBox(height: 6),
          Text(
            'Testez vos connaissances avec des QCM générés par IA à partir de vos résumés de cours.',
            style: TextStyle(
              color: Colors.white.withOpacity(0.85),
              fontSize: 14,
              height: 1.4,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildFeaturesSection(ThemeData theme) {
    final features = [
      {'icon': Icons.auto_awesome_rounded, 'title': 'QCM générés par IA', 'desc': 'Questions pertinentes basées sur le contenu'},
      {'icon': Icons.all_inclusive_rounded, 'title': 'Accès illimité', 'desc': 'Générez autant de QCM que vous voulez'},
      {'icon': Icons.analytics_rounded, 'title': 'Suivi de performance', 'desc': 'Statistiques et historique de vos scores'},
      {'icon': Icons.lightbulb_rounded, 'title': 'Explications détaillées', 'desc': 'Comprenez chaque réponse correcte'},
    ];

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Ce qui est inclus',
          style: theme.textTheme.titleLarge?.copyWith(
            fontWeight: FontWeight.w700,
            color: theme.colorScheme.onSurface,
          ),
        ),
        const SizedBox(height: 12),
        ...features.map((f) => Padding(
          padding: const EdgeInsets.only(bottom: 10),
          child: Row(
            children: [
              Container(
                width: 40,
                height: 40,
                decoration: BoxDecoration(
                  color: AppTheme.primaryBlue.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Icon(f['icon'] as IconData, color: AppTheme.primaryBlue, size: 20),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      f['title'] as String,
                      style: TextStyle(
                        fontWeight: FontWeight.w600,
                        fontSize: 14,
                        color: theme.colorScheme.onSurface,
                      ),
                    ),
                    Text(
                      f['desc'] as String,
                      style: TextStyle(fontSize: 12, color: Colors.grey[600]),
                    ),
                  ],
                ),
              ),
            ],
          ),
        )),
      ],
    );
  }

  Widget _buildServiceCard(dynamic service, ThemeData theme) {
    final isSelected = _selectedService != null && _selectedService!['id'] == service['id'];
    final price = service['price'] ?? 0;
    final currency = service['currency'] ?? 'CDF';
    final duration = service['duree_mois'] ?? 1;
    final features = service['features'] is List ? service['features'] as List : [];

    return GestureDetector(
      onTap: () {
        setState(() {
          _selectedService = Map<String, dynamic>.from(service as Map);
        });
      },
      child: Container(
        margin: const EdgeInsets.only(bottom: 12),
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: theme.colorScheme.surface,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: isSelected ? AppTheme.primaryBlue : Colors.grey[300]!,
            width: isSelected ? 2 : 1,
          ),
          boxShadow: isSelected ? [
            BoxShadow(
              color: AppTheme.primaryBlue.withOpacity(0.15),
              blurRadius: 12,
              offset: const Offset(0, 4),
            ),
          ] : [],
        ),
        child: Row(
          children: [
            // Radio indicator
            Container(
              width: 22,
              height: 22,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                border: Border.all(
                  color: isSelected ? AppTheme.primaryBlue : Colors.grey[400]!,
                  width: 2,
                ),
                color: isSelected ? AppTheme.primaryBlue : Colors.transparent,
              ),
              child: isSelected
                  ? const Icon(Icons.check_rounded, color: Colors.white, size: 14)
                  : null,
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    service['nom'] ?? 'Service',
                    style: TextStyle(
                      fontWeight: FontWeight.w700,
                      fontSize: 16,
                      color: theme.colorScheme.onSurface,
                    ),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    '$duration mois',
                    style: TextStyle(fontSize: 12, color: Colors.grey[600]),
                  ),
                  if (features.isNotEmpty) ...[
                    const SizedBox(height: 6),
                    ...features.take(3).map((f) => Padding(
                      padding: const EdgeInsets.only(bottom: 2),
                      child: Row(
                        children: [
                          const Icon(Icons.check_circle_rounded, size: 14, color: AppTheme.success),
                          const SizedBox(width: 6),
                          Expanded(
                            child: Text(
                              f.toString(),
                              style: TextStyle(fontSize: 11, color: Colors.grey[600]),
                            ),
                          ),
                        ],
                      ),
                    )),
                  ],
                ],
              ),
            ),
            Column(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Text(
                  '$price',
                  style: TextStyle(
                    fontWeight: FontWeight.w800,
                    fontSize: 22,
                    color: isSelected ? AppTheme.primaryBlue : theme.colorScheme.onSurface,
                  ),
                ),
                Text(
                  currency,
                  style: TextStyle(fontSize: 12, color: Colors.grey[600]),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildNoServicesCard(ThemeData theme) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: theme.colorScheme.surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.grey[300]!),
      ),
      child: Column(
        children: [
          Icon(Icons.info_outline_rounded, size: 40, color: Colors.grey[400]),
          const SizedBox(height: 12),
          Text(
            'Aucun service disponible',
            style: TextStyle(
              fontWeight: FontWeight.w600,
              fontSize: 16,
              color: theme.colorScheme.onSurface,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            'Les services d\'abonnement ne sont pas encore configurés.',
            textAlign: TextAlign.center,
            style: TextStyle(fontSize: 13, color: Colors.grey[600]),
          ),
        ],
      ),
    );
  }
}

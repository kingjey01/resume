import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:resume_plus_clean/models/service.dart';
import 'package:resume_plus_clean/models/abonnement.dart';
import 'package:resume_plus_clean/features/subscriptions/providers/subscription_provider.dart';
import 'package:resume_plus_clean/services/snackbar_service.dart';
import 'package:resume_plus_clean/services/api_service.dart';
import 'package:resume_plus_clean/models/payment_method.dart';
import 'package:resume_plus_clean/features/purchases/screens/payment_status_screen.dart';

class ServiceCard extends ConsumerWidget {
  final Service service;

  const ServiceCard({
    super.key,
    required this.service,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);
    final subscriptionsAsync = ref.watch(subscriptionsProvider);

    // Déterminer l'état de l'abonnement pour CE service
    final now = DateTime.now();
    Abonnement? activeSubscription;
    subscriptionsAsync.whenData((subs) {
      try {
        activeSubscription = subs.where((s) =>
          s.service == service.id && s.isActive && s.dateFin.isAfter(now)
        ).firstOrNull;
      } catch (_) {}
    });

    final isActive = activeSubscription != null;
    final remainingDays = isActive
        ? activeSubscription!.dateFin.difference(now).inDays
        : 0;
    final isExpiringSoon = isActive && remainingDays <= 7;
    final canSubscribe = !isActive || isExpiringSoon;

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Header avec nom et prix
            Row(
              children: [
                Expanded(
                  child: Text(
                    service.nom,
                    style: theme.textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                  decoration: BoxDecoration(
                    color: theme.colorScheme.primaryContainer,
                    borderRadius: BorderRadius.circular(16),
                  ),
                  child: Text(
                    '${service.prix.toStringAsFixed(0)} FC',
                    style: theme.textTheme.labelLarge?.copyWith(
                      color: theme.colorScheme.onPrimaryContainer,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ],
            ),

            if (service.description != null && service.description!.isNotEmpty) ...[
              const SizedBox(height: 12),
              Text(
                service.description!,
                style: theme.textTheme.bodyMedium?.copyWith(
                  color: theme.colorScheme.onSurface.withOpacity(0.7),
                ),
              ),
            ],

            // Badge abonnement actif
            if (isActive) ...[
              const SizedBox(height: 10),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                decoration: BoxDecoration(
                  color: isExpiringSoon
                      ? Colors.orange.withOpacity(0.12)
                      : Colors.green.withOpacity(0.12),
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(
                    color: isExpiringSoon
                        ? Colors.orange.withOpacity(0.4)
                        : Colors.green.withOpacity(0.4),
                  ),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(
                      isExpiringSoon ? Icons.warning_amber_rounded : Icons.check_circle_rounded,
                      size: 16,
                      color: isExpiringSoon ? Colors.orange : Colors.green,
                    ),
                    const SizedBox(width: 6),
                    Text(
                      isExpiringSoon
                          ? 'Expire dans $remainingDays jour${remainingDays > 1 ? 's' : ''} — Renouvelable'
                          : 'Abonné jusqu\'au ${_formatDate(activeSubscription!.dateFin)} ($remainingDays j)',
                      style: TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.w500,
                        color: isExpiringSoon ? Colors.orange : Colors.green,
                      ),
                    ),
                  ],
                ),
              ),
            ],

            const SizedBox(height: 12),

            // Bouton d'abonnement
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: canSubscribe
                    ? () => _openPaymentDialog(context, ref)
                    : null,
                icon: Icon(isExpiringSoon
                    ? Icons.autorenew_rounded
                    : isActive
                        ? Icons.lock_rounded
                        : Icons.card_membership),
                label: Text(isExpiringSoon
                    ? 'Renouveler'
                    : isActive
                        ? 'Déjà abonné'
                        : 'S\'abonner'),
                style: ElevatedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 12),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  String _formatDate(DateTime date) {
    return '${date.day.toString().padLeft(2, '0')}/${date.month.toString().padLeft(2, '0')}/${date.year}';
  }

  void _openPaymentDialog(BuildContext context, WidgetRef ref) {
    final descriptionController = TextEditingController();
    final formKey = GlobalKey<FormState>();
    
    // Dates fixes pour un abonnement d'1 mois
    final dateDebut = DateTime.now();
    final dateFin = DateTime.now().add(const Duration(days: 30));
    
    // Variables pour le paiement
    PaymentMethod? _selectedPaymentMethod = PaymentMethod.availableMethods.first; // Mobile Money par défaut
    PaymentDetails? _paymentDetails;
    bool _isProcessing = false;
    
    final _cardNumberController = TextEditingController();
    final _expiryDateController = TextEditingController();
    final _cvvController = TextEditingController();
    final _holderNameController = TextEditingController();
    final _phoneNumberController = TextEditingController();
    final _providerController = TextEditingController(text: 'Orange'); // Opérateur par défaut

    showDialog(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setState) {
          final theme = Theme.of(context);
          return AlertDialog(
          title: Text('S\'abonner à ${service.nom}'),
          contentPadding: const EdgeInsets.all(16),
          content: SizedBox(
            width: MediaQuery.of(context).size.width * 0.9,
            child: Form(
              key: formKey,
              child: SingleChildScrollView(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const SizedBox(height: 8),
                    
                    // Dates readonly - Compact design
                    Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: theme.colorScheme.surfaceVariant.withOpacity(0.4),
                        borderRadius: BorderRadius.circular(8),
                        border: Border.all(color: theme.colorScheme.outline.withOpacity(0.4)),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              Icon(Icons.calendar_today, color: theme.colorScheme.onSurfaceVariant, size: 16),
                              const SizedBox(width: 6),
                              Expanded(
                                child: Text(
                                  'Début: ${dateDebut.day.toString().padLeft(2, '0')}/${dateDebut.month.toString().padLeft(2, '0')}/${dateDebut.year}',
                                  style: TextStyle(fontSize: 13, fontWeight: FontWeight.w500, color: theme.colorScheme.onSurface),
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 6),
                          Row(
                            children: [
                              Icon(Icons.event_busy, color: theme.colorScheme.onSurfaceVariant, size: 16),
                              const SizedBox(width: 6),
                              Expanded(
                                child: Text(
                                  'Fin: ${dateFin.day.toString().padLeft(2, '0')}/${dateFin.month.toString().padLeft(2, '0')}/${dateFin.year}',
                                  style: TextStyle(fontSize: 13, fontWeight: FontWeight.w500, color: theme.colorScheme.onSurface),
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 4),
                          Text(
                            'Durée: 1 mois (fixe)',
                            style: TextStyle(fontSize: 11, color: theme.colorScheme.onSurfaceVariant),
                          ),
                        ],
                      ),
                    ),
                    
                    const SizedBox(height: 16),
                    
                    // Méthodes de paiement - Uniquement Mobile Money
                    Text('Méthode de paiement', style: TextStyle(fontWeight: FontWeight.w600, color: theme.colorScheme.onSurface)),
                    const SizedBox(height: 8),
                    ...PaymentMethod.availableMethods.where((method) => 
                      method.type == PaymentMethodType.mobileMoney || method.type == PaymentMethodType.rtlMoney
                    ).map((method) {
                      final isSelected = _selectedPaymentMethod == method;
                      return Container(
                        margin: const EdgeInsets.only(bottom: 8),
                        decoration: BoxDecoration(
                          color: theme.colorScheme.surface,
                          borderRadius: BorderRadius.circular(8),
                          border: isSelected
                              ? Border.all(color: theme.colorScheme.primary, width: 2)
                              : Border.all(color: theme.colorScheme.outline.withOpacity(0.4)),
                        ),
                        child: RadioListTile<PaymentMethod>(
                          contentPadding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                          dense: true,
                          activeColor: theme.colorScheme.primary,
                          title: Row(
                            children: [
                              Text(method.icon, style: const TextStyle(fontSize: 20)),
                              const SizedBox(width: 8),
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(method.name, style: TextStyle(fontWeight: FontWeight.w600, fontSize: 14, color: theme.colorScheme.onSurface)),
                                    Text(method.description, style: TextStyle(color: theme.colorScheme.onSurfaceVariant, fontSize: 12)),
                                  ],
                                ),
                              ),
                            ],
                          ),
                          value: method,
                          groupValue: _selectedPaymentMethod,
                          onChanged: (PaymentMethod? value) {
                            setState(() {
                              _selectedPaymentMethod = value;
                              _paymentDetails = null;
                              _phoneNumberController.clear();
                              _providerController.clear();
                            });
                          },
                        ),
                      );
                    }).toList(),
                    
                    // Formulaire de paiement
                    if (_selectedPaymentMethod != null) ...[
                      const SizedBox(height: 16),
                      _buildPaymentForm(setState, _selectedPaymentMethod!, 
                          _phoneNumberController, _providerController, (details) {
                        _paymentDetails = details;
                      }),
                    ],
                    
                    const SizedBox(height: 16),
                    
                    // Montant (lecture seule)
                    Container(
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: theme.colorScheme.primaryContainer.withOpacity(0.3),
                        borderRadius: BorderRadius.circular(8),
                        border: Border.all(color: theme.colorScheme.primary.withOpacity(0.3)),
                      ),
                      child: Row(
                        children: [
                          Icon(Icons.attach_money, color: theme.colorScheme.primary),
                          const SizedBox(width: 8),
                          Text(
                            'Montant: ${service.prix.toStringAsFixed(0)} FC',
                            style: TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.w500,
                              color: theme.colorScheme.onSurface,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(),
              child: const Text('Annuler'),
            ),
            ElevatedButton(
              onPressed: _isProcessing ? null : () async {
                if (formKey.currentState!.validate() && _selectedPaymentMethod != null && _paymentDetails != null) {  
                  setState(() {
                    _isProcessing = true;
                  });
                  
                  try {
                    final apiService = ApiService();
                    
                    // Log des données envoyées
                    final paymentData = {
                      'service_id': service.id,
                      'phone_number': _paymentDetails!.details['phoneNumber'] ?? '',
                      'payment_method': _selectedPaymentMethod!.typeString,
                    };
                    
                    print('🚀 [FRONTEND] Initiation paiement abonnement');
                    print('📦 Données envoyées: $paymentData');
                    print('📱 Numéro téléphone: ${_paymentDetails!.details['phoneNumber']}');
                    print('💳 Méthode paiement: ${_selectedPaymentMethod!.typeString}');
                    print('🏷️ Service: ${service.nom} (ID: ${service.id})');
                    
                    // Initier le paiement avec le vrai système
                    final response = await apiService.post('/abonnements/initiate-payment/', data: paymentData);
                    
                    // Log de la réponse brute
                    print('✅ [FRONTEND] Réponse reçue du backend');
                    print('📄 Status code: ${response.statusCode}');
                    print('📦 Response data: ${response.data}');
                    
                    if (response.statusCode == 200 || response.statusCode == 201) {
                      final responseData = response.data as Map<String, dynamic>;
                      final isSimulated = responseData['simulated'] == true;
                      final reference = responseData['reference']?.toString() ?? '';
                      final amount = responseData['amount']?.toString() ?? service.prix.toStringAsFixed(0);
                      final currency = responseData['currency']?.toString() ?? 'CDF';

                      if (context.mounted) {
                        Navigator.of(context).pop(); // fermer le dialog

                        if (isSimulated) {
                          SnackbarService.showSuccess('Abonnement activé (simulation) !');
                          ref.invalidate(subscriptionsProvider);
                        } else if (reference.isNotEmpty) {
                          final subscribed = await Navigator.of(context).push<bool>(
                            MaterialPageRoute(
                              builder: (_) => PaymentStatusScreen(
                                transactionRef: reference,
                                summaryTitle: service.nom,
                                amount: amount,
                                currency: currency,
                                successMessage: 'Abonnement activé !',
                                successSubtitle: 'Votre abonnement au service\nest maintenant actif.',
                                onPaymentConfirmed: () async {
                                  await apiService.createSubscriptionAfterPayment(
                                    reference,
                                    service.id,
                                  );
                                },
                              ),
                            ),
                          );
                          if (subscribed == true) {
                            ref.invalidate(subscriptionsProvider);
                          }
                        } else {
                          SnackbarService.showSuccess('Paiement initié !');
                          ref.invalidate(subscriptionsProvider);
                        }
                      }
                    } else {
                      final errorData = response.data;
                      String errorMessage = errorData['error'] ?? 'Erreur lors de la souscription';

                      if (errorMessage.contains('déjà un abonnement')) {
                        errorMessage = 'Vous avez déjà un abonnement actif pour ce service.';
                      } else if (errorMessage.contains('Service non trouvé')) {
                        errorMessage = 'Service indisponible. Veuillez réessayer.';
                      } else if (errorMessage.contains('connexion')) {
                        errorMessage = 'Erreur de connexion. Vérifiez votre connexion internet.';
                      } else if (errorMessage.contains('téléphone')) {
                        errorMessage = 'Numéro de téléphone invalide ou manquant.';
                      }

                      if (context.mounted) SnackbarService.showError(errorMessage);
                    }
                  } catch (e) {
                    String errorMessage = 'Erreur lors de la souscription';
                    final s = e.toString();
                    if (s.contains('déjà un abonnement')) {
                      errorMessage = 'Vous avez déjà un abonnement actif pour ce service.';
                    } else if (s.contains('network') || s.contains('connection') || s.contains('connexion')) {
                      errorMessage = 'Erreur de connexion. Vérifiez votre connexion internet.';
                    } else if (s.contains('timeout')) {
                      errorMessage = 'Délai d\'attente dépassé. Veuillez réessayer.';
                    } else if (s.contains('404')) {
                      errorMessage = 'Service indisponible.';
                    } else if (s.contains('500')) {
                      errorMessage = 'Erreur serveur. Veuillez réessayer plus tard.';
                    }
                    if (context.mounted) SnackbarService.showError(errorMessage);
                  } finally {
                    if (context.mounted) {
                      setState(() {
                        _isProcessing = false;
                      });
                    }
                  }
                }
              },
              child: _isProcessing
                  ? SizedBox(
                      width: 20,
                      height: 20,
                      child: CircularProgressIndicator(strokeWidth: 2, color: theme.colorScheme.onPrimary),
                    )
                  : const Text('S\'abonner'),
            ),
          ],
          );
        },
      ),
    );
  }

  Widget _buildPaymentForm(
    StateSetter setState,
    PaymentMethod paymentMethod,
    TextEditingController phoneNumberController,
    TextEditingController providerController,
    Function(PaymentDetails) onUpdateDetails,
  ) {
    // Uniquement Mobile Money
    return Column(
      children: [
        TextField(
          controller: phoneNumberController,
          decoration: const InputDecoration(
            labelText: 'Numéro de téléphone',
            hintText: '+243 900 000 000',
            prefixIcon: Icon(Icons.phone),
            border: OutlineInputBorder(),
          ),
          keyboardType: TextInputType.phone,
          onChanged: (value) => onUpdateDetails(PaymentDetails(
            type: PaymentMethodType.mobileMoney,
            details: {'phoneNumber': value, 'provider': providerController.text},
          )),
        ),
        const SizedBox(height: 12),
        DropdownButtonFormField<String>(
          value: providerController.text.isEmpty ? null : providerController.text,
          decoration: const InputDecoration(
            labelText: 'Opérateur',
            prefixIcon: Icon(Icons.business),
            border: OutlineInputBorder(),
          ),
          items: const [
            DropdownMenuItem(value: 'Orange', child: Text('Orange Money')),
            DropdownMenuItem(value: 'Airtel', child: Text('Airtel Money')),
            DropdownMenuItem(value: 'Vodacom', child: Text('Vodacom M-Pesa')),
            DropdownMenuItem(value: 'Africell', child: Text('Afrimoney')),
          ],
          onChanged: (value) {
            providerController.text = value ?? '';
            onUpdateDetails(PaymentDetails(
              type: PaymentMethodType.mobileMoney,
              details: {'phoneNumber': phoneNumberController.text, 'provider': value ?? ''},
            ));
          },
        ),
      ],
    );
  }
}

// Classe pour les détails de paiement
class PaymentDetails {
  final PaymentMethodType type;
  final Map<String, String> details;

  PaymentDetails({
    required this.type,
    required this.details,
  });
}

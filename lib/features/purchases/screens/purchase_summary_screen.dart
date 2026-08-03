import 'package:flutter/material.dart';
import 'package:resume_plus_clean/models/summary.dart';
import 'package:resume_plus_clean/models/payment_method.dart';
import 'package:resume_plus_clean/services/api_service.dart';
import 'package:resume_plus_clean/services/snackbar_service.dart';
import 'package:resume_plus_clean/theme/app_theme.dart';
import 'package:resume_plus_clean/features/purchases/screens/payment_status_screen.dart';

class PurchaseSummaryScreen extends StatefulWidget {
  final Summary summary;

  const PurchaseSummaryScreen({
    super.key,
    required this.summary,
  });

  @override
  State<PurchaseSummaryScreen> createState() => _PurchaseSummaryScreenState();
}

class _PurchaseSummaryScreenState extends State<PurchaseSummaryScreen> {
  PaymentMethod? _selectedPaymentMethod;
  PaymentDetails? _paymentDetails;
  bool _isProcessing = false;
  final _apiService = ApiService();
  
  final _cardNumberController = TextEditingController();
  final _expiryDateController = TextEditingController();
  final _cvvController = TextEditingController();
  final _holderNameController = TextEditingController();
  
  final _phoneNumberController = TextEditingController();
  final _providerController = TextEditingController();

  @override
  void dispose() {
    _cardNumberController.dispose();
    _expiryDateController.dispose();
    _cvvController.dispose();
    _holderNameController.dispose();
    _phoneNumberController.dispose();
    _providerController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final topPadding = MediaQuery.of(context).padding.top;

    return Scaffold(
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      body: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
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
                    'Acheter le résumé',
                    style: theme.textTheme.headlineMedium?.copyWith(color: Colors.white, fontWeight: FontWeight.w700),
                  ),
                ],
              ),
            ),

            const SizedBox(height: 20),

            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _buildSummaryInfo(),
                  const SizedBox(height: 16),
                  _buildPaymentMethods(),
                  _buildPaymentForm(),
                  const SizedBox(height: 16),
                  _buildPurchaseButton(),
                  const SizedBox(height: 40),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSummaryInfo() {
    final theme = Theme.of(context);
    return Container(
      padding: const EdgeInsets.all(16),
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
                width: 36, height: 36,
                decoration: BoxDecoration(
                  color: AppTheme.primaryBlue.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: const Icon(Icons.description_rounded, color: AppTheme.primaryBlue, size: 20),
              ),
              const SizedBox(width: 10),
              Text('Résumé à acheter', style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w600, color: AppTheme.textPrimary)),
            ],
          ),
          const SizedBox(height: 14),
          Text(widget.summary.title, style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w600, color: AppTheme.textPrimary)),
          const SizedBox(height: 4),
          Text(widget.summary.subject, style: const TextStyle(color: AppTheme.textLight, fontSize: 13)),
          const SizedBox(height: 14),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text('Prix:', style: TextStyle(fontSize: 15, fontWeight: FontWeight.w600, color: AppTheme.textPrimary)),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
                decoration: BoxDecoration(
                  color: AppTheme.success.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(20),
                ),
                child: Text(
                  '${widget.summary.price.toStringAsFixed(0)} CDF',
                  style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700, color: AppTheme.success),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildPaymentMethods() {
    final paymentMethods = PaymentMethod.availableMethods;
    final theme = Theme.of(context);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Container(
              width: 32, height: 32,
              decoration: BoxDecoration(
                color: AppTheme.primaryBlue.withOpacity(0.1),
                borderRadius: BorderRadius.circular(8),
              ),
              child: const Icon(Icons.payment_rounded, color: AppTheme.primaryBlue, size: 18),
            ),
            const SizedBox(width: 10),
            Text('Méthode de paiement', style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w600, color: AppTheme.textPrimary)),
          ],
        ),
        const SizedBox(height: 12),
        ...paymentMethods.map((method) {
          final isSelected = _selectedPaymentMethod == method;
          return Container(
            margin: const EdgeInsets.only(bottom: 10),
            decoration: BoxDecoration(
              color: theme.colorScheme.surface,
              borderRadius: BorderRadius.circular(14),
              boxShadow: AppTheme.softShadow,
              border: isSelected ? Border.all(color: AppTheme.primaryBlue, width: 2) : null,
            ),
            child: RadioListTile<PaymentMethod>(
              contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
              activeColor: AppTheme.primaryBlue,
              title: Row(
                children: [
                  Text(method.icon, style: const TextStyle(fontSize: 24)),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(method.name, style: TextStyle(fontWeight: FontWeight.w600, fontSize: 15, color: Theme.of(context).colorScheme.onSurface)),
                        Text(method.description, style: TextStyle(color: Theme.of(context).colorScheme.onSurfaceVariant, fontSize: 13)),
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
                  _cardNumberController.clear();
                  _expiryDateController.clear();
                  _cvvController.clear();
                  _holderNameController.clear();
                  _phoneNumberController.clear();
                  _providerController.clear();
                });
              },
            ),
          );
        }).toList(),
      ],
    );
  }

  Widget _buildPaymentForm() {
    if (_selectedPaymentMethod == null) {
      return const SizedBox.shrink();
    }
    final theme = Theme.of(context);

    return Container(
      margin: const EdgeInsets.only(top: 16),
      padding: const EdgeInsets.all(16),
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
                width: 32, height: 32,
                decoration: BoxDecoration(
                  color: AppTheme.primaryBlue.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: const Icon(Icons.credit_card_rounded, color: AppTheme.primaryBlue, size: 18),
              ),
              const SizedBox(width: 10),
              Text('Informations de paiement', style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w600, color: AppTheme.textPrimary)),
            ],
          ),
          const SizedBox(height: 16),
          _buildPaymentMethodForm(),
        ],
      ),
    );
  }

  Widget _buildPaymentMethodForm() {
    switch (_selectedPaymentMethod!.type) {
      case PaymentMethodType.card:
        return _buildCardForm();
      case PaymentMethodType.mobileMoney:
      case PaymentMethodType.rtlMoney:
        return _buildMobileMoneyForm();
    }
  }

  Widget _buildCardForm() {
    return Column(
      children: [
        TextField(
          controller: _cardNumberController,
          decoration: const InputDecoration(
            labelText: 'Numéro de carte',
            hintText: '1234 5678 9012 3456',
            prefixIcon: Icon(Icons.credit_card),
          ),
          keyboardType: TextInputType.number,
          onChanged: (value) => _updatePaymentDetails('cardNumber', value),
        ),
        const SizedBox(height: 16),
        Row(
          children: [
            Expanded(
              child: TextField(
                controller: _expiryDateController,
                decoration: const InputDecoration(
                  labelText: 'Date d\'expiration',
                  hintText: 'MM/AA',
                  prefixIcon: Icon(Icons.calendar_today),
                ),
                keyboardType: TextInputType.datetime,
                onChanged: (value) => _updatePaymentDetails('expiryDate', value),
              ),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: TextField(
                controller: _cvvController,
                decoration: const InputDecoration(
                  labelText: 'CVV',
                  hintText: '123',
                  prefixIcon: Icon(Icons.lock),
                ),
                keyboardType: TextInputType.number,
                obscureText: true,
                onChanged: (value) => _updatePaymentDetails('cvv', value),
              ),
            ),
          ],
        ),
        const SizedBox(height: 16),
        TextField(
          controller: _holderNameController,
          decoration: const InputDecoration(
            labelText: 'Nom du titulaire',
            hintText: 'Jean Dupont',
            prefixIcon: Icon(Icons.person),
          ),
          textCapitalization: TextCapitalization.words,
          onChanged: (value) => _updatePaymentDetails('holderName', value),
        ),
      ],
    );
  }

  Widget _buildMobileMoneyForm() {
    return Column(
      children: [
        TextField(
          controller: _phoneNumberController,
          decoration: const InputDecoration(
            labelText: 'Numéro de téléphone',
            hintText: '+243 900 000 000',
            prefixIcon: Icon(Icons.phone),
          ),
          keyboardType: TextInputType.phone,
          onChanged: (value) => _updatePaymentDetails('phoneNumber', value),
        ),
        const SizedBox(height: 16),
        DropdownButtonFormField<String>(
          value: _providerController.text.isEmpty ? null : _providerController.text,
          decoration: const InputDecoration(
            labelText: 'Opérateur',
            prefixIcon: Icon(Icons.business),
          ),
          items: const [
            DropdownMenuItem(value: 'Vodacom', child: Text('Vodacom M-Pesa')),
            DropdownMenuItem(value: 'Airtel', child: Text('Airtel Money')),
            DropdownMenuItem(value: 'Orange', child: Text('Orange Money')),
          ],
          onChanged: (value) {
            _providerController.text = value ?? '';
            _updatePaymentDetails('provider', value ?? '');
          },
        ),
      ],
    );
  }

  Widget _buildPurchaseButton() {
    final phoneNumber = _paymentDetails?.details['phoneNumber'] ?? '';
    final canPurchase = _selectedPaymentMethod != null &&
                       _paymentDetails != null &&
                       _isFormValid() &&
                       phoneNumber.isNotEmpty &&
                       !_isProcessing;

    return SizedBox(
      width: double.infinity,
      height: 52,
      child: ElevatedButton(
        onPressed: canPurchase ? _processPurchase : null,
        style: ElevatedButton.styleFrom(
          backgroundColor: AppTheme.success,
          foregroundColor: Colors.white,
          disabledBackgroundColor: AppTheme.textLight.withOpacity(0.3),
          elevation: 0,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
        ),
        child: _isProcessing
            ? const Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white)),
                  SizedBox(width: 12),
                  Text('Traitement en cours...', style: TextStyle(fontSize: 15, fontWeight: FontWeight.w600)),
                ],
              )
            : Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(Icons.shopping_cart_checkout_rounded, color: Colors.white, size: 20),
                  const SizedBox(width: 8),
                  Text('Acheter pour ${widget.summary.price.toStringAsFixed(0)} CDF', style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w600)),
                ],
              ),
      ),
    );
  }

  bool _isFormValid() {
    if (_selectedPaymentMethod == null || _paymentDetails == null) return false;
    
    switch (_selectedPaymentMethod!.type) {
      case PaymentMethodType.card:
        final cardNumber = _paymentDetails!.details['cardNumber'] ?? '';
        final expiryDate = _paymentDetails!.details['expiryDate'] ?? '';
        final cvv = _paymentDetails!.details['cvv'] ?? '';
        final holderName = _paymentDetails!.details['holderName'] ?? '';
        
        return cardNumber.isNotEmpty &&
               expiryDate.isNotEmpty &&
               cvv.isNotEmpty &&
               holderName.isNotEmpty &&
               cardNumber.length >= 16 &&
               expiryDate.length >= 5 &&
               cvv.length >= 3;
      case PaymentMethodType.mobileMoney:
      case PaymentMethodType.rtlMoney:
        final phoneNumber = _paymentDetails!.details['phoneNumber'] ?? '';
        final provider = _paymentDetails!.details['provider'] ?? '';
        
        return phoneNumber.isNotEmpty &&
               provider.isNotEmpty &&
               phoneNumber.length >= 10;
    }
  }

  void _updatePaymentDetails(String key, String value) {
    if (_paymentDetails == null) {
      _paymentDetails = PaymentDetails(
        type: _selectedPaymentMethod!.type,
        details: {},
      );
    }
    
    setState(() {
      _paymentDetails!.details[key] = value;
    });
  }

  Future<void> _processPurchase() async {
    if (_selectedPaymentMethod == null || _paymentDetails == null) return;

    final phoneNumber = _paymentDetails!.details['phoneNumber'] ?? '';
    if (phoneNumber.isEmpty) {
      SnackbarService.show('❌ Numéro de téléphone requis', isError: true);
      return;
    }

    setState(() {
      _isProcessing = true;
    });

    try {
      final response = await _apiService.post(
        '/initiate-summary-purchase/',
        data: {
          'summary_id': widget.summary.id,
          'phone_number': phoneNumber,
        },
      );

      if (response.statusCode == 200 || response.statusCode == 201) {
        final data = response.data as Map<String, dynamic>;
        if (data['success'] == true) {
          final reference = data['reference']?.toString() ?? '';
          final summaryTitle = data['summary_title']?.toString() ?? widget.summary.title;
          final amount = data['amount']?.toString() ?? widget.summary.price.toStringAsFixed(0);
          final currency = data['currency']?.toString() ?? 'CDF';

          final isSimulated = data['simulated'] == true;

          if (mounted && isSimulated) {
            // Mode simulation → succès direct
            SnackbarService.show('Paiement réussi !', isError: false);
            Navigator.of(context).popUntil((route) => route.isFirst);
          } else if (mounted && reference.isNotEmpty) {
            Navigator.of(context).pushReplacement(
              MaterialPageRoute(
                builder: (_) => PaymentStatusScreen(
                  transactionRef: reference,
                  summaryTitle: summaryTitle,
                  amount: amount,
                  currency: currency,
                ),
              ),
            );
          } else if (mounted) {
            SnackbarService.show('Paiement initié !', isError: false);
            Navigator.of(context).popUntil((route) => route.isFirst);
          }
        } else {
          final errorMessage = data['error'] ?? 'Erreur lors de l\'initiation du paiement';
          if (mounted) SnackbarService.show('❌ $errorMessage', isError: true);
        }
      } else {
        final data = response.data as Map<String, dynamic>? ?? {};
        final errorMessage = data['error'] ?? 'Erreur lors du paiement';
        if (mounted) SnackbarService.show('❌ $errorMessage', isError: true);
      }
    } catch (e) {
      String errorMessage = 'Erreur lors de l\'achat';
      final s = e.toString();

      if (s.contains('déjà acheté') || s.contains('already purchased')) {
        errorMessage = 'Vous avez déjà acheté ce résumé. Consultez-le dans "Mes Achats".';
      } else if (s.contains('network') || s.contains('connection') || s.contains('connexion')) {
        errorMessage = 'Erreur de connexion. Vérifiez votre connexion internet.';
      } else if (s.contains('timeout')) {
        errorMessage = 'Délai d\'attente dépassé. Veuillez réessayer.';
      } else if (s.contains('abonnement') || s.contains('subscription')) {
        errorMessage = 'Un abonnement actif est requis pour acheter ce résumé.';
      } else if (s.contains('400')) {
        errorMessage = 'Données invalides. Vérifiez votre numéro.';
      } else if (s.contains('500')) {
        errorMessage = 'Erreur serveur. Veuillez réessayer plus tard.';
      }

      if (mounted) SnackbarService.show('❌ $errorMessage', isError: true);
    } finally {
      if (mounted) {
        setState(() {
          _isProcessing = false;
        });
      }
    }
  }
}

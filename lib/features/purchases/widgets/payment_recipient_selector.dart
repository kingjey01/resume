import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:resume_plus_clean/exceptions/api_exception.dart';
import 'package:resume_plus_clean/services/api_service.dart';
import 'package:resume_plus_clean/services/storage_service.dart';
import 'package:resume_plus_clean/theme/app_theme.dart';

/// Tâche 70 — « Payer pour un autre étudiant ».
///
/// Ce fichier centralise :
/// - l'état du choix « Payer pour moi / Payer pour un autre » ;
/// - la vérification du numéro du bénéficiaire avant paiement ;
/// - le widget réutilisé par les écrans d'achat de résumé et d'abonnement.
///
/// La fonctionnalité est volontairement limitée à Android : sur iOS et sur le
/// Web, le widget ne s'affiche pas et l'état reste « Payer pour moi ».

bool get payForSomeoneEnabled =>
    !kIsWeb && defaultTargetPlatform == TargetPlatform.android;

class PaymentRecipientController extends ChangeNotifier {
  PaymentRecipientController({String? payerPhone}) : payerPhone = payerPhone ?? '';

  bool isGift = false;
  String payerPhone;
  String beneficiaryPhone = '';

  String? verifiedName;
  String? verifiedPromotion;
  String? verifiedMaskedPhone;

  bool isVerifying = false;
  String? error;

  /// Un paiement « pour un autre » n'est envoyé que si le numéro a été
  /// vérifié côté serveur.
  bool get isReady =>
      !isGift || (verifiedName != null && verifiedName!.isNotEmpty);

  void setMode(bool gift) {
    if (isGift == gift) return;
    isGift = gift;
    error = null;
    if (!gift) {
      beneficiaryPhone = '';
      _clearVerification();
    }
    notifyListeners();
  }

  void setPayerPhone(String value) {
    payerPhone = value;
    notifyListeners();
  }

  void setBeneficiaryPhone(String value) {
    beneficiaryPhone = value;
    _clearVerification();
    error = null;
    notifyListeners();
  }

  void _clearVerification() {
    verifiedName = null;
    verifiedPromotion = null;
    verifiedMaskedPhone = null;
  }

  Future<bool> verify(ApiService api) async {
    final phone = beneficiaryPhone.trim();
    if (phone.isEmpty) {
      error = 'Saisissez le numéro du bénéficiaire.';
      notifyListeners();
      return false;
    }

    isVerifying = true;
    error = null;
    _clearVerification();
    notifyListeners();

    try {
      final data = await api.verifyBeneficiary(phone);
      if (data['found'] == true) {
        verifiedName = data['display_name']?.toString();
        verifiedPromotion = data['promotion']?.toString();
        verifiedMaskedPhone = data['phone_masked']?.toString();
        return true;
      }
      error = data['error']?.toString() ?? 'Bénéficiaire introuvable.';
      return false;
    } catch (e) {
      error = e is ApiException ? e.message : 'Bénéficiaire introuvable.';
      return false;
    } finally {
      isVerifying = false;
      notifyListeners();
    }
  }
}

class PaymentRecipientSelector extends StatefulWidget {
  final PaymentRecipientController controller;
  final ApiService apiService;

  /// Appelé quand l'utilisateur change de mode (le parent peut masquer son
  /// propre champ « numéro de téléphone » en mode cadeau).
  final ValueChanged<bool>? onModeChanged;

  const PaymentRecipientSelector({
    super.key,
    required this.controller,
    required this.apiService,
    this.onModeChanged,
  });

  @override
  State<PaymentRecipientSelector> createState() =>
      _PaymentRecipientSelectorState();
}

class _PaymentRecipientSelectorState extends State<PaymentRecipientSelector> {
  final TextEditingController _beneficiaryController = TextEditingController();
  final TextEditingController _payerController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _payerController.text = widget.controller.payerPhone;
    _beneficiaryController.text = widget.controller.beneficiaryPhone;
    _loadAccountPhone();
  }

  Future<void> _loadAccountPhone() async {
    if (!payForSomeoneEnabled) return;
    if (widget.controller.payerPhone.isNotEmpty) return;
    final stored = await StorageService().getRegisteredPhone();
    if (!mounted || stored == null || stored.isEmpty) return;
    widget.controller.setPayerPhone(stored);
    _payerController.text = stored;
  }

  @override
  void dispose() {
    _beneficiaryController.dispose();
    _payerController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (!payForSomeoneEnabled) return const SizedBox.shrink();

    final controller = widget.controller;
    final theme = Theme.of(context);

    return ListenableBuilder(
      listenable: controller,
      builder: (context, _) {
        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                ChoiceChip(
                  label: const Text('Payer pour moi'),
                  avatar: const Icon(Icons.person_rounded, size: 18),
                  selected: !controller.isGift,
                  onSelected: (_) {
                    controller.setMode(false);
                    widget.onModeChanged?.call(false);
                  },
                ),
                ChoiceChip(
                  label: const Text('Payer pour un autre'),
                  avatar: const Icon(Icons.card_giftcard_rounded, size: 18),
                  selected: controller.isGift,
                  onSelected: (_) {
                    controller.setMode(true);
                    widget.onModeChanged?.call(true);
                  },
                ),
              ],
            ),
            if (controller.isGift) ...[
              const SizedBox(height: 16),
              TextField(
                controller: _payerController,
                keyboardType: TextInputType.phone,
                decoration: const InputDecoration(
                  labelText: 'Numéro du payeur (Mobile Money)',
                  hintText: 'Ex: 0973123456',
                  prefixIcon: Icon(Icons.payments_outlined),
                  border: OutlineInputBorder(),
                ),
                onChanged: controller.setPayerPhone,
              ),
              const SizedBox(height: 12),
              TextField(
                controller: _beneficiaryController,
                keyboardType: TextInputType.phone,
                decoration: InputDecoration(
                  labelText: 'Numéro du bénéficiaire',
                  hintText: 'Compte étudiant qui reçoit l\'achat',
                  prefixIcon: const Icon(Icons.school_outlined),
                  border: const OutlineInputBorder(),
                  suffixIcon: TextButton(
                    onPressed: controller.isVerifying
                        ? null
                        : () => controller.verify(widget.apiService),
                    child: controller.isVerifying
                        ? const SizedBox(
                            width: 16,
                            height: 16,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          )
                        : const Text('Vérifier'),
                  ),
                ),
                onChanged: controller.setBeneficiaryPhone,
              ),
              if (controller.error != null) ...[
                const SizedBox(height: 8),
                Text(
                  controller.error!,
                  style: const TextStyle(color: AppTheme.error, fontSize: 12),
                ),
              ],
              if (controller.verifiedName != null) ...[
                const SizedBox(height: 10),
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: AppTheme.success.withValues(alpha: 0.08),
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(
                        color: AppTheme.success.withValues(alpha: 0.3)),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.verified_user_rounded,
                          color: AppTheme.success, size: 20),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              controller.verifiedName!,
                              style: const TextStyle(
                                fontWeight: FontWeight.w600,
                                fontSize: 13,
                              ),
                            ),
                            Text(
                              [
                                if (controller.verifiedMaskedPhone != null)
                                  controller.verifiedMaskedPhone!,
                                if (controller.verifiedPromotion != null)
                                  controller.verifiedPromotion!,
                              ].join(' • '),
                              style: TextStyle(
                                fontSize: 11,
                                color: theme.colorScheme.onSurfaceVariant,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 6),
                const Text(
                  'L\'achat sera attribué à ce compte. Vous resterez enregistré '
                  'comme payeur.',
                  style: TextStyle(fontSize: 11, color: AppTheme.textLight),
                ),
              ],
            ],
          ],
        );
      },
    );
  }
}

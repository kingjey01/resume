import 'package:flutter/material.dart';
import 'package:resume_plus_clean/models/purchase.dart';
import 'package:resume_plus_clean/models/summary.dart';
import 'package:resume_plus_clean/features/summary_details/screens/summary_details_screen.dart';
import 'package:resume_plus_clean/theme/app_theme.dart';

class PurchasedSummaryCard extends StatelessWidget {
  final dynamic purchase;

  const PurchasedSummaryCard({
    super.key,
    required this.purchase,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final amount = _getAmountSafely(purchase);
    final rawTitle = _getPropertySafely(purchase, 'summary_title', '');
    final summaryTitle = rawTitle.trim().isEmpty ? 'Résumé sans titre' : rawTitle;
    final createdAt = _getPropertySafely(purchase, 'created_at', '');
    final paymentMethod = _getPropertySafely(purchase, 'payment_method', '');

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      decoration: BoxDecoration(
        color: theme.colorScheme.surface,
        borderRadius: BorderRadius.circular(16),
        boxShadow: AppTheme.softShadow,
      ),
      child: Material(
        color: Colors.transparent,
        borderRadius: BorderRadius.circular(16),
        child: InkWell(
          borderRadius: BorderRadius.circular(16),
          onTap: () => _openSummary(context),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                      decoration: BoxDecoration(
                        color: AppTheme.success.withOpacity(0.1),
                        borderRadius: BorderRadius.circular(20),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: const [
                          Icon(Icons.check_circle_rounded, size: 14, color: AppTheme.success),
                          SizedBox(width: 4),
                          Text(
                            'ACHETÉ',
                            style: TextStyle(
                              fontSize: 11,
                              fontWeight: FontWeight.w600,
                              color: AppTheme.success,
                            ),
                          ),
                        ],
                      ),
                    ),
                    const Spacer(),
                    Text(
                      '${amount.toStringAsFixed(0)} CDF',
                      style: theme.textTheme.titleSmall?.copyWith(
                        fontWeight: FontWeight.w700,
                        color: AppTheme.primaryBlue,
                      ),
                    ),
                  ],
                ),
                
                const SizedBox(height: 12),
                
                Text(
                  summaryTitle,
                  style: theme.textTheme.titleSmall?.copyWith(
                    fontWeight: FontWeight.w600,
                    color: theme.colorScheme.onSurface,
                  ),
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),
                
                const SizedBox(height: 10),
                
                Row(
                  children: [
                    Icon(Icons.calendar_today_rounded, size: 13, color: theme.colorScheme.onSurface.withOpacity(0.7)),
                    const SizedBox(width: 4),
                    Text(
                      'Acheté le ${_formatDate(createdAt)}',
                      style: TextStyle(color: theme.colorScheme.onSurface.withOpacity(0.7), fontSize: 12),
                    ),
                    const Spacer(),
                    Icon(Icons.payment_rounded, size: 13, color: theme.colorScheme.onSurface.withOpacity(0.7)),
                    const SizedBox(width: 4),
                    Text(
                      _getPaymentMethodText(paymentMethod),
                      style: TextStyle(color: theme.colorScheme.onSurface.withOpacity(0.7), fontSize: 12),
                    ),
                  ],
                ),
                
                const SizedBox(height: 14),
                
                Row(
                  children: [
                    Expanded(
                      child: SizedBox(
                        height: 46,
                        child: ElevatedButton.icon(
                          onPressed: () => _openSummary(context),
                          icon: const Icon(Icons.visibility_rounded, size: 17),
                          label: const Text('Consulter', style: TextStyle(fontSize: 13), overflow: TextOverflow.ellipsis),
                          style: ElevatedButton.styleFrom(
                            backgroundColor: AppTheme.primaryBlue,
                            foregroundColor: Colors.white,
                            elevation: 0,
                            padding: const EdgeInsets.symmetric(horizontal: 8),
                            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: SizedBox(
                        height: 46,
                        child: ElevatedButton.icon(
                          onPressed: null, // Désactivé pour éviter le partage entre utilisateurs
                          icon: const Icon(Icons.download_rounded, size: 17, color: Colors.grey),
                          label: const Text('Télécharger', style: TextStyle(fontSize: 13, color: Colors.grey), overflow: TextOverflow.ellipsis),
                          style: ElevatedButton.styleFrom(
                            backgroundColor: Colors.grey.withOpacity(0.1),
                            foregroundColor: Colors.grey,
                            disabledBackgroundColor: Colors.grey.withOpacity(0.1),
                            disabledForegroundColor: Colors.grey,
                            elevation: 0,
                            padding: const EdgeInsets.symmetric(horizontal: 8),
                            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  // Méthodes utilitaires pour accès sécurisé aux propriétés
  String _getPropertySafely(dynamic obj, String key, String defaultValue) {
    try {
      if (obj == null) return defaultValue;
      if (obj is Map<String, dynamic>) {
        return obj[key]?.toString() ?? defaultValue;
      }
      // Si c'est un objet avec des propriétés
      final value = obj.runtimeType.toString().contains('Purchase') 
          ? _getPurchaseProperty(obj, key) 
          : null;
      return value?.toString() ?? defaultValue;
    } catch (e) {
      return defaultValue;
    }
  }

  double _getAmountSafely(dynamic obj) {
    try {
      if (obj == null) return 0.0;
      if (obj is Map<String, dynamic>) {
        final amount = obj['amount'];
        if (amount is double) return amount;
        if (amount is int) return amount.toDouble();
        if (amount is String) return double.tryParse(amount) ?? 0.0;
        return 0.0;
      }
      // Si c'est un objet Purchase
      if (obj.runtimeType.toString().contains('Purchase')) {
        return _getPurchaseProperty(obj, 'amount') as double? ?? 0.0;
      }
      return 0.0;
    } catch (e) {
      return 0.0;
    }
  }

  dynamic _getPurchaseProperty(dynamic purchase, String property) {
    try {
      switch (property) {
        case 'amount':
          return purchase.amount;
        case 'summary_title':
          return purchase.summaryTitle;
        case 'created_at':
          return purchase.createdAt;
        case 'payment_method':
          return purchase.paymentMethod;
        default:
          return null;
      }
    } catch (e) {
      return null;
    }
  }

  String _formatDate(String? dateString) {
    if (dateString == null || dateString.isEmpty) return 'Date inconnue';
    
    try {
      final date = DateTime.parse(dateString);
      return '${date.day.toString().padLeft(2, '0')}/${date.month.toString().padLeft(2, '0')}/${date.year}';
    } catch (e) {
      return 'Date invalide';
    }
  }

  String _getPaymentMethodText(String? method) {
    switch (method) {
      case 'mobile_money':
        return 'Mobile Money';
      case 'card':
        return 'Carte Bancaire';
      case 'points':
        return 'Points';
      default:
        return 'Autre';
    }
  }

  void _openSummary(BuildContext context) {
    // Créer un objet Summary à partir des données de purchase
    final summary = _createSummaryFromPurchase();
    if (summary != null) {
      Navigator.of(context).push(
        MaterialPageRoute(
          builder: (context) => SummaryDetailsScreen(summary: summary),
        ),
      );
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Erreur: Impossible d\'ouvrir le résumé')),
      );
    }
  }

  Summary? _createSummaryFromPurchase() {
    try {
      final rawSummaryId = _getPropertySafely(purchase, 'summary', '0');
      final summaryId = int.tryParse(rawSummaryId) ?? 0;
      if (summaryId == 0) return null;

      final rawTitle = _getPropertySafely(purchase, 'summary_title', '');
      final title = rawTitle.trim().isEmpty ? 'Résumé acheté' : rawTitle;
      final amount = _getAmountSafely(purchase);

      return Summary(
        id: summaryId,
        title: title,
        subject: 'Résumé acheté',
        imageUrl: '',
        content: '__FETCH_REQUIRED__',
        price: amount,
        isFree: false,
        authorName: '',
        createdAt: DateTime.now(),
        isPurchased: true,
      );
    } catch (e) {
      return null;
    }
  }

  void _downloadSummary(BuildContext context) {
    // Téléchargement désactivé pour éviter le partage entre utilisateurs
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Le téléchargement est désactivé pour protéger les contenus achetés. Vous pouvez consulter le résumé en ligne.'),
        duration: Duration(seconds: 4),
      ),
    );
  }
}

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:resume_plus_clean/features/summaries/providers/purchased_summaries_provider.dart';
import 'package:resume_plus_clean/providers/tab_refresh_provider.dart';
import 'package:resume_plus_clean/features/summaries/widgets/purchased_summary_card.dart';
import 'package:resume_plus_clean/theme/app_theme.dart';

class PurchasesScreen extends ConsumerStatefulWidget {
  const PurchasesScreen({super.key});

  @override
  ConsumerState<PurchasesScreen> createState() => _PurchasesScreenState();
}

class _PurchasesScreenState extends ConsumerState<PurchasesScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;
  String _searchQuery = '';

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final topPadding = MediaQuery.of(context).padding.top;

    // Rafraîchir les données à chaque fois qu'on arrive sur l'onglet Achats
    ref.listen<int>(purchasesRefreshProvider, (prev, next) {
      if (prev != next) {
        ref.invalidate(purchasedSummariesProvider);
      }
    });

    return Scaffold(
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      body: Column(
        children: [
          // Header avec gradient bleu
          Container(
            padding: EdgeInsets.only(top: topPadding + 16, left: 20, right: 20, bottom: 0),
            decoration: const BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
                colors: [
                  AppTheme.primaryBlueDark,
                  AppTheme.primaryBlue,
                  AppTheme.primaryBlueLight,
                ],
              ),
              borderRadius: BorderRadius.only(
                bottomLeft: Radius.circular(24),
                bottomRight: Radius.circular(24),
              ),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      'Mes Achats',
                      style: theme.textTheme.headlineMedium?.copyWith(
                        color: Colors.white,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                    IconButton(
                      onPressed: () => ref.invalidate(purchasedSummariesProvider),
                      icon: const Icon(Icons.refresh_rounded, color: Colors.white),
                      tooltip: 'Rafraîchir',
                    ),
                  ],
                ),
                const SizedBox(height: 4),
                // Barre de recherche pill
                Container(
                  height: 46,
                  decoration: BoxDecoration(
                    color: Colors.white.withOpacity(0.2),
                    borderRadius: BorderRadius.circular(23),
                  ),
                  child: TextField(
                    style: const TextStyle(color: Colors.white, fontSize: 14),
                    decoration: InputDecoration(
                      hintText: 'Rechercher...',
                      hintStyle: TextStyle(color: Colors.white.withOpacity(0.7), fontSize: 14),
                      prefixIcon: Icon(Icons.search_rounded, color: Colors.white.withOpacity(0.8)),
                      suffixIcon: _searchQuery.isNotEmpty
                          ? IconButton(
                              icon: Icon(Icons.close_rounded, color: Colors.white.withOpacity(0.8), size: 20),
                              onPressed: () => setState(() => _searchQuery = ''),
                            )
                          : null,
                      border: InputBorder.none,
                      enabledBorder: InputBorder.none,
                      focusedBorder: InputBorder.none,
                      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                      filled: false,
                    ),
                    onChanged: (value) => setState(() => _searchQuery = value),
                  ),
                ),
                const SizedBox(height: 14),
                // Tabs
                TabBar(
                  controller: _tabController,
                  labelColor: Colors.white,
                  unselectedLabelColor: Colors.white.withOpacity(0.6),
                  indicatorColor: Colors.white,
                  indicatorWeight: 3,
                  indicatorSize: TabBarIndicatorSize.label,
                  dividerColor: Colors.transparent,
                  labelStyle: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600),
                  unselectedLabelStyle: const TextStyle(fontSize: 13, fontWeight: FontWeight.w500),
                  tabs: const [
                    Tab(text: 'Résumés Achetés'),
                    Tab(text: 'Historique Paiements'),
                  ],
                ),
              ],
            ),
          ),
          
          // Contenu des onglets
          Expanded(
            child: TabBarView(
              controller: _tabController,
              children: [
                _buildPurchasedSummariesTab(),
                _buildPaymentHistoryTab(),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildPurchasedSummariesTab() {
    final purchasedSummariesAsync = ref.watch(purchasedSummariesProvider);

    return RefreshIndicator(
      onRefresh: () async {
        ref.invalidate(purchasedSummariesProvider);
      },
      child: purchasedSummariesAsync.when(
        data: (allPurchases) {
          // 🧩11: only show completed summary purchases (exclude subscriptions)
          final purchasedSummaries = allPurchases
              .where((p) {
                final status = _getPropertySafely(p, 'status', '');
                final summary = p is Map ? p['summary'] : null;
                return status == 'completed' && summary != null;
              })
              .toList();

          if (purchasedSummaries.isEmpty) {
            return _buildEmptyState(
              icon: Icons.library_books_outlined,
              title: _searchQuery.isNotEmpty
                  ? 'Aucun résumé trouvé'
                  : 'Aucun résumé acheté',
              subtitle: _searchQuery.isNotEmpty
                  ? 'Essayez avec d\'autres mots-clés'
                  : 'Vos résumés achetés apparaîtront ici',
            );
          }

          try {
            final filteredPurchased = _filterPurchasedSummaries(purchasedSummaries);
            
            if (filteredPurchased.isEmpty) {
              return _buildEmptyState(
                icon: Icons.library_books_outlined,
                title: 'Aucun résumé trouvé',
                subtitle: 'Essayez avec d\'autres mots-clés',
              );
            }

            return ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: filteredPurchased.length,
              itemBuilder: (context, index) {
                try {
                  final purchase = filteredPurchased[index];
                  if (purchase == null) {
                    return const SizedBox.shrink();
                  }
                  return PurchasedSummaryCard(purchase: purchase);
                } catch (e) {
                  print('Erreur lors de la construction de PurchasedSummaryCard: $e');
                  return const SizedBox.shrink();
                }
              },
            );
          } catch (e) {
            print('Erreur dans _buildPurchasedSummariesTab: $e');
            return _buildErrorState('Erreur lors du chargement des résumés achetés');
          }
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, stack) => _buildErrorState(error.toString()),
      ),
    );
  }

  Widget _buildPaymentHistoryTab() {
    final purchasedSummariesAsync = ref.watch(purchasedSummariesProvider);

    return RefreshIndicator(
      onRefresh: () async {
        ref.invalidate(purchasedSummariesProvider);
      },
      child: purchasedSummariesAsync.when(
        data: (purchases) {
          if (purchases.isEmpty) {
            return _buildEmptyState(
              icon: Icons.payment_outlined,
              title: _searchQuery.isNotEmpty 
                  ? 'Aucun paiement trouvé'
                  : 'Aucun historique de paiement',
              subtitle: _searchQuery.isNotEmpty
                  ? 'Essayez avec d\'autres mots-clés'
                  : 'Vos paiements apparaîtront ici',
            );
          }

          try {
            final filteredPurchases = _filterPaymentHistory(purchases);
            
            if (filteredPurchases.isEmpty) {
              return _buildEmptyState(
                icon: Icons.payment_outlined,
                title: 'Aucun paiement trouvé',
                subtitle: 'Essayez avec d\'autres mots-clés',
              );
            }

            return ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: filteredPurchases.length,
              itemBuilder: (context, index) {
                try {
                  return _buildPaymentHistoryCard(filteredPurchases[index]);
                } catch (e) {
                  return Card(
                    margin: const EdgeInsets.only(bottom: 12),
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Text('Erreur d\'affichage: $e'),
                    ),
                  );
                }
              },
            );
          } catch (e) {
            print('Erreur dans _buildPaymentHistoryTab: $e');
            return _buildErrorState('Erreur lors du chargement de l\'historique');
          }
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, stack) => _buildErrorState(error.toString()),
      ),
    );
  }

  Widget _buildPaymentHistoryCard(dynamic purchase) {
    final theme = Theme.of(context);
    
    final status = _getPropertySafely(purchase, 'status', 'pending');
    final amount = _getAmountSafely(purchase);
    final rawSummaryTitle = _getPropertySafely(purchase, 'summary_title', '');
    final serviceName = _getPropertySafely(purchase, 'service_name', '');
    final summaryTitle = rawSummaryTitle.isNotEmpty 
        ? rawSummaryTitle 
        : serviceName.isNotEmpty 
            ? 'Abonnement: $serviceName' 
            : 'Paiement';
    final createdAt = _getPropertySafely(purchase, 'created_at', '');
    final paymentMethod = _getPropertySafely(purchase, 'payment_method', '');
    final transactionId = _getPropertySafely(purchase, 'transaction_id', '');
    
    return Container(
      margin: const EdgeInsets.only(bottom: 12, left: 20, right: 20),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surface,
        borderRadius: BorderRadius.circular(14),
        boxShadow: AppTheme.softShadow,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                decoration: BoxDecoration(
                  color: _getStatusColor(status).withOpacity(0.1),
                  borderRadius: BorderRadius.circular(20),
                ),
                child: Text(
                  _getStatusText(status),
                  style: TextStyle(
                    fontSize: 11,
                    fontWeight: FontWeight.w600,
                    color: _getStatusColor(status),
                  ),
                ),
              ),
              const Spacer(),
              Text(
                '${amount.toStringAsFixed(0)} CDF',
                style: theme.textTheme.titleMedium?.copyWith(
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
                'Payé le ${_formatDate(createdAt)}',
                style: TextStyle(color: theme.colorScheme.onSurface.withOpacity(0.7), fontSize: 12),
              ),
            ],
          ),
          
          const SizedBox(height: 4),
          
          Row(
            children: [
              Icon(Icons.payment_rounded, size: 13, color: theme.colorScheme.onSurface.withOpacity(0.7)),
              const SizedBox(width: 4),
              Text(
                _getPaymentMethodText(paymentMethod),
                style: TextStyle(color: theme.colorScheme.onSurface.withOpacity(0.7), fontSize: 12),
              ),
              if (transactionId.isNotEmpty) ...[
                const SizedBox(width: 16),
                Icon(Icons.receipt_rounded, size: 13, color: theme.colorScheme.onSurface.withOpacity(0.7)),
                const SizedBox(width: 4),
                Flexible(
                  child: Text(
                    'ID: $transactionId',
                    style: TextStyle(color: theme.colorScheme.onSurface.withOpacity(0.7), fontSize: 12),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
              ],
            ],
          ),
        ],
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
        case 'status':
          return purchase.status;
        case 'amount':
          return purchase.amount;
        case 'summary_title':
          return purchase.summaryTitle;
        case 'created_at':
          return purchase.createdAt;
        case 'payment_method':
          return purchase.paymentMethod;
        case 'transaction_id':
          return purchase.transactionId;
        default:
          return null;
      }
    } catch (e) {
      return null;
    }
  }

  List<dynamic> _filterPurchasedSummaries(List<dynamic> purchases) {
    if (_searchQuery.isEmpty) return purchases;
    
    return purchases.where((purchase) {
      final title = _getPropertySafely(purchase, 'summary_title', '').toLowerCase();
      final query = _searchQuery.toLowerCase();
      
      return title.contains(query);
    }).toList();
  }

  List<dynamic> _filterPaymentHistory(List<dynamic> purchases) {
    if (_searchQuery.isEmpty) return purchases;
    
    return purchases.where((purchase) {
      final title = _getPropertySafely(purchase, 'summary_title', '').toLowerCase();
      final transactionId = _getPropertySafely(purchase, 'transaction_id', '').toLowerCase();
      final query = _searchQuery.toLowerCase();
      
      return title.contains(query) || transactionId.contains(query);
    }).toList();
  }

  Color _getStatusColor(String status) {
    switch (status) {
      case 'completed':
        return Colors.green;
      case 'pending':
        return Colors.orange;
      case 'failed':
        return Colors.red;
      case 'refunded':
        return Colors.blue;
      default:
        return Colors.grey;
    }
  }

  String _getStatusText(String status) {
    switch (status) {
      case 'completed':
        return 'PAYÉ';
      case 'pending':
        return 'EN ATTENTE';
      case 'failed':
        return 'ÉCHOUÉ';
      case 'refunded':
        return 'REMBOURSÉ';
      default:
        return 'INCONNU';
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

  String _formatDate(String? dateString) {
    if (dateString == null) return 'Date inconnue';
    
    try {
      final date = DateTime.parse(dateString);
      return '${date.day.toString().padLeft(2, '0')}/${date.month.toString().padLeft(2, '0')}/${date.year}';
    } catch (e) {
      return 'Date invalide';
    }
  }

  Widget _buildEmptyState({
    required IconData icon,
    required String title,
    required String subtitle,
  }) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              width: 80,
              height: 80,
              decoration: BoxDecoration(
                color: AppTheme.primaryBlue.withOpacity(0.1),
                shape: BoxShape.circle,
              ),
              child: Icon(icon, size: 36, color: AppTheme.primaryBlue),
            ),
            const SizedBox(height: 20),
            Text(
              title,
              style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w600, color: AppTheme.textPrimary),
            ),
            const SizedBox(height: 8),
            Text(
              subtitle,
              style: const TextStyle(color: AppTheme.textLight, fontSize: 14),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildErrorState(String error) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              width: 80,
              height: 80,
              decoration: BoxDecoration(
                color: AppTheme.error.withOpacity(0.1),
                shape: BoxShape.circle,
              ),
              child: const Icon(Icons.error_outline_rounded, size: 36, color: AppTheme.error),
            ),
            const SizedBox(height: 20),
            const Text('Erreur de chargement', style: TextStyle(fontSize: 17, fontWeight: FontWeight.w600, color: AppTheme.textPrimary)),
            const SizedBox(height: 8),
            Text(error, style: const TextStyle(color: AppTheme.textLight, fontSize: 13), textAlign: TextAlign.center),
            const SizedBox(height: 20),
            ElevatedButton(
              onPressed: () => ref.invalidate(purchasedSummariesProvider),
              child: const Text('Réessayer'),
            ),
          ],
        ),
      ),
    );
  }
}

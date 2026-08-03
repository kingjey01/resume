import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:resume_plus_clean/models/service.dart';
import 'package:resume_plus_clean/models/abonnement.dart';
import 'package:resume_plus_clean/features/subscriptions/providers/subscription_provider.dart';
import 'package:resume_plus_clean/features/subscriptions/providers/service_provider.dart';
import 'package:resume_plus_clean/features/subscriptions/widgets/subscription_card.dart';
import 'package:resume_plus_clean/features/subscriptions/widgets/service_card.dart';
import 'package:resume_plus_clean/theme/app_theme.dart';

class SubscriptionsScreen extends ConsumerStatefulWidget {
  const SubscriptionsScreen({super.key});

  @override
  ConsumerState<SubscriptionsScreen> createState() => _SubscriptionsScreenState();
}

class _SubscriptionsScreenState extends ConsumerState<SubscriptionsScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;

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

    return Scaffold(
      backgroundColor: theme.scaffoldBackgroundColor,
      body: Column(
        children: [
          // Header bleu avec onglets
          Container(
            padding: EdgeInsets.only(top: topPadding + 8, left: 20, right: 20),
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
                Row(
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
                    const SizedBox(width: 14),
                    Expanded(
                      child: Text(
                        'Abonnements',
                        style: theme.textTheme.titleLarge?.copyWith(color: Colors.white, fontWeight: FontWeight.w700),
                      ),
                    ),
                    // 🧩15: Bouton rafraîchissement
                    IconButton(
                      onPressed: () {
                        ref.invalidate(subscriptionsProvider);
                        ref.invalidate(servicesProvider);
                      },
                      icon: const Icon(Icons.refresh_rounded, color: Colors.white),
                      tooltip: 'Rafraîchir',
                    ),
                  ],
                ),
                const SizedBox(height: 16),
                Container(
                  height: 44,
                  decoration: BoxDecoration(
                    color: Colors.white.withOpacity(0.15),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: TabBar(
                    controller: _tabController,
                    indicator: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(10),
                    ),
                    indicatorSize: TabBarIndicatorSize.tab,
                    indicatorPadding: const EdgeInsets.all(3),
                    labelColor: AppTheme.primaryBlue,
                    unselectedLabelColor: Colors.white.withOpacity(0.8),
                    labelStyle: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600),
                    unselectedLabelStyle: const TextStyle(fontSize: 13, fontWeight: FontWeight.w500),
                    dividerColor: Colors.transparent,
                    tabs: const [
                      Tab(text: 'Mes Abonnements'),
                      Tab(text: 'Services'),
                    ],
                  ),
                ),
                const SizedBox(height: 16),
              ],
            ),
          ),

          // Contenu des onglets
          Expanded(
            child: TabBarView(
              controller: _tabController,
              children: [
                _buildMySubscriptionsTab(),
                _buildAvailableServicesTab(),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMySubscriptionsTab() {
    final subscriptionsAsync = ref.watch(subscriptionsProvider);

    return RefreshIndicator(
      color: AppTheme.primaryBlue,
      onRefresh: () async {
        ref.invalidate(subscriptionsProvider);
      },
      child: subscriptionsAsync.when(
        data: (subscriptions) {
          if (subscriptions.isEmpty) {
            return Center(
              child: Padding(
                padding: const EdgeInsets.all(32),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Container(
                      width: 80, height: 80,
                      decoration: BoxDecoration(
                        color: AppTheme.primaryBlue.withOpacity(0.1),
                        shape: BoxShape.circle,
                      ),
                      child: const Icon(Icons.card_membership_outlined, size: 36, color: AppTheme.primaryBlue),
                    ),
                    const SizedBox(height: 20),
                    const Text('Aucun abonnement actif', style: TextStyle(fontSize: 17, fontWeight: FontWeight.w600, color: AppTheme.textPrimary)),
                    const SizedBox(height: 8),
                    const Text(
                      'Consultez les services disponibles pour vous abonner',
                      style: TextStyle(color: AppTheme.textLight, fontSize: 14),
                      textAlign: TextAlign.center,
                    ),
                  ],
                ),
              ),
            );
          }

          return ListView.builder(
            padding: const EdgeInsets.fromLTRB(20, 16, 20, 20),
            itemCount: subscriptions.length,
            itemBuilder: (context, index) {
              return Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: SubscriptionCard(subscription: subscriptions[index]),
              );
            },
          );
        },
        loading: () => const Center(child: CircularProgressIndicator(color: AppTheme.primaryBlue)),
        error: (error, stack) => Center(
          child: Padding(
            padding: const EdgeInsets.all(32),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Container(
                  width: 80, height: 80,
                  decoration: BoxDecoration(color: AppTheme.error.withOpacity(0.1), shape: BoxShape.circle),
                  child: const Icon(Icons.error_outline_rounded, size: 36, color: AppTheme.error),
                ),
                const SizedBox(height: 20),
                Text('Erreur: $error', textAlign: TextAlign.center, style: const TextStyle(color: AppTheme.textLight, fontSize: 13)),
                const SizedBox(height: 20),
                ElevatedButton(onPressed: () => ref.invalidate(subscriptionsProvider), child: const Text('Réessayer')),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildAvailableServicesTab() {
    final servicesAsync = ref.watch(servicesProvider);

    return RefreshIndicator(
      color: AppTheme.primaryBlue,
      onRefresh: () async {
        ref.invalidate(servicesProvider);
      },
      child: servicesAsync.when(
        data: (services) {
          if (services.isEmpty) {
            return Center(
              child: Padding(
                padding: const EdgeInsets.all(32),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Container(
                      width: 80, height: 80,
                      decoration: BoxDecoration(
                        color: AppTheme.primaryBlue.withOpacity(0.1),
                        shape: BoxShape.circle,
                      ),
                      child: const Icon(Icons.store_outlined, size: 36, color: AppTheme.primaryBlue),
                    ),
                    const SizedBox(height: 20),
                    const Text('Aucun service disponible', style: TextStyle(fontSize: 17, fontWeight: FontWeight.w600, color: AppTheme.textPrimary)),
                  ],
                ),
              ),
            );
          }

          return ListView.builder(
            padding: const EdgeInsets.fromLTRB(20, 16, 20, 20),
            itemCount: services.length,
            itemBuilder: (context, index) {
              return Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: ServiceCard(service: services[index]),
              );
            },
          );
        },
        loading: () => const Center(child: CircularProgressIndicator(color: AppTheme.primaryBlue)),
        error: (error, stack) => Center(
          child: Padding(
            padding: const EdgeInsets.all(32),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Container(
                  width: 80, height: 80,
                  decoration: BoxDecoration(color: AppTheme.error.withOpacity(0.1), shape: BoxShape.circle),
                  child: const Icon(Icons.error_outline_rounded, size: 36, color: AppTheme.error),
                ),
                const SizedBox(height: 20),
                Text('Erreur: $error', textAlign: TextAlign.center, style: const TextStyle(color: AppTheme.textLight, fontSize: 13)),
                const SizedBox(height: 20),
                ElevatedButton(onPressed: () => ref.invalidate(servicesProvider), child: const Text('Réessayer')),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

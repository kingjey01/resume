import 'package:flutter/material.dart';
import 'package:resume_plus_clean/models/abonnement.dart';
import 'package:intl/intl.dart';

class SubscriptionCard extends StatelessWidget {
  final Abonnement subscription;
  final VoidCallback? onTap;

  const SubscriptionCard({
    super.key,
    required this.subscription,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final dateFormat = DateFormat('dd/MM/yyyy');

    Color statusColor;
    IconData statusIcon;
    
    if (subscription.isActive) {
      statusColor = Colors.green;
      statusIcon = Icons.check_circle;
    } else if (DateTime.now().isBefore(subscription.dateDebut)) {
      statusColor = Colors.orange;
      statusIcon = Icons.schedule;
    } else {
      statusColor = Colors.red;
      statusIcon = Icons.cancel;
    }

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Header avec nom du service et statut
              Row(
                children: [
                  Expanded(
                    child: Text(
                      subscription.serviceNom,
                      style: theme.textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(
                      color: statusColor.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: statusColor.withOpacity(0.3)),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(statusIcon, size: 16, color: statusColor),
                        const SizedBox(width: 4),
                        Text(
                          subscription.statusText,
                          style: TextStyle(
                            color: statusColor,
                            fontWeight: FontWeight.w500,
                            fontSize: 12,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              
              if (subscription.description != null && subscription.description!.isNotEmpty) ...[
                const SizedBox(height: 8),
                Text(
                  subscription.description!,
                  style: theme.textTheme.bodyMedium?.copyWith(
                    color: theme.colorScheme.onSurface.withOpacity(0.7),
                  ),
                ),
              ],
              
              const SizedBox(height: 12),
              
              // Informations sur les dates et montant
              Row(
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Icon(Icons.calendar_today, 
                                 size: 16, 
                                 color: theme.colorScheme.primary),
                            const SizedBox(width: 4),
                            Text(
                              'Début: ${dateFormat.format(subscription.dateDebut)}',
                              style: theme.textTheme.bodySmall,
                            ),
                          ],
                        ),
                        const SizedBox(height: 4),
                        Row(
                          children: [
                            Icon(Icons.event_busy, 
                                 size: 16, 
                                 color: theme.colorScheme.primary),
                            const SizedBox(width: 4),
                            Text(
                              'Fin: ${dateFormat.format(subscription.dateFin)}',
                              style: theme.textTheme.bodySmall,
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.end,
                    children: [
                      Text(
                        subscription.formattedMontant,
                        style: theme.textTheme.titleMedium?.copyWith(
                          fontWeight: FontWeight.bold,
                          color: theme.colorScheme.primary,
                        ),
                      ),
                      Text(
                        subscription.devise,
                        style: theme.textTheme.bodySmall?.copyWith(
                          color: theme.colorScheme.onSurface.withOpacity(0.6),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
              
              // Barre de progression pour les abonnements actifs
              if (subscription.isActive) ...[
                const SizedBox(height: 12),
                _buildProgressBar(context),
              ],
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildProgressBar(BuildContext context) {
    final theme = Theme.of(context);
    final now = DateTime.now();
    final totalDuration = subscription.dateFin.difference(subscription.dateDebut).inDays;
    final elapsedDuration = now.difference(subscription.dateDebut).inDays;
    final progress = (elapsedDuration / totalDuration).clamp(0.0, 1.0);
    final remainingDays = subscription.dateFin.difference(now).inDays;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(
              'Progression',
              style: theme.textTheme.bodySmall?.copyWith(
                fontWeight: FontWeight.w500,
              ),
            ),
            Text(
              '$remainingDays jours restants',
              style: theme.textTheme.bodySmall?.copyWith(
                color: theme.colorScheme.onSurface.withOpacity(0.7),
              ),
            ),
          ],
        ),
        const SizedBox(height: 4),
        LinearProgressIndicator(
          value: progress,
          backgroundColor: theme.colorScheme.surfaceVariant,
          valueColor: AlwaysStoppedAnimation<Color>(
            remainingDays > 7 ? Colors.green : Colors.orange,
          ),
        ),
      ],
    );
  }
}

"""
Endpoints administrateur de statistiques de Résumé+.

Tous les endpoints :
- sont réservés aux administrateurs autorisés (staff/superuser Django
  ou profil groupe ADMIN) ;
- ne retournent que des données agrégées et anonymisées (aucun email,
  téléphone, nom, token ou contenu personnel) ;
- acceptent le filtre de période : today, last_7_days, last_30_days,
  this_week, this_month, last_month, custom (start_date/end_date).

Endpoints :
/api/admin/statistics/overview/
/api/admin/statistics/users/
/api/admin/statistics/summaries/
/api/admin/statistics/qcm/
/api/admin/statistics/transactions/
/api/admin/statistics/purchases/
/api/admin/statistics/subscriptions/
/api/admin/statistics/revenue/
/api/admin/statistics/export/excel/
/api/admin/statistics/export/csv/
"""
from django.http import HttpResponse
from django.views.generic import TemplateView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from . import services
from .exports import build_excel_response, build_csv_response
from .periods import PERIOD_CHOICES, iso, resolve_period
from .permissions import IsAdminStatisticsUser

TRANSACTION_TYPES = ('summary', 'service')


class _StatsBaseView(APIView):
    """Base commune : admin uniquement + résolution de période."""
    permission_classes = [IsAuthenticated, IsAdminStatisticsUser]

    def get_period(self, request):
        period_key = request.query_params.get('period', 'last_30_days')
        if period_key not in PERIOD_CHOICES:
            raise ValueError(f"Période inconnue: {period_key}")
        return resolve_period(
            period_key,
            start_date=request.query_params.get('start_date'),
            end_date=request.query_params.get('end_date'),
        )

    def get(self, request, *args, **kwargs):
        try:
            period = self.get_period(request)
            data = self.get_stats(period, request)
        except ValueError as exc:
            return Response({'error': str(exc)}, status=400)
        return Response({
            'period': {
                'key': period['key'],
                'label': period['label'],
                'start': iso(period['start']),
                'end': iso(period['end']),
            },
            'data': data,
        })

    def get_stats(self, period, request):
        raise NotImplementedError


class OverviewStatsView(_StatsBaseView):
    """Cartes principales du dashboard (tous domaines agrégés)."""

    def get_stats(self, period, request):
        return services.overview_stats(period['start'], period['end'])


class UsersStatsView(_StatsBaseView):
    """Utilisateurs : total, nouveaux et évolution par jour/semaine/mois."""

    def get_stats(self, period, request):
        return services.users_stats(period['start'], period['end'])


class SummariesStatsView(_StatsBaseView):
    """Résumés générés : total, fenêtres fixes et évolutions."""

    def get_stats(self, period, request):
        return services.summaries_stats(period['start'], period['end'])


class QcmStatsView(_StatsBaseView):
    """QCM générés : total, fenêtres fixes et évolutions (classiques + personnalisés)."""

    def get_stats(self, period, request):
        return services.qcm_stats(period['start'], period['end'])


class TransactionsStatsView(_StatsBaseView):
    """
    Transactions : lancées / réussies / échouées / annulées, taux de réussite,
    évolutions. Filtres : status (pending|completed|failed|refunded),
    type (summary|service).
    """

    def get_stats(self, period, request):
        status = request.query_params.get('status')
        if status and status not in services.TRANSACTION_STATUSES:
            raise ValueError(f"Statut inconnu: {status}")
        txn_type = request.query_params.get('type')
        if txn_type and txn_type not in TRANSACTION_TYPES:
            raise ValueError(f"Type inconnu: {txn_type}")
        return services.transactions_stats(
            period['start'], period['end'], status=status, txn_type=txn_type,
        )


class PurchasesStatsView(_StatsBaseView):
    """Achats de résumés : quantités et montants (transactions réussies uniquement)."""

    def get_stats(self, period, request):
        return services.purchases_stats(period['start'], period['end'])


class SubscriptionsStatsView(_StatsBaseView):
    """
    Abonnements : actifs / nouveaux / expirés / annulés et revenus.
    Filtre : service_id (type d'abonnement).
    """

    def get_stats(self, period, request):
        service_id = request.query_params.get('service_id')
        if service_id is not None:
            try:
                service_id = int(service_id)
            except (TypeError, ValueError):
                raise ValueError("service_id doit être un entier")
        return services.subscriptions_stats(period['start'], period['end'], service_id)


class RevenueStatsView(_StatsBaseView):
    """
    Revenus : achats de résumés, abonnements, total, évolution
    et comparaison avec la période précédente (transactions réussies uniquement).
    """

    def get_stats(self, period, request):
        service_id = request.query_params.get('service_id')
        if service_id is not None:
            try:
                service_id = int(service_id)
            except (TypeError, ValueError):
                raise ValueError("service_id doit être un entier")
        return services.revenue_stats(period['start'], period['end'], service_id)


# ══════════════════════════════════════════════════════════════════
# DASHBOARD ADMIN (page web)
# ══════════════════════════════════════════════════════════════════

class AdminDashboardView(TemplateView):
    """
    Page « Statistiques » du dashboard administrateur.
    La page elle-même ne contient aucune donnée : tout est chargé via les
    endpoints /api/admin/statistics/* après connexion (username + mot de passe
    d'un compte administrateur — staff/superuser ou groupe ADMIN).
    """
    template_name = 'admin_dashboard.html'


# ══════════════════════════════════════════════════════════════════
# EXPORTS (Excel / CSV) — statistiques agrégées, période + filtres respectés
# ══════════════════════════════════════════════════════════════════

CSV_SECTIONS = ('overview', 'users', 'summaries', 'qcm', 'transactions',
                'purchases', 'subscriptions', 'revenue')


class ExportExcelView(_StatsBaseView):
    """Export Excel (multi-feuilles) des statistiques agrégées de la période."""

    def get(self, request, *args, **kwargs):
        try:
            period = self.get_period(request)
        except ValueError as exc:
            return Response({'error': str(exc)}, status=400)
        response = build_excel_response(period, request)
        return response


class ExportCsvView(_StatsBaseView):
    """Export CSV de la section demandée (?section=...), période respectée."""

    def get(self, request, *args, **kwargs):
        try:
            period = self.get_period(request)
        except ValueError as exc:
            return Response({'error': str(exc)}, status=400)
        section = request.query_params.get('section', 'overview')
        if section not in CSV_SECTIONS:
            return Response({'error': f"Section inconnue: {section}"}, status=400)
        response = build_csv_response(period, request, section)
        return response

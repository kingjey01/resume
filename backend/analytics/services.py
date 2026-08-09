"""
Agrégations statistiques métier et financières de Résumé+.

Règles appliquées (voir prompt) :
- Réutilise les données existantes, aucun stockage supplémentaire.
- Les revenus proviennent UNIQUEMENT des transactions réellement payées
  (Purchase.status == 'completed') — jamais de Firebase ni d'estimation.
- Les statistiques sont agrégées et anonymisées : aucune donnée personnelle
  (email, téléphone, nom, token) n'est produite par ces fonctions.
- Pas de suivi des utilisateurs actifs, temps d'utilisation, sessions,
  contenu des résumés, QCM commencés/terminés.
- Agrégations ORM (Count/Sum/Trunc*) : pas de requêtes N+1.

Sources des données :
- Utilisateurs     → auth.User.date_joined
- Résumés          → courses.Summary.created_at
- QCM              → courses.Exercise + courses.UserPersonalizedExercise (created_at)
- Transactions     → payments.Purchase (pending=lancée, completed=réussie,
                     failed=échouée, refunded=annulée)
- Achats résumés   → Purchase.summary non nul
- Abonnements      → payments.Abonnement ; revenus = Purchase.service non nul
"""
from datetime import timedelta

from django.contrib.auth.models import User
from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncDay, TruncMonth, TruncWeek
from django.utils import timezone

from courses.models import Exercise, Summary, UserPersonalizedExercise
from payments.models import Abonnement, Purchase

from .periods import (
    _start_of_day,
    _start_of_month,
    _start_of_week,
    day_key,
    fixed_windows,
    month_key,
    week_key,
)

TRUNCS = {'day': TruncDay, 'week': TruncWeek, 'month': TruncMonth}
GRANS = {'day': 'daily', 'week': 'weekly', 'month': 'monthly'}

# Statuts de transaction (Purchase) → libellés métier
TRANSACTION_STATUSES = {
    'pending': 'lancée',
    'completed': 'réussie',
    'failed': 'échouée',
    'refunded': 'annulée',
}


# ══════════════════════════════════════════════════════════════════
# Helpers d'agrégation
# ══════════════════════════════════════════════════════════════════

def _in_window(qs, date_field, start, end):
    return qs.filter(**{f'{date_field}__gte': start, f'{date_field}__lt': end})


def _money(value):
    """Montant → float arrondi à 2 décimales (affichage monétaire)."""
    return round(float(value or 0), 2)


def _points(start, end, gran):
    """Liste des points de série (jour/lundi du lundi/1er du mois) sur [start, end)."""
    cur = start
    step = timedelta(days=1)
    if gran == 'week':
        cur = _start_of_week(start)
        step = timedelta(days=7)
    elif gran == 'month':
        cur = _start_of_month(start)
        step = timedelta(days=32)  # avance d'un mois par saut calendaire
    points, guard = [], 0
    while cur < end and guard < 3000:
        points.append(cur)
        cur += step
        if gran == 'month':
            cur = _start_of_month(cur)
        guard += 1
    return points


def _key_of(point, gran):
    if gran == 'day':
        return day_key(point)
    if gran == 'week':
        return week_key(point)
    return month_key(point)


def _series(qs, date_field, gran, start, end, sum_field=None):
    """
    Série temporelle agrégée sur [start, end) avec remplissage des trous à 0.
    - sum_field=None → compte (Count) ; sinon somme du champ (montants).
    Retourne [{date, count}] ou [{date, total}].
    """
    fn = TRUNCS[gran]
    filtered = _in_window(qs, date_field, start, end).annotate(period=fn(date_field))
    if sum_field is None:
        filtered = filtered.values('period').annotate(value=Count('id'))
    else:
        filtered = filtered.values('period').annotate(value=Sum(sum_field))
    rows = {_key_of(r['period'], gran): r['value'] for r in filtered}
    key = 'count' if sum_field is None else 'total'
    out = []
    for p in _points(start, end, gran):
        k = _key_of(p, gran)
        v = rows.get(k, 0)
        out.append({'date': k, key: _money(v) if sum_field else v})
    return out


def _all_series(qs, date_field, start, end, sum_field=None):
    """Les trois granularités (daily/weekly/monthly) en une fois."""
    return {GRANS[g]: _series(qs, date_field, g, start, end, sum_field) for g in GRANS}


def _fixed_counts(qs, date_field, windows=None):
    """Comptes fixes aujourd'hui / cette semaine / ce mois."""
    windows = windows or fixed_windows()
    out = {}
    for label, (w_start, w_end) in windows.items():
        out[label] = _in_window(qs, date_field, w_start, w_end).count()
    return out


def _amount_in(qs, start, end):
    return _money(qs.filter(created_at__gte=start, created_at__lt=end)
                  .aggregate(total=Sum('amount'))['total'])


def _fixed_amounts(qs, windows=None):
    """Montants fixes aujourd'hui / cette semaine / ce mois."""
    windows = windows or fixed_windows()
    out = {}
    for label, (w_start, w_end) in windows.items():
        out[label] = _money(qs.filter(created_at__gte=w_start, created_at__lt=w_end)
                            .aggregate(total=Sum('amount'))['total'])
    return out


# ══════════════════════════════════════════════════════════════════
# 1. UTILISATEURS
# ══════════════════════════════════════════════════════════════════

def users_stats(start, end):
    base = User.objects.all()
    return {
        'total': base.count(),  # nombre total d'utilisateurs (tous temps)
        'new_in_period': _in_window(base, 'date_joined', start, end).count(),
        **_all_series(base, 'date_joined', start, end),
    }


# ══════════════════════════════════════════════════════════════════
# 2. RÉSUMÉS
# ══════════════════════════════════════════════════════════════════

def summaries_stats(start, end):
    base = Summary.objects.all()
    return {
        'total': base.count(),  # nombre total de résumés générés (tous temps)
        'in_period': _in_window(base, 'created_at', start, end).count(),
        **_fixed_counts(base, 'created_at'),
        **_all_series(base, 'created_at', start, end),
    }


# ══════════════════════════════════════════════════════════════════
# 3. QCM
# ══════════════════════════════════════════════════════════════════

def qcm_stats(start, end):
    classic = Exercise.objects.all()
    personalized = UserPersonalizedExercise.objects.all()

    classic_total = classic.count()
    personalized_total = personalized.count()

    # Série combinée (classiques + personnalisés) par granularité.
    combined = {}
    for g in GRANS:
        c_rows = {r['date']: r['count'] for r in _series(classic, 'created_at', g, start, end)}
        p_rows = {r['date']: r['count'] for r in _series(personalized, 'created_at', g, start, end)}
        all_dates = sorted(set(c_rows) | set(p_rows))
        combined[GRANS[g]] = [{'date': d, 'count': c_rows.get(d, 0) + p_rows.get(d, 0)}
                              for d in all_dates]

    # Fenêtres fixes combinées (aujourd'hui / cette semaine / ce mois).
    combined_fixed = {}
    for label, (w_start, w_end) in fixed_windows().items():
        combined_fixed[label] = (
            classic.filter(created_at__gte=w_start, created_at__lt=w_end).count()
            + personalized.filter(created_at__gte=w_start, created_at__lt=w_end).count()
        )

    return {
        'total': classic_total + personalized_total,  # total QCM générés (tous temps)
        'classic_total': classic_total,
        'personalized_total': personalized_total,
        'in_period': (_in_window(classic, 'created_at', start, end).count()
                      + _in_window(personalized, 'created_at', start, end).count()),
        **combined_fixed,
        **combined,
    }


# ══════════════════════════════════════════════════════════════════
# 4. TRANSACTIONS
# ══════════════════════════════════════════════════════════════════

def transactions_stats(start, end, status=None, txn_type=None):
    base = Purchase.objects.all()
    if txn_type == 'summary':
        base = base.filter(summary__isnull=False)
    elif txn_type == 'service':
        base = base.filter(service__isnull=False)

    window = _in_window(base, 'created_at', start, end)

    # Comptes par statut sur la fenêtre complète (les sous-comptes reflètent
    # toujours les 4 statuts, même si un filtre status est appliqué — le taux
    # de réussite reste ainsi représentatif).
    by_status = {s: window.filter(status=s).count() for s in TRANSACTION_STATUSES}

    # Le filtre status s'applique au total et aux séries.
    filtered = window.filter(status=status) if status else window
    total = filtered.count()

    window_total = window.count()
    success_rate = round(by_status['completed'] / window_total * 100, 1) if window_total else 0.0

    return {
        'total': total,
        'by_status': by_status,
        'success_rate': success_rate,
        **_all_series(filtered, 'created_at', start, end),
        'by_type': {
            'summary': _type_breakdown(base, 'summary', start, end),
            'service': _type_breakdown(base, 'service', start, end),
        },
    }


def _type_breakdown(base, kind, start, end):
    """Sous-ensemble summary|service : comptes + montants des transactions réussies."""
    if kind == 'summary':
        qs = base.filter(summary__isnull=False)
    else:
        qs = base.filter(service__isnull=False)
    window = _in_window(qs, 'created_at', start, end)
    completed = window.filter(status='completed')
    amount = completed.aggregate(total=Sum('amount'))['total']
    return {
        'count': window.count(),
        'completed': completed.count(),
        'amount_completed': _money(amount),
    }


# ══════════════════════════════════════════════════════════════════
# 5. ACHATS DE RÉSUMÉS
# ══════════════════════════════════════════════════════════════════

def purchases_stats(start, end):
    base = Purchase.objects.filter(summary__isnull=False)
    completed = base.filter(status='completed')

    in_period_completed = _in_window(completed, 'created_at', start, end)
    in_period_total = _in_window(base, 'created_at', start, end)

    amount_all_time = completed.aggregate(total=Sum('amount'))['total']
    amount_period = in_period_completed.aggregate(total=Sum('amount'))['total']

    count_period = in_period_completed.count()
    return {
        'total': completed.count(),  # nombre total de résumés achetés (réussis)
        'pending_in_period': _in_window(base, 'created_at', start, end)
                             .filter(status='pending').count(),
        'in_period': count_period,
        **_fixed_counts(completed, 'created_at'),
        **_all_series(completed, 'created_at', start, end),
        'amount_total': _money(amount_all_time),   # montant total généré (réussi)
        'amount_in_period': _money(amount_period),
        **_fixed_amounts(completed),
        'amount_series': _all_series(completed, 'created_at', start, end, sum_field='amount'),
        'avg_basket': _money(amount_period / count_period) if count_period else 0.0,
        'avg_basket_all_time': _money(amount_all_time / completed.count()) if completed.count() else 0.0,
    }


# ══════════════════════════════════════════════════════════════════
# 6. ABONNEMENTS
# ══════════════════════════════════════════════════════════════════

def subscriptions_stats(start, end, service_id=None):
    base = Abonnement.objects.all()
    if service_id:
        base = base.filter(service_id=service_id)

    now = timezone.now()

    # Revenus des abonnements = paiements réussis liés à un service.
    revenue_qs = Purchase.objects.filter(service__isnull=False, status='completed')
    if service_id:
        revenue_qs = revenue_qs.filter(service_id=service_id)

    # Abonnements ayant expiré DANS la période : statut expiré + date_fin dans la fenêtre.
    expired_in_period = base.filter(status='expired', date_fin__gte=start, date_fin__lt=end).count()
    # Abonnements annulés créés dans la période (pas de date d'annulation tracée :
    # on compte les créés avec statut 'cancelled' pendant la fenêtre).
    cancelled_new_in_period = base.filter(status='cancelled', created_at__gte=start, created_at__lt=end).count()

    return {
        'active': base.filter(status='active', date_fin__gte=now).count(),
        'new_in_period': _in_window(base, 'created_at', start, end).count(),
        # Non traçable avec les modèles actuels : aucun champ ne distingue un
        # renouvellement d'un nouvel achat (l'Abonnement actif existant n'est
        # pas recréé sur paiement). Voir payments/flexpay_integration.py.
        'renewed': None,
        'renewed_not_trackable': True,
        'expired': base.filter(status='expired').count(),
        'expired_in_period': expired_in_period,
        'cancelled': base.filter(status='cancelled').count(),
        'cancelled_new_in_period': cancelled_new_in_period,
        'total': base.count(),  # nombre total d'abonnements (tous temps)
        **_all_series(base, 'created_at', start, end),
        'revenue': {
            'amount_total': _money(revenue_qs.aggregate(total=Sum('amount'))['total']),
            'amount_in_period': _amount_in(revenue_qs, start, end),
            **_fixed_amounts(revenue_qs),
            'amount_series': _all_series(revenue_qs, 'created_at', start, end, sum_field='amount'),
        },
    }


# ══════════════════════════════════════════════════════════════════
# 7. REVENUS
# ══════════════════════════════════════════════════════════════════

def revenue_stats(start, end, service_id=None):
    purchases_qs = Purchase.objects.filter(summary__isnull=False, status='completed')
    subscriptions_qs = Purchase.objects.filter(service__isnull=False, status='completed')
    if service_id:
        subscriptions_qs = subscriptions_qs.filter(service_id=service_id)

    purchases_amount = purchases_qs.aggregate(total=Sum('amount'))['total']
    subscriptions_amount = subscriptions_qs.aggregate(total=Sum('amount'))['total']

    purchases_period = _amount_in(purchases_qs, start, end)
    subscriptions_period = _amount_in(subscriptions_qs, start, end)

    previous_start, previous_end = start - (end - start), start
    previous_total = _amount_in(purchases_qs, previous_start, previous_end) + \
        _amount_in(subscriptions_qs, previous_start, previous_end)
    current_total = purchases_period + subscriptions_period
    evolution = (round((current_total - previous_total) / previous_total * 100, 1)
                 if previous_total else None)

    def _merge_amount_series():
        p = {r['date']: r['total'] for r in
             _series(purchases_qs, 'created_at', 'day', start, end, sum_field='amount')}
        s = {r['date']: r['total'] for r in
             _series(subscriptions_qs, 'created_at', 'day', start, end, sum_field='amount')}
        return [{'date': d, 'purchases': p.get(d, 0), 'subscriptions': s.get(d, 0),
                 'total': round(p.get(d, 0) + s.get(d, 0), 2)}
                for d in sorted(set(p) | set(s))]

    return {
        'purchases': {
            'quantity': purchases_qs.count(),  # résumés achetés (réussis, tous temps)
            'quantity_in_period': _in_window(purchases_qs, 'created_at', start, end).count(),
            'amount_total': _money(purchases_amount),
            'amount_in_period': purchases_period,
            **_fixed_amounts(purchases_qs),
            'amount_series': _all_series(purchases_qs, 'created_at', start, end, sum_field='amount'),
        },
        'subscriptions': {
            'quantity': subscriptions_qs.count(),
            'quantity_in_period': _in_window(subscriptions_qs, 'created_at', start, end).count(),
            'amount_total': _money(subscriptions_amount),
            'amount_in_period': subscriptions_period,
            **_fixed_amounts(subscriptions_qs),
            'amount_series': _all_series(subscriptions_qs, 'created_at', start, end, sum_field='amount'),
        },
        'total': {
            'amount_total': _money((purchases_amount or 0) + (subscriptions_amount or 0)),
            'amount_in_period': current_total,
            # Montants fixes (aujourd'hui / cette semaine / ce mois) sur
            # l'ensemble des paiements réussis (achats de résumés + abonnements).
            **_fixed_amounts(Purchase.objects.filter(
                status='completed',
            ).filter(Q(summary__isnull=False) | Q(service__isnull=False))),
            'daily': _merge_amount_series(),
        },
        'previous_period': {
            'start': previous_start.isoformat(),
            'end': previous_end.isoformat(),
            'amount_total': _money(previous_total),
        },
        'evolution_percent': evolution,
    }


# ══════════════════════════════════════════════════════════════════
# 9. VUE GÉNÉRALE (overview — cartes principales du dashboard)
# ══════════════════════════════════════════════════════════════════

def overview_stats(start, end):
    now = timezone.now()
    purchases_qs = Purchase.objects.filter(status='completed')
    revenue_total = purchases_qs.aggregate(total=Sum('amount'))['total']
    return {
        'users': {
            'total': User.objects.count(),
            'new_in_period': _in_window(User.objects.all(), 'date_joined', start, end).count(),
        },
        'summaries': {
            'total': Summary.objects.count(),
            'in_period': _in_window(Summary.objects.all(), 'created_at', start, end).count(),
        },
        'qcm': {
            'total': Exercise.objects.count() + UserPersonalizedExercise.objects.count(),
            'in_period': (_in_window(Exercise.objects.all(), 'created_at', start, end).count()
                          + _in_window(UserPersonalizedExercise.objects.all(),
                                       'created_at', start, end).count()),
        },
        'transactions': {
            'total': _in_window(Purchase.objects.all(), 'created_at', start, end).count(),
            'launched': _in_window(Purchase.objects.filter(status='pending'),
                                   'created_at', start, end).count(),
            'succeeded': _in_window(Purchase.objects.filter(status='completed'),
                                    'created_at', start, end).count(),
            'failed': _in_window(Purchase.objects.filter(status='failed'),
                                 'created_at', start, end).count(),
            'cancelled': _in_window(Purchase.objects.filter(status='refunded'),
                                    'created_at', start, end).count(),
        },
        'purchases': {
            'total': purchases_qs.filter(summary__isnull=False).count(),
            'in_period': _in_window(purchases_qs.filter(summary__isnull=False),
                                    'created_at', start, end).count(),
        },
        'subscriptions': {
            'active': Abonnement.objects.filter(status='active', date_fin__gte=now).count(),
            'new_in_period': _in_window(Abonnement.objects.all(), 'created_at',
                                        start, end).count(),
        },
        'revenue': {
            'total': _money(revenue_total),
            'in_period': _money(purchases_qs.filter(
                created_at__gte=start, created_at__lt=end).aggregate(total=Sum('amount'))['total']),
        },
    }

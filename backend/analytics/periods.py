"""
Résolution des fenêtres de période pour les statistiques.

Toutes les bornes sont calculées dans le timezone configuré de Django
(Africa/Kinshasa). Les fenêtres sont des demi-ouvertes [start, end) :
start est inclus, end est exclus. Pour 'custom', end est inclusif
(23:59:59.999999 de la date de fin).
"""
from datetime import datetime, timedelta

from django.utils import timezone

# Périodes acceptées par l'API (clé → libellé d'affichage)
PERIOD_CHOICES = {
    'today': "Aujourd'hui",
    'last_7_days': '7 derniers jours',
    'last_30_days': '30 derniers jours',
    'this_week': 'Cette semaine',
    'this_month': 'Ce mois',
    'last_month': 'Mois précédent',
    'custom': 'Période personnalisée',
}

# Fenêtres fixes toujours disponibles (aujourd'hui, cette semaine, ce mois)
# utilisées pour les sous-métriques "aujourd'hui / cette semaine / ce mois".


def local_now():
    """Maintenant dans le timezone local (Africa/Kinshasa)."""
    return timezone.localtime(timezone.now())


def _start_of_day(dt):
    return dt.replace(hour=0, minute=0, second=0, microsecond=0)


def _start_of_week(dt):
    """Lundi de la semaine du datetime donné (Python: weekday() == 0 → lundi)."""
    return _start_of_day(dt) - timedelta(days=dt.weekday())


def _start_of_month(dt):
    return dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def fixed_windows():
    """
    Fenêtres fixes "aujourd'hui", "cette semaine", "ce mois" (hors filtre global).
    Retourne { 'today': (start, end), 'this_week': (start, end), 'this_month': (start, end) }
    """
    now = local_now()
    today_start = _start_of_day(now)
    week_start = _start_of_week(now)
    month_start = _start_of_month(now)
    return {
        'today': (today_start, today_start + timedelta(days=1)),
        'this_week': (week_start, week_start + timedelta(days=7)),
        'this_month': (month_start, _start_of_month(now + timedelta(days=32))),
    }


def _month_bounds(month_start):
    """[1er du mois, 1er du mois suivant)."""
    return month_start, _start_of_month(month_start + timedelta(days=32))


def resolve_period(period_key='last_30_days', start_date=None, end_date=None):
    """
    Résout une période en bornes datetimes aware.

    Retourne un dict :
      key, label, start, end, previous_start, previous_end
    start inclus, end exclus (pour 'custom' : end inclusif, arrondi à la ms).
    """
    now = local_now()

    if period_key == 'today':
        start = _start_of_day(now)
        end = start + timedelta(days=1)
    elif period_key == 'last_7_days':
        start = _start_of_day(now) - timedelta(days=6)
        end = _start_of_day(now) + timedelta(days=1)
    elif period_key == 'last_30_days':
        start = _start_of_day(now) - timedelta(days=29)
        end = _start_of_day(now) + timedelta(days=1)
    elif period_key == 'this_week':
        start = _start_of_week(now)
        end = start + timedelta(days=7)
    elif period_key == 'this_month':
        start = _start_of_month(now)
        end = _start_of_month(now + timedelta(days=32))
    elif period_key == 'last_month':
        start = _start_of_month(_start_of_month(now) - timedelta(days=1))
        end, _ = _month_bounds(start)
    elif period_key == 'custom':
        # Période personnalisée : dates au format YYYY-MM-DD (timezone local).
        start = _parse_custom_date(start_date, default=_start_of_day(now))
        end_raw = _parse_custom_date(end_date, default=start)
        end = end_raw.replace(hour=23, minute=59, second=59, microsecond=999999)
        previous_start = None
        previous_end = None
    else:
        raise ValueError(f"Période inconnue: {period_key}")

    # Fenêtre précédente (comparaison avec la période précédente).
    if period_key != 'custom':
        span = end - start
        previous_start = start - span
        previous_end = start
    else:
        previous_start, previous_end = None, None

    return {
        'key': period_key,
        'label': PERIOD_CHOICES.get(period_key, period_key),
        'start': start,
        'end': end,
        'previous_start': previous_start,
        'previous_end': previous_end,
    }


def _parse_custom_date(value, default):
    """Parse une date 'YYYY-MM-DD' en datetime aware (timezone local)."""
    if not value:
        return default
    try:
        return timezone.make_aware(datetime.strptime(str(value), '%Y-%m-%d'))
    except (ValueError, TypeError):
        return default


def iso(dt):
    """Format ISO 8601 avec offset pour une réponse JSON."""
    return dt.isoformat() if dt else None


def day_key(dt):
    """Clé 'YYYY-MM-DD' en timezone local (pour les séries)."""
    return timezone.localtime(dt).strftime('%Y-%m-%d')


def week_key(dt):
    """Clé 'YYYY-MM-DD' du lundi de la semaine en timezone local."""
    return day_key(_start_of_week(timezone.localtime(dt)))


def month_key(dt):
    """Clé 'YYYY-MM' en timezone local."""
    return timezone.localtime(dt).strftime('%Y-%m')

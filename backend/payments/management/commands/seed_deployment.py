"""Seed de déploiement — données de référence et plans d'abonnement.

Contrairement à `seed_production` (qui crée des utilisateurs de test et des
résumés d'exemple), cette commande est **sûre en production** :

- aucun utilisateur n'est créé ;
- aucune donnée n'est supprimée ;
- la commande est idempotente (`get_or_create`) ;
- les identifiants Apple ne sont jamais inventés : ils viennent des options ou
  de l'environnement, et restent vides sinon.

Usage :

    python manage.py seed_deployment \
        --qcm-product-id com.kingjey01.resumeplus.qcm.monthly \
        --summary-product com.kingjey01.resumeplus.summary.300=300 \
        --summary-product com.kingjey01.resumeplus.summary.500=500

Variables d'environnement lues (si l'option n'est pas fournie) :
    APPLE_QCM_PRODUCT_ID
"""

import os
from decimal import Decimal, InvalidOperation

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from courses.models import Filiere, Promotion, Universite
from payments.models import Service


class Command(BaseCommand):
    help = (
        'Préremplit les référentiels (promotions, filières, université) et '
        'les services d’abonnement, sans créer d’utilisateur ni de données de test.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-reference',
            action='store_true',
            help='Ne pas créer promotions/filières/université.',
        )
        parser.add_argument(
            '--universite',
            default='Université de Kinshasa',
            help='Nom de l’université à créer (défaut : Université de Kinshasa).',
        )
        parser.add_argument(
            '--filiere',
            action='append',
            dest='filieres',
            help='Nom d’une filière à créer (répétable). Défaut : liste intégrée.',
        )
        parser.add_argument(
            '--promotion',
            action='append',
            dest='promotions',
            help='Nom d’une promotion à créer (répétable). Défaut : L1..M2.',
        )
        parser.add_argument(
            '--qcm-product-id',
            default=os.environ.get('APPLE_QCM_PRODUCT_ID', ''),
            help='Identifiant du produit d’abonnement Apple QCM (sinon variable APPLE_QCM_PRODUCT_ID).',
        )
        parser.add_argument(
            '--qcm-nom',
            default='Abonnement QCM',
            help='Nom du service QCM (défaut : Abonnement QCM).',
        )
        parser.add_argument(
            '--qcm-price',
            default='5000',
            help='Prix du service QCM en CDF (défaut : 5000).',
        )
        parser.add_argument(
            '--qcm-currency',
            default='CDF',
            help='Devise du service QCM (défaut : CDF).',
        )
        parser.add_argument(
            '--qcm-duration-months',
            type=int,
            default=1,
            help='Durée du service QCM en mois (défaut : 1).',
        )
        parser.add_argument(
            '--qcm-quota',
            type=int,
            default=10,
            help='Générations complètes de QCM par période (0 = illimité).',
        )
        parser.add_argument(
            '--qcm-daily-cap',
            type=int,
            default=2,
            help='Générations complètes par jour (0 = dérivé du quota).',
        )
        parser.add_argument(
            '--qcm-apple-price',
            default='',
            help='Prix Apple déclaré du produit QCM (ex. 0.99), sans conversion automatique.',
        )
        parser.add_argument(
            '--qcm-apple-currency',
            default='',
            help='Devise du prix Apple (ex. USD).',
        )
        parser.add_argument(
            '--with-legacy-plans',
            action='store_true',
            help='Créer aussi les anciens plans Basic / Premium / VIP.',
        )
        parser.add_argument(
            '--update-existing',
            action='store_true',
            help='Mettre à jour les services existants (prix, quotas, produit Apple).',
        )
        parser.add_argument(
            '--summary-product',
            action='append',
            dest='summary_products',
            default=[],
            metavar='PRODUCT_ID=PRIX',
            help='Produit consommable de résumé et son prix CDF (répétable). '
                 'Sert uniquement à afficher APPLE_SUMMARY_PRODUCTS pour le .env.',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Afficher ce qui serait fait sans écrire en base.',
        )

    def handle(self, *args, **options):
        self.dry_run = options['dry_run']
        self.update_existing = options['update_existing']

        if not options['skip_reference']:
            self._seed_reference(
                universite=options['universite'],
                filieres=options['filieres'],
                promotions=options['promotions'],
            )

        self._seed_services(options)

        summary_products = self._parse_summary_products(
            options['summary_products']
        )
        if summary_products:
            import json

            self.stdout.write('')
            self.stdout.write(self.style.WARNING(
                'À ajouter dans le .env du serveur (ne pas commiter) :'
            ))
            self.stdout.write(
                'APPLE_SUMMARY_PRODUCTS='
                + json.dumps(
                    {pid: str(price) for pid, price in summary_products.items()},
                    separators=(',', ':'),
                )
            )
        elif options['summary_products']:
            raise CommandError('Option --summary-product invalide.')

        if self.dry_run:
            self.stdout.write(self.style.WARNING(
                'Mode --dry-run : aucune écriture effectuée.'
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                'Seed de déploiement terminé. Aucun utilisateur créé.'
            ))

    # ─── Référentiels ─────────────────────────────────────────────────────

    def _seed_reference(self, *, universite, filieres, promotions):
        annee = timezone.now().year
        filieres = filieres or [
            'Informatique', 'Droit', 'Médecine',
            'Économie', 'Lettres', 'Sciences',
        ]
        promotions = promotions or ['L1', 'L2', 'L3', 'M1', 'M2']

        self.stdout.write('Référentiels :')

        promotions_obj = []
        for nom in promotions:
            obj, created = self._get_or_create(
                Promotion, {'nom': nom}, {'annee': annee}, label=f'Promotion {nom}'
            )
            promotions_obj.append(obj)

        filieres_obj = []
        for nom in filieres:
            obj, created = self._get_or_create(
                Filiere, {'nom': nom}, {'description': f'Filière {nom}'},
                label=f'Filière {nom}',
            )
            filieres_obj.append(obj)
            if not self.dry_run and promotions_obj:
                obj.promotions.add(*promotions_obj)

        universite_obj, _ = self._get_or_create(
            Universite, {'nom': universite}, {}, label=f'Université {universite}'
        )
        if not self.dry_run and filieres_obj:
            universite_obj.filieres.add(*filieres_obj)

    # ─── Services ─────────────────────────────────────────────────────────

    def _seed_services(self, options):
        self.stdout.write('')
        self.stdout.write('Services d’abonnement :')

        try:
            qcm_price = Decimal(str(options['qcm_price']))
        except (InvalidOperation, TypeError):
            raise CommandError('--qcm-price invalide.')

        if qcm_price < 0:
            raise CommandError('--qcm-price doit être positif ou nul.')

        qcm_defaults = {
            'description': (
                'Générations de QCM personnalisés : chaque pack couvre les '
                '3 niveaux (Facile, Moyen, Difficile) d’un résumé.'
            ),
            'type': 'basic',
            'price': qcm_price,
            'currency': options['qcm_currency'],
            'duree_mois': options['qcm_duration_months'],
            'features': [
                'QCM personnalisés par résumé',
                '3 niveaux de difficulté par pack',
                'Historique des tentatives',
            ],
            'is_active': True,
            'quota_qcm_mensuel': options['qcm_quota'],
            'plafond_qcm_journalier': options['qcm_daily_cap'],
        }
        if options['qcm_product_id']:
            qcm_defaults['apple_product_id'] = options['qcm_product_id']

        if options['qcm_apple_price']:
            if not options['qcm_apple_currency']:
                raise CommandError(
                    '--qcm-apple-currency est requis avec --qcm-apple-price.'
                )
            try:
                qcm_defaults['apple_price'] = Decimal(
                    str(options['qcm_apple_price'])
                )
            except (InvalidOperation, TypeError):
                raise CommandError('--qcm-apple-price invalide.')
            qcm_defaults['apple_currency'] = (
                options['qcm_apple_currency'].strip().upper()
            )

        self._ensure_service(options['qcm_nom'], qcm_defaults)

        if options['with_legacy_plans']:
            legacy = [
                ('Abonnement Basic', 'basic', Decimal('5000.00'), 1,
                 ['5 résumés par mois', 'Support email', 'Accès aux résumés gratuits']),
                ('Abonnement Premium', 'premium', Decimal('15000.00'), 1,
                 ['Résumés illimités', 'Support prioritaire', 'Accès aux PDF', 'Lecture audio']),
                ('Abonnement VIP', 'vip', Decimal('35000.00'), 3,
                 ['Résumés illimités', 'Support 24/7', 'PDF', 'Audio', 'Hors ligne', 'Partage']),
            ]
            for nom, type_, prix, duree, features in legacy:
                self._ensure_service(nom, {
                    'description': f'Plan {nom}',
                    'type': type_,
                    'price': prix,
                    'currency': 'CDF',
                    'duree_mois': duree,
                    'features': features,
                    'is_active': True,
                })

    def _ensure_service(self, nom, defaults):
        existant = Service.objects.filter(nom=nom).first()

        if existant is None:
            if self.dry_run:
                self.stdout.write(f'  - {nom} : serait créé')
            else:
                Service.objects.create(nom=nom, **defaults)
                self.stdout.write(self.style.SUCCESS(f'  - {nom} : créé'))
            return

        if not self.update_existing:
            self.stdout.write(f'  - {nom} : existant (inchangé)')
            return

        # Ne jamais écraser un identifiant Apple existant par une valeur vide.
        for champ, valeur in defaults.items():
            if champ == 'apple_product_id' and not valeur:
                continue
            setattr(existant, champ, valeur)

        if self.dry_run:
            self.stdout.write(f'  - {nom} : serait mis à jour')
        else:
            existant.save()
            self.stdout.write(self.style.SUCCESS(f'  - {nom} : mis à jour'))

    # ─── Utilitaires ──────────────────────────────────────────────────────

    def _get_or_create(self, model, lookup, defaults, *, label):
        obj = model.objects.filter(**lookup).first()
        if obj is not None:
            self.stdout.write(f'  - {label} : existant')
            return obj, False
        if self.dry_run:
            self.stdout.write(f'  - {label} : serait créé')
            # Objet non sauvegardé, utilisé seulement pour l’affichage.
            return model(**{**lookup, **defaults}), True
        obj, created = model.objects.get_or_create(
            defaults=defaults, **lookup
        )
        self.stdout.write(self.style.SUCCESS(
            f'  - {label} : {"créé" if created else "existant"}'
        ))
        return obj, created

    def _parse_summary_products(self, raw_values):
        produits = {}
        for raw in raw_values:
            if '=' not in raw:
                raise CommandError(
                    f'--summary-product attend PRODUCT_ID=PRIX, reçu : {raw}'
                )
            product_id, prix = raw.split('=', 1)
            product_id = product_id.strip()
            if not product_id:
                raise CommandError('Identifiant produit vide.')
            try:
                valeur = Decimal(prix.strip())
            except (InvalidOperation, TypeError):
                raise CommandError(f'Prix invalide pour {product_id}.')
            if valeur <= 0:
                raise CommandError(f'Le prix de {product_id} doit être > 0.')
            produits[product_id] = valeur
        return produits

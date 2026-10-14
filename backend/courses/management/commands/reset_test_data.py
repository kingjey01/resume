"""Remise à zéro des données de test, en conservant les administrateurs.

    python manage.py reset_test_data --dry-run \
        --base-attendue resumecours --sauvegarde /root/sauvegardes/resume_2026-10-14.sql

POURQUOI CETTE COMMANDE EXISTE : l'application est en phase de tests sur un
serveur en ligne, et il faut pouvoir repartir d'une base propre sans perdre les
comptes d'administration ni les permissions Django.

CE QU'ELLE FAIT
  • vide les données métier (cours, résumés, sessions audio, exercices, achats,
    paiements, notifications, jetons, profils…) ;
  • supprime les comptes qui ne sont PAS administrateurs, avec leurs données
    liées (les suppressions en cascade s'en chargent) ;
  • conserve les administrateurs, leurs mots de passe, leurs profils et leurs
    permissions, ainsi que Group / Permission / ContentType ;
  • ne touche NI aux tables, NI aux colonnes, NI aux migrations.

CE QU'ELLE NE FAIT JAMAIS SANS AUTORISATION EXPLICITE
  • écrire quoi que ce soit en mode `--dry-run` ;
  • s'exécuter sans `--base-attendue` correspondant à la base réellement
    connectée, ni sans `--sauvegarde` récente et non vide ;
  • supprimer les fichiers audio sur le disque sans `--supprimer-fichiers`
    (ils sont alors seulement comptés et signalés).

GARDE-FOU SUR LES ADMINISTRATEURS : un compte est reconnu administrateur s'il
est `is_superuser`, OU si son profil porte le groupe du projet `ADMIN`
(`Profile.is_admin`). Un compte `is_staff` qui n'est NI l'un NI l'autre est
AMBIGU : la commande s'arrête et le signale, plutôt que de trancher à votre
place. `--accepter-ambigus` permet de passer outre en connaissance de cause.
"""

import os
import time

from django.apps import apps
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, models, transaction


# Applications dont le contenu est de la DONNÉE MÉTIER : vidées intégralement.
APPLICATIONS_METIER = [
    'courses', 'payments', 'security', 'notifications', 'analytics', 'users',
]

# Modèles traités À PART, jamais vidés par la boucle générique :
#   • auth.User    — on ne supprime que les non-administrateurs ;
#   • users.Profile — il suit son utilisateur, et celui d'un administrateur
#     doit survivre.
MODELES_ECARTES = {('auth', 'user'), ('users', 'profile')}


class Command(BaseCommand):
    help = (
        "Vide les données métier et supprime les comptes non administrateurs, "
        "en conservant les administrateurs et les permissions Django. "
        "Voir --help pour les garde-fous (base attendue, sauvegarde, dry-run)."
    )

    # ------------------------------------------------------------------ args

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run', action='store_true',
            help="Bilan complet, AUCUNE écriture. À lancer en premier.",
        )
        parser.add_argument(
            '--base-attendue', metavar='NOM',
            help="Nom de la base sur laquelle l'opération est autorisée. "
                 "Toute autre base est refusée. Obligatoire hors --dry-run.",
        )
        parser.add_argument(
            '--sauvegarde', metavar='FICHIER',
            help="Dump de la base, réalisé juste avant. Il doit exister, être "
                 "non vide et récent. Obligatoire hors --dry-run.",
        )
        parser.add_argument(
            '--age-max-heures', type=int, default=24, metavar='H',
            help="Âge maximal accepté pour la sauvegarde (défaut : 24 h).",
        )
        parser.add_argument(
            '--confirmer', action='store_true',
            help="Ne pas demander la confirmation interactive. À réserver aux "
                 "exécutions scriptées, une fois le --dry-run relu.",
        )
        parser.add_argument(
            '--accepter-ambigus', action='store_true',
            help="Autoriser l'exécution malgré des comptes `is_staff` dont le "
                 "statut d'administrateur est ambigu (ils seraient supprimés).",
        )
        parser.add_argument(
            '--supprimer-fichiers', action='store_true',
            help="Supprimer aussi les fichiers audio/images du disque. Par "
                 "défaut ils sont seulement comptés et signalés.",
        )

    # ------------------------------------------------------------- exécution

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        self.stdout.write(self.style.MIGRATE_HEADING(
            "\n=== Remise à zéro des données de test ==="))

        # 1. Sur QUELLE base suis-je en train d'opérer ? C'est la question qui
        #    évite de vider une base de production par erreur d'environnement.
        self._verifier_base(options)

        # 2. Qui est administrateur ? Et le statut de quelqu'un est-il ambigu ?
        admins, ambigus = self._administrateurs()
        self._verifier_ambigus(ambigus, options)

        # 3. Ce qui sera supprimé, et ce qui restera.
        modeles = self._modeles_a_vider()
        fichiers = self._fichiers_associes(modeles)

        self._afficher_bilan(admins, modeles, fichiers, dry_run)

        if dry_run:
            self.stdout.write(self.style.WARNING(
                "\nMODE SIMULATION — aucune donnée n'a été modifiée.\n"
                "Relisez ce bilan, puis relancez sans --dry-run.\n"))
            return

        # 4. Une sauvegarde fraîche et exploitable est la condition pour écrire.
        self._verifier_sauvegarde(options)

        # 5. Confirmation explicite.
        self._confirmer(options)

        # 6. Tout ou rien : une erreur en cours de route laisse la base intacte.
        with transaction.atomic():
            supprimes = self._vider(modeles, admins)

        if options['supprimer_fichiers']:
            self._supprimer_fichiers(fichiers)
        elif fichiers:
            self.stdout.write(self.style.WARNING(
                f"\n{len(fichiers)} fichier(s) média laissés sur le disque "
                f"(relancez avec --supprimer-fichiers pour les effacer)."))

        self._afficher_resultat(supprimes, admins)

    # ------------------------------------------------------------- garde-fous

    def _verifier_base(self, options):
        nom = connection.settings_dict.get('NAME', '')
        attendue = options.get('base_attendue')
        self.stdout.write(f"Base connectée  : {nom}")
        if not attendue:
            raise CommandError(
                "--base-attendue est obligatoire : indiquez le nom EXACT de la "
                "base à vider, ne serait-ce que pour vérifier que vous visez la "
                "bonne. Rien n'a été modifié.")
        if nom != attendue:
            raise CommandError(
                f"REFUS : la base connectée est « {nom} », alors que "
                f"--base-attendue vaut « {attendue} ». Rien n'a été modifié.")

    def _administrateurs(self):
        """Renvoie (administrateurs, ambigus) selon les règles DU PROJET."""
        Utilisateur = get_user_model()
        admins, ambigus = [], []
        for utilisateur in Utilisateur.objects.all().order_by('pk'):
            profil = getattr(utilisateur, 'profile', None)
            est_super = bool(utilisateur.is_superuser)
            est_admin_projet = bool(profil is not None
                                    and getattr(profil, 'is_admin', False))
            if est_super or est_admin_projet:
                admins.append(utilisateur)
            elif utilisateur.is_staff:
                # `is_staff` ouvre l'interface d'administration, mais ne dit
                # rien du rôle métier : on ne décide pas à votre place.
                ambigus.append(utilisateur)
        return admins, ambigus

    def _verifier_ambigus(self, ambigus, options):
        if not ambigus:
            return
        lignes = "\n".join(
            f"    - {u.username} (id={u.pk}, is_staff={u.is_staff}, "
            f"is_superuser={u.is_superuser}, groupe="
            f"{getattr(getattr(u, 'profile', None), 'groupe', '—')})"
            for u in ambigus)
        message = (
            "STATUT AMBIGU pour {} compte(s) `is_staff` qui ne sont ni "
            "superutilisateur ni du groupe ADMIN du projet :\n{}\n"
            "Ils SERAIENT SUPPRIMÉS. Vérifiez chacun, puis relancez avec "
            "--accepter-ambigus si c'est bien voulu."
        ).format(len(ambigus), lignes)
        if not options.get('accepter_ambigus'):
            raise CommandError("REFUS :\n" + message)
        self.stdout.write(self.style.WARNING("Ambiguïtés acceptées :\n" + message))

    def _verifier_sauvegarde(self, options):
        chemin = options.get('sauvegarde')
        if not chemin:
            raise CommandError(
                "--sauvegarde est obligatoire : indiquez le dump réalisé juste "
                "avant (pg_dump). Rien n'a été modifié.")
        if not os.path.isfile(chemin):
            raise CommandError(f"REFUS : la sauvegarde « {chemin} » est "
                               "introuvable. Rien n'a été modifié.")
        taille = os.path.getsize(chemin)
        if taille == 0:
            raise CommandError(f"REFUS : la sauvegarde « {chemin} » est vide "
                               "(0 octet) — elle n'est pas exploitable. Rien "
                               "n'a été modifié.")
        age_heures = (time.time() - os.path.getmtime(chemin)) / 3600
        if age_heures > options['age_max_heures']:
            raise CommandError(
                f"REFUS : la sauvegarde date de {age_heures:.1f} h, au-delà de "
                f"--age-max-heures ({options['age_max_heures']}). Refaites un "
                "dump avant de recommencer.")
        self.stdout.write(self.style.SUCCESS(
            f"Sauvegarde      : {chemin} "
            f"({taille / 1024 / 1024:.1f} Mo, {age_heures:.1f} h)"))

    def _confirmer(self, options):
        if options.get('confirmer'):
            self.stdout.write(self.style.WARNING(
                "Confirmation fournie par --confirmer."))
            return
        self.stdout.write(self.style.ERROR(
            "\nTOUT va être supprimé, sauf les administrateurs ci-dessus.\n"
            "Tapez exactement « OUI » pour continuer :"))
        reponse = input('> ').strip()
        if reponse != 'OUI':
            raise CommandError("Annulé. Rien n'a été modifié.")

    # ------------------------------------------------------------ inventaire

    def _modeles_a_vider(self):
        """Modèles à vider : les applications métier, sauf les exceptions."""
        trouves = []
        for etiquette in APPLICATIONS_METIER:
            for modele in apps.get_app_config(etiquette).get_models():
                cle = (modele._meta.app_label, modele._meta.model_name)
                if cle in MODELES_ECARTES:
                    continue
                if not modele._meta.managed:
                    # Django ne gère pas son schéma : ses lignes appartiennent à
                    # une table créée autrement, et elles partiront avec leurs
                    # parents par cascade. On ne les vide pas à la main.
                    continue
                trouves.append(modele)
        return trouves

    def _fichiers_associes(self, modeles):
        """Chemins des fichiers des modèles qui vont être vidés."""
        chemins = []
        for modele in modeles:
            champs = [c for c in modele._meta.get_fields()
                      if isinstance(c, models.FileField)]
            if not champs:
                continue
            for champ in champs:
                for valeur in (modele.objects
                               .exclude(**{f"{champ.name}": ''})
                               .exclude(**{f"{champ.name}": None})
                               .values_list(champ.name, flat=True)):
                    try:
                        chemin = valeur.path
                    except (NotImplementedError, ValueError):
                        continue
                    if os.path.isfile(chemin):
                        chemins.append(chemin)
        return chemins

    def _afficher_bilan(self, admins, modeles, fichiers, dry_run):
        Utilisateur = get_user_model()
        total_utilisateurs = Utilisateur.objects.count()
        a_supprimer = total_utilisateurs - len(admins)

        self.stdout.write(self.style.MIGRATE_HEADING("\n-- Administrateurs conservés --"))
        for u in admins:
            profil = getattr(u, 'profile', None)
            self.stdout.write(
                f"    {u.username} (id={u.pk}, "
                f"{'superutilisateur' if u.is_superuser else 'groupe ADMIN'})"
                f"{', profil ' + str(profil.groupe) if profil else ''}")
        self.stdout.write(
            f"    soit {len(admins)} compte(s) sur {total_utilisateurs} ; "
            f"{a_supprimer} compte(s) non administrateur(s) seront supprimés.")

        self.stdout.write(self.style.MIGRATE_HEADING("\n-- Données métier à supprimer --"))
        total = 0
        for modele in modeles:
            nombre = modele.objects.count()
            total += nombre
            if nombre:
                self.stdout.write(f"    {nombre:>7}  "
                                  f"{modele._meta.app_label}.{modele._meta.model_name}")
        self.stdout.write(f"    {total:>7}  enregistrements au total "
                          f"({len(modeles)} modèles examinés)")

        # L'historique de l'interface d'administration n'est ni une donnée
        # métier ni un réglage : il est vidé, et signalé comme tel.
        historique = apps.get_model('admin', 'LogEntry').objects.count()

        self.stdout.write(self.style.MIGRATE_HEADING("\n-- Fichiers média --"))
        if fichiers:
            octets = sum(os.path.getsize(c) for c in fichiers)
            self.stdout.write(f"    {len(fichiers)} fichier(s), "
                              f"{octets / 1024 / 1024:.1f} Mo")
        else:
            self.stdout.write("    aucun")

        self.stdout.write(
            f"\nHistorique d'administration (LogEntry) : {historique} ligne(s) "
            "seront vidées.\nConservés : Group, Permission, ContentType, "
            "django_migrations, et les comptes administrateurs.")

    # -------------------------------------------------------------- exécution

    def _vider(self, modeles, admins):
        """Vide les modèles puis supprime les non-administrateurs.

        Appelée dans une transaction : soit tout passe, soit rien.
        """
        Utilisateur = get_user_model()
        Profil = apps.get_model('users', 'Profile')
        identifiants_admins = [u.pk for u in admins]

        supprimes = {}
        for modele in modeles:
            etiquette = f"{modele._meta.app_label}.{modele._meta.model_name}"
            nombre, _ = modele.objects.all().delete()
            supprimes[etiquette] = nombre

        # LogEntry : historique de l'administration, ni métier ni réglage.
        ligne, _ = apps.get_model('admin', 'LogEntry').objects.all().delete()
        supprimes['admin.LogEntry'] = ligne

        # Les non-administrateurs, en DERNIER : leurs données liées (profils,
        # sessions, jetons, achats) partent avec eux par cascade.
        Profil.objects.exclude(user_id__in=identifiants_admins).delete()
        comptes, _ = (Utilisateur.objects
                      .exclude(pk__in=identifiants_admins)
                      .delete())
        supprimes['Comptes non administrateurs'] = comptes
        return supprimes

    def _supprimer_fichiers(self, fichiers):
        from django.conf import settings
        racine = os.path.realpath(str(settings.MEDIA_ROOT))
        effaces = 0
        for chemin in fichiers:
            # Jamais en dehors du dossier média : un chemin de traversée ne doit
            # pas pouvoir faire effacer autre chose.
            if not os.path.realpath(chemin).startswith(racine):
                self.stdout.write(self.style.WARNING(
                    f"    ignoré (hors MEDIA_ROOT) : {chemin}"))
                continue
            try:
                os.remove(chemin)
                effaces += 1
            except OSError as erreur:
                self.stdout.write(self.style.WARNING(
                    f"    non supprimé : {chemin} ({erreur})"))
        self.stdout.write(f"{effaces} fichier(s) supprimé(s) du disque.")

    def _afficher_resultat(self, supprimes, admins):
        self.stdout.write(self.style.SUCCESS("\n=== BILAN APRÈS ==="))
        for etiquette, nombre in supprimes.items():
            self.stdout.write(f"    {nombre:>7}  supprimés — {etiquette}")
        self.stdout.write(
            f"\n{len(admins)} administrateur(s) conservé(s), "
            "avec leurs profils et leurs permissions.")
        self.stdout.write(
            "Group, Permission, ContentType et les migrations sont intacts.")
        self.stdout.write(self.style.SUCCESS("Remise à zéro terminée.\n"))

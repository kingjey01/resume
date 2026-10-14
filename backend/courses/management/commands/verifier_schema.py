"""Vérifie que le SCHÉMA de la base correspond aux modèles, table par table.

POURQUOI CETTE COMMANDE (2026-10-14)

La base de production porte un historique de migrations venu d'un AUTRE jeu de
fichiers : `0002_exercise_difficulty`, `0008_remove_userpersonalizedattempt_
results_detail_and_more`… Ces noms n'ont jamais existé dans ce dépôt (`git log`
est vide pour eux). Autrement dit, la série de migrations du dépôt
(`0002_filiere_promotion_universite` … `0027_…`) n'a JAMAIS été appliquée à la
production — alors que son résultat, lui, est bien dans le schéma, puisque
l'application fonctionne.

Avant de déclarer cette série « déjà appliquée » — ce qui est la seule façon de
débloquer `migrate` — il faut la PREUVE que le schéma en place la reflète
réellement. C'est ce que fait cette commande : elle interroge chaque modèle
(lecture seule, un SELECT d'une ligne) et signale ceux dont une colonne manque.

Le symptôme qui a motivé tout ceci — `courses_professeur_filieres.created_at` —
aurait été signalé ici, sur ce modèle précis.

    python manage.py verifier_schema
"""

from django.apps import apps
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = ("Interroge chaque table pour révéler une colonne ou une table "
            "manquante. LECTURE SEULE : ne modifie rien.")

    def handle(self, *args, **options):
        conformes, en_erreur, ignores = [], [], []

        for modele in apps.get_models():
            etiquette = modele._meta.label
            if not modele._meta.managed:
                # Tables non gérées par Django : hors périmètre des migrations.
                ignores.append((etiquette, "managed = False"))
                continue
            try:
                # Le SELECT d'une seule ligne suffit : une colonne absente en
                # base fait lever ProgrammingError AVANT toute autre chose.
                modele.objects.first()
                conformes.append(etiquette)
            except Exception as erreur:  # noqa: BLE001 — on veut TOUT voir
                en_erreur.append((etiquette, str(erreur).strip().split('\n')[0]))

        self.stdout.write(self.style.MIGRATE_HEADING(
            f"\nModèles interrogés : {len(conformes) + len(en_erreur)} "
            f"({len(ignores)} ignorés)"))

        if not en_erreur:
            self.stdout.write(self.style.SUCCESS(
                "\nAucun écart détecté : le schéma correspond aux modèles.\n"
                "La série de migrations du dépôt peut donc être déclarée "
                "« déjà appliquée » sans risque de masquer un changement.\n"))
        else:
            self.stdout.write(self.style.ERROR(
                f"\n{len(en_erreur)} modèle(s) EN ÉCART — le schéma ne "
                "correspond PAS aux modèles :\n"))
            for etiquette, message in en_erreur:
                self.stdout.write(f"    {etiquette}\n        {message}")
            self.stdout.write(self.style.WARNING(
                "\nNE PAS déclarer la série « déjà appliquée » avant d'avoir "
                "compris ces écarts : chacun est un changement réel qui "
                "manque à la base.\n"))

        if ignores:
            self.stdout.write("\nIgnorés (non gérés par Django) :")
            for etiquette, raison in ignores:
                self.stdout.write(f"    {etiquette} — {raison}")

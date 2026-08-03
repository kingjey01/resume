from django.core.management.base import BaseCommand
from courses.models import Course, Universite, Filiere, Promotion


class Command(BaseCommand):
    help = 'Migrer les anciens cours (CharField) vers les M2M (universites/filieres/promotions)'

    def handle(self, *args, **options):
        self.stdout.write("=" * 60)
        self.stdout.write(self.style.SUCCESS("MIGRATION DES COURS VERS LE SYSTÈME M2M"))
        self.stdout.write("=" * 60)

        total_courses = Course.objects.count()
        migrated = 0
        errors = 0

        self.stdout.write(f"\nTotal de cours à migrer: {total_courses}")
        self.stdout.write("\nDébut de la migration...\n")

        for course in Course.objects.prefetch_related('universites', 'filieres', 'promotions').all():
            try:
                # Verifier si deja migre
                if course.universites.exists() and course.filieres.exists() and course.promotions.exists():
                    self.stdout.write(self.style.SUCCESS(f"[OK] Cours '{course.nom}' deja migre"))
                    migrated += 1
                    continue

                # Migrer l'universite depuis le champ texte
                if course.university and not course.universites.exists():
                    try:
                        univ = Universite.objects.get(nom__iexact=course.university.strip())
                    except Universite.DoesNotExist:
                        univ = Universite.objects.create(nom=course.university.strip())
                        self.stdout.write(self.style.WARNING(f"  -> Universite creee: {univ.nom}"))
                    except Universite.MultipleObjectsReturned:
                        univ = Universite.objects.filter(nom__iexact=course.university.strip()).first()
                    course.universites.add(univ)
                    self.stdout.write(f"  -> Universite: {course.university} -> {univ.nom}")

                # Migrer la filiere depuis le champ texte
                if course.filiere and not course.filieres.exists():
                    try:
                        fil = Filiere.objects.get(nom__iexact=course.filiere.strip())
                    except Filiere.DoesNotExist:
                        fil = Filiere.objects.create(nom=course.filiere.strip())
                        self.stdout.write(self.style.WARNING(f"  -> Filiere creee: {fil.nom}"))
                    except Filiere.MultipleObjectsReturned:
                        fil = Filiere.objects.filter(nom__iexact=course.filiere.strip()).first()
                    course.filieres.add(fil)
                    self.stdout.write(f"  -> Filiere: {course.filiere} -> {fil.nom}")

                # Assigner une promotion par defaut si non definie
                if not course.promotions.exists():
                    try:
                        promo = Promotion.objects.get(nom='L1')
                    except Promotion.DoesNotExist:
                        promo = Promotion.objects.create(nom='L1', annee=2024)
                        self.stdout.write(self.style.WARNING(f"  -> Promotion creee: {promo.nom}"))
                    course.promotions.add(promo)
                    self.stdout.write(f"  -> Promotion assignee: {promo.nom}")

                migrated += 1
                self.stdout.write(self.style.SUCCESS(f"[OK] Cours '{course.nom}' migre avec succes\n"))

            except Exception as e:
                errors += 1
                self.stdout.write(self.style.ERROR(f"[ERREUR] Cours '{course.nom}': {str(e)}\n"))

        self.stdout.write("=" * 60)
        self.stdout.write(self.style.SUCCESS("RESUME DE LA MIGRATION"))
        self.stdout.write("=" * 60)
        self.stdout.write(f"Total de cours: {total_courses}")
        self.stdout.write(self.style.SUCCESS(f"Migres avec succes: {migrated}"))
        self.stdout.write(self.style.ERROR(f"Erreurs: {errors}"))
        self.stdout.write("=" * 60)

        # Verification finale
        self.stdout.write("\nVERIFICATION FINALE:")
        courses_without_m2m = [
            c for c in Course.objects.prefetch_related('universites', 'filieres', 'promotions').all()
            if not c.universites.exists() or not c.filieres.exists() or not c.promotions.exists()
        ]

        if courses_without_m2m:
            self.stdout.write(self.style.WARNING(
                f"[ATTENTION] {len(courses_without_m2m)} cours n'ont pas tous les M2M remplis:"
            ))
            for c in courses_without_m2m[:5]:
                self.stdout.write(f"  - {c.nom} (ID: {c.id})")
        else:
            self.stdout.write(self.style.SUCCESS("[OK] Tous les cours ont ete migres avec succes!"))

"""Ajoute la colonne `created_at` manquante à courses_professeur_filieres.

LE BUG CORRIGÉ ICI (erreur 500 à la suppression d'un utilisateur) :

    django.db.utils.ProgrammingError:
    ERREUR: la colonne courses_professeur_filieres.created_at n'existe pas

TROIS PIÈCES, ET ELLES S'EMBOÎTENT MAL :

1. `Professeur.filieres` est un ManyToManyField ORDINAIRE (courses/models.py:316).
   Django a donc créé lui-même la table `courses_professeur_filieres`, avec
   seulement id / professeur_id / filiere_id — SANS created_at.

2. Le modèle `ProfesseurFilieres` (courses/models.py:60) pointe sur la MÊME
   table (`db_table = 'courses_professeur_filieres'`) mais déclare
   `created_at = models.DateTimeField(auto_now_add=True)`.

3. Il est `managed = False` : Django ne gère pas son schéma, donc aucune
   migration n'a jamais été produite pour ce champ. Les migrations 0010 et 0014
   créent son ÉTAT sans `created_at` — le champ a été ajouté au modèle APRÈS,
   sans migration correspondante.

RÉSULTAT : toute lecture de `ProfesseurFilieres` demande la colonne
`created_at`. Supprimer un utilisateur supprime son `Professeur`, ce qui fait
cascader Django vers `ProfesseurFilieres` — un SELECT qui échoue. D'où le 500.

LE CORRECTIF suit la règle demandée : on ne retire pas le champ du modèle, on
n'écrit pas directement en base, on ne « fake » aucune migration. On aligne la
BASE sur le modèle, par une migration contrôlée et réversible, en conservant les
données existantes.

POURQUOI UN `DEFAULT now()` CONSERVÉ : les insertions du ManyToMany ordinaire
n'alimentent pas cette colonne. Sans valeur par défaut, toute nouvelle
association professeur↔filière échouerait sur une violation NOT NULL.
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0028_course_created_by'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            # L'ÉTAT : le champ existe désormais dans l'état Django comme dans
            # le modèle. Sans cela, `makemigrations` proposerait indéfiniment la
            # même migration, et la dérive resterait invisible.
            state_operations=[
                migrations.AddField(
                    model_name='professeurfilieres',
                    name='created_at',
                    field=models.DateTimeField(auto_now_add=True),
                ),
            ],
            # LA BASE : ajout de la colonne, idempotent, réversible.
            database_operations=[
                migrations.RunSQL(
                    sql=(
                        "ALTER TABLE courses_professeur_filieres "
                        "ADD COLUMN IF NOT EXISTS created_at "
                        "timestamp with time zone NOT NULL DEFAULT now();"
                    ),
                    reverse_sql=(
                        "ALTER TABLE courses_professeur_filieres "
                        "DROP COLUMN IF EXISTS created_at;"
                    ),
                ),
            ],
        ),
    ]

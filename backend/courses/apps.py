from django.apps import AppConfig


class CoursesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'courses'

    def ready(self):
        """Enregistrer les signaux de l'application courses."""
        import courses.signals  # noqa

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Promotion(models.Model):
    nom = models.CharField(max_length=50)  # L1, L2, L3, M1, M2
    annee = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        if self.annee:
            return f"{self.nom} - {self.annee}"
        return self.nom
    
    class Meta:
        verbose_name = "Promotion"
        verbose_name_plural = "Promotions"
        ordering = ['nom']


class Filiere(models.Model):
    nom = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    promotions = models.ManyToManyField(
        Promotion,
        related_name='filieres',
        blank=True
    )
    
    def __str__(self):
        return self.nom
    
    class Meta:
        verbose_name = "Filière"
        verbose_name_plural = "Filières"
        ordering = ['nom']


class Universite(models.Model):
    nom = models.CharField(max_length=200, unique=True)
    adresse = models.TextField(blank=True, null=True)
    filieres = models.ManyToManyField(
        Filiere,
        related_name='universites',
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.nom
    
    class Meta:
        verbose_name = "Université"
        verbose_name_plural = "Universités"
        ordering = ['nom']


class ProfesseurFilieres(models.Model):
    professeur = models.ForeignKey('Professeur', on_delete=models.CASCADE)
    filiere = models.ForeignKey(Filiere, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'courses_professeur_filieres'
        managed = False
        unique_together = ('professeur', 'filiere')
        verbose_name = "Relation Professeur-Filière"
        verbose_name_plural = "Relations Professeur-Filières"

    def __str__(self):
        return f"{self.professeur} - {self.filiere}"


class Course(models.Model):
    nom = models.CharField(max_length=200)
    filiere = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    university = models.CharField(max_length=200)
    # Relations multiples pour l'appartenance à plusieurs structures
    # et pour le contrôle d'accès (ManyToMany)
    universites = models.ManyToManyField(Universite, related_name='courses', blank=True)
    filieres = models.ManyToManyField(Filiere, related_name='courses', blank=True)
    promotions = models.ManyToManyField(Promotion, related_name='courses', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        uni = self.universites.first()
        fil = self.filieres.first()
        if uni and fil:
            return f"{self.nom} - {fil.nom} ({uni.nom})"
        return f"{self.nom} - {self.filiere}"

    def is_accessible_by_user(self, user):
        """Vérifie si l'utilisateur peut accéder à ce cours"""
        if not hasattr(user, 'profile'):
            return False
        profile = user.profile
        # Profil incomplet → accès refusé
        if not profile.universite or not profile.promotion or not profile.filiere:
            return False
        # Vérification via les M2M : l'utilisateur doit appartenir à toutes les structures assignées
        if self.universites.exists() and self.promotions.exists() and self.filieres.exists():
            return (
                self.universites.filter(id=profile.universite_id).exists() and
                self.promotions.filter(id=profile.promotion_id).exists() and
                self.filieres.filter(id=profile.filiere_id).exists()
            )
        # Fallback sur les anciens champs texte
        return (
            profile.universite and profile.universite.nom == self.university and
            profile.filiere and profile.filiere.nom == self.filiere
        )

    class Meta:
        verbose_name = "Cours"
        verbose_name_plural = "Cours"


class Session(models.Model):
    PROCESSING_STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('processing', 'En cours de traitement'),
        ('transcribed', 'Transcrit'),
        ('summarized', 'Résumé disponible'),
        ('failed', 'Échec'),
    ]
    
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='sessions')
    professeur_fk = models.ForeignKey('Professeur', on_delete=models.CASCADE, related_name='sessions', null=True, blank=True)
    date = models.DateTimeField()
    professeur = models.CharField(max_length=200, blank=True, default='')  # Nom texte pour compatibilité (optionnel)
    audio_file = models.FileField(upload_to='audio_sessions/', blank=True, null=True)
    audio_duration = models.FloatField(default=0, help_text="Durée de l'audio en secondes")
    summary_title = models.CharField(max_length=200, blank=True, default='', help_text="Titre du résumé à générer")
    summary_price = models.FloatField(default=0.0, help_text="Prix du résumé à générer")
    processing_status = models.CharField(max_length=20, choices=PROCESSING_STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True, null=True, help_text="Message d'erreur en cas d'échec")
    submitted_at = models.DateTimeField(blank=True, null=True, help_text="Date de soumission au traitement")
    processed_at = models.DateTimeField(blank=True, null=True, help_text="Date de fin de traitement")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.course.nom} - {self.date.strftime('%d/%m/%Y')}"
    
    @property
    def audio_duration_formatted(self):
        """Retourne la durée formatée (HH:MM:SS)"""
        if self.audio_duration <= 0:
            return "00:00"
        hours = int(self.audio_duration // 3600)
        minutes = int((self.audio_duration % 3600) // 60)
        seconds = int(self.audio_duration % 60)
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"
    
    @property
    def is_duration_valid(self):
        """Vérifie si la durée est <= 3 heures (10800 secondes)"""
        return self.audio_duration <= 10800
    
    class Meta:
        verbose_name = "Séance"
        verbose_name_plural = "Séances"
        ordering = ['-date']


class Transcription(models.Model):
    """
    Modèle pour stocker les transcriptions audio (Étape 1)
    La transcription brute de Deepgram est stockée ici avant d'être résumée
    """
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('processing', 'En cours'),
        ('completed', 'Terminée'),
        ('failed', 'Échouée'),
    ]
    
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='transcriptions')
    texte_transcription = models.TextField(help_text="Texte brut transcrit par Deepgram")
    langue = models.CharField(max_length=10, default='fr')
    duree_audio = models.FloatField(default=0, help_text="Durée de l'audio en secondes")
    confidence = models.FloatField(default=0, help_text="Score de confiance Deepgram (0-1)")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Transcription - {self.session} ({self.status})"
    
    class Meta:
        verbose_name = "Transcription"
        verbose_name_plural = "Transcriptions"
        ordering = ['-created_at']


class Summary(models.Model):
    """
    Modèle pour stocker les résumés (Étape 2)
    Le résumé est généré à partir d'une transcription
    """
    AUTHOR_CHOICES = [
        ('cp', 'Chef de Promo'),
        ('ai', 'Intelligence Artificielle'),
    ]
    
    titre = models.CharField(max_length=200)
    texte_resume = models.TextField()
    professeur = models.ForeignKey('Professeur', on_delete=models.CASCADE, related_name='summaries', null=True, blank=True)
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='summaries', blank=True, null=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='summaries')
    transcription = models.ForeignKey(Transcription, on_delete=models.SET_NULL, related_name='summaries', blank=True, null=True, help_text="Transcription source du résumé")
    author_type = models.CharField(max_length=10, choices=AUTHOR_CHOICES, default='cp')
    author_user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    pdf_file = models.FileField(upload_to='summaries/pdfs/', blank=True, null=True)
    prix = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_free = models.BooleanField(default=False)
    is_validated = models.BooleanField(default=False, help_text="Validation par le CP pour rendre le résumé public")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.titre} - {self.course.nom}"
    
    def save(self, *args, **kwargs):
        """
        Méthode save personnalisée pour auto-valider les résumés créés manuellement
        """
        # Si c'est un nouveau résumé créé manuellement par un CP, le valider automatiquement
        if not self.pk and self.author_type == 'cp':
            self.is_validated = True
        
        super().save(*args, **kwargs)
    
    @property
    def can_generate_exercises(self):
        """Vérifie si ce résumé peut générer des exercices"""
        return self.is_validated
    
    @property
    def author_badge(self):
        """Retourne le badge d'auteur pour l'affichage"""
        badges = {
            'ai': {
                'label': 'IA',
                'color': '#3B82F6',  # Bleu
                'icon': '🤖',
                'description': 'Généré par Intelligence Artificielle'
            },
            'cp': {
                'label': 'CP',
                'color': '#10B981',  # Vert
                'icon': '✍️',
                'description': 'Rédigé par Chef de Promotion'
            }
        }
        return badges.get(self.author_type, badges['cp'])
    
    def get_author_display_for_user(self, user):
        """Retourne les informations d'auteur selon les permissions de l'utilisateur"""
        # Seuls les CP et Admin peuvent voir les badges de distinction
        if hasattr(user, 'profile') and (user.profile.is_cp or user.profile.is_admin):
            return {
                'show_badge': True,
                'author_type': self.author_type,
                'badge': self.author_badge,
                'author_name': self.author_user.get_full_name() if self.author_user else 'Système IA'
            }
        else:
            # Les étudiants ne voient pas les badges
            return {
                'show_badge': False,
                'author_type': None,
                'badge': None,
                'author_name': 'Résumé+ Team'
            }
    
    class Meta:
        verbose_name = "Résumé"
        verbose_name_plural = "Résumés"
        ordering = ['-created_at']


class Professeur(models.Model):
    """
    Modèle pour les professeurs enseignants
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='professeur')
    telephone = models.CharField(max_length=20, blank=True, null=True)
    specialite = models.CharField(max_length=200, blank=True, null=True, help_text="Matière ou domaine d'expertise")
    universite = models.ForeignKey(Universite, on_delete=models.CASCADE, related_name='professeurs')
    filieres = models.ManyToManyField(Filiere, related_name='professeurs', blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.specialite or 'Professeur'}"
    
    class Meta:
        verbose_name = "Professeur"
        verbose_name_plural = "Professeurs"
        ordering = ['user__last_name', 'user__first_name']


class Dispense(models.Model):
    """
    Table métier de liaison entre Professeur, Cours, Université, Filière et Promotion.
    Source officielle pour déterminer quel professeur dispense quel cours.
    """
    professeur = models.ForeignKey(
        Professeur,
        on_delete=models.CASCADE,
        related_name='dispenses'
    )
    cours = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='dispenses'
    )
    universite = models.ForeignKey(
        Universite,
        on_delete=models.CASCADE,
        related_name='dispenses'
    )
    filiere = models.ForeignKey(
        Filiere,
        on_delete=models.CASCADE,
        related_name='dispenses'
    )
    promotion = models.ForeignKey(
        Promotion,
        on_delete=models.CASCADE,
        related_name='dispenses'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Dispense"
        verbose_name_plural = "Dispenses"
        unique_together = ('cours', 'professeur', 'promotion')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.professeur} dispense {self.cours} ({self.promotion})"


class Service(models.Model):
    nom = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True, null=True)
    prix = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True, help_text="Service actif et disponible à l'abonnement")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.nom
    
    class Meta:
        verbose_name = "Service"
        verbose_name_plural = "Services"
        ordering = ['nom']


class Abonnement(models.Model):
    DEVISE_CHOICES = [
        ('CDF', 'Franc Congolais'),
        ('USD', 'Dollar Américain'),
        ('EUR', 'Euro'),
    ]
    
    description = models.CharField(max_length=500, blank=True, null=True)
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='abonnements')
    etudiant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='course_abonnements')
    date_debut = models.DateTimeField()
    date_fin = models.DateTimeField()
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    devise = models.CharField(max_length=3, choices=DEVISE_CHOICES, default='CDF')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.etudiant.username} - {self.service.nom}"
    
    @property
    def is_active(self):
        from django.utils import timezone
        now = timezone.now()
        return self.date_debut <= now <= self.date_fin
    
    class Meta:
        verbose_name = "Abonnement"
        verbose_name_plural = "Abonnements"
        ordering = ['-created_at']


class Exercise(models.Model):
    """
    Modèle pour les exercices QCM générés par IA
    """
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('generating', 'Génération en cours'),
        ('completed', 'Terminé'),
        ('failed', 'Échec'),
    ]
    
    summary = models.ForeignKey(Summary, on_delete=models.CASCADE, related_name='exercises')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='exercises', null=True, blank=True)
    titre = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    difficulty = models.CharField(max_length=20, default='medium', choices=[('easy', 'Facile'), ('medium', 'Moyen'), ('hard', 'Difficile')])
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    generated_by_ai = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Exercice - {self.summary.titre}"
    
    @property
    def questions_count(self):
        return self.questions.count()
    
    class Meta:
        verbose_name = "Exercice"
        verbose_name_plural = "Exercices"
        ordering = ['-created_at']


class ExerciseQuestion(models.Model):
    """
    Modèle pour les questions d'exercices QCM
    """
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    option_a = models.CharField(max_length=500)
    option_b = models.CharField(max_length=500)
    option_c = models.CharField(max_length=500)
    option_d = models.CharField(max_length=500)
    correct_answer = models.CharField(max_length=1, choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')])
    explanation = models.TextField(blank=True, null=True, help_text="Explication de la bonne réponse")
    code_language = models.CharField(
        max_length=50, blank=True, null=True,
        help_text="Langage ou type du contenu technique (python, latex, sql, formula, algorithm, etc.)"
    )
    code_block = models.TextField(
        blank=True, null=True,
        help_text="Contenu technique (code source, formule, algorithme, commande, pseudo-code)"
    )
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Question {self.order} - {self.exercise.titre}"
    
    class Meta:
        verbose_name = "Question d'exercice"
        verbose_name_plural = "Questions d'exercices"
        ordering = ['exercise', 'order']


class ExerciseAttempt(models.Model):
    """
    Modèle pour les tentatives d'exercices par les étudiants
    """
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE, related_name='attempts')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='exercise_attempts')
    answers = models.JSONField(default=dict, help_text="Réponses de l'étudiant {question_id: 'A/B/C/D'}")
    score = models.FloatField(default=0.0, help_text="Score en pourcentage")
    completed_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.student.username} - {self.exercise.titre} ({self.score}%)"
    
    def calculate_score(self):
        """Calcule le score basé sur les réponses"""
        if not self.answers:
            return 0.0
        
        correct_answers = 0
        total_questions = self.exercise.questions.count()
        
        for question in self.exercise.questions.all():
            user_answer = self.answers.get(str(question.id))
            if user_answer == question.correct_answer:
                correct_answers += 1
        
        if total_questions > 0:
            self.score = (correct_answers / total_questions) * 100
        else:
            self.score = 0.0
        
        self.save()
        return self.score

    class Meta:
        verbose_name = "Tentative d'exercice"
        verbose_name_plural = "Tentatives d'exercices"
        ordering = ['-completed_at']


# ═══════════════════════════════════════════════════════════════════════════════
#  USER PERSONALIZED EXERCISES (NOUVEAU - QCM personnalisés par utilisateur)
# ═══════════════════════════════════════════════════════════════════════════════

class UserPersonalizedExercise(models.Model):
    """
    Exercice QCM personnalisé généré pour UN utilisateur spécifique.
    Chaque utilisateur a ses propres questions uniques pour chaque résumé.
    Isolé du modèle Exercise existant (pas de FK) pour garantir l'anti-triche.
    """
    DIFFICULTY_CHOICES = [
        ('easy', 'Facile'),
        ('medium', 'Moyen'),
        ('hard', 'Difficile'),
    ]

    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('generating', 'Génération en cours'),
        ('completed', 'Terminé'),
        ('failed', 'Échec'),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='personalized_exercises',
        help_text="Utilisateur propriétaire de cet exercice personnalisé"
    )
    summary = models.ForeignKey(
        Summary, on_delete=models.CASCADE,
        related_name='personalized_exercises',
        help_text="Résumé source sur lequel est basé l'exercice"
    )

    # Difficulté choisie par l'utilisateur
    difficulty = models.CharField(
        max_length=10, choices=DIFFICULTY_CHOICES, default='medium',
        help_text="Niveau de difficulté sélectionné"
    )

    # Questions stockées en JSON (isolation totale)
    questions = models.JSONField(
        default=list,
        help_text="Liste des 8 questions QCM au format JSON unique pour cet utilisateur"
    )

    # Gestion de la régénération
    seed = models.IntegerField(
        help_text="Seed aléatoire utilisée pour la génération (permet variation)"
    )
    regenerated_count = models.IntegerField(
        default=0,
        help_text="Nombre de fois que l'utilisateur a régénéré cet exercice"
    )

    # Statut de génération
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='pending'
    )
    generated_by_ai = models.BooleanField(default=False)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_accessed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Exercice Personnalisé Utilisateur"
        verbose_name_plural = "Exercices Personnalisés Utilisateurs"
        ordering = ['-created_at']
        unique_together = ['user', 'summary']  # 1 exercice perso par user par résumé
        indexes = [
            models.Index(fields=['user', 'summary']),
            models.Index(fields=['status']),
            models.Index(fields=['difficulty']),
        ]

    def __str__(self):
        return f"Exercice perso - {self.user.username} - {self.summary.titre} ({self.difficulty})"

    @property
    def questions_count(self):
        return len(self.questions) if self.questions else 0

    def mark_accessed(self):
        """Met à jour la date du dernier accès"""
        self.last_accessed_at = timezone.now()
        self.save(update_fields=['last_accessed_at'])


class UserPersonalizedAttempt(models.Model):
    """
    Tentative d'un utilisateur sur son exercice personnalisé.
    Equivalent à ExerciseAttempt mais pour les QCM personnalisés.
    """
    personalized_exercise = models.ForeignKey(
        UserPersonalizedExercise, on_delete=models.CASCADE,
        related_name='attempts',
        help_text="Exercice personnalisé concerné"
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='personalized_exercise_attempts',
        help_text="Utilisateur qui a tenté (redondant mais pratique)"
    )

    # Réponses au format {question_index: "A/B/C/D"}
    answers = models.JSONField(
        default=dict,
        help_text="Réponses de l'utilisateur {index_question: 'A/B/C/D'}"
    )

    # Résultats détaillés calculés
    results_detail = models.JSONField(
        default=list,
        help_text="Détail de chaque question avec correction"
    )
    score = models.FloatField(
        default=0.0,
        help_text="Score en pourcentage (0-100)"
    )
    correct_answers_count = models.IntegerField(
        default=0,
        help_text="Nombre de bonnes réponses"
    )

    # Timings
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    time_spent_seconds = models.IntegerField(
        default=0,
        help_text="Temps passé en secondes"
    )

    class Meta:
        verbose_name = "Tentative d'exercice personnalisé"
        verbose_name_plural = "Tentatives d'exercices personnalisés"
        ordering = ['-started_at']

    def __str__(self):
        return f"{self.user.username} - {self.personalized_exercise.summary.titre} ({self.score}%)"

    def calculate_results(self):
        """
        Calcule le score et génère les résultats détaillés.
        Compare les réponses utilisateur avec les questions stockées.
        """
        if not self.answers or not self.personalized_exercise.questions:
            self.score = 0.0
            self.correct_answers_count = 0
            self.save()
            return

        questions = self.personalized_exercise.questions
        results = []
        correct_count = 0

        for idx, question in enumerate(questions):
            user_answer = self.answers.get(str(idx), '')
            correct_answer = question.get('correct_answer', '')
            is_correct = user_answer.upper() == correct_answer.upper()

            if is_correct:
                correct_count += 1

            results.append({
                'question_index': idx,
                'question_text': question.get('question_text') or question.get('question', ''),
                'user_answer': user_answer,
                'correct_answer': correct_answer,
                'is_correct': is_correct,
                'explanation': question.get('explanation', ''),
                'options': question.get('options', {}),
            })

        total = len(questions)
        self.score = (correct_count / total * 100) if total > 0 else 0.0
        self.correct_answers_count = correct_count
        self.results_detail = results
        self.completed_at = timezone.now()

        # Calculer temps passé
        if self.started_at and self.completed_at:
            delta = self.completed_at - self.started_at
            self.time_spent_seconds = int(delta.total_seconds())

        self.save()
        return self.score

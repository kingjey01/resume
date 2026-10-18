from django.db import models
from django.contrib.auth.models import User
from courses.models import Summary
from django.utils import timezone
from datetime import timedelta


class Service(models.Model):
    SERVICE_TYPES = [
        ('premium', 'Premium'),
        ('vip', 'VIP'),
        ('basic', 'Basic'),
    ]
    
    CURRENCY_CHOICES = [
        ('CDF', 'Franc Congolais'),
        ('USD', 'Dollar Américain'),
        #('EUR', 'Euro'),
    ]
    
    nom = models.CharField(max_length=100)
    description = models.TextField()
    type = models.CharField(max_length=20, choices=SERVICE_TYPES)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='CDF')
    duree_mois = models.IntegerField(help_text="Durée en mois")
    features = models.JSONField(default=list, help_text="Liste des fonctionnalités")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # QUOTA DE GÉNÉRATIONS QCM (tâche 57, prompt 2).
    #
    # L'unité est UNE génération de QCM (un niveau de difficulté, 8 questions),
    # et non chaque question. Le plafond de 8 questions × 3 niveaux = 24 par
    # résumé reste une règle de contenu, distincte de ce quota d'abonnement.
    # `0` = illimité, ce qui laisse les plans existants fonctionner sans
    # changement tant que l'administrateur n'a pas fixé de valeur.
    quota_qcm_mensuel = models.PositiveIntegerField(
        default=0,
        help_text="Générations de QCM par période de 30 jours (0 = illimité)",
    )
    plafond_qcm_journalier = models.PositiveIntegerField(
        default=0,
        help_text=(
            "Générations de QCM autorisées par jour. "
            "0 = plafond dérivé du quota mensuel (quota / 30, minimum 1)."
        ),
    )
    
    def get_date_fin(self, date_debut=None):
        """
        Calcule la date de fin d'un abonnement à ce service.
        Utilise timedelta(days=duree_mois * 30) pour 1 mois ≈ 30 jours.
        """
        from datetime import timedelta
        from django.utils import timezone
        debut = date_debut or timezone.now()
        return debut + timedelta(days=self.duree_mois * 30)

    def __str__(self):
        return f"{self.nom} - {self.price} {self.currency}"

    class Meta:
        verbose_name = "Service"
        verbose_name_plural = "Services"
        ordering = ['-created_at']


class Abonnement(models.Model):
    STATUS_CHOICES = [
        ('active', 'Actif'),
        ('expired', 'Expiré'),
        ('cancelled', 'Annulé'),
        ('pending', 'En attente'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='abonnements')
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='abonnements')
    date_debut = models.DateTimeField(default=timezone.now)
    date_fin = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    auto_renew = models.BooleanField(default=False)
    progress = models.IntegerField(default=0, help_text="Progression en pourcentage")
    created_at = models.DateTimeField(auto_now_add=True)

    # ── QUOTA DE GÉNÉRATIONS QCM (tâche 57, prompt 2) ──────────────────────
    #
    # Ces valeurs sont figées à la création de l'abonnement : une modification
    # ultérieure du Service ne change pas un abonnement déjà vendu.
    #
    # Les compteurs (`consomme`, `jour_consomme`) sont la SEULE source de
    # vérité. Ils ne sont jamais alimentés par l'application Flutter ; les vues
    # les incrémentent sous `select_for_update()` pour empêcher deux requêtes
    # simultanées de dépasser le quota.
    quota_qcm_mensuel = models.PositiveIntegerField(
        default=0,
        help_text="Générations de QCM par période de 30 jours (0 = illimité)",
    )
    plafond_qcm_journalier = models.PositiveIntegerField(
        default=0,
        help_text="Générations de QCM autorisées par jour (0 = dérivé du mensuel)",
    )
    quota_qcm_consomme = models.PositiveIntegerField(
        default=0,
        help_text="Générations consommées sur la période courante",
    )
    quota_qcm_periode_debut = models.DateTimeField(
        null=True, blank=True,
        help_text="Début de la période de consommation courante (30 jours)",
    )
    quota_qcm_jour = models.DateField(
        null=True, blank=True,
        help_text="Jour du compteur journalier courant",
    )
    quota_qcm_jour_consomme = models.PositiveIntegerField(
        default=0,
        help_text="Générations consommées aujourd'hui",
    )

    def save(self, *args, **kwargs):
        if self._state.adding:
            # Figer le plan au moment de l'achat. Un `0` explicite reste
            # possible : il signifie « illimité », sauf si le service vendu
            # définit lui-même un quota.
            if not self.quota_qcm_mensuel and self.service_id:
                self.quota_qcm_mensuel = self.service.quota_qcm_mensuel or 0
            if not self.plafond_qcm_journalier and self.service_id:
                self.plafond_qcm_journalier = self.service.plafond_qcm_journalier or 0
            if self.quota_qcm_periode_debut is None:
                self.quota_qcm_periode_debut = self.date_debut or timezone.now()
        if not self.date_fin:
            self.date_fin = self.service.get_date_fin(self.date_debut)
        super().save(*args, **kwargs)
    
    @property
    def is_active(self):
        return self.status == 'active' and self.date_fin > timezone.now()
    
    def __str__(self):
        return f"{self.user.username} - {self.service.nom}"
    
    class Meta:
        verbose_name = "Abonnement"
        verbose_name_plural = "Abonnements"
        ordering = ['-created_at']


class Purchase(models.Model):
    PAYMENT_METHODS = [
        ('mobile_money', 'Mobile Money'),
        #('card', 'Carte Bancaire'),
        #('points', 'Points'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('completed', 'Complété'),
        ('failed', 'Échoué'),
        ('refunded', 'Remboursé'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='purchases')
    summary = models.ForeignKey(Summary, on_delete=models.CASCADE, related_name='purchases', null=True, blank=True)
    service = models.ForeignKey(Service, on_delete=models.SET_NULL, null=True, blank=True, related_name='purchases')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    transaction_id = models.CharField(max_length=100, unique=True, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    
    def __str__(self):
        summary_name = self.summary.titre if self.summary else 'Abonnement'
        return f"{self.user.username} - {summary_name} - {self.amount}€"
    
    class Meta:
        verbose_name = "Achat"
        verbose_name_plural = "Achats"
        ordering = ['-created_at']

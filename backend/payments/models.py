from django.db import models
from django.contrib.auth.models import User
from courses.models import Summary
from django.utils import timezone
from datetime import timedelta


PAYMENT_SOURCE_CHOICES = [
    ('flexpay', 'FlexPay'),
    ('apple', 'Apple In-App Purchase'),
    ('other', 'Autre'),
]


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
    # L'unité est UNE GÉNÉRATION COMPLÈTE pour un résumé : le pack de ses
    # 3 niveaux de difficulté (8 questions × 3 = 24 questions), et non chaque
    # question ni chaque niveau isolé. Le plafond de 24 questions par résumé
    # reste une règle de contenu, distincte de ce quota d'abonnement.
    # `0` = illimité, ce qui laisse les plans existants fonctionner sans
    # changement tant que l'administrateur n'a pas fixé de valeur.
    quota_qcm_mensuel = models.PositiveIntegerField(
        default=0,
        help_text="Générations complètes de QCM (3 niveaux) par période de 30 jours (0 = illimité)",
    )
    plafond_qcm_journalier = models.PositiveIntegerField(
        default=0,
        help_text=(
            "Générations complètes de QCM autorisées par jour. "
            "0 = plafond dérivé du quota mensuel (quota / 30, minimum 1)."
        ),
    )

    # Tâche 71 — identifiant du produit d'abonnement auto-renouvelable Apple.
    # Vide tant que le produit n'a pas été créé dans App Store Connect.
    apple_product_id = models.CharField(
        max_length=200, blank=True, default='',
        help_text="Identifiant du produit d'abonnement Apple (App Store Connect)",
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
    
    # `user` est le BÉNÉFICIAIRE de l'abonnement (celui qui y a droit).
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='abonnements')
    # `payer` est celui qui a financé l'abonnement. Il vaut `user` pour un
    # achat personnel ; il en diffère pour un abonnement offert (tâche 70).
    payer = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='abonnements_offerts',
        help_text="Compte payeur ; NULL pour les abonnements antérieurs à la tâche 70",
    )
    # Tâche 71 — source de l'abonnement (FlexPay, Apple IAP).
    source = models.CharField(
        max_length=20, choices=PAYMENT_SOURCE_CHOICES, default='flexpay',
    )
    apple_original_transaction_id = models.CharField(
        max_length=100, blank=True, null=True, db_index=True,
        help_text="Identifiant de transaction d'origine Apple",
    )
    apple_environment = models.CharField(max_length=20, blank=True, null=True)
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
        help_text="Générations complètes de QCM (3 niveaux) par période de 30 jours (0 = illimité)",
    )
    plafond_qcm_journalier = models.PositiveIntegerField(
        default=0,
        help_text="Générations complètes de QCM autorisées par jour (0 = dérivé du mensuel)",
    )
    quota_qcm_consomme = models.PositiveIntegerField(
        default=0,
        help_text="Packs de QCM consommés sur la période courante",
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
        help_text="Packs de QCM consommés aujourd'hui",
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

    @property
    def est_cadeau(self):
        """Vrai si l'abonnement a été financé par un autre compte."""
        return bool(self.payer_id and self.payer_id != self.user_id)
    
    def __str__(self):
        return f"{self.user.username} - {self.service.nom}"
    
    class Meta:
        verbose_name = "Abonnement"
        verbose_name_plural = "Abonnements"
        ordering = ['-created_at']


class Purchase(models.Model):
    PAYMENT_METHODS = [
        ('mobile_money', 'Mobile Money'),
        ('apple', 'Apple In-App Purchase'),
        #('card', 'Carte Bancaire'),
        #('points', 'Points'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('completed', 'Complété'),
        ('failed', 'Échoué'),
        ('refunded', 'Remboursé'),
    ]
    
    # `user` est le BÉNÉFICIAIRE de l'achat (celui qui reçoit le droit d'accès).
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='purchases')
    # Traçabilité « Payer pour un autre » (tâche 70).
    payer = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='purchases_payees',
        help_text="Compte initiateur/financeur ; NULL pour les achats antérieurs",
    )
    payer_phone = models.CharField(
        max_length=20, blank=True, null=True,
        help_text="Numéro Mobile Money réellement utilisé pour payer",
    )
    beneficiary_phone = models.CharField(
        max_length=20, blank=True, null=True,
        help_text="Numéro du compte bénéficiaire",
    )
    # Tâche 71 — source du paiement et traçabilité Apple.
    source = models.CharField(
        max_length=20, choices=PAYMENT_SOURCE_CHOICES, default='flexpay',
    )
    apple_transaction_id = models.CharField(
        max_length=100, unique=True, null=True, blank=True,
        help_text="Identifiant de transaction Apple (unique)",
    )
    apple_original_transaction_id = models.CharField(
        max_length=100, blank=True, null=True, db_index=True,
    )
    apple_environment = models.CharField(max_length=20, blank=True, null=True)
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

    @property
    def est_cadeau(self):
        """Vrai si l'achat a été financé par un autre compte."""
        return bool(self.payer_id and self.payer_id != self.user_id)

    @property
    def type_operation(self):
        """Type lisible de l'opération (traçabilité)."""
        if self.summary_id:
            return 'achat_resume'
        if self.service_id:
            return 'abonnement_qcm'
        return 'inconnu'

    class Meta:
        verbose_name = "Achat"
        verbose_name_plural = "Achats"
        ordering = ['-created_at']


class AppleTransaction(models.Model):
    """Journal des transactions Apple validées (tâche 71).

    Sert de source d'idempotence : un `transaction_id` Apple ne peut être
    traité qu'une seule fois. Aucune donnée de paiement sensible (carte,
    Apple ID, reçu brut) n'est stockée ici.
    """

    KIND_CHOICES = [
        ('consumable', 'Achat consommable'),
        ('subscription', 'Abonnement'),
    ]
    STATUS_CHOICES = [
        ('granted', 'Droit accordé'),
        ('refunded', 'Remboursé'),
        ('revoked', 'Révoqué'),
        ('ignored', 'Ignoré'),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='apple_transactions',
    )
    product_id = models.CharField(max_length=200, db_index=True)
    transaction_id = models.CharField(max_length=100, unique=True)
    original_transaction_id = models.CharField(
        max_length=100, blank=True, null=True, db_index=True,
    )
    purchase_date = models.DateTimeField(null=True, blank=True)
    expires_date = models.DateTimeField(null=True, blank=True)
    environment = models.CharField(max_length=20)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='granted',
    )
    kind = models.CharField(max_length=20, choices=KIND_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Transaction Apple"
        verbose_name_plural = "Transactions Apple"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'product_id']),
            models.Index(fields=['original_transaction_id', '-created_at']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.product_id} - {self.status}"


class AppleNotification(models.Model):
    """Journal idempotent des App Store Server Notifications V2."""

    notification_uuid = models.CharField(max_length=100, unique=True)
    notification_type = models.CharField(max_length=50)
    subtype = models.CharField(max_length=50, blank=True, null=True)
    transaction_id = models.CharField(
        max_length=100, blank=True, null=True, db_index=True,
    )
    original_transaction_id = models.CharField(
        max_length=100, blank=True, null=True, db_index=True,
    )
    environment = models.CharField(max_length=20, blank=True, null=True)
    processing_status = models.CharField(
        max_length=20, default='received',
        help_text="received / processed / ignored / error",
    )
    error_message = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Notification Apple"
        verbose_name_plural = "Notifications Apple"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.notification_type} - {self.notification_uuid}"

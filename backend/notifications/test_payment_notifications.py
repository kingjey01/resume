"""
Tests for payment and subscription notifications.
Verifies that notifications are sent correctly for:
- Subscription payment
- Subscription expiring soon
- Subscription expired
- Summary purchase
"""
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from payments.models import Service, Abonnement, Purchase
from courses.models import Summary, Course, Universite, Filiere, Promotion
from notifications.models import AppNotification, UserNotification
from notifications.tasks import (
    notify_subscription_paid,
    notify_subscription_expiring_soon,
    notify_subscription_expired,
    notify_summary_purchased,
)


class SubscriptionNotificationTest(TestCase):
    """Test subscription-related notifications."""

    def setUp(self):
        """Create test data."""
        self.user = User.objects.create_user(
            username='test_user',
            email='test@example.com',
            password='test123'
        )
        
        self.service = Service.objects.create(
            nom='Premium',
            description='Premium subscription',
            type='premium',
            price=Decimal('9.99'),
            currency='USD',
            duree_mois=1,
            features=['Feature 1', 'Feature 2'],
            is_active=True,
        )

    def test_subscription_paid_notification(self):
        """Test notification when subscription is paid."""
        # Create subscription
        abonnement = Abonnement.objects.create(
            user=self.user,
            service=self.service,
            date_debut=timezone.now(),
            date_fin=timezone.now() + timedelta(days=30),
            status='active',
        )
        
        # Trigger notification task
        result = notify_subscription_paid(abonnement.id)
        
        # Verify notification was created
        self.assertIn('notification_id', result)
        notif = AppNotification.objects.get(id=result['notification_id'])
        self.assertIn('Abonnement activé', notif.title)
        self.assertEqual(notif.notification_type, 'payment')
        
        # Verify user notification was created
        user_notif = UserNotification.objects.filter(
            user=self.user,
            notification=notif
        ).exists()
        self.assertTrue(user_notif, "UserNotification should be created")

    def test_subscription_expiring_soon_notification(self):
        """Test notification when subscription is expiring soon."""
        # Create subscription expiring in 5 days
        abonnement = Abonnement.objects.create(
            user=self.user,
            service=self.service,
            date_debut=timezone.now() - timedelta(days=25),
            date_fin=timezone.now() + timedelta(days=5),
            status='active',
        )
        
        # Trigger notification task
        result = notify_subscription_expiring_soon(abonnement.id)
        
        # Verify notification was created
        self.assertIn('notification_id', result)
        self.assertIn('days_left', result)
        notif = AppNotification.objects.get(id=result['notification_id'])
        self.assertIn('expire bientôt', notif.title)
        self.assertEqual(notif.notification_type, 'payment')
        
        # Verify user notification was created
        user_notif = UserNotification.objects.filter(
            user=self.user,
            notification=notif
        ).exists()
        self.assertTrue(user_notif, "UserNotification should be created")

    def test_subscription_expired_notification(self):
        """Test notification when subscription has expired."""
        # Create expired subscription
        abonnement = Abonnement.objects.create(
            user=self.user,
            service=self.service,
            date_debut=timezone.now() - timedelta(days=60),
            date_fin=timezone.now() - timedelta(days=1),
            status='expired',
        )
        
        # Trigger notification task
        result = notify_subscription_expired(abonnement.id)
        
        # Verify notification was created
        self.assertIn('notification_id', result)
        notif = AppNotification.objects.get(id=result['notification_id'])
        self.assertIn('expiré', notif.title)
        self.assertEqual(notif.notification_type, 'payment')
        
        # Verify user notification was created
        user_notif = UserNotification.objects.filter(
            user=self.user,
            notification=notif
        ).exists()
        self.assertTrue(user_notif, "UserNotification should be created")

    def test_multiple_subscriptions_notifications(self):
        """Test that each subscription gets its own notification."""
        # Create multiple subscriptions
        for i in range(3):
            Abonnement.objects.create(
                user=self.user,
                service=self.service,
                date_debut=timezone.now(),
                date_fin=timezone.now() + timedelta(days=30),
                status='active',
            )
        
        # Get all subscriptions
        abonnements = Abonnement.objects.filter(user=self.user)
        self.assertEqual(abonnements.count(), 3)
        
        # Trigger notifications for each
        # (les signaux de création d'abonnement en créent aussi → compter le delta)
        before = AppNotification.objects.filter(notification_type='payment').count()
        for abonnement in abonnements:
            notify_subscription_paid(abonnement.id)
        after = AppNotification.objects.filter(notification_type='payment').count()

        # Verify 3 notifications were created by the tasks
        self.assertEqual(after - before, 3)


class PurchaseNotificationTest(TestCase):
    """Test purchase-related notifications."""

    def setUp(self):
        """Create test data."""
        self.user = User.objects.create_user(
            username='test_user',
            email='test@example.com',
            password='test123'
        )
        
        # Create course and summary (schéma M2M actuel)
        self.universite = Universite.objects.create(nom='Test University')
        self.filiere = Filiere.objects.create(nom='Test Filiere')
        self.filiere.universites.add(self.universite)
        self.promotion = Promotion.objects.create(nom='L1')
        self.promotion.filieres.add(self.filiere)

        self.course = Course.objects.create(
            nom='Test Course',
            university=self.universite.nom,
            filiere=self.filiere.nom,
        )
        self.course.universites.add(self.universite)
        self.course.filieres.add(self.filiere)
        self.course.promotions.add(self.promotion)

        self.summary = Summary.objects.create(
            titre='Test Summary',
            texte_resume='Test content',
            course=self.course,
            author_user=self.user,
            is_validated=True,
        )

    def test_summary_purchase_notification(self):
        """Test notification when summary is purchased."""
        # Create purchase
        purchase = Purchase.objects.create(
            user=self.user,
            summary=self.summary,
            amount=Decimal('5.00'),
            payment_method='mobile_money',
            status='completed',
        )
        
        # Trigger notification task
        result = notify_summary_purchased(purchase.id)
        
        # Verify notification was created
        self.assertIn('notification_id', result)
        self.assertIn('summary_id', result)
        notif = AppNotification.objects.get(id=result['notification_id'])
        self.assertIn('Résumé acheté', notif.title)
        self.assertEqual(notif.notification_type, 'payment')
        self.assertIn(self.summary.titre, notif.body)
        
        # Verify user notification was created
        user_notif = UserNotification.objects.filter(
            user=self.user,
            notification=notif
        ).exists()
        self.assertTrue(user_notif, "UserNotification should be created")

    def test_multiple_purchases_notifications(self):
        """Test that each purchase gets its own notification."""
        # Create multiple purchases
        for i in range(3):
            summary = Summary.objects.create(
                titre=f'Summary {i}',
                texte_resume='Test content',
                course=self.course,
                author_user=self.user,
                is_validated=True,
            )
            Purchase.objects.create(
                user=self.user,
                summary=summary,
                amount=Decimal('5.00'),
                payment_method='mobile_money',
                status='completed',
            )
        
        # Get all purchases
        purchases = Purchase.objects.filter(user=self.user)
        self.assertEqual(purchases.count(), 3)
        
        # Trigger notifications for each
        # (les signaux de création d'achat en créent aussi → compter le delta)
        before = AppNotification.objects.filter(notification_type='payment').count()
        for purchase in purchases:
            notify_summary_purchased(purchase.id)
        after = AppNotification.objects.filter(notification_type='payment').count()

        # Verify 3 notifications were created by the tasks
        self.assertEqual(after - before, 3)

    def test_purchase_without_summary(self):
        """Test that purchase without summary doesn't crash."""
        # Create subscription purchase (no summary)
        service = Service.objects.create(
            nom='Premium',
            description='Premium subscription',
            type='premium',
            price=Decimal('9.99'),
            currency='USD',
            duree_mois=1,
            features=['Feature 1'],
            is_active=True,
        )
        
        purchase = Purchase.objects.create(
            user=self.user,
            service=service,
            amount=Decimal('9.99'),
            payment_method='mobile_money',
            status='completed',
        )
        
        # This should not crash even though summary is None
        # (In real scenario, we'd only call notify_summary_purchased for summary purchases)
        # This test just verifies the model allows it
        self.assertIsNone(purchase.summary)

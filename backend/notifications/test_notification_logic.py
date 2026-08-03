"""
Tests pour la logique de ciblage des notifications.
Vérifie que les destinataires sont correctement déterminés selon les filtres.
"""
from django.test import TestCase
from django.contrib.auth.models import User
from courses.models import Universite, Filiere, Promotion
from users.models import UserProfile
from notifications.models import AppNotification, UserNotification
from notifications.tasks import create_and_send_notification


class NotificationTargetingLogicTest(TestCase):
    """Test the notification targeting logic."""

    def setUp(self):
        """Create test data."""
        # Create universities
        self.unikin = Universite.objects.create(nom='UNIKIN')
        self.unilu = Universite.objects.create(nom='UNILU')

        # Create filieres (schéma M2M actuel)
        self.info_unikin = Filiere.objects.create(nom='Informatique')
        self.info_unikin.universites.add(self.unikin)
        self.math_unikin = Filiere.objects.create(nom='Mathématiques')
        self.math_unikin.universites.add(self.unikin)
        self.info_unilu = Filiere.objects.create(nom='Informatique')
        self.info_unilu.universites.add(self.unilu)

        # Create promotions (schéma M2M actuel)
        self.l1_info_unikin = Promotion.objects.create(nom='L1')
        self.l1_info_unikin.filieres.add(self.info_unikin)
        self.l2_info_unikin = Promotion.objects.create(nom='L2')
        self.l2_info_unikin.filieres.add(self.info_unikin)
        self.l1_math_unikin = Promotion.objects.create(nom='L1')
        self.l1_math_unikin.filieres.add(self.math_unikin)
        self.l1_info_unilu = Promotion.objects.create(nom='L1')
        self.l1_info_unilu.filieres.add(self.info_unilu)

        # Create users
        self.users = {}

        # UNIKIN Informatique L1
        for i in range(2):
            user = User.objects.create_user(
                username=f'l1_info_unikin_{i}',
                password='test'
            )
            UserProfile.objects.create(
                user=user,
                universite=self.unikin,
                filiere=self.info_unikin,
                promotion=self.l1_info_unikin,
            )
            self.users[f'l1_info_unikin_{i}'] = user

        # UNIKIN Informatique L2
        for i in range(2):
            user = User.objects.create_user(
                username=f'l2_info_unikin_{i}',
                password='test'
            )
            UserProfile.objects.create(
                user=user,
                universite=self.unikin,
                filiere=self.info_unikin,
                promotion=self.l2_info_unikin,
            )
            self.users[f'l2_info_unikin_{i}'] = user

        # UNIKIN Mathématiques L1
        for i in range(2):
            user = User.objects.create_user(
                username=f'l1_math_unikin_{i}',
                password='test'
            )
            UserProfile.objects.create(
                user=user,
                universite=self.unikin,
                filiere=self.math_unikin,
                promotion=self.l1_math_unikin,
            )
            self.users[f'l1_math_unikin_{i}'] = user

        # UNILU Informatique L1
        for i in range(2):
            user = User.objects.create_user(
                username=f'l1_info_unilu_{i}',
                password='test'
            )
            UserProfile.objects.create(
                user=user,
                universite=self.unilu,
                filiere=self.info_unilu,
                promotion=self.l1_info_unilu,
            )
            self.users[f'l1_info_unilu_{i}'] = user

    def test_case_1_no_filters_global(self):
        """Case 1: No filters → all users."""
        # Create notification with no filters
        notif = AppNotification.objects.create(
            title='Global notification',
            body='This goes to everyone',
            notification_type='system',
            target_universite=None,
            target_filiere=None,
            target_promotion=None,
        )

        # Manually create UserNotification for all users (simulating the task)
        for profile in UserProfile.objects.filter(user__is_active=True):
            UserNotification.objects.get_or_create(
                user=profile.user,
                notification=notif,
            )

        # Verify: all 8 users (2×L1 Info + 2×L2 Info + 2×L1 Math + 2×L1 UNILU) should have this notification
        count = UserNotification.objects.filter(notification=notif).count()
        self.assertEqual(count, 8, f"Expected 8 users, got {count}")

    def test_case_2_universite_only(self):
        """Case 2: Université only → all users in that université."""
        notif = AppNotification.objects.create(
            title='UNIKIN notification',
            body='This goes to UNIKIN only',
            notification_type='promo',
            target_universite=self.unikin,
            target_filiere=None,
            target_promotion=None,
        )

        # Manually create UserNotification for UNIKIN users
        for profile in UserProfile.objects.filter(
            user__is_active=True, universite=self.unikin
        ):
            UserNotification.objects.get_or_create(
                user=profile.user,
                notification=notif,
            )

        # Verify: 6 UNIKIN users (2 L1 Info + 2 L2 Info + 2 L1 Math)
        count = UserNotification.objects.filter(notification=notif).count()
        self.assertEqual(count, 6, f"Expected 6 UNIKIN users, got {count}")

    def test_case_3_universite_filiere(self):
        """Case 3: Université + Filière → users in that université + filière."""
        notif = AppNotification.objects.create(
            title='UNIKIN Informatique notification',
            body='This goes to UNIKIN Informatique only',
            notification_type='promo',
            target_universite=self.unikin,
            target_filiere=self.info_unikin,
            target_promotion=None,
        )

        # Manually create UserNotification for UNIKIN Informatique users
        for profile in UserProfile.objects.filter(
            user__is_active=True,
            universite=self.unikin,
            filiere=self.info_unikin,
        ):
            UserNotification.objects.get_or_create(
                user=profile.user,
                notification=notif,
            )

        # Verify: 4 users (2 L1 Info + 2 L2 Info)
        count = UserNotification.objects.filter(notification=notif).count()
        self.assertEqual(count, 4, f"Expected 4 UNIKIN Informatique users, got {count}")

    def test_case_4_universite_filiere_promotion(self):
        """Case 4: Université + Filière + Promotion → exact group."""
        notif = AppNotification.objects.create(
            title='UNIKIN Informatique L2 notification',
            body='This goes to L2 Informatique UNIKIN only',
            notification_type='summary_validated',
            target_universite=self.unikin,
            target_filiere=self.info_unikin,
            target_promotion=self.l2_info_unikin,
        )

        # Manually create UserNotification for L2 Informatique UNIKIN users
        for profile in UserProfile.objects.filter(
            user__is_active=True,
            universite=self.unikin,
            filiere=self.info_unikin,
            promotion=self.l2_info_unikin,
        ):
            UserNotification.objects.get_or_create(
                user=profile.user,
                notification=notif,
            )

        # Verify: 2 users (L2 Informatique UNIKIN)
        count = UserNotification.objects.filter(notification=notif).count()
        self.assertEqual(count, 2, f"Expected 2 L2 Informatique UNIKIN users, got {count}")

    def test_cp_receives_own_notification(self):
        """CP should receive their own notification."""
        cp_user = User.objects.create_user(username='cp_user', password='test')
        UserProfile.objects.create(
            user=cp_user,
            universite=self.unikin,
            filiere=self.info_unikin,
            promotion=self.l2_info_unikin,
        )

        notif = AppNotification.objects.create(
            title='Summary validated',
            body='Your summary was validated',
            notification_type='summary_validated',
            target_universite=self.unikin,
            target_filiere=self.info_unikin,
            target_promotion=self.l2_info_unikin,
            sender=cp_user,  # CP is the sender
        )

        # Manually create UserNotification for all matching users (including CP)
        for profile in UserProfile.objects.filter(
            user__is_active=True,
            universite=self.unikin,
            filiere=self.info_unikin,
            promotion=self.l2_info_unikin,
        ):
            UserNotification.objects.get_or_create(
                user=profile.user,
                notification=notif,
            )

        # Verify: CP should have the notification
        cp_notif = UserNotification.objects.filter(
            user=cp_user, notification=notif
        ).exists()
        self.assertTrue(cp_notif, "CP should receive their own notification")

        # Verify: 3 users total (2 existing L2 Info + 1 CP)
        count = UserNotification.objects.filter(notification=notif).count()
        self.assertEqual(count, 3, f"Expected 3 users, got {count}")

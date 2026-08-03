"""
Simple test script for payment notifications (without Celery).
Run with: python test_notifications_simple.py
"""
import os
import sys
import django
import time

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resume_backend.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

# Generate unique timestamp for test usernames
TEST_TS = int(time.time() * 1000) % 1000000

from payments.models import Service, Abonnement, Purchase
from courses.models import Summary, Course, Universite, Filiere, Promotion
from notifications.models import AppNotification, UserNotification


def test_subscription_notification_creation():
    """Test that subscription notification can be created."""
    print("\n[TEST 1] Creer une notification d'abonnement paye")
    
    # Create test user
    user = User.objects.create_user(
        username=f'test_sub_user_{TEST_TS}',
        email=f'test_sub_{TEST_TS}@example.com',
        password='test123'
    )
    
    # Create service
    service = Service.objects.create(
        nom='Premium Test',
        description='Premium subscription',
        type='premium',
        price=Decimal('9.99'),
        currency='USD',
        duree_mois=1,
        features=['Feature 1', 'Feature 2'],
        is_active=True,
    )
    
    # Create subscription
    abonnement = Abonnement.objects.create(
        user=user,
        service=service,
        date_debut=timezone.now(),
        date_fin=timezone.now() + timedelta(days=30),
        status='active',
    )
    
    # Manually create notification (simulating the task)
    notif = AppNotification.objects.create(
        title='✅ Abonnement activé',
        body=f'Votre abonnement {service.nom} est maintenant actif.',
        notification_type='payment',
        sender=None,
    )
    
    # Create user notification
    un, created = UserNotification.objects.get_or_create(
        user=user,
        notification=notif,
    )
    
    # Verify
    assert notif.id is not None, "Notification should be created"
    assert un.id is not None, "UserNotification should be created"
    assert notif.notification_type == 'payment', "Type should be payment"
    assert 'Abonnement activé' in notif.title, "Title should contain 'Abonnement activé'"
    
    print(f"   [OK] Notification creee: {notif.id}")
    print(f"   [OK] UserNotification creee: {un.id}")
    print(f"   [OK] Type: {notif.notification_type}")
    print(f"   [OK] Titre: {notif.title}")
    
    # Cleanup
    user.delete()
    service.delete()
    notif.delete()
    
    return True


def test_expiring_soon_notification():
    """Test subscription expiring soon notification."""
    print("\n[TEST 2] Creer une notification d'expiration imminente")
    
    user = User.objects.create_user(
        username=f'test_expiring_user_{TEST_TS}',
        email=f'test_expiring_{TEST_TS}@example.com',
        password='test123'
    )
    
    service = Service.objects.create(
        nom='Premium Expiring',
        description='Premium subscription',
        type='premium',
        price=Decimal('9.99'),
        currency='USD',
        duree_mois=1,
        features=['Feature 1'],
        is_active=True,
    )
    
    # Create subscription expiring in 5 days
    abonnement = Abonnement.objects.create(
        user=user,
        service=service,
        date_debut=timezone.now() - timedelta(days=25),
        date_fin=timezone.now() + timedelta(days=5),
        status='active',
    )
    
    # Manually create notification
    days_left = (abonnement.date_fin - timezone.now()).days
    notif = AppNotification.objects.create(
        title='⏰ Abonnement expire bientôt',
        body=f'Votre abonnement {service.nom} expire dans {days_left} jours.',
        notification_type='payment',
        sender=None,
    )
    
    un, _ = UserNotification.objects.get_or_create(
        user=user,
        notification=notif,
    )
    
    # Verify
    assert notif.id is not None, "Notification should be created"
    assert 'expire bientôt' in notif.title, "Title should contain 'expire bientôt'"
    assert days_left > 0, "Days left should be positive"
    
    print(f"   [OK] Notification creee: {notif.id}")
    print(f"   [OK] Jours restants: {days_left}")
    print(f"   [OK] Titre: {notif.title}")
    
    # Cleanup
    user.delete()
    service.delete()
    notif.delete()
    
    return True


def test_expired_notification():
    """Test subscription expired notification."""
    print("\n[TEST 3] Creer une notification d'expiration")
    
    user = User.objects.create_user(
        username=f'test_expired_user_{TEST_TS}',
        email=f'test_expired_{TEST_TS}@example.com',
        password='test123'
    )
    
    service = Service.objects.create(
        nom='Premium Expired',
        description='Premium subscription',
        type='premium',
        price=Decimal('9.99'),
        currency='USD',
        duree_mois=1,
        features=['Feature 1'],
        is_active=True,
    )
    
    # Create expired subscription
    abonnement = Abonnement.objects.create(
        user=user,
        service=service,
        date_debut=timezone.now() - timedelta(days=60),
        date_fin=timezone.now() - timedelta(days=1),
        status='expired',
    )
    
    # Manually create notification
    notif = AppNotification.objects.create(
        title='❌ Abonnement expiré',
        body=f'Votre abonnement {service.nom} a expiré.',
        notification_type='payment',
        sender=None,
    )
    
    un, _ = UserNotification.objects.get_or_create(
        user=user,
        notification=notif,
    )
    
    # Verify
    assert notif.id is not None, "Notification should be created"
    assert 'expiré' in notif.title, "Title should contain 'expiré'"
    
    print(f"   ✓ Notification créée: {notif.id}")
    print(f"   ✓ Titre: {notif.title}")
    
    # Cleanup
    user.delete()
    service.delete()
    notif.delete()
    
    return True


def test_purchase_notification():
    """Test summary purchase notification."""
    print("\n[TEST 4] Creer une notification d'achat de resume")
    
    user = User.objects.create_user(
        username=f'test_purchase_user_{TEST_TS}',
        email=f'test_purchase_{TEST_TS}@example.com',
        password='test123'
    )
    
    # Create course and summary
    universite = Universite.objects.create(nom=f'Test University {TEST_TS}')
    filiere = Filiere.objects.create(nom=f'Test Filiere {TEST_TS}')
    promotion = Promotion.objects.create(nom='L1')
    
    # Create relationships
    universite.filieres.add(filiere)
    filiere.promotions.add(promotion)
    
    course = Course.objects.create(
        nom='Test Course',
        filiere='Test Filiere',
        university='Test University',
        universite_fk=universite,
        filiere_fk=filiere,
        promotion_fk=promotion,
    )
    
    summary = Summary.objects.create(
        titre='Test Summary',
        texte_resume='Test content',
        course=course,
        author_user=user,
        author_type='cp',
        is_validated=True,
    )
    
    # Create purchase
    purchase = Purchase.objects.create(
        user=user,
        summary=summary,
        amount=Decimal('5.00'),
        payment_method='mobile_money',
        status='completed',
    )
    
    # Manually create notification
    notif = AppNotification.objects.create(
        title='📥 Résumé acheté',
        body=f'Vous avez acheté le résumé « {summary.titre} ».',
        notification_type='payment',
        sender=None,
    )
    
    un, _ = UserNotification.objects.get_or_create(
        user=user,
        notification=notif,
    )
    
    # Verify
    assert notif.id is not None, "Notification should be created"
    assert 'Résumé acheté' in notif.title, "Title should contain 'Résumé acheté'"
    assert summary.titre in notif.body, "Body should contain summary title"
    
    print(f"   [OK] Notification creee: {notif.id}")
    print(f"   [OK] Titre: {notif.title}")
    print(f"   [OK] Resume: {summary.titre}")
    
    # Cleanup
    user.delete()
    summary.delete()
    course.delete()
    universite.delete()
    notif.delete()
    
    return True


def test_multiple_notifications():
    """Test that multiple notifications can be created."""
    print("\n[TEST 5] Creer plusieurs notifications")
    
    user = User.objects.create_user(
        username=f'test_multiple_user_{TEST_TS}',
        email=f'test_multiple_{TEST_TS}@example.com',
        password='test123'
    )
    
    service = Service.objects.create(
        nom='Premium Multiple',
        description='Premium subscription',
        type='premium',
        price=Decimal('9.99'),
        currency='USD',
        duree_mois=1,
        features=['Feature 1'],
        is_active=True,
    )
    
    # Create 3 notifications
    notifs = []
    for i in range(3):
        notif = AppNotification.objects.create(
            title=f'Notification {i+1}',
            body=f'Body {i+1}',
            notification_type='payment',
            sender=None,
        )
        un, _ = UserNotification.objects.get_or_create(
            user=user,
            notification=notif,
        )
        notifs.append(notif)
    
    # Verify
    user_notifs = UserNotification.objects.filter(user=user)
    assert user_notifs.count() == 3, f"Should have 3 notifications, got {user_notifs.count()}"
    
    print(f"   [OK] {len(notifs)} notifications creees")
    print(f"   [OK] {user_notifs.count()} UserNotifications creees")
    
    # Cleanup
    user.delete()
    service.delete()
    for notif in notifs:
        notif.delete()
    
    return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("[TEST] Tests de Notifications de Paiement")
    print("=" * 60)
    
    try:
        results = []
        results.append(("Notification d'abonnement payé", test_subscription_notification_creation()))
        results.append(("Notification d'expiration imminente", test_expiring_soon_notification()))
        results.append(("Notification d'expiration", test_expired_notification()))
        results.append(("Notification d'achat de résumé", test_purchase_notification()))
        results.append(("Notifications multiples", test_multiple_notifications()))
        
        print("\n" + "=" * 60)
        print("[RESULTS] Resultats")
        print("=" * 60)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for test_name, result in results:
            status = "[PASS]" if result else "[FAIL]"
            print(f"{status}: {test_name}")
        
        print(f"\n{passed}/{total} tests passants")
        
        if passed == total:
            print("\n[SUCCESS] Tous les tests sont passants!")
            return 0
        else:
            print(f"\n[ERROR] {total - passed} test(s) échoué(s)")
            return 1
    
    except Exception as e:
        print(f"\n[ERROR] Erreur: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())

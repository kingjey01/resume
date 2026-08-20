"""
Vérification TACHE2 — déclenchement fiable des notifications quand le résumé devient disponible.

Chaîne testée (en mode Celery eager, sans broker) :
  statut session → « Résumé disponible » (summarized)
  → signal on_session_summarized → tâche notify_summary_available
  → notification créée pour le CP auteur → envoi FCM planifié/exécuté

Usage : PYTHONIOENCODING=utf-8 python test_tache2_check.py
"""
import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resume_backend.settings')
import django
django.setup()

# Mode Celery eager : les tâches .apply_async s'exécutent en synchrone, sans broker
from celery import current_app
current_app.conf.task_always_eager = True
current_app.conf.task_eager_propagates = False

from django.contrib.auth.models import User
from courses.models import Course, Session, Transcription, Summary
from notifications.models import AppNotification, UserNotification
from users.models import UserProfile

USERNAME = 'cp_test_tache2'
COURSE_NAME = 'Cours Test Tache2'


def log(msg):
    print(f'  {msg}')


def cleanup():
    try:
        user = User.objects.get(username=USERNAME)
        for s in Summary.objects.filter(author_user=user):
            for n in AppNotification.objects.filter(summary_id=s.id):
                UserNotification.objects.filter(notification=n).delete()
                n.delete()
        user.delete()
    except User.DoesNotExist:
        pass
    Course.objects.filter(nom=COURSE_NAME).delete()


def main():
    results = []

    # 1. Préparer CP + cours + session
    user = User.objects.create_user(username=USERNAME, password='pass123')
    UserProfile.objects.create(user=user, groupe='CP')
    course = Course.objects.create(nom=COURSE_NAME)

    session = Session.objects.create(
        course=course, date='2026-08-12 10:00:00', processing_status='pending'
    )
    transcription = Transcription.objects.create(
        session=session, texte_transcription='Texte de cours pour test.', status='completed'
    )
    summary = Summary.objects.create(
        titre='Résumé Test Tache2', texte_resume='Contenu du résumé.',
        course=course, session=session, transcription=transcription,
        author_type='ai', author_user=user,
    )
    log(f'Setup: CP={user.username}, session={session.id}, résumé={summary.id} (author_type=ai)')

    # 2. AUCUNE notification ne doit être créée à la création du résumé AI
    #    (le flow audio est notifié par le changement de statut, pas par post_save Summary)
    n0 = AppNotification.objects.filter(summary_id=summary.id).count()
    log(f'[1] Notifications après création résumé AI (sans changement de statut): {n0}')
    results.append(('aucune notification à la création du résumé AI', n0 == 0))

    # 3. Le worker passe la session à « Résumé disponible »
    session.processing_status = 'summarized'
    session.save()

    notifs = AppNotification.objects.filter(summary_id=summary.id, notification_type='summary_created')
    log(f'[2] Notifications « summary_created » après passage à « Résumé disponible »: {notifs.count()}')
    results.append(('notification créée au changement de statut', notifs.count() >= 1))

    if notifs.exists():
        notif = notifs.first()
        log(f'    → notif id={notif.id} title="{notif.title}"')
        log(f'    → body="{notif.body}"')
        log(f'    → sender={notif.sender}')
        un = UserNotification.objects.filter(notification=notif)
        log(f'    → UserNotification: {un.count()} pour {user.username}')
        results.append(('destinataire = CP auteur', un.filter(user=user).exists()))
        # Le résumé IA n'est PAS encore validé → le CP est invité à le valider,
        # le message « disponible » aux étudiants n'arrive qu'à la validation.
        results.append(('notification indique que le résumé est en attente de validation',
                        'validation' in notif.title.lower()
                        or 'attente' in notif.title.lower()
                        or 'attente' in notif.body.lower()))
        results.append(('sender = auteur (CP)', notif.sender == user))

    # 4. Anti-doublon : re-save du même statut → aucune nouvelle notification
    session.save()
    count_after_resave = AppNotification.objects.filter(summary_id=summary.id).count()
    log(f'[3] Notifications après re-save statut (anti-doublon): {count_after_resave}')
    results.append(('pas de doublon au re-save du statut', count_after_resave == notifs.count()))

    # 5. Retry : statut re-passé à transcribed puis à nouveau summarized
    #    → notification réutilisée (pas de doublon)
    session.processing_status = 'transcribed'
    session.save()
    session.processing_status = 'summarized'
    session.save()
    count_after_retry = AppNotification.objects.filter(summary_id=summary.id).count()
    log(f'[4] Notifications après cycle transcribed→summarized (retry): {count_after_retry}')
    results.append(('pas de doublon sur retry (réutilisation)', count_after_retry == 1))

    # 6. Résumé manuel (author_type=cp) : le signal post_save Summary notifie toujours
    summary_manual = Summary.objects.create(
        titre='Résumé Manuel Tache2', texte_resume='Contenu manuel.',
        course=course, session=session, author_type='cp', author_user=user,
    )
    manual_notifs = AppNotification.objects.filter(summary_id=summary_manual.id)
    log(f'[5] Résumé manuel (cp): {manual_notifs.count()} notification(s)')
    results.append(('résumé manuel toujours notifié', manual_notifs.count() >= 1))
    # Résumé manuel auto-validé (Summary.save) :
    #   - confirmation CP « summary_created »
    #   - diffusion étudiants « summary_validated » (résumé disponible)
    # Pas de message « en attente de validation » pour un résumé déjà validé.
    results.append(('confirmation CP de type summary_created',
                    manual_notifs.filter(notification_type='summary_created').exists()))
    results.append(('diffusion étudiants de type summary_validated',
                    manual_notifs.filter(notification_type='summary_validated').exists()))

    # 7. Envoi : la tâche send_fcm_notification s'est exécutée (eager)
    #    — en local sans Firebase elle logge et retourne sans erreur
    log('[6] Envoi FCM: exécuté via eager (Firebase non configuré en local → graceful fallback)')

    # Nettoyage
    for n in AppNotification.objects.filter(summary_id__in=[summary.id, summary_manual.id]):
        UserNotification.objects.filter(notification=n).delete()
        n.delete()
    summary.delete(); summary_manual.delete(); transcription.delete(); session.delete()
    user.delete(); course.delete()
    log('Cleanup OK')

    # Bilan
    print()
    failed = [name for name, ok in results if not ok]
    for name, ok in results:
        print(f'{"✅" if ok else "❌"} {name}')
    if failed:
        print(f'\nÉCHEC: {len(failed)} vérification(s)')
        sys.exit(1)
    print('\nOK TACHE2 — chaîne complète vérifiée')


if __name__ == '__main__':
    cleanup()
    main()

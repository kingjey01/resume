import 'package:flutter_test/flutter_test.dart';
import 'package:resume_plus_clean/services/audio_upload_service.dart';

/// Tâche 59 — la progression UI ne doit jamais confondre « en file » avec
/// « 0 % ». Ces tests verrouillent la traduction des états natifs.
void main() {
  group('phaseDepuisStatut', () {
    test('enqueued = en attente, jamais 0 %', () {
      expect(phaseDepuisStatut('enqueued'), AudioUploadPhase.queued);
    });

    test('running = envoi en cours', () {
      expect(phaseDepuisStatut('running'), AudioUploadPhase.uploading);
    });

    test('waitingToRetry et paused = reprise en attente', () {
      expect(phaseDepuisStatut('waitingToRetry'), AudioUploadPhase.queued);
      expect(phaseDepuisStatut('paused'), AudioUploadPhase.queued);
    });

    test('complete = confirmation serveur en cours', () {
      expect(phaseDepuisStatut('complete'), AudioUploadPhase.uploading);
    });

    test('failed/canceled ne concluent pas avant le repli Dio', () {
      expect(phaseDepuisStatut('failed'), isNull);
      expect(phaseDepuisStatut('canceled'), isNull);
      expect(phaseDepuisStatut('notFound'), isNull);
    });
  });

  group('AudioUploadSnapshot', () {
    test('un état en file est indéterminé et non un faux 0 %', () {
      const snapshot = AudioUploadSnapshot(
        draftId: 'd1',
        key: 'k1',
        phase: AudioUploadPhase.queued,
        message: 'En attente de démarrage…',
      );
      expect(snapshot.enCours, isTrue);
      expect(snapshot.progress, isNull);
    });

    test('interrompu = reprise possible', () {
      const snapshot = AudioUploadSnapshot(
        draftId: 'd1',
        key: 'k1',
        phase: AudioUploadPhase.interrupted,
        message: 'Envoi interrompu',
      );
      expect(snapshot.reprisePossible, isTrue);
      expect(snapshot.enCours, isFalse);
    });
  });
}

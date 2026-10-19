import 'dart:typed_data';

import 'package:flutter/foundation.dart';
import 'package:flutter/widgets.dart';
import 'package:resume_plus_clean/services/api_service.dart';
import 'package:resume_plus_clean/services/audio_draft_service.dart';

/// Phase réelle d'un envoi audio (tâche 59).
///
/// `queued` est important : une tâche WorkManager/URLSession peut être EN FILE
/// sans avoir commencé. L'UI doit alors afficher « en attente » avec une barre
/// indéterminée, et non un faux 0 %.
enum AudioUploadPhase {
  preparing,
  queued,
  uploading,
  completed,
  interrupted,
  failed,
}

/// Traduit un état natif (`TaskStatus.name`) en phase UI.
///
/// `failed`/`canceled`/`notFound` renvoient `null` : le repli Dio peut encore
/// réussir, et l'échec définitif est décidé par le `catch` de l'envoi.
@visibleForTesting
AudioUploadPhase? phaseDepuisStatut(String statut) {
  switch (statut) {
    case 'enqueued':
      return AudioUploadPhase.queued;
    case 'running':
      return AudioUploadPhase.uploading;
    case 'waitingToRetry':
    case 'paused':
      return AudioUploadPhase.queued;
    case 'complete':
      return AudioUploadPhase.uploading;
    default:
      return null;
  }
}

class AudioUploadSnapshot {
  final String draftId;
  final String key;
  final AudioUploadPhase phase;
  final double? progress; // 0..1, null = indéterminé
  final String message;
  final int? sessionId;

  const AudioUploadSnapshot({
    required this.draftId,
    required this.key,
    required this.phase,
    this.progress,
    required this.message,
    this.sessionId,
  });

  bool get enCours =>
      phase == AudioUploadPhase.preparing ||
      phase == AudioUploadPhase.queued ||
      phase == AudioUploadPhase.uploading;

  bool get reprisePossible =>
      phase == AudioUploadPhase.interrupted ||
      phase == AudioUploadPhase.failed;

  AudioUploadSnapshot copyWith({
    AudioUploadPhase? phase,
    double? progress,
    String? message,
    int? sessionId,
    bool progressIndetermine = false,
  }) {
    return AudioUploadSnapshot(
      draftId: draftId,
      key: key,
      phase: phase ?? this.phase,
      progress: progressIndetermine ? null : (progress ?? this.progress),
      message: message ?? this.message,
      sessionId: sessionId ?? this.sessionId,
    );
  }
}

/// Envoi audio indépendant du cycle de vie des widgets (tâche 59).
///
/// L'écran d'enregistrement peut être détruit à tout moment (retour, navigation,
/// application en arrière-plan). Le transfert, lui, doit continuer : il vit donc
/// ici, dans un singleton de durée applicative, et l'UI ne fait qu'observer
/// [active].
class AudioUploadService {
  AudioUploadService._();
  static final AudioUploadService instance = AudioUploadService._();

  final ApiService _api = ApiService();
  final AudioDraftService _drafts = AudioDraftService();

  /// Dernier état émis (pour l'écran qui se remonte après une navigation).
  final ValueNotifier<AudioUploadSnapshot?> active = ValueNotifier(null);

  final Map<String, AudioUploadSnapshot> _etats = {};
  final Map<String, Future<Map<String, dynamic>>> _enCours = {};

  AudioUploadSnapshot? etatPour(String? key) =>
      key == null ? null : _etats[key];

  void _emettre(AudioUploadSnapshot snapshot) {
    _etats[snapshot.key] = snapshot;
    active.value = snapshot;
  }

  /// Démarre (ou rejoint) l'envoi d'un brouillon.
  ///
  /// Le retour se complète avec la réponse serveur. Si l'écran disparaît, le
  /// future continue : le brouillon est confirmé/supprimé par ce service.
  Future<Map<String, dynamic>> demarrer({
    required AudioDraft draft,
    required Uint8List audioBytes,
    required String fileName,
    required String mimeType,
    required Map<String, dynamic> metadata,
    void Function(int sent, int total)? onProgress,
  }) {
    final key =
        draft.idempotenceKey ?? AudioDraftService.nouvelleCleIdempotence();
    final deja = _enCours[key];
    if (deja != null) return deja;

    final futur = _executer(
      draft: draft,
      key: key,
      audioBytes: audioBytes,
      fileName: fileName,
      mimeType: mimeType,
      metadata: metadata,
      onProgress: onProgress,
    );
    _enCours[key] = futur;
    futur.whenComplete(() => _enCours.remove(key));
    return futur;
  }

  Future<Map<String, dynamic>> _executer({
    required AudioDraft draft,
    required String key,
    required Uint8List audioBytes,
    required String fileName,
    required String mimeType,
    required Map<String, dynamic> metadata,
    void Function(int sent, int total)? onProgress,
  }) async {
    final observateur = _ObservateurArrierePlan();
    WidgetsBinding.instance.addObserver(observateur);

    var snapshot = AudioUploadSnapshot(
      draftId: draft.id,
      key: key,
      phase: AudioUploadPhase.preparing,
      message: 'Préparation de l\'envoi…',
    );
    _emettre(snapshot);

    try {
      await _drafts.setUploadState(draft.id, 'uploading');

      final response = await _api.uploadAudio(
        audioBytes: audioBytes,
        audioFilePath: draft.audioFilePath,
        fileName: fileName,
        mimeType: mimeType,
        metadata: metadata,
        idempotenceKey: key,
        onSendProgress: (sent, total) {
          final ratio = total > 0 ? sent / total : null;
          snapshot = snapshot.copyWith(
            phase: AudioUploadPhase.uploading,
            progress: ratio,
            message: 'Envoi en cours…',
            progressIndetermine: ratio == null,
          );
          _emettre(snapshot);
          onProgress?.call(sent, total);
        },
        onStatus: (statut) {
          final phase = phaseDepuisStatut(statut);
          if (phase == null) return;
          switch (statut) {
            case 'enqueued':
              snapshot = snapshot.copyWith(
                phase: phase,
                message: 'En attente de démarrage…',
                progressIndetermine: true,
              );
            case 'running':
              snapshot = snapshot.copyWith(
                phase: phase,
                message: 'Envoi en cours…',
                progressIndetermine: snapshot.progress == null,
              );
            case 'waitingToRetry':
            case 'paused':
              snapshot = snapshot.copyWith(
                phase: phase,
                message: 'Reprise du transfert…',
                progressIndetermine: true,
              );
            case 'complete':
              snapshot = snapshot.copyWith(
                phase: phase,
                progress: 1.0,
                message: 'Envoi terminé, confirmation du serveur…',
              );
          }
          _emettre(snapshot);
        },
      );

      final sessionId = response['session']?['id'];
      await _drafts.setUploadState(
        draft.id,
        'uploaded',
        sessionId: sessionId is int ? sessionId : null,
      );
      await _drafts.deleteDraft(draft.id);
      _emettre(snapshot.copyWith(
        phase: AudioUploadPhase.completed,
        progress: 1.0,
        message: 'Envoi terminé.',
        sessionId: sessionId is int ? sessionId : null,
      ));
      return response;
    } catch (_) {
      final interrompu = observateur.estPasseEnArrierePlan ||
          WidgetsBinding.instance.lifecycleState != AppLifecycleState.resumed;
      await _drafts.setUploadState(
        draft.id,
        interrompu ? 'pending' : 'failed',
      );
      _emettre(snapshot.copyWith(
        phase: interrompu
            ? AudioUploadPhase.interrupted
            : AudioUploadPhase.failed,
        message: interrompu
            ? 'Envoi interrompu — le fichier est conservé.'
            : 'L\'envoi a échoué.',
      ));
      rethrow;
    } finally {
      WidgetsBinding.instance.removeObserver(observateur);
    }
  }
}

class _ObservateurArrierePlan with WidgetsBindingObserver {
  bool estPasseEnArrierePlan = false;

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.paused ||
        state == AppLifecycleState.inactive) {
      estPasseEnArrierePlan = true;
    }
  }
}

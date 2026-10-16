import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:flutter_foreground_task/flutter_foreground_task.dart';

/// Maintient l'application vivante pendant un enregistrement ou un envoi.
///
/// POURQUOI (tâche 40) — ET POURQUOI C'EST ANDROID SEULEMENT :
///
/// Android retire l'accès au microphone aux applications en arrière-plan depuis
/// Android 9, et peut geler leur processus — l'envoi en cours meurt alors avec
/// lui. Un SERVICE DE PREMIER PLAN, signalé par une notification persistante,
/// est la voie prévue par la plateforme : le processus reste vivant, le micro
/// reste accessible, et l'envoi se poursuit.
///
/// iOS n'a PAS d'équivalent, et n'en a pas besoin : le mode audio déclaré dans
/// `Info.plist` (`UIBackgroundModes`) suffit à maintenir l'application vivante
/// pendant un enregistrement. Toutes les méthodes ci-dessous sont donc sans
/// effet sur iOS et sur le web.
///
/// CE SERVICE NE FAIT AUCUN TRAVAIL. C'est sa simple existence qui compte :
/// l'enregistreur et l'envoi vivent dans l'isolate principal et continuent
/// d'y tourner tant que le processus est vivant.

/// Point d'entrée de l'isolate du service. Le paquet l'exige ; il n'enregistre
/// qu'un gestionnaire vide.
@pragma('vm:entry-point')
void pointEntreeService() {
  FlutterForegroundTask.setTaskHandler(_TacheSansTravail());
}

class _TacheSansTravail extends TaskHandler {
  @override
  Future<void> onStart(DateTime timestamp, TaskStarter starter) async {}

  @override
  Future<void> onRepeatEvent(DateTime timestamp) async {}

  @override
  Future<void> onDestroy(DateTime timestamp, bool isTimeout) async {}
}

class BackgroundTaskService {
  BackgroundTaskService._();

  static bool _initialise = false;

  /// Android uniquement : voir l'explication en tête de fichier.
  static bool get _concerneCettePlateforme => !kIsWeb && Platform.isAndroid;

  static void _initialiser() {
    if (_initialise) return;
    FlutterForegroundTask.init(
      androidNotificationOptions: AndroidNotificationOptions(
        channelId: 'muhtasari_arriere_plan',
        channelName: 'Enregistrement et envoi',
        channelDescription:
            "Maintient l'enregistrement et l'envoi en cours lorsque "
            "l'application passe en arrière-plan ou que le téléphone est "
            'verrouillé.',
        onlyAlertOnce: true,
      ),
      // Rien à afficher côté iOS : le mode audio s'en charge, sans notification.
      iosNotificationOptions: const IOSNotificationOptions(
        showNotification: false,
        playSound: false,
      ),
      foregroundTaskOptions: ForegroundTaskOptions(
        // Aucun travail périodique : le service ne fait que maintenir le
        // processus vivant.
        eventAction: ForegroundTaskEventAction.nothing(),
        allowWakeLock: true,
        allowWifiLock: true,
      ),
    );
    _initialise = true;
  }

  /// Démarre le service, ou met à jour sa notification s'il tourne déjà.
  ///
  /// NE FAIT JAMAIS ÉCHOUER L'APPELANT : le service est un confort, pas une
  /// condition. S'il ne démarre pas — permission refusée, version d'Android
  /// récalcitrante — l'enregistrement et l'envoi continuent exactement comme
  /// avant, simplement sans la garantie d'arrière-plan.
  static Future<void> demarrer({
    required String titre,
    required String texte,
  }) async {
    if (!_concerneCettePlateforme) return;
    try {
      _initialiser();
      if (await FlutterForegroundTask.isRunningService) {
        await FlutterForegroundTask.updateService(
          notificationTitle: titre,
          notificationText: texte,
        );
        return;
      }
      await FlutterForegroundTask.startService(
        serviceId: 400,
        // `microphone` : l'accès au micro doit être déclaré au service depuis
        // Android 14, sinon l'enregistrement s'arrête en arrière-plan.
        // `dataSync` : l'envoi du fichier.
        serviceTypes: const [
          ForegroundServiceTypes.microphone,
          ForegroundServiceTypes.dataSync,
        ],
        notificationTitle: titre,
        notificationText: texte,
        callback: pointEntreeService,
      );
    } catch (e) {
      debugPrint('⚠️ Service de premier plan indisponible : $e');
    }
  }

  /// Arrête le service. Sans effet s'il ne tourne pas.
  static Future<void> arreter() async {
    if (!_concerneCettePlateforme) return;
    try {
      if (await FlutterForegroundTask.isRunningService) {
        await FlutterForegroundTask.stopService();
      }
    } catch (e) {
      debugPrint('⚠️ Arrêt du service de premier plan impossible : $e');
    }
  }
}

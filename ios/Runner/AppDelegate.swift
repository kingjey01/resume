import Flutter
import UIKit
import FirebaseCore

@main
@objc class AppDelegate: FlutterAppDelegate {
  override func application(
    _ application: UIApplication,
    didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]?
  ) -> Bool {
    FirebaseApp.configure()
    if #available(iOS 10.0, *) {
      UNUserNotificationCenter.current().delegate = self as UNUserNotificationCenterDelegate
    }

    // Channel pour le badge sur l'icône
    // NB: on utilise le binaryMessenger du FlutterViewController.
    // self.registrar(forPlugin:) retournerait nil (aucun plugin "BadgePlugin")
    // et le force-unwrap ferait CRASHER l'app au lancement.
    guard let controller = window?.rootViewController as? FlutterViewController else {
      return super.application(application, didFinishLaunchingWithOptions: launchOptions)
    }
    let badgeChannel = FlutterMethodChannel(
      name: "resume_plus/badge",
      binaryMessenger: controller.binaryMessenger
    )

    badgeChannel.setMethodCallHandler { (call, result) in
      switch call.method {
      case "isSupported":
        result(true)
      case "setBadge":
        if let args = call.arguments as? [String: Any],
           let count = args["count"] as? Int {
          DispatchQueue.main.async {
            UIApplication.shared.applicationIconBadgeNumber = count
          }
          result(true)
        } else {
          result(FlutterError(code: "INVALID_ARGS", message: "count required", details: nil))
        }
      case "removeBadge":
        DispatchQueue.main.async {
          UIApplication.shared.applicationIconBadgeNumber = 0
        }
        result(true)
      default:
        result(FlutterMethodNotImplemented)
      }
    }

    GeneratedPluginRegistrant.register(with: self)
    return super.application(application, didFinishLaunchingWithOptions: launchOptions)
  }
}

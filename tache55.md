. Nous devons maintenant activer les capacités push dans le projet Xcode et préparer le code Flutter.

Objectifs :

S'assurer que le fichier GoogleService-Info.plist est correctement placé et référencé.

Activer les capacités "Push Notifications" et "Background Modes" dans le fichier project.pbxproj.

Ajouter le code Dart minimal pour l'initialisation de FCM et la demande de permission.

🛠️ Actions à exécuter
1. Intégration du fichier GoogleService-Info.plist

Vérifier que le fichier GoogleService-Info.plist (fourni par l'utilisateur) est présent dans le dossier ios/Runner/.

Ouvrir ios/Runner.xcodeproj/project.pbxproj.

Chercher la section PBXResourcesBuildPhase pour le target Runner.

S'assurer que la ligne GoogleService-Info.plist in Resources y est présente. Si elle manque, l'ajouter manuellement avec un identifiant unique (ex: A1B2C3D4E5F6G7H8I9J0K1L2).

2. Activation des capacités dans project.pbxproj

Chercher la section SystemCapabilities dans project.pbxproj. Si elle n'existe pas, la créer.

Ajouter les deux entrées suivantes :

xml
SystemCapabilities = {
    com.apple.Push = {
        enabled = 1;
    };
    com.apple.BackgroundModes = {
        enabled = 1;
    };
};
Chercher la section buildSettings pour le target Runner. Ajouter la clé CODE_SIGN_ENTITLEMENTS = Runner/Runner.entitlements;.

Créer le fichier ios/Runner/Runner.entitlements s'il n'existe pas, avec le contenu suivant :

xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>aps-environment</key>
    <string>development</string>
</dict>
</plist>
(Note : pour le build de distribution via Codemagic, Apple gérera automatiquement le passage en production si le profil est de type App Store).

3. Ajout du code Dart pour FCM

Ouvrir lib/main.dart.

Ajouter les imports nécessaires (firebase_core, firebase_messaging).

Dans la fonction main(), avant runApp(), ajouter :

dart
WidgetsFlutterBinding.ensureInitialized();
await Firebase.initializeApp();
Créer une fonction setupFCM() (ou l'ajouter à l'initialisation) pour demander les permissions :

dart
final messaging = FirebaseMessaging.instance;
await messaging.requestPermission(
  alert: true,
  announcement: false,
  badge: true,
  carPlay: false,
  criticalAlert: false,
  provisional: false,
  sound: true,
);
S'assurer que le token APNs est bien récupéré (utile pour le débogage) :

dart
String? apnsToken = await messaging.getAPNSToken();
print('APNs Token: $apnsToken');
4. Mise à jour de codemagic.yaml

Vérifier que le fichier GoogleService-Info.plist est bien pris en compte (s'il est commité, c'est bon).

Si le fichier Runner.entitlements est créé, s'assurer qu'il est également commité.


NB: s'il manque un coté dont j'ai pas pu couvrir ou te dire de faire , fais ton analyse et complete le pour que tout soit bon et fonctionnel.
📝 Compte rendu attendu
À la fin de ces modifications, génère un rapport listant :

Le fichier project.pbxproj a-t-il été modifié avec succès (les 2 capacités sont-elles présentes) ?

Le fichier Runner.entitlements a-t-il été créé ?

Le fichier GoogleService-Info.plist est-il bien référencé dans les ressources ?

Le code Dart (main.dart) a-t-il été mis à jour avec l'initialisation Firebase ?

Y a-t-il des conflits ou des erreurs détectées ?


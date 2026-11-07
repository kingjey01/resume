#!/usr/bin/env bash

set -o pipefail

# Xcode 26 active les modules Swift explicites par défaut ; les pods
# Flutter ne les gèrent pas encore (même réglage dans ios/Podfile).
export SWIFT_ENABLE_EXPLICIT_MODULES=NO

mkdir -p /tmp/xcodebuild_logs
LOG_FILE="/tmp/xcodebuild_logs/codemagic-build-ipa-console.log"

set +e
xcode-project build-ipa \
  --workspace ios/Runner.xcworkspace \
  --scheme Runner 2>&1 | tee "$LOG_FILE"
statut=${PIPESTATUS[0]}
set -e

if [ "$statut" -ne 0 ]; then
  # LE DÉTAIL N'EST PAS DANS LA CONSOLE, ET C'EST TOUT LE PROBLÈME.
  # `xcode-project` n'affiche que ses grandes étapes ; l'erreur de
  # compilation, elle, part dans ses propres journaux sous
  # /tmp/xcodebuild_logs/. Sans ce bloc, un échec d'archive tient en
  # trois lignes — « Failed to archive » — sans dire pourquoi, et il
  # faut relancer un build entier pour apprendre quelque chose.
  echo "===== xcodebuild a échoué (code $statut) — détail ci-dessous ====="
  ls -la /tmp/xcodebuild_logs
  for journal in /tmp/xcodebuild_logs/*.log; do
    [ "$journal" = "$LOG_FILE" ] && continue
    echo "----- $journal : 250 dernières lignes -----"
    tail -250 "$journal"
  done
  exit "$statut"
fi

# CE QUE LE BINAIRE CONTIENT RÉELLEMENT. Un Info.plist correct dans le
# dépôt ne prouve rien : c'est le seul contrôle qui compte, et il a
# fallu un plantage au lancement pour s'en rendre compte (voir
# GoogleService-Info.plist). On lit donc l'Info.plist EMBARQUÉ dans
# l'IPA, pas celui du dépôt.
ipa=$(ls build/ios/ipa/*.ipa 2>/dev/null | head -1)
if [ -n "$ipa" ]; then
  echo "=== Info.plist embarque dans $(basename "$ipa") ==="
  unzip -p "$ipa" "Payload/Runner.app/Info.plist" | plutil -p - \
    | grep -E "UsageDescription|ITSAppUsesNonExemptEncryption|UIRequiresFullScreen" || true
  echo "=== fichiers embarques (extrait) ==="
  unzip -l "$ipa" | grep -E "GoogleService|Runner.app/Info.plist" || true
else
  echo "AVERTISSEMENT: aucun IPA trouve pour verifier son contenu."
fi
Using Xcode 26.6 (17F113)
Check Runner.xcworkspace build settings
Execute "xcodebuild -workspace ios/Runner.xcworkspace -scheme Runner -showBuildSettings"

Archive Runner.xcworkspace
Execute "xcodebuild -workspace ios/Runner.xcworkspace -scheme Runner -archivePath /Users/builder/clone/build/ios/xcarchive/Runner_iymr5i69.xcarchive archive COMPILER_INDEX_STORE_ENABLE=NO DEVELOPMENT_TEAM=458794274R 'CODE_SIGN_IDENTITY=Apple Distribution' CODE_SIGN_STYLE=Manual"

Failed to archive ios/Runner.xcworkspace
===== xcodebuild a échoué (code 65) — détail ci-dessous =====
total 272
drwxr-xr-x  4 builder  wheel    128 Oct 17 22:48 .
drwxrwxrwt  4 root     wheel    128 Oct 17 22:47 ..
-rw-r--r--  1 builder  wheel    551 Oct 17 22:48 codemagic-build-ipa-console.log
-rw-r--r--  1 builder  wheel  83435 Oct 17 22:48 Runner.log
----- /tmp/xcodebuild_logs/Runner.log : 250 dernières lignes -----
        ➜ Implicit dependency on target 'FirebaseInstallations' in project 'Pods' via options '-framework FirebaseInstallations' in build setting 'OTHER_LDFLAGS'
        ➜ Implicit dependency on target 'FirebaseMessaging' in project 'Pods' via options '-framework FirebaseMessaging' in build setting 'OTHER_LDFLAGS'
        ➜ Implicit dependency on target 'GoogleDataTransport' in project 'Pods' via options '-framework GoogleDataTransport' in build setting 'OTHER_LDFLAGS'
        ➜ Implicit dependency on target 'GoogleUtilities' in project 'Pods' via options '-framework GoogleUtilities' in build setting 'OTHER_LDFLAGS'
        ➜ Implicit dependency on target 'SDWebImage' in project 'Pods' via options '-framework SDWebImage' in build setting 'OTHER_LDFLAGS'
        ➜ Implicit dependency on target 'ScreenProtectorKit' in project 'Pods' via options '-framework ScreenProtectorKit' in build setting 'OTHER_LDFLAGS'
        ➜ Implicit dependency on target 'SwiftyGif' in project 'Pods' via options '-framework SwiftyGif' in build setting 'OTHER_LDFLAGS'
        ➜ Implicit dependency on target 'audioplayers_darwin' in project 'Pods' via options '-framework audioplayers_darwin' in build setting 'OTHER_LDFLAGS'
        ➜ Implicit dependency on target 'background_downloader' in project 'Pods' via options '-framework background_downloader' in build setting 'OTHER_LDFLAGS'
        ➜ Implicit dependency on target 'connectivity_plus' in project 'Pods' via options '-framework connectivity_plus' in build setting 'OTHER_LDFLAGS'
        ➜ Implicit dependency on target 'file_picker' in project 'Pods' via options '-framework file_picker' in build setting 'OTHER_LDFLAGS'
        ➜ Implicit dependency on target 'firebase_core' in project 'Pods' via options '-framework firebase_core' in build setting 'OTHER_LDFLAGS'
        ➜ Implicit dependency on target 'firebase_messaging' in project 'Pods' via options '-framework firebase_messaging' in build setting 'OTHER_LDFLAGS'
        ➜ Implicit dependency on target 'flutter_foreground_task' in project 'Pods' via options '-framework flutter_foreground_task' in build setting 'OTHER_LDFLAGS'
        ➜ Implicit dependency on target 'flutter_local_notifications' in project 'Pods' via options '-framework flutter_local_notifications' in build setting 'OTHER_LDFLAGS'
        ➜ Implicit dependency on target 'flutter_secure_storage' in project 'Pods' via options '-framework flutter_secure_storage' in build setting 'OTHER_LDFLAGS'
        ➜ Implicit dependency on target 'flutter_tts' in project 'Pods' via options '-framework flutter_tts' in build setting 'OTHER_LDFLAGS'
        ➜ Implicit dependency on target 'image_picker_ios' in project 'Pods' via options '-framework image_picker_ios' in build setting 'OTHER_LDFLAGS'
        ➜ Implicit dependency on target 'integration_test' in project 'Pods' via options '-framework integration_test' in build setting 'OTHER_LDFLAGS'
        ➜ Implicit dependency on target 'nanopb' in project 'Pods' via options '-framework nanopb' in build setting 'OTHER_LDFLAGS'
        ➜ Implicit dependency on target 'package_info_plus' in project 'Pods' via options '-framework package_info_plus' in build setting 'OTHER_LDFLAGS'
        ➜ Implicit dependency on target 'path_provider_foundation' in project 'Pods' via options '-framework path_provider_foundation' in build setting 'OTHER_LDFLAGS'
        ➜ Implicit dependency on target 'permission_handler_apple' in project 'Pods' via options '-framework permission_handler_apple' in build setting 'OTHER_LDFLAGS'
        ➜ Implicit dependency on target 'record_darwin' in project 'Pods' via options '-framework record_darwin' in build setting 'OTHER_LDFLAGS'
        ➜ Implicit dependency on target 'screen_protector' in project 'Pods' via options '-framework screen_protector' in build setting 'OTHER_LDFLAGS'
        ➜ Implicit dependency on target 'shared_preferences_foundation' in project 'Pods' via options '-framework shared_preferences_foundation' in build setting 'OTHER_LDFLAGS'
        ➜ Implicit dependency on target 'sqflite_darwin' in project 'Pods' via options '-framework sqflite_darwin' in build setting 'OTHER_LDFLAGS'
        ➜ Implicit dependency on target 'url_launcher_ios' in project 'Pods' via options '-framework url_launcher_ios' in build setting 'OTHER_LDFLAGS'
    Target 'Pods-Runner' in project 'Pods'
        ➜ Explicit dependency on target 'DKImagePickerController' in project 'Pods'
        ➜ Explicit dependency on target 'DKPhotoGallery' in project 'Pods'
        ➜ Explicit dependency on target 'Firebase' in project 'Pods'
        ➜ Explicit dependency on target 'FirebaseCore' in project 'Pods'
        ➜ Explicit dependency on target 'FirebaseCoreInternal' in project 'Pods'
        ➜ Explicit dependency on target 'FirebaseInstallations' in project 'Pods'
        ➜ Explicit dependency on target 'FirebaseMessaging' in project 'Pods'
        ➜ Explicit dependency on target 'Flutter' in project 'Pods'
        ➜ Explicit dependency on target 'GoogleDataTransport' in project 'Pods'
        ➜ Explicit dependency on target 'GoogleUtilities' in project 'Pods'
        ➜ Explicit dependency on target 'PromisesObjC' in project 'Pods'
        ➜ Explicit dependency on target 'SDWebImage' in project 'Pods'
        ➜ Explicit dependency on target 'ScreenProtectorKit' in project 'Pods'
        ➜ Explicit dependency on target 'SwiftyGif' in project 'Pods'
        ➜ Explicit dependency on target 'audioplayers_darwin' in project 'Pods'
        ➜ Explicit dependency on target 'background_downloader' in project 'Pods'
        ➜ Explicit dependency on target 'connectivity_plus' in project 'Pods'
        ➜ Explicit dependency on target 'file_picker' in project 'Pods'
        ➜ Explicit dependency on target 'firebase_core' in project 'Pods'
        ➜ Explicit dependency on target 'firebase_messaging' in project 'Pods'
        ➜ Explicit dependency on target 'flutter_foreground_task' in project 'Pods'
        ➜ Explicit dependency on target 'flutter_local_notifications' in project 'Pods'
        ➜ Explicit dependency on target 'flutter_secure_storage' in project 'Pods'
        ➜ Explicit dependency on target 'flutter_tts' in project 'Pods'
        ➜ Explicit dependency on target 'image_picker_ios' in project 'Pods'
        ➜ Explicit dependency on target 'integration_test' in project 'Pods'
        ➜ Explicit dependency on target 'nanopb' in project 'Pods'
        ➜ Explicit dependency on target 'package_info_plus' in project 'Pods'
        ➜ Explicit dependency on target 'path_provider_foundation' in project 'Pods'
        ➜ Explicit dependency on target 'permission_handler_apple' in project 'Pods'
        ➜ Explicit dependency on target 'record_darwin' in project 'Pods'
        ➜ Explicit dependency on target 'screen_protector' in project 'Pods'
        ➜ Explicit dependency on target 'shared_preferences_foundation' in project 'Pods'
        ➜ Explicit dependency on target 'sqflite_darwin' in project 'Pods'
        ➜ Explicit dependency on target 'url_launcher_ios' in project 'Pods'
    Target 'url_launcher_ios' in project 'Pods'
        ➜ Explicit dependency on target 'Flutter' in project 'Pods'
        ➜ Explicit dependency on target 'url_launcher_ios-url_launcher_ios_privacy' in project 'Pods'
    Target 'url_launcher_ios-url_launcher_ios_privacy' in project 'Pods' (no dependencies)
    Target 'sqflite_darwin' in project 'Pods'
        ➜ Explicit dependency on target 'Flutter' in project 'Pods'
        ➜ Explicit dependency on target 'sqflite_darwin-sqflite_darwin_privacy' in project 'Pods'
    Target 'sqflite_darwin-sqflite_darwin_privacy' in project 'Pods' (no dependencies)
    Target 'shared_preferences_foundation' in project 'Pods'
        ➜ Explicit dependency on target 'Flutter' in project 'Pods'
        ➜ Explicit dependency on target 'shared_preferences_foundation-shared_preferences_foundation_privacy' in project 'Pods'
    Target 'shared_preferences_foundation-shared_preferences_foundation_privacy' in project 'Pods' (no dependencies)
    Target 'screen_protector' in project 'Pods'
        ➜ Explicit dependency on target 'Flutter' in project 'Pods'
        ➜ Explicit dependency on target 'ScreenProtectorKit' in project 'Pods'
    Target 'record_darwin' in project 'Pods'
        ➜ Explicit dependency on target 'Flutter' in project 'Pods'
        ➜ Explicit dependency on target 'record_darwin-record_darwin_privacy' in project 'Pods'
    Target 'record_darwin-record_darwin_privacy' in project 'Pods' (no dependencies)
    Target 'permission_handler_apple' in project 'Pods'
        ➜ Explicit dependency on target 'Flutter' in project 'Pods'
        ➜ Explicit dependency on target 'permission_handler_apple-permission_handler_apple_privacy' in project 'Pods'
    Target 'permission_handler_apple-permission_handler_apple_privacy' in project 'Pods' (no dependencies)
    Target 'path_provider_foundation' in project 'Pods'
        ➜ Explicit dependency on target 'Flutter' in project 'Pods'
        ➜ Explicit dependency on target 'path_provider_foundation-path_provider_foundation_privacy' in project 'Pods'
    Target 'path_provider_foundation-path_provider_foundation_privacy' in project 'Pods' (no dependencies)
    Target 'package_info_plus' in project 'Pods'
        ➜ Explicit dependency on target 'Flutter' in project 'Pods'
        ➜ Explicit dependency on target 'package_info_plus-package_info_plus_privacy' in project 'Pods'
    Target 'package_info_plus-package_info_plus_privacy' in project 'Pods' (no dependencies)
    Target 'integration_test' in project 'Pods'
        ➜ Explicit dependency on target 'Flutter' in project 'Pods'
    Target 'image_picker_ios' in project 'Pods'
        ➜ Explicit dependency on target 'Flutter' in project 'Pods'
        ➜ Explicit dependency on target 'image_picker_ios-image_picker_ios_privacy' in project 'Pods'
    Target 'image_picker_ios-image_picker_ios_privacy' in project 'Pods' (no dependencies)
    Target 'flutter_tts' in project 'Pods'
        ➜ Explicit dependency on target 'Flutter' in project 'Pods'
    Target 'flutter_secure_storage' in project 'Pods'
        ➜ Explicit dependency on target 'Flutter' in project 'Pods'
        ➜ Explicit dependency on target 'flutter_secure_storage-flutter_secure_storage' in project 'Pods'
    Target 'flutter_secure_storage-flutter_secure_storage' in project 'Pods' (no dependencies)
    Target 'flutter_local_notifications' in project 'Pods'
        ➜ Explicit dependency on target 'Flutter' in project 'Pods'
        ➜ Explicit dependency on target 'flutter_local_notifications-flutter_local_notifications_privacy' in project 'Pods'
    Target 'flutter_local_notifications-flutter_local_notifications_privacy' in project 'Pods' (no dependencies)
    Target 'flutter_foreground_task' in project 'Pods'
        ➜ Explicit dependency on target 'Flutter' in project 'Pods'
    Target 'firebase_messaging' in project 'Pods'
        ➜ Explicit dependency on target 'Firebase' in project 'Pods'
        ➜ Explicit dependency on target 'Flutter' in project 'Pods'
        ➜ Explicit dependency on target 'firebase_core' in project 'Pods'
        ➜ Explicit dependency on target 'firebase_messaging-firebase_messaging_Privacy' in project 'Pods'
    Target 'firebase_messaging-firebase_messaging_Privacy' in project 'Pods' (no dependencies)
    Target 'firebase_core' in project 'Pods'
        ➜ Explicit dependency on target 'Firebase' in project 'Pods'
        ➜ Explicit dependency on target 'Flutter' in project 'Pods'
    Target 'file_picker' in project 'Pods'
        ➜ Explicit dependency on target 'DKImagePickerController' in project 'Pods'
        ➜ Explicit dependency on target 'Flutter' in project 'Pods'
        ➜ Explicit dependency on target 'file_picker-file_picker_ios_privacy' in project 'Pods'
    Target 'file_picker-file_picker_ios_privacy' in project 'Pods'
        ➜ Implicit dependency on target 'DKImagePickerController' in project 'Pods' via options '-framework DKImagePickerController' in build setting 'OTHER_LDFLAGS'
    Target 'connectivity_plus' in project 'Pods'
        ➜ Explicit dependency on target 'Flutter' in project 'Pods'
        ➜ Explicit dependency on target 'connectivity_plus-connectivity_plus_privacy' in project 'Pods'
    Target 'connectivity_plus-connectivity_plus_privacy' in project 'Pods' (no dependencies)
    Target 'background_downloader' in project 'Pods'
        ➜ Explicit dependency on target 'Flutter' in project 'Pods'
        ➜ Explicit dependency on target 'background_downloader-background_downloader_privacy' in project 'Pods'
    Target 'background_downloader-background_downloader_privacy' in project 'Pods' (no dependencies)
    Target 'audioplayers_darwin' in project 'Pods'
        ➜ Explicit dependency on target 'Flutter' in project 'Pods'
    Target 'ScreenProtectorKit' in project 'Pods' (no dependencies)
    Target 'Flutter' in project 'Pods' (no dependencies)
    Target 'Firebase' in project 'Pods'
        ➜ Explicit dependency on target 'FirebaseCore' in project 'Pods'
        ➜ Explicit dependency on target 'FirebaseMessaging' in project 'Pods'
    Target 'FirebaseMessaging' in project 'Pods'
        ➜ Explicit dependency on target 'FirebaseCore' in project 'Pods'
        ➜ Explicit dependency on target 'FirebaseInstallations' in project 'Pods'
        ➜ Explicit dependency on target 'FirebaseMessaging-FirebaseMessaging_Privacy' in project 'Pods'
        ➜ Explicit dependency on target 'GoogleDataTransport' in project 'Pods'
        ➜ Explicit dependency on target 'GoogleUtilities' in project 'Pods'
        ➜ Explicit dependency on target 'nanopb' in project 'Pods'
    Target 'FirebaseMessaging-FirebaseMessaging_Privacy' in project 'Pods'
        ➜ Implicit dependency on target 'FirebaseCore' in project 'Pods' via options '-framework FirebaseCore' in build setting 'OTHER_LDFLAGS'
        ➜ Implicit dependency on target 'FirebaseInstallations' in project 'Pods' via options '-framework FirebaseInstallations' in build setting 'OTHER_LDFLAGS'
        ➜ Implicit dependency on target 'GoogleDataTransport' in project 'Pods' via options '-framework GoogleDataTransport' in build setting 'OTHER_LDFLAGS'
        ➜ Implicit dependency on target 'GoogleUtilities' in project 'Pods' via options '-framework GoogleUtilities' in build setting 'OTHER_LDFLAGS'
        ➜ Implicit dependency on target 'nanopb' in project 'Pods' via options '-framework nanopb' in build setting 'OTHER_LDFLAGS'
    Target 'GoogleDataTransport' in project 'Pods'
        ➜ Explicit dependency on target 'GoogleDataTransport-GoogleDataTransport_Privacy' in project 'Pods'
        ➜ Explicit dependency on target 'PromisesObjC' in project 'Pods'
        ➜ Explicit dependency on target 'nanopb' in project 'Pods'
    Target 'GoogleDataTransport-GoogleDataTransport_Privacy' in project 'Pods'
        ➜ Implicit dependency on target 'PromisesObjC' in project 'Pods' via options '-framework FBLPromises' in build setting 'OTHER_LDFLAGS'
        ➜ Implicit dependency on target 'nanopb' in project 'Pods' via options '-framework nanopb' in build setting 'OTHER_LDFLAGS'
    Target 'nanopb' in project 'Pods'
        ➜ Explicit dependency on target 'nanopb-nanopb_Privacy' in project 'Pods'
    Target 'nanopb-nanopb_Privacy' in project 'Pods' (no dependencies)
    Target 'FirebaseInstallations' in project 'Pods'
        ➜ Explicit dependency on target 'FirebaseCore' in project 'Pods'
        ➜ Explicit dependency on target 'FirebaseInstallations-FirebaseInstallations_Privacy' in project 'Pods'
        ➜ Explicit dependency on target 'GoogleUtilities' in project 'Pods'
        ➜ Explicit dependency on target 'PromisesObjC' in project 'Pods'
    Target 'FirebaseInstallations-FirebaseInstallations_Privacy' in project 'Pods'
        ➜ Implicit dependency on target 'PromisesObjC' in project 'Pods' via options '-framework FBLPromises' in build setting 'OTHER_LDFLAGS'
        ➜ Implicit dependency on target 'FirebaseCore' in project 'Pods' via options '-framework FirebaseCore' in build setting 'OTHER_LDFLAGS'
        ➜ Implicit dependency on target 'GoogleUtilities' in project 'Pods' via options '-framework GoogleUtilities' in build setting 'OTHER_LDFLAGS'
    Target 'PromisesObjC' in project 'Pods'
        ➜ Explicit dependency on target 'PromisesObjC-FBLPromises_Privacy' in project 'Pods'
    Target 'PromisesObjC-FBLPromises_Privacy' in project 'Pods' (no dependencies)
    Target 'FirebaseCore' in project 'Pods'
        ➜ Explicit dependency on target 'FirebaseCore-FirebaseCore_Privacy' in project 'Pods'
        ➜ Explicit dependency on target 'FirebaseCoreInternal' in project 'Pods'
        ➜ Explicit dependency on target 'GoogleUtilities' in project 'Pods'
    Target 'FirebaseCore-FirebaseCore_Privacy' in project 'Pods'
        ➜ Implicit dependency on target 'FirebaseCoreInternal' in project 'Pods' via options '-framework FirebaseCoreInternal' in build setting 'OTHER_LDFLAGS'
        ➜ Implicit dependency on target 'GoogleUtilities' in project 'Pods' via options '-framework GoogleUtilities' in build setting 'OTHER_LDFLAGS'
    Target 'FirebaseCoreInternal' in project 'Pods'
        ➜ Explicit dependency on target 'FirebaseCoreInternal-FirebaseCoreInternal_Privacy' in project 'Pods'
        ➜ Explicit dependency on target 'GoogleUtilities' in project 'Pods'
    Target 'FirebaseCoreInternal-FirebaseCoreInternal_Privacy' in project 'Pods'
        ➜ Implicit dependency on target 'GoogleUtilities' in project 'Pods' via options '-framework GoogleUtilities' in build setting 'OTHER_LDFLAGS'
    Target 'GoogleUtilities' in project 'Pods'
        ➜ Explicit dependency on target 'GoogleUtilities-GoogleUtilities_Privacy' in project 'Pods'
    Target 'GoogleUtilities-GoogleUtilities_Privacy' in project 'Pods' (no dependencies)
    Target 'DKImagePickerController' in project 'Pods'
        ➜ Explicit dependency on target 'DKImagePickerController-DKImagePickerController' in project 'Pods'
        ➜ Explicit dependency on target 'DKPhotoGallery' in project 'Pods'
    Target 'DKImagePickerController-DKImagePickerController' in project 'Pods'
        ➜ Implicit dependency on target 'DKPhotoGallery' in project 'Pods' via options '-framework DKPhotoGallery' in build setting 'OTHER_LDFLAGS'
    Target 'DKPhotoGallery' in project 'Pods'
        ➜ Explicit dependency on target 'DKPhotoGallery-DKPhotoGallery' in project 'Pods'
        ➜ Explicit dependency on target 'SDWebImage' in project 'Pods'
        ➜ Explicit dependency on target 'SwiftyGif' in project 'Pods'
    Target 'DKPhotoGallery-DKPhotoGallery' in project 'Pods'
        ➜ Implicit dependency on target 'SDWebImage' in project 'Pods' via options '-framework SDWebImage' in build setting 'OTHER_LDFLAGS'
        ➜ Implicit dependency on target 'SwiftyGif' in project 'Pods' via options '-framework SwiftyGif' in build setting 'OTHER_LDFLAGS'
    Target 'SwiftyGif' in project 'Pods'
        ➜ Explicit dependency on target 'SwiftyGif-SwiftyGif' in project 'Pods'
    Target 'SwiftyGif-SwiftyGif' in project 'Pods' (no dependencies)
    Target 'SDWebImage' in project 'Pods'
        ➜ Explicit dependency on target 'SDWebImage-SDWebImage' in project 'Pods'
    Target 'SDWebImage-SDWebImage' in project 'Pods' (no dependencies)

GatherProvisioningInputs

CreateBuildDescription

ExecuteExternalTool /Applications/Xcode-26.6.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/clang -v -E -dM -arch arm64 -isysroot /Applications/Xcode-26.6.app/Contents/Developer/Platforms/iPhoneOS.platform/Developer/SDKs/iPhoneOS26.5.sdk -x c -c /dev/null

ExecuteExternalTool /Applications/Xcode-26.6.app/Contents/Developer/usr/bin/actool --version --output-format xml1

ExecuteExternalTool /Applications/Xcode-26.6.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/clang -v -E -dM -isysroot /Applications/Xcode-26.6.app/Contents/Developer/Platforms/iPhoneOS.platform/Developer/SDKs/iPhoneOS26.5.sdk -x c -c /dev/null

ExecuteExternalTool /Applications/Xcode-26.6.app/Contents/Developer/usr/bin/ibtool --version --output-format xml1

ExecuteExternalTool /Applications/Xcode-26.6.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/clang -v -E -dM -arch arm64 -isysroot /Applications/Xcode-26.6.app/Contents/Developer/Platforms/iPhoneOS.platform/Developer/SDKs/iPhoneOS26.5.sdk -x objective-c -c /dev/null

ExecuteExternalTool /Applications/Xcode-26.6.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/ld -version_details

ExecuteExternalTool /Applications/Xcode-26.6.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/swiftc --version

ExecuteExternalTool /Applications/Xcode-26.6.app/Contents/Developer/usr/bin/actool --print-asset-tag-combinations --output-format xml1 /Users/builder/clone/ios/Runner/Assets.xcassets

ExecuteExternalTool /Applications/Xcode-26.6.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/libtool -V

Build description signature: a23e3fc7f7bd7560cf737af65dd1d355
Build description path: /Users/builder/Library/Developer/Xcode/DerivedData/Runner-edaimyiflreloheqntgnhkmwcclv/Build/Intermediates.noindex/ArchiveIntermediates/Runner/IntermediateBuildFilesPath/XCBuildData/a23e3fc7f7bd7560cf737af65dd1d355.xcbuilddata
/Users/builder/clone/ios/Runner.xcodeproj: error: Provisioning profile "muhtasari AppStore" doesn't include the Push Notifications capability. (in target 'Runner' from project 'Runner')
/Users/builder/clone/ios/Runner.xcodeproj: error: Provisioning profile "muhtasari AppStore" doesn't include the aps-environment entitlement. (in target 'Runner' from project 'Runner')
note: Run script build phase 'Thin Binary' will be run during every build because the option to run the script phase "Based on dependency analysis" is unchecked. (in target 'Runner' from project 'Runner')
note: Run script build phase 'Run Script' will be run during every build because the option to run the script phase "Based on dependency analysis" is unchecked. (in target 'Runner' from project 'Runner')
** ARCHIVE FAILED **


The following build commands failed:
	Archiving workspace Runner with scheme Runner
(1 failure)


<<< Process completed with status code 65 in 00:06



Build failed :|
Step 8 script `Build IPA and preserve diagnostic log` exited with status code 65

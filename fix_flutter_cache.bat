@echo off
echo 🚀 NETTOYAGE DU CACHE FLUTTER ET RECOMPILATION
echo ================================================

echo 🧹 Nettoyage du cache Flutter...
flutter clean

echo 📦 Récupération des dépendances...
flutter pub get

echo 🔧 Nettoyage du cache Dart...
dart pub cache clean

echo 🌐 Nettoyage du cache Web...
rmdir /s /q build\web 2>nul
rmdir /s /q .dart_tool\build 2>nul

echo ✅ Cache nettoyé ! Maintenant recompilez votre application.
echo 💡 Pour le web: flutter run -d chrome
echo 💡 Pour mobile: flutter run

pause
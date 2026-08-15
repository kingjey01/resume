=======restruction et amandement de google console apres examen
1) Pour votre prochaine version
Il se peut que l'affichage de bord à bord ne soit pas disponible pour tous les utilisateurs
À partir d'Android 15, les applis ciblant le SDK 35 proposeront par défaut l'affichage de bord à bord. Les applis ciblant le SDK 35 doivent gérer les encarts pour s'assurer qu'elles s'affichent correctement sous Android 15 et version ultérieure. Étudiez ce problème, et prenez le temps de tester l'affichage de bord à bord et d'apporter les modifications nécessaires. Vous pouvez aussi appeler enableEdgeToEdge() pour Kotlin ou EdgeToEdge.enable() pour Java afin d'assurer la rétrocompatibilité.

2) Votre appli utilise des API ou des paramètres obsolètes pour l'affichage de bord à bord
Au moins une des API que vous utilisez ou un des paramètres que vous avez définis pour l'affichage de bord à bord et des fenêtres sont devenus obsolètes dans Android 15. Votre appli utilise les API ou paramètres obsolètes suivants :

android.view.Window.setStatusBarColor
android.view.Window.setNavigationBarColor
android.view.Window.setNavigationBarDividerColor
Ceux-ci se trouvent aux emplacements suivants :

io.flutter.app.FlutterActivityDelegate.onCreate
io.flutter.embedding.android.FlutterActivity.configureStatusBarForFullscreenFlutterExperience
io.flutter.embedding.android.FlutterFragmentActivity.configureStatusBarForFullscreenFlutterExperience
io.flutter.plugin.platform.PlatformPlugin.setSystemChromeSystemUIOverlayStyle
io.flutter.util.PathUtils$$ExternalSyntheticApiModelOutline0.m
Pour résoudre ce problème, arrêtez d'utiliser ces API ou ces paramètres.

3) Supprimez les restrictions de redimensionnement et d'orientation dans votre appli pour la rendre compatible avec les appareils à grand écran
À partir d'Android 16, Android ignorera les restrictions de redimensionnement et d'orientation pour les appareils à grand écran, comme les appareils pliables et les tablettes. Cela pourra entraîner des problèmes de mise en page et d'usabilité pour vos utilisateurs.

Nous avons détecté les restrictions de redimensionnement et d'orientation suivantes dans votre appli :

<activity android:name="com.resumeplus.jeycode.MainActivity" android:screenOrientation="PORTRAIT" />
Pour améliorer l'expérience utilisateur de votre appli, supprimez ces restrictions et vérifiez que les mises en page de l'appli fonctionnent sur différentes tailles et orientations d'écran en les testant sur Android 16 et versions antérieures.

4) Recompilez votre appli avec un alignement des bibliothèques natives pour 16 ko
Votre appli utilise des bibliothèques natives qui ne sont pas alignées pour prendre en charge les appareils avec des tailles de page de mémoire de 16 ko. Il est possible que votre appli ne puisse pas être installée ou lancée sur ces appareils, ou qu'elle plante après avoir démarré.

Cette version comporte de nouveaux app bundles qui ne sont pas compatibles avec les tailles de page de mémoire de 16 ko.

Codes de version :

10
Android 15 prend en charge les appareils dont les tailles de page de mémoire sont de 16 ko, ce qui peut améliorer les performances de votre appli. Nous vous recommandons de recompiler votre appli lorsque vous migrez vers Android 15, et de la tester dans un environnement 16 ko afin d'éviter les problèmes pour les utilisateurs.

NB: suis ces instructions et améliore l'application selon, ces recommandation


====nouveau examen
L'appli doit cibler Android 16 (niveau d'API 36) ou une version ultérieure
Pour offrir une expérience sécurisée aux utilisateurs, Google Play exige que toutes les applis répondent aux exigences du niveau d'API cible.
À compter du 31 août 2026, si votre appli ne cible pas un niveau d'API disponible depuis moins d'un an après la dernière version d'Android, vous ne serez plus en mesure de mettre à jour votre appli.


Dépannage
Votre niveau d'API cible non conforme le plus élevé est Android 15 (niveau d'API 35).


Pour pouvoir continuer à mettre à jour votre appli :

Mettez-la à jour afin qu'elle cible Android 16 (niveau d'API 36) ou une version ultérieure.
Publiez une nouvelle version de votre appli en production. Vous pouvez d'abord tester votre appli à l'aide de tests internes, fermés ou ouverts.
Accéder à la vue d'ensemble des versions

Une fois cette étape terminée, nous vous enverrons une notification pour confirmer que votre appli a bien été mise à jour et qu'elle n'est plus affectée par ce problème.


Cette info est-elle utile ?

-Erreur
Cette version ne prend plus en charge 1 971 appareils qui étaient compatibles avec votre version précédente. Si vous continuez, votre appli ne sera pas disponible pour les nouveaux utilisateurs sur ces appareils non pris en charge, et les mises à jour ne seront pas disponibles pour les utilisateurs qui ont déjà installé votre appli sur ces appareils. Consultez les modifications apportées à vos appareils pris en charge pour voir quels appareils sont concernés.



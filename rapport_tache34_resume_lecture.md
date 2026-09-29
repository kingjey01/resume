# Tâche 34 — Indicateur « vu », lecture depuis la page courante, card CP, responsive audio

**Date :** 27/09/2026

**Fichiers modifiés**

| Fichier | Point |
|---|---|
| `lib/features/summaries/providers/seen_summaries_provider.dart` *(nouveau)* | 1 |
| `lib/features/home/widgets/summary_card.dart` | 1 |
| `lib/features/summary_details/screens/summary_details_screen.dart` | 1 + 2 |
| `lib/widgets/ai_content_view.dart` | 2 |
| `lib/features/home/screens/home_screen.dart` | 3 |
| `lib/widgets/audio_player_widget.dart` | 4 |

**Fichiers de test**

- `test/summary_seen_indicator_test.dart` *(nouveau)*
- `test/summary_audio_start_page_test.dart` *(nouveau)*
- `test/summary_audio_responsive_test.dart` *(nouveau)*
- `test/cp_role_sync_test.dart` *(3 cas ajoutés)*

---

## 1. Indicateur « résumé déjà vu / non vu »

### Analyse préalable

Rien n'existait côté « vu » :

- `Summary` (Flutter comme Django) n'a **aucun** champ `is_viewed` / `seen_at` ;
- il n'existe **aucun** modèle de jonction `user × summary` ni endpoint associé ;
- le seul précédent « lu / non lu » est celui des **notifications**
  (`UserNotification.is_read` + pastille bleue + fond teinté), et il est
  **côté serveur**.

Deux mécanismes voisins ont été écartés pour éviter tout conflit d'état :

- les badges `ValidatedSummariesBadgeNotifier` / `CreatedSummariesBadgeNotifier`
  reposent sur un **timestamp global** (`badge_last_viewed_summaries`), pas sur
  un résumé précis : ils ne peuvent pas répondre à « ce résumé-ci a-t-il été
  vu ? » ;
- `summariesProvider` sert la liste et son cache : y ajouter l'état « vu »
  aurait obligé à l'invalider à chaque ouverture.

Le cahier des charges demandant explicitement une gestion **côté Flutter** et
**propre à l'utilisateur connecté**, l'indicateur est un état local persistant,
sans aucun appel réseau ni modification du backend.

### Correction appliquée

**`seen_summaries_provider.dart` (nouveau)** — `StateNotifierProvider<SeenSummariesNotifier, Set<int>>` :

- état = ensemble d'identifiants de résumés vus ;
- persistance `SharedPreferences` sous une clé **par utilisateur** :
  `seen_summaries_user_<id>` — sur un même téléphone, un second compte
  n'hérite pas des résumés vus par le premier (même précaution que
  `StorageService.resetGeneralOnboarding`) ;
- le provider `watch` `currentUserProvider` : au changement de compte, un
  nouveau notifier est créé avec la bonne clé (`User` compare par `id`, donc un
  simple rafraîchissement de profil ne le recrée pas) ;
- `markSeen` est **idempotent** et met à jour l'état avant d'écrire : l'UI ne
  dépend jamais de la réussite du stockage.

**`summary_card.dart`** — `StatelessWidget` → `ConsumerWidget` (les 4 onglets
« Tous / Gratuits / Payants / Récents », l'accueil, les écrans filière et cours
passent tous par cette carte, donc l'indicateur est cohérent partout) :

- résumé **non vu** → fond teinté (`Color.alphaBlend` de `primaryBlue` à 6 %
  clair / 14 % sombre sur la surface : la carte reste opaque et lisible) ;
- résumé **non vu** → pastille bleue 8×8, identique à celle des notifications
  (`AppTheme.primaryBlue`, `BoxShape.circle`), placée dans la ligne du titre
  (elle ne peut donc pas chevaucher le badge auteur CP/IA) ;
- résumé **vu** → fond de surface normal, aucune pastille ;
- `AnimatedContainer` 200 ms, comme la tuile de notification.

**`summary_details_screen.dart`** — passage en `ConsumerStatefulWidget` (le
`ref` est nécessaire à l'ouverture) et marquage dans `initState` :

```dart
ref.read(seenSummariesProvider.notifier).markSeen(widget.summary.id);
```

L'écran de détail est le **seul point de passage** de tous les chemins
d'ouverture (carte de résumé, carte d'achat, écran Achats) : marquer ici couvre
tous les cas, sans dépendre de l'endroit d'où l'on vient.

Cohérence : l'état est réactif (donc les listes se mettent à jour seules au
retour du détail, sans `invalidate` ni rechargement) **et** persisté (donc il
survit à un redémarrage et reste identique d'un onglet à l'autre).

### Test effectué

`test/summary_seen_indicator_test.dart` — 5 cas : pastille présente sur un
résumé jamais ouvert ; disparition après `markSeen` **sans rechargement de la
liste** ; indifférence aux autres résumés ; persistance relue au « redémarrage »
(nouvelle instance du notifier) ; **isolation entre deux comptes**.

---

## 2. Lecture audio à partir de la page courante

### Analyse préalable

Le blocage était architectural : `AiContentView` (qui **est** la pagination —
une `List<String> _pages` + un index, pas un `PageView`) gardait `_currentPage`
**privé**, sans `onPageChanged` ni `Notifier`. L'écran de détail ignorait donc
totalement la page affichée et transmettait **le texte intégral** au TTS
(`AudioPlayerWidget.text`), qui repartait systématiquement du début.

### Correction appliquée

**`ai_content_view.dart`**

1. Le découpage (`_splitContent`) est extrait en
   `static List<String> splitIntoPages(String content)` — **une seule source**
   du découpage, réutilisée par l'écran de détail. Dupliquer l'algorithme aurait
   fait diverger l'index de page et le texte lu. La logique de découpage
   elle-même est **inchangée**.
2. Nouveau paramètre `onPageChanged` et méthode `_goToPage()` qui notifie le
   parent **uniquement** lors d'une navigation réelle par les flèches (aucun
   appel pendant `build`).

**`summary_details_screen.dart`**

- `_audioStartPage` mémorise la page remontée par `AiContentView` ;
- `_pages` (getter) met en cache `AiContentView.splitIntoPages(_summaryContent)`
  et ne le recalcule que si le contenu change ;
- `_audioText` renvoie `pages.sublist(pageAffichée).join('\n\n')` — soit **de la
  page affichée jusqu'à la fin** ; l'index est borné pour résister à un
  changement de contenu ;
- l'`AudioPlayerWidget` reçoit `text: _audioText`.

Comportement obtenu : page 1 → résumé complet ; page 5 → lecture **depuis la
page 5** puis poursuite normale jusqu'à la fin. La pagination, l'affichage, le
bouton Pause/Reprendre/Arrêter et le service TTS sont inchangés — seule la
valeur du texte lu change. Revenir en arrière élargit de nouveau la lecture,
puisque le point de départ suit la page affichée.

### Test effectué

`test/summary_audio_start_page_test.dart` — 4 cas sur l'écran réel
(`SummaryDetailsScreen` + `AudioPlayerWidget` de production), avec un résumé de
3 sections : page 1 → texte complet ; page 2 → **plus de section 1**, sections 2
**et 3** présentes (« ne repart pas du début » + « continue jusqu'à la fin ») ;
page 3 → dernière page seulement ; retour arrière → la section 2 réapparaît.

---

## 3. Masquer complètement la demande de CP impossible

### Analyse préalable

Une seule bannière existe : `_buildCPRequestBanner` dans `home_screen.dart`,
affichée sous la condition `!_isLoadingProfile && rôle != CP/ADMIN`. Le
« grisage » n'était pas un `enabled: false` mais un **remplacement du contenu**
(icône cadenas + « Promotion déjà couverte ») et la disparition du bouton
« Demander ».

Deux sources alimentent cet état, via `GET /auth/cp-request/status/` :

- `combination_blocked` → une demande `pending` ou `approved` existe pour la
  même **université + filière + promotion** (c'est la règle exacte demandée) ;
- `request.status == 'pending'` → demande personnelle en attente.

Statuts possibles : `pending`, `approved`, `rejected` (seul `rejected` autorise
une nouvelle demande). La règle métier backend
(`create_cp_request_view`, `views.py:1084-1112`) reste **intacte** : elle
refuse toujours une demande en double.

### Correction appliquée

**`home_screen.dart`**

1. Getter `_cpRequestImpossible` = `_cpRequestPending || _cpRequestBlocked` —
   un seul point de vérité pour la règle.
2. La condition d'affichage devient
   `!_isLoadingProfile && _cpStatusLoaded && !_cpRequestImpossible && rôle != CP/ADMIN` :
   le card n'est **plus construit du tout** (et non plus grisé).
3. **`_cpStatusLoaded`** (nouveau) : le statut CP arrive dans un second appel
   réseau, après le profil. Sans ce garde-fou, un étudiant déjà couvert voyait
   apparaître puis disparaître la bannière — le contrôle est donc fait avec des
   données **chargées**, jamais avec l'état initial par défaut.
4. Corps de la bannière simplifié : les variantes « grisées » (cadenas,
   sablier) sont supprimées puisqu'elles ne peuvent plus être atteintes ; le
   contenu, les couleurs et le bouton « Demander » sont identiques.
5. Garde du dialogue alignée sur la même règle (`if (_cpRequestImpossible) return;`)
   pour ne pas ouvrir un formulaire dont la soumission serait refusée.
6. `_loadCPRequestStatus()` est désormais aussi appelé à la **resélection de
   l'onglet Accueil** (`homeRefreshProvider`) : c'était le seul chemin de
   rafraîchissement qui ne rechargeait pas le statut, donc un utilisateur dont
   la promotion venait d'être couverte continuait de voir la bannière.

En cas d'erreur réseau, `_cpStatusLoaded` passe à `true` avec les valeurs par
défaut : la bannière reste visible et cliquable, et le backend reste l'autorité
finale (comportement existant conservé).

### Test effectué

`test/cp_role_sync_test.dart` — 3 cas ajoutés : demande **en attente** →
bannière absente *et* ancien texte « Demande en cours de traitement » absent ;
**promotion déjà couverte** → bannière absente *et* « Promotion déjà couverte »
absent ; demande **refusée** → bannière et bouton « Demander » toujours
présents (la possibilité de redemander est conservée).

---

## 4. Correction responsive des boutons audio

### Analyse préalable

La zone fautive est une `Row(mainAxisAlignment: center)` avec deux
`ElevatedButton.icon` en largeur **intrinsèque** : aucun `Expanded`,
`Flexible`, `Wrap` ni `LayoutBuilder`. Sur un écran de 320 px, l'espace
réellement disponible pour les boutons est de ~208 px après les paddings
(écran 20+20, conteneur 16+16, carte 16+16, marge de `Card` 4+4), pour
~234 px de boutons → débordement horizontal, qui décalait le contenu.

### Correction appliquée

**`audio_player_widget.dart`** — la `Row` est remplacée par un
`LayoutBuilder` + `Wrap` :

- `spacing: 12` reproduit exactement l'espacement d'origine, `runSpacing: 8`
  sépare les lignes quand les boutons s'empilent ;
- `alignment: WrapAlignment.center` conserve le centrage actuel ;
- côte à côte quand la largeur suffit, **empilés verticalement** sinon ;
- chaque bouton est enveloppé dans un `ConstrainedBox(maxWidth: largeur
  disponible)` pour qu'un bouton seul ne puisse jamais dépasser son conteneur ;
- les libellés passent en `maxLines: 1` + `TextOverflow.ellipsis`.

Les deux boutons sont extraits en `_buildPlayPauseButton()` /
`_buildStopButton()` **sans aucun changement** de style, de couleur, de libellé
ni de logique (`_playPause`, `_stop`, états `_isPlaying`/`_isPaused` inchangés).

Règle de non-régression respectée : seule la présentation de cette zone a été
touchée — aucun endpoint, aucun état, aucune fonctionnalité.

### Test effectué

`test/summary_audio_responsive_test.dart` — le cas qui cassait réellement
l'écran est celui des **deux** boutons (« Écouter » + « Arrêter »). Le bouton
« Arrêter » n'apparaît que pendant une lecture, qui dépend du moteur TTS du
téléphone : les rappels du canal `flutter_tts` (`speak.onStart`) sont donc
simulés, ce qui fait passer le lecteur en lecture **sans appareil réel**.

Cas couverts : les deux boutons sont bien affichés pendant la lecture ;
écran large → les deux libellés sont au même niveau (côte à côte) ; écran
étroit (200 px) → le second est **au-dessus** du premier (empilés) ; et
**aucun débordement** (`takeException()` est nul, ce qui remonte tout
`RenderFlex overflow`) pour 200, 240, 280, 320, 360, 480 et 900 px, **lecture
arrêtée comme en lecture**.

---

## 5. Deux problèmes découverts pendant les tests (et corrigés)

Ces deux points ne se voyaient **pas** à la lecture du code : ils ne sont
apparus qu'à l'exécution.

**a) Marquer « vu » depuis `initState` est interdit par Riverpod.**
`markSeen` fait passer le provider à un nouvel état ; appelé directement dans
`initState`, Riverpod lève
`Tried to modify a provider while the widget tree was building`. Le marquage est
donc **différé après la première frame** :

```dart
WidgetsBinding.instance.addPostFrameCallback((_) {
  if (!mounted) return;
  ref.read(seenSummariesProvider.notifier).markSeen(widget.summary.id);
});
```

**b) L'écran de détail exige désormais un `ProviderScope`.**
`SummaryDetailsScreen` étant devenu un `ConsumerStatefulWidget`, le test de
non-régression `test/summary_info_layout_test.dart` échouait
(`Bad state: No ProviderScope found`) : il montait l'écran sans `ProviderScope`.
C'est le test qui était incomplet — l'application, elle, enveloppe tout dans un
`ProviderScope` (`main.dart:57`). Le test a été corrigé (ajout du `ProviderScope`
+ surcharge de `seenSummariesProvider`), **sans toucher à ce qu'il vérifie**.

---

## Vérifications de non-régression

- `flutter analyze lib test` : **0 erreur**. Aucun avertissement nouveau sur les
  fichiers modifiés ni sur les nouveaux tests. Les `warning`/`info` qui
  subsistent dans les fichiers touchés sont **antérieurs** et vérifiés comme
  tels (`import` inutilisés `dio` et `app_theme` présents à l'identique dans
  `HEAD`, `withOpacity` déprécié, `print` de debug).
- **79 tests passent** :

  | Fichier | Résultat |
  |---|---|
  | `test/summary_seen_indicator_test.dart` *(nouveau)* | 5/5 |
  | `test/summary_audio_start_page_test.dart` *(nouveau)* | 5/5 |
  | `test/summary_audio_responsive_test.dart` *(nouveau)* | 4/4 |
  | `test/summary_info_layout_test.dart` *(non-régression, corrigé)* | 14/14 |
  | `test/cp_role_sync_test.dart` *(3 cas ajoutés)* | OK |
  | `test/formula_block_test.dart` + `test/math_formula_rendering_test.dart` | OK |

  Les deux derniers fichiers pompent `AiContentView` : ils confirment que
  l'extraction de `splitIntoPages` n'a pas modifié le rendu Markdown ni le rendu
  des formules.

- `test/widget_test.dart` **échoue**, mais pour une raison **antérieure à cette
  tâche** : ce test template monte `MyApp` sans `ProviderScope`
  (`Bad state: No ProviderScope found`) et cherche un compteur qui n'existe plus.
  Aucun lien avec les modifications de cette tâche.

---

## Résultat

| Point demandé | Avant | Après |
|---|---|---|
| 1. Résumé vu / non vu | inexistant | pastille bleue + fond teinté, marquage à l'ouverture, persistant et par utilisateur |
| 2. Lecture audio | toujours depuis la page 1 | démarre à la page affichée et va jusqu'à la fin |
| 3. Card demande de CP | grisé avec un message | **totalement masqué** si demande en attente / promotion couverte ; conservé si demande refusée |
| 4. Boutons audio | débordement horizontal sur petits écrans | zone responsive, empilement vertical, aucun débordement de 200 à 900 px |

Aucun endpoint, aucun modèle, aucune réponse d'API, aucun workflow backend n'a
été modifié. La règle métier backend de la demande de CP reste la protection
finale.

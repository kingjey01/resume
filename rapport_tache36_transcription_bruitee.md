# Tâche 36 — Transcription interrompue avec voix parasites

**Date :** 29/09/2026
**Fichier modifié :** `backend/courses/deepgram_service.py`
**Fichiers ajoutés :** `backend/diagnostic_tache36_couverture.py`,
`backend/diagnostic_tache36_segments.py`, `backend/test_tache36_recuperation.py`,
`backend/courses/test_tache36_recuperation.py`

---

## 1. INVESTIGATION

### Méthode

L'investigation est repartie du code réel et de mesures refaites aujourd'hui
contre l'API, sans réutiliser les conclusions de la tâche 33. Le code a d'abord
été lu en entier : il n'existe **qu'un seul** chemin de transcription
(`audio_processing._step1_transcribe_audio` → `deepgram_service.transcribe_file`),
**aucun découpage/segment**, **aucun streaming**, **aucune reprise**, et un seul
appel `POST /v1/listen` en pre-recorded.

### Ce qui a été écarté par la mesure

Les deux fichiers de test ont été analysés au niveau de leurs trames AMR :

| Audio | Structure | Durée | Anomalies |
|---|---|---|---|
| clair | AMR-NB, 20 162 trames, **mode 7 partout** | 403,2 s | **0** |
| bruité | AMR-NB, 19 558 trames, **mode 7 partout** | 391,2 s | **0** |

Les deux fichiers sont donc **intègres et intégralement décodables** : ni
enregistrement interrompu, ni silence codé (SID / No Data), ni changement de
mode, ni fichier tronqué. L'hypothèse « une portion est prise à tort pour une
fin d'audio ou un silence prolongé » est donc **écartée** : il n'existe aucun
mécanisme de ce genre dans le code, et rien de tel dans les fichiers.

### CAUSE N°1 — la correction de la tâche 33 n'est pas déployée

Même fichier, même jour, deux configurations :

| Configuration | Modèle réellement utilisé | Mots | Dernier mot | Couverture |
|---|---|---|---|---|
| **celle déployée** (`HEAD`) : nova-2 + `fr` | `2-general-nova` | 213 | **220,0 s** | **56,2 %** |
| **celle du code actuel** : nova-3 + `multi` | `general-nova-3` | 857 | 390,6 s | **99,9 %** |

Le texte produit par la configuration déployée s'arrête en pleine phrase —
« *…car ici on l'a vu pour les additions* » — exactement le symptôme décrit.

**La correction de la tâche 33 existe dans le dépôt de travail mais n'a jamais
été commitée** : `git status` montre `deepgram_service.py` et
`audio_processing.py` modifiés (206 lignes), et `git show HEAD:` contient
toujours `MODEL = 'nova-2'` et `language='fr'`. **La production exécute donc
encore l'ancien code.** C'est la raison directe pour laquelle « le problème
reste présent en production » alors que les tests passaient.

### CAUSE N°2 — un appel sur le fichier entier perd des passages (invisible)

C'est la découverte que les tests précédents ne pouvaient pas faire : le taux de
couverture ne mesurait que **la fin du dernier mot**, jamais les trous internes.

Sur l'audio bruité avec la configuration actuelle (99,9 % affichés), trois
passages ne produisaient **aucun mot** : 40,6→76,0 s, 298,4→314,5 s,
358,1→374,5 s. Le même constat existe sur l'audio clair (286,7→302,1 s).

Chaque passage a été extrait dans un fichier AMR autonome (recopie de trames,
sans ré-encodage) et transcrit **seul** :

| Passage | En fichier entier | Transcrit seul | Verdict |
|---|---|---|---|
| bruité 358,1→374,5 s | 0 mot | **26 mots** | récupérable |
| clair 286,7→302,1 s | 0 mot | **37 mots** | récupérable |
| bruité **220,0→391,2 s** (la queue perdue) | 0 mot | **363 mots** | récupérable |
| bruité 40,6→76,0 s | 0 mot | 0 mot | réellement inexploitable |
| bruité 298,4→314,5 s | 0 mot | 0 mot | réellement inexploitable |

**Conclusion : l'appel sur le fichier entier abandonne silencieusement des
passages que le même audio, découpé, transcrit parfaitement.** À cela s'ajoute
que la métrique de couverture masquait totalement ces trous.

---

## 2. CORRECTION APPLIQUÉE

`backend/courses/deepgram_service.py` — aucune signature, aucune clé de retour,
aucun endpoint modifié.

### a) Configuration nominale (tâche 33, conservée)

`MODEL = 'nova-3'`, `DEFAULT_LANGUAGE = 'multi'` : déjà présents dans le dépôt
de travail, mesurés à nouveau aujourd'hui à **99,9 %**.

### b) Récupération des passages perdus (nouveau)

Après l'appel principal, le service cherche les passages qu'**aucun mot** ne
recouvre — trous internes **et** queue manquante (`_trouver_trous`, seuil 10 s).
Chacun est alors :

1. **extrait sans perte** (`_extraire_segment`) : un AMR est une suite de trames
   de 20 ms, donc recopier les trames de la fenêtre suffit. **Aucun
   ré-encodage** : un ré-encodage dégraderait l'audio et recréerait le problème ;
2. **transcrit avec exactement les mêmes paramètres** que l'appel principal
   (`_envoyer`, point d'envoi unique) ;
3. **recollé à sa position réelle** (décalage des horodatages, puis tri
   chronologique) — les mots existants ne sont jamais retirés, la correction ne
   peut qu'**ajouter** ce qui manquait.

Le texte n'est reconstruit depuis les mots que **si** une récupération a eu
lieu : sans trou, la sortie Deepgram est conservée telle quelle
(`smart_format`, paragraphes).

**Coût maîtrisé** : un audio sans trou reste à **un seul appel** (cas courant,
comportement et coût inchangés). Seules les fenêtres manquantes sont
re-transcrites, plafonnées à 600 s d'audio et 12 passages par fichier. Mesuré :
15 s et 16 s de ré-audio pour les deux audios de test.

### c) Diagnostics visibles en production

Le logger `courses` n'est pas déclaré dans `LOGGING` : seuls les WARNING
remontent (le logger racine n'a aucun handler). Les bilans de récupération sont
donc émis en **WARNING**, sans quoi tout ce diagnostic resterait invisible —
c'est précisément ce qui a masqué le problème :

```
⚠️ 3 passage(s) sans mot détecté(s) sur audio_test.amr : 26 mots récupérés par
   découpage (16s ré-audio), 2 passage(s) restent inexploitables (51s d'audio)
```

Un passage réellement inexploitable est distingué d'un passage récupéré.

---

## 3. TEST EFFECTUÉ

### Tests unitaires (sans réseau) — `courses/test_tache36_recuperation.py`

**21 tests** : détection des trous internes et de la queue perdue, non-déclenchement
sur une transcription complète ou vide, découpage AMR exact (fenêtre demandée,
jusqu'à la fin du fichier, fenêtre vide, format non AMR refusé sans
ré-encodage), reconstruction du texte, calcul de couverture, bornes de
récupération.

### Bout en bout contre l'API réelle

| Audio | Mots (avant correction) | Mots (après) | Couverture | Passages restants |
|---|---|---|---|---|
| clair | 1 058 | **1 098** (+40) | 98,6 % | **0** |
| bruité | 857 | **870** (+26) | 99,5 % | 2 (inexploitables, 51 s) |
| long ~3 h | 22 309 | **22 401** | **100,0 %** | — |

La phrase finale du cours est atteinte dans les trois cas.

### La correction protège même l'ancienne configuration

En simulant la configuration **actuellement déployée** (nova-2 + fr) :

| | Mots | Couverture |
|---|---|---|
| appel brut (ce que fait la production aujourd'hui) | 213 | **56,2 %** |
| même appel **+ récupération** | 242 | **87,8 %** |

La queue perdue de 171,2 s est en grande partie reconstituée
(220,0→333,6 s récupérés). Le mécanisme est donc **auto-réparateur** : même si
une configuration redevient défavorable, la transcription ne s'arrête plus
silencieusement à mi-parcours.

### Non-régression

- `manage.py test courses` : **47/47 OK** (dont les 7 tests de suppression de
  résumé et les 10 de la règle « résumé acheté » de la tâche 35).
- `manage.py check` : **0 problème**.
- `test_tache33_couverture.py` (script de la tâche 33) : **tous les cas
  couverts**, audio de 3 h à 100 %.

---

## 4. RÉSULTAT

**CAUSE IDENTIFIÉE**
1. **La correction de la tâche 33 n'est pas déployée** : le code de production
   (`HEAD`) utilise encore `nova-2` + `language='fr'`, ce qui arrête la
   transcription à 220,0 s sur 391,2 s (56,2 %). Mesuré le même jour, même
   fichier, avec les `request_id` et les noms de modèles réels à l'appui.
2. **Même avec la bonne configuration, l'appel sur le fichier entier perd des
   passages entiers** (jusqu'à 35 s d'affilée) que le découpage récupère, et la
   métrique de couverture ne voyait pas ces trous internes.

**FICHIERS/FONCTIONS CONCERNÉS** — `courses/deepgram_service.py`
(`MODEL`/`DEFAULT_LANGUAGE`, `transcribe_file`, `_compute_coverage`) et
`courses/audio_processing._step1_transcribe_audio` (qui appelait
`transcribe_file(file_path, language='fr')`).

**CORRECTION APPLIQUÉE** — nova-3 + `multi` (conservé), **plus** détection des
passages sans mot et re-transcription par découpage AMR sans perte, recollage
aux horodatages réels, coût borné et nul pour un audio sain, bilan en WARNING
visible en production.

**TEST EFFECTUÉ** — 21 tests unitaires, 47 tests Django, bout en bout sur audio
clair / bruité / ~3 h, et simulation de l'ancienne configuration.

**RÉSULTAT** — aucune interruption silencieuse : 0 passage perdu sur l'audio
clair, 51 s réellement inexploitables (parole masquée) sur le bruité, 100 % sur
l'audio de 3 h.

---

## 5. À FAIRE CÔTÉ DÉPLOIEMENT

**La correction ne sert à rien tant qu'elle n'est pas déployée.** Les deux
fichiers de la tâche 33 sont modifiés mais **non commités** :

| Fichier | État |
|---|---|
| `backend/courses/deepgram_service.py` | modifié (tâche 33 + 36), **non commité** |
| `backend/courses/audio_processing.py` | modifié (tâche 33), **non commité** |

Après déploiement : redémarrer le service applicatif **et** le worker Celery
(c'est le worker qui exécute la transcription). Aucune migration.

### Point de vigilance relevé au passage

Le logger `courses` n'est déclaré ni dans `resume_backend/settings.py` (`LOGGING`)
ni ailleurs : tous les `logger.info` du module de transcription (dont le
diagnostic d'étape 1) sont **perdus** en production. Déclarer un logger
`courses` rendrait ces diagnostics exploitables — non modifié ici, car cela
change le volume de logs de toute l'application : à décider.

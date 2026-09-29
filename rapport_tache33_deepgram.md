# Tâche 33 — Transcription Deepgram interrompue prématurément

**Date :** 26/09/2026
**Fichiers modifiés :** `backend/courses/deepgram_service.py`, `backend/courses/audio_processing.py`

---

## 1. INVESTIGATION

### Ce que le code faisait réellement

| Question | Réponse |
|---|---|
| Service qui parle à Deepgram | `backend/courses/deepgram_service.py` |
| Streaming ou Pre-recorded ? | **Pre-recorded** — un `POST` de tout le fichier sur `/v1/listen` |
| `is_final` / `speech_final` / `endpointing` / `utterance_end` / VAD | **Aucun n'est utilisé** (ces paramètres n'existent qu'en streaming) |
| Ce qui déclenchait l'arrêt | Rien dans notre code : c'est **Deepgram qui cessait d'émettre des mots** |
| Segments finalisés perdus | Non — `_extract_transcript` lit bien la réponse complète |

Le streaming n'était donc **pas** la cause : la piste suggérée par la tâche
(« si le streaming actuel est la cause ») ne s'appliquait pas. Le problème
venait bien du couple **modèle + langue** envoyé à Deepgram.

### Mesure du problème (avant toute modification)

Même cours, deux enregistrements : `audio_test_claire.amr` (calme) et
`audio_test.amr` (voix parasites). Comparaison de la fin du dernier mot
transcrit avec la durée réelle du fichier :

| Audio | Durée | Mots | Fin du dernier mot | Couverture |
|---|---|---|---|---|
| clair | 403,2 s | 996 | 397,5 s | **98,6 %** ✅ |
| bruité | 391,2 s | 213 | **220,0 s** | **56,2 %** ❌ |

**171 secondes du cours bruité n'étaient jamais transcrites**, et le texte
s'arrêtait en pleine phrase :

> « …car ici on l'a vu pour les additions »

Détail aggravant : Deepgram renvoyait `HTTP 200`, `metadata.duration = 391,16`
(il avait bien lu tout le fichier) et **aucune erreur**. Notre code
enregistrait donc la transcription en `status='completed'` avec une confiance
élevée — la panne était totalement silencieuse.

### Isolation de la cause

Le même fichier bruité, envoyé avec différents paramètres :

| Configuration | Couverture | Mots |
|---|---|---|
| `nova-2` + `language=fr` *(configuration d'origine)* | 56,2 % | 213 |
| `nova-2` + `fr` + `diarize=true` | 56,2 % | 213 |
| `nova-2` + `fr` + `utterances=true` | 56,2 % | 213 |
| `nova-3` + `language=fr` | 70,0 % | 149 |
| `nova-3` + `language=fr` + `diarize=true` | 70,0 % | 149 |
| **`nova-3` + `language=multi`** | **99,9 %** | **857** |
| `nova-2` + `language=multi` | 0 % | 0 *(non supporté)* |

**La diarisation et `utterances` n'ont aucun effet sur la couverture.** Le
facteur déterminant est la **langue** : en mode `fr`, le modèle mono-langue
abandonne les passages où plusieurs voix se superposent ; le mode `multi` de
nova-3 les transcrit.

### Cause secondaire trouvée au passage (audios longs)

Le timeout de l'appel était calculé sur la **taille** du fichier :

```python
adaptive_timeout = min(1800, 300 + int(file_size_mb / 50) * 120)
```

Or l'AMR est fortement compressé : un cours de **3 h ne pèse que ~17 Mo**, donc
`int(17/50) = 0` et le timeout restait bloqué à **300 s**, quelle que soit la
durée réelle. Vérifié :

| Audio | Taille | Timeout avant |
|---|---|---|
| 3 h | 16,5 Mo | **300 s (5 min)** |
| 3 h | 16,5 Mo | 300 s *(identique — la formule ne monte jamais)* |

Un cours long pouvait donc être coupé par **notre propre backend**, ce que la
tâche demandait explicitement de vérifier.

---

## 2. CORRECTION APPLIQUÉE

### `deepgram_service.py`

1. **`model` : `nova-2` → `nova-3`** et **`language` : `fr` → `multi`**
   (constantes `MODEL` / `DEFAULT_LANGUAGE`), avec le relevé de mesures en
   commentaire pour justifier le choix.
2. **Timeout recalibré sur la durée** (`_adaptive_timeout`) : durée lue via
   mutagen, repli pessimiste sur la taille (500 o/s, débit plancher des
   formats compressés), 6 s accordées par minute d'audio, borné entre 300 s
   et 1800 s (< `soft_time_limit` Celery de 3300 s).
3. **Mesure de couverture** (`_extract_duration`, `_compute_coverage`) :
   `transcribe_file` renvoie désormais `duration`, `covered_until` et
   `coverage`. En dessous de `SEUIL_COUVERTURE` (90 %), un `logger.warning`
   explicite est émis. La panne ne peut plus être silencieuse.

### `audio_processing.py`

4. Appel changé en `transcribe_file(file_path)` — plus de `language='fr'`
   forcé, qui réintroduisait le bug.
5. La couverture est journalisée, et une alerte est émise si elle est
   partielle.

**Non modifié, volontairement :** la logique DeepSeek, les endpoints, les
serializers, le modèle `Transcription` (le champ `langue` reste `'fr'` — c'est
la langue du contenu, et il est exposé par l'API), le chemin Celery.

---

## 3. TEST EFFECTUÉ

`backend/test_tache33_couverture.py` — teste le service **de production**
(`deepgram_service.transcribe_file`), pas une copie. L'audio long est construit
sans ffmpeg : un AMR est un en-tête de 6 octets suivi de trames brutes, donc
concaténer les trames produit un AMR valide de durée cumulée.

```
CAS 1 - audio clair                     : 403,2 s   -> couverture  98,6 %  (1058 mots)
CAS 2 - audio bruité (voix parasites)   : 391,2 s   -> couverture  99,9 %  ( 857 mots)
CAS 3 - audio long (2 h 56, 27 copies)  : 10561,3 s -> couverture 100,0 %  (22309 mots)
```

Pour chaque cas, la phrase finale du cours (« *…cette séquence est terminée* »)
est bien présente dans le texte produit — preuve que la transcription atteint
la fin réelle de l'enregistrement.

Chaîne vérifiée jusqu'à DeepSeek : `result['transcript']` →
`transcription.texte_transcription` (affectation directe, ligne 300) →
`deepseek_service.generate_summary(transcription_text=…)` (ligne 375).
Le `[:500]` de la ligne 193 n'est que l'aperçu de la **réponse API**, il ne
concerne pas le texte envoyé à DeepSeek.

**Non-régression :** `manage.py check` sans erreur, **16/16 tests Django OK**,
qualité du français conservée sur l'audio clair (même phrase finale, 996 → 1058
mots).

---

## 4. RÉSULTAT

| | Avant | Après |
|---|---|---|
| Audio bruité | 56,2 % (**171 s perdues**) | **99,9 %** |
| Audio clair | 98,6 % | 98,6 % (préservé) |
| Audio long 3 h | non testé / risque de coupure à 5 min | **100,0 %**, timeout 30 min |
| Détection d'une coupure | **silencieuse** | avertissement journalisé |

**CAUSE IDENTIFIÉE** → `language='fr'` avec `nova-2` : le modèle mono-langue
cessait d'émettre des mots au milieu du fichier dès que des voix parasites
couvraient la scène (56 % de l'audio), sans renvoyer d'erreur. Cause
secondaire : timeout calculé sur la taille du fichier, plafonné à 5 min même
pour 3 h d'audio.

**CORRECTION APPLIQUÉE** → `nova-3` + `language='multi'`, timeout calibré sur
la durée, mesure de couverture avec alerte explicite.

**TEST EFFECTUÉ** → `backend/test_tache33_couverture.py` sur les deux audios
fournis + un audio long de ~3 h, via le service de production. 16/16 tests
Django OK.

**RÉSULTAT** → la transcription couvre la totalité de l'audio dans les trois
cas (99,9 % bruité, 100 % long), la phrase finale du cours est atteinte, et
DeepSeek reçoit la transcription intégrale.

---

### Scripts conservés

- `backend/test_tache33_couverture.py` — test reproductible des 3 cas
- `backend/diagnostic_deepgram_matrice.py` — matrice de paramètres qui a isolé
  la cause (justifie le choix `nova-3` + `multi`)

### Point de vigilance

`language='multi'` est un mode **multilingue** de nova-3. Sur les deux audios
de test, la sortie reste du français correct. Si un cours devait un jour être
transcrit dans une langue mal détectée, le diagnostic est direct : comparer
`coverage` et relire le texte produit.

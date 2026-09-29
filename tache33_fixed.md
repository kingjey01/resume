Analyse et corrige le problème de transcription Deepgram dans Résumé Plus, sans modifier les autres fonctionnalités qui fonctionnent actuellement.

PROBLÈME :
Lorsqu’un audio de cours est enregistré dans un environnement calme, la transcription est complète. Mais lorsqu’il y a des voix parasites, des étudiants qui parlent ou du bruit en arrière-plan, la transcription peut s’interrompre prématurément et ne couvre pas tout l’audio. Cela provoque ensuite un résumé IA incomplet.

OBJECTIF :
Faire en sorte qu’un audio de cours soit transcrit jusqu’à sa fin réelle, même lorsqu’il contient des pauses, du bruit ou plusieurs voix.

1. INVESTIGATION AVANT MODIFICATION
Analyse d’abord le code actuel et identifie précisément :
- le service/fichier qui communique avec Deepgram ;
- si nous utilisons Streaming ou Pre-recorded ;
- comment les réponses Deepgram sont récupérées et concaténées ;
- l’utilisation éventuelle de `is_final`, `speech_final`, `endpointing`, `utterance_end`, VAD, `interim_results`, etc. ;
- ce qui déclenche actuellement la fin ou l’arrêt de la transcription ;
- si certains segments finalisés sont perdus ;
- si une voix parasite ou une pause peut actuellement être interprétée comme une fin de transcription ;
- si le problème vient de Deepgram ou de notre propre logique backend.

Compare également la durée réelle du fichier avec la durée couverte par la transcription et ses timestamps.

2. CORRECTION
Après avoir identifié la cause exacte, corrige directement le problème.

Règles importantes :
- Une pause ou une voix parasite ne doit jamais provoquer l'arrêt définitif de la transcription du cours.
- `speech_final` ou un événement équivalent ne doit pas être utilisé comme indication que tout le fichier est terminé.
- Tous les segments finalisés doivent être conservés et correctement concaténés.
- La transcription doit continuer jusqu'à la fin réelle de l'audio/session.
- Si le streaming actuel est la cause du problème, évalue la possibilité d'utiliser le traitement Pre-recorded pour les fichiers audio complets, particulièrement pour les enregistrements longs.
- Pour les audios longs (jusqu'à 3 heures), vérifier également les limites, timeouts et traitements asynchrones afin qu'aucune coupure ne soit provoquée par notre backend.
- Si la diarisation est déjà utilisée ou pertinente, elle peut être conservée/ajoutée pour distinguer les locuteurs, mais elle ne doit pas supprimer arbitrairement les segments.

3. TEST OBLIGATOIRE
Utilise un même fichier audio de test et compare :
- audio avec voix principale claire ;
- audio avec plusieurs voix/bruits en arrière-plan ;
- audio long.

NB: il y'a 2 audio pour le test avec le meme contenue , l'un est claire l'autre contient plusieur voix. nom des fichier audio à la racine du projet: - audio_test_claire et audio_test

Vérifie que la transcription finale couvre bien toute la durée du fichier et que le contenu transmis ensuite à DeepSeek est complet.

4. INTÉGRATION AVEC LE RÉSUMÉ IA
Ne modifie pas la logique de génération du résumé DeepSeek si elle fonctionne déjà.
Assure-toi simplement que DeepSeek reçoit la transcription complète et finale, et non une transcription coupée.

IMPORTANT :
- Analyse avant de modifier.
- Ne fais aucune modification inutile.
- Ne change pas les endpoints, modèles ou réponses API existants.
- Conserve la compatibilité avec le système actuel de Celery/worker.
- Ne régresses aucune fonctionnalité existante.
- Si tu identifies plusieurs causes possibles, teste-les avant de choisir la correction.
- À la fin, indique clairement : CAUSE IDENTIFIÉE → CORRECTION APPLIQUÉE → TEST EFFECTUÉ → RÉSULTAT.
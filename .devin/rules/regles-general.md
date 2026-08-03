Code production-ready.

OWASP obligatoire.

Clean architecture.

Performance first.

Analyser existant avant modifications.
Toujours suivre le workflow Git professionnel.

Avant chaque commit ou push :

1. analyser les modifications
2. vérifier erreurs compilation
3. lancer les tests nécessaires
4. vérifier sécurité OWASP
5. vérifier régressions UI/UX
6. vérifier performances
7. corriger erreurs détectées
8. générer commit clair et professionnel

Si tout est valide :
- faire commit
- faire push GitHub automatiquement

Toujours utiliser des messages de commit professionnels.

Exemples :
- feat(auth): add secure OTP verification
- fix(ui): resolve responsive navbar issue
- refactor(api): improve DRF permissions
- perf(flutter): optimize widget rebuilds

Ne jamais push du code cassé ou non testé.

Toujours vérifier :
- erreurs console
- erreurs build
- lint issues
- sécurité
- responsive
- cohérence architecture

En cas d'échec :
- expliquer problème
- proposer correction
- corriger avant push
---
trigger: manual
---


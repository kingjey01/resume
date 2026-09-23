"""
Vérification de l'AAB produit (Tâche 30).

Lancer depuis la RACINE du projet :
    backend/.venv/Scripts/python.exe verifier_aab.py

Contrôle trois choses que la console du build ne garantit PAS :
  1. intégrité de l'archive (aucune entrée corrompue) ;
  2. version réellement embarquée dans le manifest ;
  3. présence des polices mathématiques (preuve que le rendu des formules
     est bien embarqué, et non absent du paquet).
"""

import os
import re
import sys
import zipfile

AAB = r'build/app/outputs/bundle/release/app-release.aab'

print('=' * 78)
print("1) INTEGRITE DE L'ARCHIVE")
print('=' * 78)

with zipfile.ZipFile(AAB) as z:
    corrompu = z.testzip()
    if corrompu is None:
        print('  [OK] Aucune entree corrompue.')
    else:
        print(f'  [ECHEC] Entree corrompue : {corrompu}')
        sys.exit(1)

    noms = z.namelist()
    print(f'  Nombre d\'entrees : {len(noms)}')

    # ── 2. Version embarquee dans le manifest protobuf ────────────────
    print()
    print('=' * 78)
    print('2) VERSION REELLEMENT EMBARQUEE (base/manifest/AndroidManifest.xml)')
    print('=' * 78)

    manifest = z.read('base/manifest/AndroidManifest.xml')

    def chaines_apres(motif):
        """
        Dans un manifest protobuf, les valeurs d'attributs sont des chaines.
        La chaine lue est suivie des octets de longueur/type du protobuf, donc
        on ne garde que les caracteres alphanumeriques et les points
        (ex. b'33"' -> '33', b'1.1.17(' -> '1.1.17').
        """
        valeurs = []
        for m in re.finditer(motif, manifest):
            bloc = manifest[m.end():m.end() + 40]
            txt = re.findall(rb'[ -~]{2,}', bloc)
            if txt:
                brut = txt[0].decode('ascii', 'replace')
                propre = re.sub(r'[^0-9A-Za-z.]+$', '', brut)
                valeurs.append(propre)
        return valeurs

    vc = chaines_apres(rb'versionCode')
    vn = chaines_apres(rb'versionName')
    print(f'  versionCode lus : {vc}')
    print(f'  versionName lus : {vn}')

    if '33' in vc:
        print('  [OK] versionCode 33 present.')
    else:
        print(f'  [ALERTE] versionCode 33 NON trouve (lu: {vc})')

    if '1.1.17' in vn:
        print('  [OK] versionName 1.1.17 present.')
    else:
        print(f'  [ALERTE] versionName 1.1.17 NON trouve (lu: {vn})')

    # ── 3. Polices mathematiques embarquees ? ─────────────────────────
    print()
    print('=' * 78)
    print('3) POLICES DU MOTEUR MATHEMATIQUE (preuve du rendu des formules)')
    print('=' * 78)

    polices = [n for n in noms if n.lower().endswith(('.ttf', '.otf'))]
    # KaTeX utilise des polices nommees KaTeX_*
    katex = [n for n in polices if 'katex' in n.lower()]
    print(f'  Polices presentes dans l\'AAB : {len(polices)}')
    for p in sorted(polices):
        taille = z.getinfo(p).file_size
        marqueur = '  <-- KaTeX' if 'katex' in p.lower() else ''
        print(f'    {taille:>9,} o  {p}{marqueur}')

    if katex:
        print(f'  [OK] {len(katex)} polices KaTeX embarquees : le rendu des formules')
        print('       est bien present dans le paquet (pas seulement dans le code).')
    else:
        print('  [ALERTE] Aucune police KaTeX trouvee : les formules risquent de')
        print('           s\'afficher avec des glyphes manquants sur l\'appareil.')

    # ── 4. flutter_svg / vector_graphics (dependances ajoutees) ──────
    print()
    print('=' * 78)
    print('4) DERNIERE MODIFICATION DE L\'ARCHIVE')
    print('=' * 78)
    import os
    import datetime
    st = os.stat(AAB)
    print(f'  Fichier : {AAB}')
    print(f'  Taille  : {st.st_size:,} octets ({st.st_size / 1024 / 1024:.1f} Mo)')
    print(f'  Date    : {datetime.datetime.fromtimestamp(st.st_mtime)}')

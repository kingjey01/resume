"""Inspection (lecture seule) : quelle forme de LaTeX est réellement stockée ?"""
import os
import re
import sys

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resume_backend.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from courses.models import Summary  # noqa: E402

PATTERNS = {
    '$$ bloc': re.compile(r'\$\$'),
    '\\[ bloc': re.compile(r'\\\['),
    '$ inline': re.compile(r'(?<!\$)\$(?!\$)'),
    'commandes \\cmd': re.compile(r'\\[a-zA-Z]+'),
}

print('=' * 78)
print('FORMES DE LATEX PRESENTES DANS LES RESUMES STOCKES')
print('=' * 78)

total = 0
avec_latex = 0
compteurs = {k: 0 for k in PATTERNS}

for s in Summary.objects.all():
    texte = s.texte_resume or ''
    total += 1
    trouve = {k: len(p.findall(texte)) for k, p in PATTERNS.items()}
    if sum(trouve.values()):
        avec_latex += 1
        for k, v in trouve.items():
            if v:
                compteurs[k] += 1
        print(f"  id={s.id} type={s.author_type} len={len(texte)}")
        print(f"     {trouve}")
        print(f"     extrait: {texte[:200]!r}")
        print()

print(f'Resumes en base : {total}')
print(f'Contenant du LaTeX : {avec_latex}')
print()
for k, v in compteurs.items():
    print(f'  resumes avec {k:18s} : {v}')

#!/usr/bin/env python3
"""Rend les fiches Markdown lisibles à l'identique sur GitHub et sur le site.

  python3 scripts/formater-markdown.py            # liste les fichiers à corriger
  python3 scripts/formater-markdown.py --write    # corrige

Le site (MkDocs, moteur Python-Markdown) est plus strict que l'affichage des
fichiers sur GitHub (GFM). Trois écarts y cassaient la mise en page :

  1. listes imbriquées indentées de 2 ou 3 espaces : GitHub les imbrique,
     MkDocs les aplatit. On ramène chaque niveau à 4 espaces, ce que les deux
     moteurs lisent de la même façon ;
  2. liste collée au paragraphe qui la précède (y compris dans une citation
     « > ») : GitHub voit une liste, MkDocs un paragraphe. On insère une ligne
     vide ;
  3. Markdown dans un bloc <details> : GitHub l'interprète, MkDocs l'affiche
     brut. On ajoute markdown="1" à la balise, que GitHub ignore.

Idempotent : un fichier déjà conforme n'est pas touché. Vérifié sur tout le
dépôt avec cmark-gfm (le moteur de GitHub) : le rendu GitHub reste le même.
"""

import argparse
import pathlib
import re

RACINE = pathlib.Path(__file__).resolve().parents[1]
IGNORES = {".git", "site", "venv", ".venv", "node_modules", "docs"}
LI = re.compile(r'^( *)([-*+]|\d+[.)])( +)(.*)$')
FENCE = re.compile(r'^ *(```|~~~)')
DETAILS = re.compile(r'^( *)<details>', re.M)


def reindenter(texte):
    """Ramène chaque niveau de liste imbriquée à 4 espaces."""
    text=texte
    lines=text.split('\n'); out=[]; st=[]  # (old_ind, old_content, new_ind)
    fence=None; fshift=0
    for l in lines:
        l2=l.expandtabs(4) if l[:1]=='\t' or l.startswith(' \t') else l
        if fence is not None:
            if FENCE.match(l2) and l2.strip().startswith(fence): fence=None
            ind=len(l2)-len(l2.lstrip(' '))
            out.append((' '*max(0,ind+fshift)+l2.lstrip(' ')) if l2.strip() else l2); continue
        if not l2.strip(): out.append(l2); continue
        ind=len(l2)-len(l2.lstrip(' '))
        m=LI.match(l2)
        if m and not re.match(r'^ *([-*_])( *\1){2,} *$',l2):
            sp=len(m.group(3)); mk=len(m.group(2))
            while st and (ind<=st[-1][0] or ind<st[-1][1]): st.pop()
            new=st[-1][2]+4 if st else 0
            if not st and ind>=4: out.append(l2); continue  # bloc de code indenté
            st.append((ind, ind+mk+min(sp,4), new))
            out.append(' '*new+l2[ind:]); continue
        if ind==0:
            if FENCE.match(l2): fence=l2.strip()[:3]; fshift=0
            if not st or l2.startswith(('#','|','>')) : st=[]
            out.append(l2); continue
        if st:
            # rattacher à l'élément le plus profond dont la colonne de contenu est atteinte
            j=len(st)-1
            while j>0 and ind<st[j][1]: j-=1
            o_ind,o_c,n_ind=st[j]
            shift=(n_ind+4-o_c) if ind>=o_c else (n_ind+4-ind if ind>o_ind else 0)
            # niveau 0 sans imbrication : ne rien toucher
            if n_ind==0 and j==0 and ind<o_c+4 and not any(s[2] for s in st): shift=0
            if FENCE.match(l2): fence=l2.strip()[:3]; fshift=shift
            out.append(' '*max(0,ind+shift)+l2[ind:]); continue
        if FENCE.match(l2): fence=l2.strip()[:3]; fshift=0
        out.append(l2)
    return '\n'.join(out)


LI0=re.compile(r'^([-*+]|1[.)]) +\S')
def separer(text):
    """Python-Markdown exige une ligne vide entre un paragraphe et la liste qui le suit."""
    out=[]; state='other'; prevpre=None; prevc=''; fence=False
    for l in text.split('\n'):
        m=re.match(r'^((?:> ?)*)(.*)$',l); pre,c=m.group(1),m.group(2)
        if c.lstrip().startswith(('```','~~~')) : fence=not fence
        if fence or c.lstrip().startswith(('```','~~~')):
            out.append(l); prevpre=pre; prevc=c; state='other'; continue
        if pre!=prevpre: state='other'; prevc=''
        if not c.strip(): out.append(l); prevpre=pre; prevc=c; continue
        if LI0.match(c) or re.match(r'^(\d+[.)]|[-*+]) ',c):
            if LI0.match(c) and state=='para' and prevc.strip():
                out.append(pre.rstrip())
            state='list'
        elif c[0] in ' \t': pass
        elif c.startswith(('#','|','<','!!!','???','---','***','___','[^')): state='other'
        elif state=='list' and prevc.strip(): pass   # ligne paresseuse dans un élément
        else: state='para'
        out.append(l); prevpre=pre; prevc=c
    return '\n'.join(out)


def _quotes(text, f):
    """Applique f au contenu des citations (lignes « > »), récursivement."""
    lines=text.split('\n'); out=[]; i=0
    while i<len(lines):
        if lines[i].startswith('>'):
            j=i
            while j<len(lines) and lines[j].startswith('>'): j+=1
            inner=[re.sub(r'^> ?','',l,count=1) for l in lines[i:j]]
            new=_quotes(f('\n'.join(inner)),f).split('\n')
            out+=[('> '+l) if l.strip() else '>' for l in new]
            # conserver les lignes inchangées telles quelles (espaces de fin, etc.)
            if new==inner: out[-len(new):]=lines[i:j]
            i=j
        else: out.append(lines[i]); i+=1
    return '\n'.join(out)

def formater(texte):
    texte = reindenter(texte)
    texte = _quotes(texte, reindenter)
    texte = separer(texte)
    return DETAILS.sub(r'\1<details markdown="1">', texte)


def documents():
    for p in sorted(RACINE.rglob("*.md")):
        if not any(part in IGNORES for part in p.relative_to(RACINE).parts):
            yield p


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--write", action="store_true", help="corrige les fichiers")
    args = p.parse_args()
    a_corriger = []
    for f in documents():
        texte = f.read_text(encoding="utf-8")
        nouveau = formater(texte)
        if nouveau != texte:
            a_corriger.append(f.relative_to(RACINE).as_posix())
            if args.write:
                f.write_text(nouveau, encoding="utf-8")
    if not a_corriger:
        print("état      : déjà à jour")
    else:
        print(f"état      : {len(a_corriger)} fichier(s) — la mise en forme diffère du fichier")
        for nom in a_corriger[:20]:
            print(f"  {nom}")
    print("écriture  : " + ("oui" if args.write else "non — relancer avec --write"))


if __name__ == "__main__":
    main()

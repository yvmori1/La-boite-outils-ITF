#!/usr/bin/env python3
"""Contrôle l'intégrité du dépôt. N'écrit jamais rien.

  python3 scripts/verifier.py            # tous les contrôles
  python3 scripts/verifier.py --bref     # une ligne par contrôle

Rend un code de sortie non nul si un contrôle échoue, ce qui permet de
l'appeler depuis un hook git ou une intégration continue.

Contrôles effectués :
  1. liens Markdown internes morts
  2. liens audio morts
  3. fichiers audio orphelins (aucun lien n'y mène)
  4. fiches vides
  5. compteurs du README racine
  6. Techniques/README.md à jour
  7. blocs « Fiches liées » à jour
  8. menus des sections (.pages) à jour de leur sommaire
  9. graphies concurrentes d'un même terme
 10. couverture des liens dans les formes
 11. mise en forme Markdown compatible GitHub et MkDocs
"""

import argparse
import collections
import pathlib
import re
import subprocess
import sys
import urllib.parse

RACINE = pathlib.Path(__file__).resolve().parents[1]
SCRIPTS = RACINE / "scripts"
AUDIO = RACINE / "audio"
DOSSIERS_FICHES = ("Techniques", "sogi", "chagi", "jirugi", "makgi", "tul",
                   "Ceintures", "Theorie")
IGNORES = {".git", "site", "venv", ".venv", "node_modules", "audio"}

# graphies dont une seule doit subsister ; la première fait référence
GRAPHIES = [
    ("An Palmok", ["anpalmok"]),
    ("Guburyo", ["Goobooryo", "Goburyo"]),
    ("서기", ["소기"]),
    ("mouvement de vague", ["onde de choc (*Sine Wave*)"]),
    # hangul fautifs (voir les notes du glossaire coréen-français)
    ("낮은데", ["낮인데", "나중데", "낮운데"]),
    ("높은데", ["높인데", "높운데"]),
    ("엎은", ["엎운", "오픈손끝"]),
    ("추켜", ["추교"]), ("그 자리 돌기", ["구자리돌기"]), ("구자", ["굿자"]),
    ("앞차기", ["압차기"]), ("걷는", ["건눈"]), ("뚫기", ["툴기"]),
    ("뛰며", ["뛰묘"]), ("쓸어차기", ["수로차기"]),
    # le hangul doit dire le terme romanisé : Tulgi, Narani, Busigi, Miro…
    ("뚫기", ["찌르기", "차틀기"]), ("나란히 서", ["평행 서"]),
    ("부시기", ["부수기"]), ("밀어", ["미뤄"]), ("들어", ["들러"]),
    ("팔굽", ["팔꿈"]), ("낮추어 서", ["낮추 서", "낮춰 서"]), ("뒤차", ["뒷차"]),
    ("멈춰", ["멈춤막기"]), ("기역자", ["기억자"]),
]
# le glossaire cite à dessein les graphies fautives qu'il a corrigées
# (tout le dossier du glossaire, découpé en une page par thème)
EXCEPTIONS_GRAPHIES = ("Theorie/glossaire/",)

LIEN_MD = re.compile(r"\[[^\]]*\]\(([^)#]+\.md)(?:#[^)]*)?\)")
# « audio/ » depuis la racine, « ../audio/ » depuis un dossier
LIEN_AUDIO = re.compile(r"\[[^\]]*\]\(((?:\.\./)*audio/[^)]+)\)")


def documents():
    for p in sorted(RACINE.rglob("*.md")):
        if any(part in IGNORES for part in p.parts):
            continue
        yield p


def controle_liens_md():
    morts = []
    for p in documents():
        for cible in LIEN_MD.findall(p.read_text(encoding="utf-8", errors="ignore")):
            chemin = (p.parent / urllib.parse.unquote(cible)).resolve()
            if not chemin.exists():
                morts.append(f"{p.relative_to(RACINE)} -> {cible}")
    return morts


def controle_liens_audio():
    morts = []
    for p in documents():
        for cible in LIEN_AUDIO.findall(p.read_text(encoding="utf-8", errors="ignore")):
            if not (p.parent / cible).resolve().exists():
                morts.append(f"{p.relative_to(RACINE)} -> {cible}")
    return morts


def controle_audio_orphelins():
    if not AUDIO.is_dir():
        return []
    utilises = set()
    for p in documents():
        for cible in LIEN_AUDIO.findall(p.read_text(encoding="utf-8", errors="ignore")):
            utilises.add((p.parent / cible).resolve())
    return sorted(str(f.relative_to(RACINE))
                  for f in AUDIO.rglob("*.m4a") if f.resolve() not in utilises)


def controle_fiches_vides():
    return sorted(str(p.relative_to(RACINE)) for p in documents()
                  if p.stat().st_size == 0)


def compte_reel(dossier):
    d = RACINE / dossier
    if not d.is_dir():
        return None
    if dossier == "images":
        # images/ et ses diagrammes de formes (images/tul/) ; les schémas sogi/ à part
        return len([f for f in [*d.iterdir(), *(d / "tul").glob("*")]
                    if f.suffix.lower() in (".png", ".svg", ".gif", ".jpg")])
    if dossier == "Theorie":
        # un document découpé en sous-pages compte pour un : son dossier
        return len([f for f in d.iterdir()
                    if f.is_dir() or (f.suffix == ".md" and f.name != "README.md")])
    return len([f for f in d.glob("*.md") if f.name != "README.md"])


def controle_compteurs():
    ecarts = []
    ligne = re.compile(r"\|\s*\[([^\]]+)\]\(([^)]+)/README\.md\)[^|]*\|[^|]*\|\s*(\d+)\s*\|")
    for l in (RACINE / "README.md").read_text(encoding="utf-8").splitlines():
        m = ligne.match(l)
        if m:
            dossier, annonce = m.group(2), int(m.group(3))
            reel = compte_reel(dossier)
            if reel is not None and reel != annonce:
                ecarts.append(f"{dossier} : annoncé {annonce}, réel {reel}")
    return ecarts


def controle_generateur(script, options=()):
    """Le fichier produit est-il identique à ce que le script générerait ?"""
    r = subprocess.run([sys.executable, str(SCRIPTS / script), *options],
                       capture_output=True, text=True)
    if r.returncode:
        return [f"{script} a échoué : {r.stderr.strip().splitlines()[-1:]}"]
    sortie = r.stdout
    if "déjà à jour" in sortie:
        return []
    if "diffère du fichier" in sortie:
        return [f"{script} : le fichier produit n'est plus à jour"]
    m = re.search(r"liens posés à ce tour\s*:\s*(\d+)", sortie)
    if m and int(m.group(1)):
        return [f"{script} : {m.group(1)} lien(s) à poser"]
    return []


def controle_graphies():
    ecarts = []
    for reference, variantes in GRAPHIES:
        for variante in variantes:
            porteurs = [str(p.relative_to(RACINE)) for p in documents()
                        if not p.relative_to(RACINE).as_posix()
                        .startswith(EXCEPTIONS_GRAPHIES)
                        and variante.lower() in p.read_text(
                            encoding="utf-8", errors="ignore").lower()]
            if porteurs:
                ecarts.append(f"« {variante} » au lieu de « {reference} » : "
                              f"{', '.join(porteurs[:4])}"
                              + (" …" if len(porteurs) > 4 else ""))
    return ecarts


def controle_couverture():
    r = subprocess.run([sys.executable, str(SCRIPTS / "lier-mouvements.py"),
                        "--couverture"], capture_output=True, text=True)
    m = re.search(r"(\d+) forme\(s\) complète\(s\) sur (\d+)"
                  r" — (\d+)/(\d+) mouvements liés \((\d+) %\)", r.stdout)
    return [f"{m.group(1)}/{m.group(2)} formes complètes, "
            f"{m.group(3)}/{m.group(4)} mouvements liés ({m.group(5)} %)"] if m else []


CONTROLES = [
    ("liens Markdown morts", controle_liens_md, True),
    ("liens audio morts", controle_liens_audio, True),
    ("fichiers audio orphelins", controle_audio_orphelins, False),
    ("fiches vides", controle_fiches_vides, False),
    ("compteurs du README racine", controle_compteurs, True),
    ("index Techniques à jour",
     lambda: controle_generateur("generer-index-techniques.py"), True),
    ("fiches liées à jour",
     lambda: controle_generateur("generer-voir-aussi.py"), True),
    ("menus des sections à jour",
     lambda: controle_generateur("generer-menus.py"), True),
    ("planches des points vitaux à jour",
     lambda: controle_generateur("generer-points-vitaux.py"), True),
    ("graphies concurrentes", controle_graphies, True),
    ("couverture des formes", controle_couverture, False),
    ("mise en forme Markdown",
     lambda: controle_generateur("formater-markdown.py"), True),
]


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--bref", action="store_true",
                   help="n'affiche pas le détail des anomalies")
    args = p.parse_args()

    echecs = 0
    for intitule, fonction, bloquant in CONTROLES:
        resultats = fonction()
        if not resultats:
            print(f"  ok    {intitule}")
            continue
        if not bloquant:
            print(f"  info  {intitule} : {len(resultats)}")
        else:
            echecs += 1
            print(f"  ÉCHEC {intitule} : {len(resultats)}")
        if not args.bref:
            for r in resultats[:10]:
                print(f"          {r}")
            if len(resultats) > 10:
                print(f"          … et {len(resultats) - 10} autres")

    print()
    print("dépôt conforme" if not echecs
          else f"{echecs} contrôle(s) en échec — voir scripts/maintenir.py")
    return 1 if echecs else 0


if __name__ == "__main__":
    sys.exit(main())

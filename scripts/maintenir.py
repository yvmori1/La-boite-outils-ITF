#!/usr/bin/env python3
"""Remet le dépôt en cohérence : enchaîne tous les générateurs, puis contrôle.

  python3 scripts/maintenir.py            # essai à blanc, n'écrit rien
  python3 scripts/maintenir.py --write    # applique tout
  python3 scripts/maintenir.py --write --sans-audio   # sans la synthèse vocale

Étapes, dans l'ordre — chacune dépend des précédentes :

  1. index de Techniques/           (les fiches ont pu changer)
  2. compteurs du README racine     (d'après le contenu réel des dossiers)
  3. graphies normalisées           (variantes sans ambiguïté)
  4. liens des formes vers les fiches, fiches liées, lectures par grade et
     révisions de fin de partie, infobulles du glossaire
  5. prononciations et liens audio  (fiches, manuel, pages de Combat/)
  6. réparation des audio manquants
  7. menus des sections (.pages)    (d'après les sommaires README)
  8. mise en forme Markdown         (listes lisibles sur GitHub et le site)
  9. contrôle final (scripts/verifier.py)

À lancer après avoir ajouté des fiches, renommé un fichier ou corrigé une
romanisation. Chaque étape est idempotente : sans changement, elle ne fait rien.
"""

import argparse
import pathlib
import re
import shutil
import subprocess
import sys

RACINE = pathlib.Path(__file__).resolve().parents[1]
SCRIPTS = RACINE / "scripts"

# substitutions sûres : la chaîne cherchée ne désigne qu'une seule chose.
# Les variantes ambiguës restent signalées par verifier.py, pas corrigées ici.
GRAPHIES = [
    ("Goobooryo", "Guburyo"),
    ("goobooryo", "guburyo"),
    ("Goburyo", "Guburyo"),
    ("anpalmok", "an palmok"),
    ("l'Onde de Choc (*Sine Wave*)", "le Mouvement de Vague (*Sine Wave*)"),
    ("l'onde de choc (*Sine Wave*)", "le mouvement de vague (*Sine Wave*)"),
    ("de l'onde de choc (*Sine Wave*)", "du mouvement de vague (*Sine Wave*)"),
    # hangul fautifs, corrigés d'après le glossaire coréen-français
    ("낮인데", "낮은데"), ("나중데", "낮은데"), ("낮운데", "낮은데"),
    ("높인데", "높은데"), ("높운데", "높은데"),
    ("오픈손끝", "엎은손끝"), ("엎운", "엎은"),
    ("추교", "추켜"), ("구자리돌기", "그 자리 돌기"), ("굿자", "구자"),
    ("압차기", "앞차기"), ("건눈", "걷는"), ("툴기", "뚫기"), ("뛰묘", "뛰며"),
    ("수로차기", "쓸어차기"),
]
IGNORES = {".git", "site", "venv", ".venv", "audio", "scripts", "docs"}
# le glossaire cite à dessein les graphies fautives qu'il a corrigées
# (tout le dossier du glossaire, découpé en une page par thème)
EXCEPTIONS = ("Theorie/glossaire/",)


def lancer(script, options, ecrire):
    """Exécute un script du dossier et rend (titre, lignes de compte-rendu)."""
    cmd = [sys.executable, str(SCRIPTS / script), *options]
    if ecrire:
        cmd.append("--write")
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        return [f"ÉCHEC : {r.stderr.strip().splitlines()[-1] if r.stderr else '?'}"]
    return [l for l in r.stdout.splitlines() if l.strip()]


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


def compteurs(ecrire):
    """Aligne les nombres de fiches du tableau du README racine."""
    fichier = RACINE / "README.md"
    lignes = fichier.read_text(encoding="utf-8").splitlines()
    motif = re.compile(r"(\|\s*\[[^\]]+\]\(([^)]+)/README\.md\)[^|]*\|[^|]*\|\s*)(\d+)(\s*\|)")
    corriges = []
    for i, l in enumerate(lignes):
        m = motif.match(l)
        if not m:
            continue
        reel = compte_reel(m.group(2))
        if reel is not None and reel != int(m.group(3)):
            corriges.append(f"{m.group(2)} : {m.group(3)} -> {reel}")
            lignes[i] = f"{m.group(1)}{reel}{m.group(4)}"
    if corriges and ecrire:
        fichier.write_text("\n".join(lignes) + "\n", encoding="utf-8")
    return corriges or ["aucun écart"]


def graphies(ecrire):
    """Applique les substitutions sans ambiguïté."""
    corriges = []
    for p in sorted(RACINE.rglob("*.md")):
        if any(part in IGNORES for part in p.parts) \
                or p.relative_to(RACINE).as_posix().startswith(EXCEPTIONS):
            continue
        t = p.read_text(encoding="utf-8", errors="ignore")
        nouveau = t
        for a, b in GRAPHIES:
            nouveau = nouveau.replace(a, b)
        if nouveau != t:
            corriges.append(str(p.relative_to(RACINE)))
            if ecrire:
                p.write_text(nouveau, encoding="utf-8")
    return [f"{len(corriges)} fichier(s) : " + ", ".join(corriges[:5])
            + (" …" if len(corriges) > 5 else "")] if corriges else ["aucun écart"]


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--write", action="store_true", help="applique les corrections")
    p.add_argument("--sans-audio", action="store_true",
                   help="saute la synthèse vocale, longue à produire")
    args = p.parse_args()

    etapes = [
        ("index de Techniques", lambda: lancer("generer-index-techniques.py",
                                               [], args.write)),
        ("compteurs du README", lambda: compteurs(args.write)),
        ("graphies normalisées", lambda: graphies(args.write)),
        ("liens des formes", lambda: lancer("lier-mouvements.py", [], args.write)),
        # les fiches liées se calculent d'après les liens que les formes portent
        ("fiches liées", lambda: lancer("generer-voir-aussi.py", [], args.write)),
        ("parcours et révisions", lambda: lancer("generer-parcours.py", [], args.write)),
        ("infobulles du glossaire",
         lambda: lancer("generer-infobulles.py", [], args.write)),
    ]
    if not args.sans_audio:
        # hors macOS, pas de synthèse : on lie seulement les hangul dont
        # l'audio existe déjà, le reste attend un passage sur Mac
        synthese = [] if shutil.which("say") else ["--sans-synthese"]
        etapes += [
            ("prononciations", lambda: lancer(
                "generer-audio.py", ["--tout", *synthese], args.write)),
            ("audio manquants", lambda: lancer(
                "generer-audio.py", ["--reparer", *synthese], args.write)),
            # les libellés des fiches ont pu recevoir des liens audio : l'index
            # qui les reprend doit suivre
            ("index de Techniques (après les liens audio)",
             lambda: lancer("generer-index-techniques.py", [], args.write)),
        ]
    # le menu suit les sommaires, que les étapes ci-dessus ont pu réécrire
    etapes.append(("menus des sections",
                   lambda: lancer("generer-menus.py", [], args.write)))
    # en dernier : les générateurs ci-dessus ont pu réécrire des listes
    etapes.append(("mise en forme Markdown (GitHub et site)",
                   lambda: lancer("formater-markdown.py", [], args.write)))

    for titre, action in etapes:
        print(f"\n=== {titre}")
        for ligne in action():
            print(f"  {ligne}")

    if not args.write:
        print("\nessai à blanc — relancer avec --write pour appliquer")
        return 0

    print("\n=== contrôle final")
    r = subprocess.run([sys.executable, str(SCRIPTS / "verifier.py")],
                       capture_output=True, text=True)
    print(r.stdout.rstrip())
    return r.returncode


if __name__ == "__main__":
    sys.exit(main())

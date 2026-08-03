#!/usr/bin/env python3
"""Produit la prononciation coréenne de chaque fiche et l'y relie.

  python3 scripts/generer-audio.py                 # essai à blanc
  python3 scripts/generer-audio.py --write         # génère l'audio et les liens
  python3 scripts/generer-audio.py --write --force # régénère même l'audio existant
  python3 scripts/generer-audio.py --limite 5      # s'arrête après 5 fiches

Pour chaque fiche de Techniques/, chagi/, jirugi/, makgi/ et tul/ :

  1. le hangul est lu dans la première phrase — « Le **Nom** (한글) est le… » ;
     pour les formes (tul/), il vient de la table NOMS_TUL ci-dessous ;
  2. un fichier audio/<dossier>/<nom-de-la-fiche>.m4a est produit par la synthèse
     coréenne de macOS (commande `say`, voix Yuna par défaut) ;
  3. un lien vers ce fichier est inséré dans la fiche, juste sous le titre.

Le script est idempotent : une fiche qui porte déjà son lien n'est pas retouchée
et son audio n'est pas régénéré, sauf avec --force. Une fiche sans hangul est
laissée intacte et signalée dans le rapport final.

Dépend de macOS : `say` et `afconvert`.
"""

import argparse
import pathlib
import re
import subprocess
import sys

RACINE = pathlib.Path(__file__).resolve().parents[1]
AUDIO = RACINE / "audio"
DOSSIERS = ("Techniques", "chagi", "jirugi", "makgi", "tul")
HORS_TRAITEMENT = {"README.md", "Dans-les-formes.md", "nomenclature.md"}

VOIX = "Yuna"
DEBIT = 130

# Noms des formes en hangul : absents des fiches, donc fournis ici.
# À vérifier par un pratiquant — ils ne proviennent pas du dépôt.
NOMS_TUL = {
    "saju-jirugi": "사주 지르기", "saju-makgi": "사주 막기",
    "saju-tulgi": "사주 뚫기",
    "chon-ji": "천지", "dan-gun": "단군", "do-san": "도산",
    "won-hyo": "원효", "yul-gok": "율곡", "joong-gun": "중근",
    "toi-gye": "퇴계", "hwa-rang": "화랑", "choong-moo": "충무",
    "kwang-gae": "광개", "po-eun": "포은", "ge-baek": "계백",
    "eui-am": "의암", "choong-jang": "충장", "juche": "주체",
    "ko-dang": "고당", "sam-il": "삼일", "yoo-sin": "유신",
    "choi-yong": "최영", "yon-gae": "연개", "ul-ji": "을지",
    "moon-moo": "문무", "so-san": "서산", "se-jong": "세종",
    "tong-il": "통일",
}

# Un jamo isolé se lit par son nom : « ㄴ자 » se prononce « 니은자 ».
JAMO = {"ㄱ": "기역", "ㄴ": "니은", "ㄷ": "디귿", "ㄹ": "리을", "ㅁ": "미음",
        "ㅂ": "비읍", "ㅅ": "시옷", "ㅇ": "이응", "ㅈ": "지읒", "ㅊ": "치읓",
        "ㅋ": "키읔", "ㅌ": "티읕", "ㅍ": "피읖", "ㅎ": "히읗"}

HANGUL = re.compile(r"[가-힣ㄱ-ㅎ]")
INTRO = re.compile(r"\*\*(.+?)\*\*\s*\(([^)]*[가-힣ㄱ-ㅎ][^)]*)\)")
DEBUT_HANGUL = re.compile(r"^[가-힣ㄱ-ㅎ][가-힣ㄱ-ㅎ\s]*")
TITRE = re.compile(r"^#\s+.+$")
MARQUE = "audio/"          # présence d'un lien audio déjà posé


def texte_coreen(fiche):
    """Le hangul à prononcer, ou None si la fiche n'en donne pas."""
    if fiche.parent.name == "tul":
        return NOMS_TUL.get(fiche.stem)
    m = INTRO.search(fiche.read_text(encoding="utf-8"))
    if not m:
        return None
    d = DEBUT_HANGUL.match(m.group(2).strip())
    if not d:
        return None
    texte = " ".join(d.group(0).split())
    return texte or None


def pour_synthese(texte):
    """Remplace les jamo isolés par leur nom, sinon ils sont épelés."""
    for jamo, nom in JAMO.items():
        texte = texte.replace(jamo, nom)
    return texte


def produire_audio(texte, cible, voix, debit):
    aiff = cible.with_suffix(".aiff")
    subprocess.run(["say", "-v", voix, "-r", str(debit), "-o", str(aiff),
                    pour_synthese(texte)], check=True)
    subprocess.run(["afconvert", "-f", "m4af", "-d", "aac",
                    str(aiff), str(cible)], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    aiff.unlink(missing_ok=True)
    # un lien ne doit jamais pointer vers un fichier absent ou vide
    if not cible.exists() or cible.stat().st_size < 1000:
        raise RuntimeError(f"audio non produit ou vide : {cible.name}")


def inserer_lien(fiche, texte, nom_audio):
    """Ajoute le lien sous le titre. Rend le nouveau contenu, ou None."""
    contenu = fiche.read_text(encoding="utf-8")
    if MARQUE in contenu:
        return None
    lignes = contenu.splitlines(keepends=True)
    i = next((k for k, l in enumerate(lignes) if TITRE.match(l.rstrip())), None)
    if i is None:
        return None
    lien = (f"\n> 🔊 **Prononciation :** [{texte}]"
            f"(../audio/{nom_audio})\n")
    lignes.insert(i + 1, lien)
    return "".join(lignes)


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--write", action="store_true",
                   help="produit l'audio et insère les liens")
    p.add_argument("--force", action="store_true",
                   help="régénère l'audio même s'il existe déjà")
    p.add_argument("--limite", type=int, default=0,
                   help="s'arrête après N fiches (pour essai)")
    p.add_argument("--voix", default=VOIX, help=f"voix `say` (défaut : {VOIX})")
    p.add_argument("--debit", type=int, default=DEBIT,
                   help=f"mots par minute (défaut : {DEBIT})")
    args = p.parse_args()

    if args.write:
        for outil in ("say", "afconvert"):
            if subprocess.run(["which", outil],
                              stdout=subprocess.DEVNULL).returncode:
                sys.exit(f"{outil} introuvable — ce script requiert macOS")
        AUDIO.mkdir(exist_ok=True)

    compte = dict(fiches=0, sans_hangul=0, audio=0, deja_audio=0,
                  liens=0, deja_lies=0)
    sans_hangul = []

    for dossier in DOSSIERS:
        for fiche in sorted((RACINE / dossier).glob("*.md")):
            if fiche.name in HORS_TRAITEMENT:
                continue
            if args.limite and compte["fiches"] >= args.limite:
                break
            compte["fiches"] += 1

            texte = texte_coreen(fiche)
            if not texte or not HANGUL.search(texte):
                compte["sans_hangul"] += 1
                sans_hangul.append(f"{dossier}/{fiche.name}")
                continue

            nom_audio = f"{dossier}/{fiche.stem}.m4a"
            cible = AUDIO / nom_audio
            cible.parent.mkdir(parents=True, exist_ok=True)
            if cible.exists() and not args.force:
                compte["deja_audio"] += 1
            elif args.write:
                produire_audio(texte, cible, args.voix, args.debit)
                compte["audio"] += 1
            else:
                compte["audio"] += 1

            nouveau = inserer_lien(fiche, texte, nom_audio)
            if nouveau is None:
                compte["deja_lies"] += 1
            else:
                compte["liens"] += 1
                if args.write:
                    fiche.write_text(nouveau, encoding="utf-8")

    print(f"fiches parcourues     : {compte['fiches']}")
    print(f"  sans hangul         : {compte['sans_hangul']}")
    print(f"audio à produire      : {compte['audio']}")
    print(f"  déjà présent        : {compte['deja_audio']}")
    print(f"liens à insérer       : {compte['liens']}")
    print(f"  déjà en place       : {compte['deja_lies']}")
    print("écriture              : " + ("OUI" if args.write
                                        else "non — relancer avec --write"))
    if sans_hangul:
        print(f"\nfiches sans hangul ({len(sans_hangul)}) :")
        for nom in sans_hangul:
            print(f"  {nom}")


if __name__ == "__main__":
    main()

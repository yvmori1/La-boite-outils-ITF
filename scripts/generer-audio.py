#!/usr/bin/env python3
"""Produit la prononciation coréenne de chaque fiche et l'y relie.

  python3 scripts/generer-audio.py                 # essai à blanc
  python3 scripts/generer-audio.py --write         # génère l'audio et les liens
  python3 scripts/generer-audio.py --write --force # régénère même l'audio existant
  python3 scripts/generer-audio.py --limite 5      # s'arrête après 5 fiches
  python3 scripts/generer-audio.py --lexique       # traite aussi Theorie/Lexique.md

Pour chaque fiche de Techniques/, chagi/, jirugi/, makgi/ et tul/ :

  1. le hangul est lu dans la première phrase — « Le **Nom** (한글) est le… » ;
     pour les formes (tul/), il vient de la table NOMS_TUL ci-dessous ;
  2. un fichier audio/<dossier>/<nom-de-la-fiche>.m4a est produit par la synthèse
     coréenne de macOS (commande `say`, voix Yuna par défaut) ;
  3. un lien vers ce fichier est inséré dans la fiche, juste sous le titre.

Le script est idempotent : une fiche qui porte déjà son lien n'est pas retouchée
et son audio n'est pas régénéré, sauf avec --force. Une fiche sans hangul est
laissée intacte et signalée dans le rapport final.

Avec --lexique, Theorie/Lexique.md reçoit une colonne « Hangul » dont chaque
entrée est un lien vers sa prononciation. Le hangul est cherché d'abord dans
les fiches du dépôt, puis dans la table LEXIQUE_HANGUL ci-dessous. Un terme
déjà couvert par une fiche renvoie vers l'audio de cette fiche plutôt que d'en
produire un doublon. Un terme dont le hangul reste introuvable est laissé vide
et signalé : aucun hangul n'est deviné.

Dépend de macOS : `say` et `afconvert`.
"""

import argparse
import collections
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

# Vocabulaire absent des fiches : préceptes, commandements et positions.
# Fourni ici faute de source dans le dépôt — à vérifier par un pratiquant.
LEXIQUE_HANGUL = {
    "ye ui": "예의", "yum chi": "염치", "in nae": "인내",
    "guk gi": "극기", "baekjul boolgool": "백절불굴",
    "taekwon-do jungshin": "태권도 정신",
    "junbi sogi": "준비 서기", "moa sogi": "모아 서기",
    "moa junbi sogi": "모아 준비 서기", "narani sogi": "나란히 서기",
    "narani junbi sogi": "나란히 준비 서기", "gunnun sogi": "걷는 서기",
    "gunnun so junbi sogi": "걷는 서 준비 서기", "niunja sogi": "니은자 서기",
    "annun sogi": "앉은 서기", "kyocha sogi": "교차 서기",
    "sasun sogi": "사선 서기", "gojung sogi": "고정 서기",
    "nachuo sogi": "낮추어 서기", "soo jik sogi": "수직 서기",
    "waebal sogi": "외발 서기", "dwitbal sogi": "뒷발 서기",
    "guburyo sogi": "구부려 서기",
    "guburyo junbi sogi": "구부려 준비 서기",
    "palja sogi": "팔자 서기",
    # commandements et vocabulaire de salle
    "charyot": "차렷", "swiyo": "쉬어", "dojang": "도장", "tul": "틀",
    "kyong ye jase": "경례 자세",
    # composés dont chaque élément est attesté dans les fiches du dépôt
    "ap jirugi": "앞 지르기", "yop jirugi": "옆 지르기",
    "kaunde jirugi": "가운데 지르기", "najunde jirugi": "낮은데 지르기",
    "nopunde jirugi": "높은데 지르기", "baro jirugi": "바로 지르기",
    "bandae jirugi": "반대 지르기", "dollyo jirugi": "돌려 지르기",
    "sewo-jirugi": "세워 지르기", "najunde tulgi": "낮은데 찌르기",
    "sonkal taerigi": "손칼 때리기", "sonkal dung taerigi": "손칼등 때리기",
    "bakuro taerigi": "바깥으로 때리기", "sonbadak taerigi": "손바닥 때리기",
    "yop sonkal taerigi": "옆 손칼 때리기",
    "ap palkup taerigi": "앞 팔굽 때리기",
    "yop palkup tulgi": "옆 팔굽 찌르기",
    "sun sonkut tulgi": "선 손끝 찌르기",
    "bakat makgi": "바깥 막기", "duro makgi": "들어 막기",
    "yobap makgi": "옆앞 막기",
    # déplacements (Dolgi) — composés à partir de 옮겨 디디며 / 돌기 / 나가기
    "mikulgi": "미끄기", "gujari dolgi": "그 자리 돌기",
    "didimyo nagagi": "디디며 나가기",
    "didimyo duruogi": "디디며 들어가기",
    "opuro omgyo didimyo": "앞으로 옮겨 디디며",
    "dwiro omgyo didimyo dolgi": "뒤로 옮겨 디디며 돌기",
    "ibo omgyo didimyo nagagi": "이보 옮겨 디디며 나가기",
    "ibo omgyo didimyo duruggi": "이보 옮겨 디디며 들어가기",
    "ibo omgyo didimyo dolgi": "이보 옮겨 디디며 돌기",
    "omgyo didigo mikulmyo dolgi": "옮겨 디디고 미끄며 돌기",
    "durogamyo jajunbal": "들어가며 자진발",
    # coups de poing — composants attestés dans les fiches du dépôt
    "op jirugi": "앞 지르기", "japgo jirugi": "잡고 지르기",
    "galcho jirugi": "걸쳐 지르기", "soop yong jirugi": "수평 지르기",
    "songarak joomuk jirugi": "손가락 주먹 지르기",
    "ghin joomuk jirugi": "긴 주먹 지르기",
    "joongi joomuk jirugi": "중지 주먹 지르기",
    "pyun joomuk jirugi": "편 주먹 지르기",
    "song joomuk sewo jirugi": "쌍 주먹 세워 지르기",
    "sang dwijibo jirugi": "쌍 뒤집어 지르기",
    "dwijibo jirugi": "뒤집어 지르기",
    "dlyo jirugi": "올려 지르기",
    "digutja jirugi": "디귿자 지르기",
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


# ---------------------------------------------------------------- lexique

LEXIQUE = RACINE / "Theorie" / "Lexique.md"
SEPARATEUR_TABLE = re.compile(r"^\|[\s:-]+\|")


def cle(s):
    """Clé de comparaison : sans casse, sans tiret, sans espace."""
    s = re.sub(r"[^a-z0-9 ]", " ", s.lower().replace("-", " "))
    return "".join(s.split())


def index_des_fiches():
    """{clé du nom de fiche: (hangul, chemin audio relatif)} pour tout le dépôt."""
    index = {}
    for dossier in DOSSIERS:
        for fiche in sorted((RACINE / dossier).glob("*.md")):
            if fiche.name in HORS_TRAITEMENT:
                continue
            texte = texte_coreen(fiche)
            if texte:
                index.setdefault(cle(fiche.stem),
                                 (texte, f"{dossier}/{fiche.stem}.m4a"))
    return index


def lignes_du_lexique(contenu):
    """Rend (indice, colonnes) pour chaque ligne de données des tables."""
    for i, ligne in enumerate(contenu.splitlines()):
        if not ligne.startswith("|") or SEPARATEUR_TABLE.match(ligne):
            continue
        colonnes = [c.strip() for c in ligne.split("|")[1:-1]]
        if len(colonnes) >= 3 and colonnes[2] not in ("", "Terme coréen"):
            yield i, colonnes


def poser(ligne, valeur, nb_colonnes):
    """Écrit la valeur dans la dernière cellule, qu'elle existe ou non."""
    ligne = ligne.rstrip()
    if nb_colonnes >= 4:
        # remplace le contenu de la dernière cellule, vide ou non
        return re.sub(r"\|[^|]*\|\s*$", f"| {valeur} |", ligne)
    return f"{ligne} {valeur} |"


def traiter_lexique(args):
    """Ajoute la colonne Hangul liée à l'audio. Rend un compte-rendu."""
    contenu = LEXIQUE.read_text(encoding="utf-8")
    lignes = contenu.splitlines()
    index = index_des_fiches()
    compte = collections.Counter()
    introuvables, ecarts = [], []

    for i, colonnes in lignes_du_lexique(contenu):
        terme = colonnes[2]
        # cellule déjà liée : intacte. Cellule contenant un hangul saisi à la
        # main : ce hangul fait foi, on lui ajoute son lien. Cellule vide :
        # on la complète depuis le dépôt ou la table interne.
        cellule = colonnes[3] if len(colonnes) >= 4 else ""
        if "](" in cellule:
            compte["deja"] += 1
            continue
        saisi = cellule if HANGUL.search(cellule) else None
        if terme == "-":
            lignes[i] = poser(lignes[i], "-", len(colonnes))
            compte["sans_terme"] += 1
            continue

        k = cle(terme)
        if saisi:
            hangul = saisi
            # l'audio d'une fiche n'est réutilisé que si son hangul est
            # identique : sinon le son dirait autre chose que l'étiquette
            if k in index and index[k][0] == saisi:
                audio = index[k][1]
                compte["saisi_fiche"] += 1
            else:
                if k in index:
                    ecarts.append((terme, saisi, index[k][0]))
                audio = f"lexique/{re.sub(r'[^A-Za-z0-9]+', '-', terme).strip('-')}.m4a"
                compte["saisi"] += 1
        elif k in index:
            hangul, audio = index[k]
            compte["fiche"] += 1
        elif k in {cle(x): x for x in LEXIQUE_HANGUL}:
            vrai = {cle(x): x for x in LEXIQUE_HANGUL}[k]
            hangul = LEXIQUE_HANGUL[vrai]
            audio = f"lexique/{re.sub(r'[^A-Za-z0-9]+', '-', terme).strip('-')}.m4a"
            compte["table"] += 1
        else:
            lignes[i] = poser(lignes[i], "", len(colonnes))
            introuvables.append(terme)
            compte["introuvable"] += 1
            continue

        cible = AUDIO / audio
        if not cible.exists():
            if args.write:
                cible.parent.mkdir(parents=True, exist_ok=True)
                produire_audio(hangul, cible, args.voix, args.debit)
            compte["audio"] += 1
        lignes[i] = poser(lignes[i], f"[{hangul}](../audio/{audio})",
                          len(colonnes))

    # en-têtes et séparateurs des tables
    for i, ligne in enumerate(lignes):
        if ligne.startswith("|") and "Terme coréen" in ligne \
                and "Hangul" not in ligne:
            lignes[i] = ligne.rstrip() + " Hangul |"
        elif SEPARATEUR_TABLE.match(ligne or "") \
                and ligne.rstrip().count("|") == 4:
            lignes[i] = ligne.rstrip() + " :--- |"

    if args.write:
        LEXIQUE.write_text("\n".join(lignes) + "\n", encoding="utf-8")
    return compte, introuvables, ecarts


# ------------------------------------------------------- documents libres

# toute suite de hangul du document (les lignes déjà liées sont ignorées)
SUITE_HANGUL = re.compile(r"[가-힣][가-힣\s]*")


def romanisation_precedente(ligne, position):
    """Dernier terme romanisé en gras ou italique avant la position donnée."""
    avant = ligne[:position]
    # d'abord la romanisation qui précède immédiatement le hangul, car elle
    # le désigne ; le terme en gras peut être la traduction française
    m = re.search(r"([A-Za-z][A-Za-z'’ \-]{2,40}?)\s*[/(]\s*$", avant)
    if m:
        return m.group(1).strip()
    dernier = None
    for dernier in re.finditer(r"\*{1,2}([A-Za-z][A-Za-z'’ \-]{1,40}?)\s*[\*(/]",
                               avant):
        pass
    return dernier.group(1).strip() if dernier else None


def index_par_hangul():
    """{hangul: chemin audio} d'après tous les liens déjà posés dans le dépôt.

    Le critère de réemploi est le hangul lui-même : deux textes identiques
    doivent renvoyer au même enregistrement, quelle que soit leur origine.
    """
    index = {}
    for md in RACINE.rglob("*.md"):
        if ".git" in str(md):
            continue
        for han, audio in re.findall(
                r"\[([가-힣ㄱ-ㅎ][가-힣ㄱ-ㅎ\s]*)\]\(\.\./audio/([^)]+)\)",
                md.read_text(encoding="utf-8", errors="ignore")):
            index.setdefault(han.strip(), audio)
    for dossier in DOSSIERS:
        for fiche in sorted((RACINE / dossier).glob("*.md")):
            if fiche.name in HORS_TRAITEMENT:
                continue
            texte = texte_coreen(fiche)
            if texte:
                index.setdefault(texte, f"{dossier}/{fiche.stem}.m4a")
    return index


def lier_document(chemin, sous_dossier, args):
    """Transforme chaque hangul du document en lien vers sa prononciation."""
    contenu = chemin.read_text(encoding="utf-8")
    index = index_par_hangul()
    compte = collections.Counter()
    sortie = []

    for ligne in contenu.splitlines():
        if "](" in ligne and "audio/" in ligne:      # ligne déjà traitée
            compte["deja"] += 1
            sortie.append(ligne)
            continue

        def remplacer(m):
            texte = m.group(0).strip()
            if not texte:
                return m.group(0)
            terme = romanisation_precedente(ligne, m.start()) or ""
            if texte in index:
                audio = index[texte]                 # même hangul : réemploi
                compte["reemploi"] += 1
            else:
                base = re.sub(r"[^A-Za-z0-9]+", "-", terme).strip("-") \
                    if terme else hangul.strip()
                audio = f"{sous_dossier}/{base}.m4a"
                compte["propre"] += 1
            cible = AUDIO / audio
            if not cible.exists():
                if args.write:
                    cible.parent.mkdir(parents=True, exist_ok=True)
                    produire_audio(texte, cible, args.voix, args.debit)
                compte["audio"] += 1
            # l'espace final éventuel est rendu au texte, pas au lien
            espace = m.group(0)[len(m.group(0).rstrip()):]
            return f"[{texte}](../audio/{audio}){espace}"

        ligne = SUITE_HANGUL.sub(remplacer, ligne)
        sortie.append(ligne)

    if args.write:
        chemin.write_text("\n".join(sortie) + "\n", encoding="utf-8")
    return compte


def reparer(args):
    """Reproduit l'audio de tout lien dont le fichier a disparu.

    Sert après correction d'un libellé : on supprime l'audio devenu faux,
    puis cette passe le régénère à partir du texte corrigé.
    """
    compte = collections.Counter()
    for md in sorted(RACINE.rglob("*.md")):
        if ".git" in str(md):
            continue
        for label, rel in re.findall(
                r"\[([가-힣ㄱ-ㅎ][^\]]*)\]\(\.\./audio/([^)]+)\)",
                md.read_text(encoding="utf-8", errors="ignore")):
            cible = AUDIO / rel
            compte["liens"] += 1
            if cible.exists():
                continue
            compte["manquants"] += 1
            if args.write:
                cible.parent.mkdir(parents=True, exist_ok=True)
                produire_audio(label.strip(), cible, args.voix, args.debit)
                compte["produits"] += 1
    return compte


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
    p.add_argument("--lexique", action="store_true",
                   help="traite aussi Theorie/Lexique.md")
    p.add_argument("--grammaire", action="store_true",
                   help="lie les hangul de Theorie/grammaire-itf.md")
    p.add_argument("--reparer", action="store_true",
                   help="reproduit l'audio des liens dont le fichier manque")
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

    if args.reparer:
        c = reparer(args)
        print(f"liens audio vérifiés  : {c['liens']}")
        print(f"  fichiers manquants  : {c['manquants']}")
        print(f"  reproduits          : {c['produits']}")
        return

    if args.grammaire:
        c = lier_document(RACINE / "Theorie" / "grammaire-itf.md",
                          "grammaire", args)
        print("\ngrammaire-itf.md")
        print(f"  hangul liés               : {c['reemploi'] + c['propre']}")
        print(f"    réemploi d'un audio     : {c['reemploi']}")
        print(f"    audio propre            : {c['propre']}")
        print(f"  audio à produire          : {c['audio']}")
        print(f"  lignes déjà traitées      : {c['deja']}")

    if args.lexique:
        compte, introuvables, ecarts = traiter_lexique(args)
        print("\nLexique.md")
        print(f"  hangul repris d'une fiche : {compte['fiche']}")
        print(f"  hangul saisi à la main    : {compte['saisi'] + compte['saisi_fiche']}"
              f" (dont {compte['saisi_fiche']} réutilisant l'audio d'une fiche)")
        print(f"  hangul de la table interne: {compte['table']}")
        print(f"  audio à produire          : {compte['audio']}")
        print(f"  sans terme coréen         : {compte['sans_terme']}")
        print(f"  déjà traité               : {compte['deja']}")
        print(f"  hangul introuvable        : {compte['introuvable']}")
        if ecarts:
            print("\n  hangul saisi différent de celui de la fiche :")
            for terme, a, b in ecarts:
                print(f"    {terme} : lexique « {a} »  /  fiche « {b} »")
        if introuvables:
            print("\n  termes sans hangul (laissés vides) :")
            for terme in introuvables:
                print(f"    {terme}")


if __name__ == "__main__":
    main()

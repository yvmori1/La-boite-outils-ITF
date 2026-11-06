#!/usr/bin/env python3
"""Produit la prononciation coréenne de chaque fiche et l'y relie.

  python3 scripts/generer-audio.py                 # essai à blanc
  python3 scripts/generer-audio.py --write         # génère l'audio et les liens
  python3 scripts/generer-audio.py --write --force # régénère même l'audio existant
  python3 scripts/generer-audio.py --limite 5      # s'arrête après 5 fiches
  python3 scripts/generer-audio.py --manuel        # lie les hangul du manuel
  python3 scripts/generer-audio.py --combats       # lie les hangul des pages de Combat/
  python3 scripts/generer-audio.py --tout          # lie les hangul de tout le site
  python3 scripts/generer-audio.py --tout --sans-synthese --write
                                                   # hors macOS : réemploi seul

Pour chaque fiche de Techniques/, sogi/, chagi/, jirugi/, makgi/ et tul/ :

  1. le hangul est lu dans la première phrase — « Le **Nom** (한글) est le… » ;
     pour les formes (tul/), il vient de la table NOMS_TUL ci-dessous ;
  2. un fichier audio/<dossier>/<nom-de-la-fiche>.m4a est produit par la synthèse
     coréenne de macOS (commande `say`, voix Yuna par défaut) ;
  3. un lien vers ce fichier est inséré dans la fiche, juste sous le titre.

Le script est idempotent : une fiche qui porte déjà son lien n'est pas retouchée
et son audio n'est pas régénéré, sauf avec --force. Une fiche sans hangul est
laissée intacte et signalée dans le rapport final.

Avec --manuel ou --combats, chaque hangul du document visé devient un lien vers
sa prononciation : pour le manuel, la grammaire, les positions et le lexique en
annexe sont traités d'un seul tenant. Un hangul déjà couvert par une fiche ou
par un autre document renvoie vers l'audio existant plutôt que d'en produire un
doublon — y compris lorsqu'il revient plusieurs fois dans le même document ; une
ligne déjà liée n'est pas retouchée.

Ce sont les deux fiches Lexique.md et grammaire-itf.md, aujourd'hui fusionnées
dans le manuel, que --manuel remplace. Leurs anciens indicateurs --lexique et
--grammaire restent acceptés et font la même chose.

Avec --tout, ce même traitement s'étend à chaque document publié du site : les
fiches (au-delà de leur ligne de prononciation), les README, le glossaire, le
manuel et Combat/. Le manuel et Combat/ gardent leur sous-dossier d'audio ; les
autres documents rangent leurs nouveaux enregistrements dans audio/termes/,
sous le nom romanisé du hangul (scripts/romanisation.py : « 옆차 뚫기 » donne
yopcha-tulgi.m4a) ; si ce nom dit déjà un autre texte, un suffixe -2, -3… le
distingue.
Le titre de la page (« # … »), les blocs de code et tout ce qui est déjà pris
dans un lien ne sont jamais retouchés.

Dépend de macOS : `say` et `afconvert`. Ailleurs, --sans-synthese lie seulement
les hangul dont l'enregistrement existe déjà et compte les autres « en
attente » : un passage ultérieur sur Mac les produit et les lie.
"""

import argparse
import collections
import os
import pathlib
import re
import subprocess
import sys

from romanisation import romaniser

RACINE = pathlib.Path(__file__).resolve().parents[1]
AUDIO = RACINE / "audio"
DOSSIERS = ("Techniques", "sogi", "chagi", "jirugi", "makgi", "tul")
HORS_TRAITEMENT = {"README.md", "Dans-les-formes.md", "nomenclature.md"}

VOIX = "Yuna"
DEBIT = 130

# Documents de fond dont chaque hangul devient un lien de prononciation, avec le
# sous-dossier d'audio qui leur est propre ; un motif glob en désigne plusieurs.
# Celui du manuel reste « grammaire », nom de la fiche d'origine : le renommer
# perdrait les enregistrements déjà liés. Le manuel est découpé en sous-pages,
# d'où le motif récursif.
DOCUMENTS = {
    "manuel": ("Theorie/manuel/**/*.md", "grammaire"),
    "combats": ("Combat/*.md", "combats"),
}

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
    "wen": "왼", "orun": "오른",
    # briques grammaticales, hangul repris de Theorie/grammaire-itf.md
    "nopunde": "높은데", "kaunde": "가운데", "kaujunde": "가운데",
    "najunde": "낮은데", "baro": "바로", "bandae": "반대",
    "ap": "앞", "yop": "옆", "anuro": "안으로", "bakuro": "밖으로",
    "dollyo": "돌려", "ollyo": "올려", "naeryo": "내려",
    "twimyo": "뛰며", "dora": "돌아", "sangbal": "쌍발", "yonsok": "연속",
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
    "mikulgi": "미끌기", "gujari dolgi": "그 자리 돌기",
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
PRONONCIATION = re.compile(
    r"\*\*Prononciation :\*\*\s*\[([가-힣ㄱ-ㅎ][^\]]*)\]\(")
LIEN_MD = re.compile(r"!?\[([^\]]*)\]\([^)]*\)")
# présence de la ligne de prononciation de la fiche. Ne pas chercher « audio/ » :
# un terme du corps de la fiche peut déjà renvoyer à un enregistrement.
MARQUE = "**Prononciation :**"


def texte_coreen(fiche):
    """Le hangul à prononcer, ou None si la fiche n'en donne pas."""
    if fiche.parent.name == "tul":
        return NOMS_TUL.get(fiche.stem)
    contenu = fiche.read_text(encoding="utf-8")
    # la ligne de prononciation déjà posée fait foi : l'audio doit dire
    # exactement ce qu'elle affiche
    m = PRONONCIATION.search(contenu)
    if m:
        return " ".join(m.group(1).split()) or None
    # le hangul de la première phrase a pu devenir un lien : on lit son texte
    m = INTRO.search(LIEN_MD.sub(r"\1", contenu))
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
    # même règle que pour les documents : un hangul déjà enregistré ailleurs
    # ne doit pas être produit une seconde fois
    par_hangul = index_par_hangul()
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
            audio = par_hangul.get(
                hangul,
                f"lexique/{re.sub(r'[^A-Za-z0-9]+', '-', terme).strip('-')}.m4a")
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

# toute suite de hangul, jamo isolés compris (« ㄷ », « ㄱ자 »)
SUITE_HANGUL = re.compile(r"[가-힣ㄱ-ㅎ][가-힣ㄱ-ㅎ\s]*")
# ce qui ne doit jamais être retouché : un lien Markdown entier (image comprise),
# déjà audio ou non, et un code en ligne
PROTEGE = re.compile(r"!?\[[^\]]*\]\([^)]*\)|`[^`]*`")
# lien audio quel que soit le niveau du document : « audio/ » à la racine,
# « ../audio/ » dans un dossier, « ../../audio/ » plus bas
LIEN_AUDIO = re.compile(
    r"\[([가-힣ㄱ-ㅎ][^\]]*)\]\((?:\.\./)*audio/([^)]+)\)")

# Documents publiés dont --tout lie chaque hangul : tous les dossiers du site.
# Les documents de DOCUMENTS gardent leur sous-dossier d'audio ; les autres
# rangent leurs nouveaux enregistrements dans audio/termes/.
DOSSIERS_PUBLIES = ("", "Ceintures", "tul", "sogi", "chagi", "makgi", "jirugi",
                    "Techniques", "Combat", "Theorie", "images", "images/sogi")
# dossiers publiés parcourus avec leurs sous-dossiers (pages découpées)
DOSSIERS_RECURSIFS = {"Theorie"}
SOUS_DOSSIER_TERMES = "termes"
# documents produits par un autre script : les lier ici ferait diverger leur
# générateur, qui les réécrirait sans les liens à chaque passage
GENERES = {"Techniques/README.md"}


def romanisation_precedente(ligne, position):
    """Dernier terme romanisé en gras ou italique avant la position donnée."""
    avant = ligne[:position]
    # d'abord la romanisation qui précède immédiatement le hangul, car elle
    # le désigne ; le terme en gras peut être la traduction française
    m = re.search(r"([A-Za-z][A-Za-z'’ \-]{2,40}?)\s*[/(]\s*$", avant)
    if m:
        return m.group(1).strip()
    # même chose pour la forme « Sambo Matsogi — 삼보 맞서기 », où un tiret
    # sépare la romanisation de son hangul
    m = re.search(r"([A-Z][A-Za-z'’ \-]{2,40}?)\s*[—–]\s*$", avant)
    if m:
        return m.group(1).strip()
    dernier = None
    for dernier in re.finditer(r"\*{1,2}([A-Za-z][A-Za-z'’ \-]{1,40}?)\s*[\*(/]",
                               avant):
        pass
    return dernier.group(1).strip() if dernier else None


def normaliser(texte):
    return " ".join(texte.split())


def index_par_hangul():
    """{hangul: chemin audio} d'après tous les liens déjà posés dans le dépôt.

    Le critère de réemploi est le hangul lui-même : deux textes identiques
    doivent renvoyer au même enregistrement, quelle que soit leur origine.
    """
    index = {}
    for md in sorted(RACINE.rglob("*.md")):
        if ".git" in md.parts or "docs" in md.relative_to(RACINE).parts[:1]:
            continue
        for han, audio in LIEN_AUDIO.findall(
                md.read_text(encoding="utf-8", errors="ignore")):
            han = normaliser(han)
            # un enregistrement présent l'emporte sur un lien dont l'audio
            # a été supprimé pour être refait
            if han not in index or not (AUDIO / index[han]).exists():
                index[han] = audio
    for dossier in DOSSIERS:
        for fiche in sorted((RACINE / dossier).glob("*.md")):
            if fiche.name in HORS_TRAITEMENT:
                continue
            texte = texte_coreen(fiche)
            if texte:
                index.setdefault(texte, f"{dossier}/{fiche.stem}.m4a")
    return index


def nom_de_fichier(texte):
    """Le nom romanisé du hangul : ASCII en minuscules, mots liés par des tirets
    (« 옆차 뚫기 » -> « yopcha-tulgi »)."""
    return romaniser(texte)


def nom_libre(sous_dossier, base, texte, utilises):
    """Premier nom « base », « base-2 », « base-3 »… qui ne dit pas déjà un
    autre texte : un même fichier ne doit jamais prononcer deux hangul."""
    audio, k = f"{sous_dossier}/{base}.m4a", 2
    while utilises.get(audio, texte) != texte or (
            audio not in utilises and (AUDIO / audio).exists()):
        audio, k = f"{sous_dossier}/{base}-{k}.m4a", k + 1
    return audio


def lier_document(chemin, sous_dossier, args, index=None, nom_hangul=False):
    """Transforme chaque hangul du document en lien vers sa prononciation.

    Un hangul déjà pris dans un lien n'est pas retouché, pas plus que le titre
    de la page (ligne « # … », qui sert aussi de titre au menu) ni les blocs de
    code. Avec --sans-synthese, seul un hangul dont l'audio existe déjà est lié ;
    les autres sont comptés « en attente » et seront liés sur macOS.

    nom_hangul : le nouvel enregistrement est nommé d'après la romanisation du
    hangul lui-même, et non d'après le terme romanisé qui le précède dans le
    texte, qui peut désigner autre chose.
    """
    contenu = chemin.read_text(encoding="utf-8")
    index = index_par_hangul() if index is None else index
    utilises = {}                       # audio -> hangul, contre les collisions
    for han, audio in index.items():
        utilises.setdefault(audio, han)
    vers_audio = os.path.relpath(AUDIO, chemin.parent).replace(os.sep, "/")
    compte = collections.Counter()
    sortie = []
    en_code = False

    for ligne in contenu.splitlines():
        if ligne.lstrip().startswith("```"):
            en_code = not en_code
        if en_code or ligne.startswith("```") or re.match(r"#\s", ligne):
            sortie.append(ligne)
            continue

        def remplacer(m):
            texte = normaliser(m.group(0))
            if not texte:
                return m.group(0)
            if texte in index:
                audio = index[texte]                 # même hangul : réemploi
                nature = "reemploi"
            else:
                terme = "" if nom_hangul else \
                    romanisation_precedente(ligne, m.start()) or ""
                base = re.sub(r"[^A-Za-z0-9]+", "-", terme).strip("-") \
                    if terme else nom_de_fichier(texte)
                audio = f"{sous_dossier}/{base}.m4a"
                if utilises.get(audio, texte) != texte:
                    # la romanisation désigne déjà un autre hangul : un même
                    # fichier ne doit jamais dire deux textes différents
                    audio = nom_libre(sous_dossier, nom_de_fichier(texte),
                                      texte, utilises)
                elif nom_hangul:
                    audio = nom_libre(sous_dossier, base, texte, utilises)
                nature = "propre"
            cible = AUDIO / audio
            if not cible.exists():
                if args.sans_synthese:
                    compte["attente"] += 1
                    attente[texte] += 1
                    return m.group(0)
                if args.write:
                    cible.parent.mkdir(parents=True, exist_ok=True)
                    produire_audio(texte, cible, args.voix, args.debit)
                compte["audio"] += 1
            # le même hangul plus loin doit renvoyer ici, et non se faire
            # enregistrer une seconde fois sous un autre nom
            index[texte] = audio
            utilises.setdefault(audio, texte)
            compte[nature] += 1
            # l'espace final éventuel est rendu au texte, pas au lien
            espace = m.group(0)[len(m.group(0).rstrip()):]
            return f"[{texte}]({vers_audio}/{audio}){espace}"

        compte["deja"] += sum(1 for p in PROTEGE.finditer(ligne)
                              if "audio/" in p.group(0))
        sortie.append(_assembler(ligne, remplacer))

    if args.write:
        nouveau = "\n".join(sortie) + "\n"
        if nouveau != contenu:
            chemin.write_text(nouveau, encoding="utf-8")
    return compte


def _assembler(ligne, remplacer):
    """Applique remplacer() aux hangul de la ligne situés hors des zones
    protégées, en conservant leurs positions dans la ligne d'origine."""
    zones = [(p.start(), p.end()) for p in PROTEGE.finditer(ligne)]

    def hors_zone(m):
        if any(a <= m.start() < b for a, b in zones):
            return m.group(0)
        return remplacer(m)
    # une suite de hangul ne chevauche jamais le début d'une zone : elle
    # s'arrête au « [ », « ! » ou « ` » qui l'ouvre
    return SUITE_HANGUL.sub(hors_zone, ligne)


# hangul encore sans audio, recensés par --sans-synthese
attente = collections.Counter()


def documents_publies():
    """Tous les documents Markdown du site, dans l'ordre du dépôt."""
    for dossier in DOSSIERS_PUBLIES:
        motif = "**/*.md" if dossier in DOSSIERS_RECURSIFS else "*.md"
        for md in sorted((RACINE / dossier).glob(motif)):
            if md.relative_to(RACINE).as_posix() not in GENERES:
                yield md


def lier_tout(args):
    """Lie chaque hangul de chaque document publié. Rend {chemin: compte}."""
    propres = {md.resolve(): sd for rel, sd in DOCUMENTS.values()
               for md in RACINE.glob(rel)}
    index = index_par_hangul()
    resultats = {}
    for md in documents_publies():
        sous_dossier = propres.get(md.resolve())
        if sous_dossier:
            c = lier_document(md, sous_dossier, args, index)
        else:
            c = lier_document(md, SOUS_DOSSIER_TERMES, args, index,
                              nom_hangul=True)
        resultats[md] = c
    return resultats


def reparer(args):
    """Reproduit l'audio de tout lien dont le fichier a disparu.

    Sert après correction d'un libellé : on supprime l'audio devenu faux,
    puis cette passe le régénère à partir du texte corrigé.
    """
    compte = collections.Counter()
    for md in sorted(RACINE.rglob("*.md")):
        if ".git" in md.parts or "docs" in md.relative_to(RACINE).parts[:1]:
            continue
        for label, rel in LIEN_AUDIO.findall(
                md.read_text(encoding="utf-8", errors="ignore")):
            cible = AUDIO / rel
            compte["liens"] += 1
            if cible.exists():
                continue
            compte["manquants"] += 1
            if args.write and not args.sans_synthese:
                cible.parent.mkdir(parents=True, exist_ok=True)
                produire_audio(normaliser(label), cible, args.voix, args.debit)
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
    p.add_argument("--manuel", action="store_true",
                   help="lie les hangul des pages de Theorie/manuel/")
    p.add_argument("--lexique", "--grammaire", dest="manuel",
                   action="store_true",
                   help="ancien nom de --manuel (fiches fusionnées au manuel)")
    p.add_argument("--combats", action="store_true",
                   help="lie les hangul des pages de Combat/")
    p.add_argument("--reparer", action="store_true",
                   help="reproduit l'audio des liens dont le fichier manque")
    p.add_argument("--tout", action="store_true",
                   help="lie les hangul de tous les documents du site "
                        "(manuel et Combat/ compris)")
    p.add_argument("--sans-synthese", action="store_true",
                   help="hors macOS : ne lie que les hangul dont l'audio existe "
                        "déjà et liste ceux qui restent à produire")
    args = p.parse_args()

    if args.write and not args.sans_synthese:
        for outil in ("say", "afconvert"):
            if subprocess.run(["which", outil],
                              stdout=subprocess.DEVNULL).returncode:
                sys.exit(f"{outil} introuvable — ce script requiert macOS "
                         "(ou --sans-synthese)")
        AUDIO.mkdir(exist_ok=True)

    compte = dict(fiches=0, sans_hangul=0, audio=0, deja_audio=0,
                  liens=0, deja_lies=0)
    sans_hangul, fiches_en_attente = [], []

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
            if cible.exists() and not args.force:
                compte["deja_audio"] += 1
            elif args.sans_synthese:
                # pas de lien vers un audio qui n'existe pas encore
                fiches_en_attente.append(f"{dossier}/{fiche.name}")
                continue
            elif args.write:
                cible.parent.mkdir(parents=True, exist_ok=True)
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
    if fiches_en_attente:
        print(f"\nfiches dont l'audio reste à produire sur macOS "
              f"({len(fiches_en_attente)}) :")
        for nom in fiches_en_attente:
            print(f"  {nom}")

    if args.reparer:
        c = reparer(args)
        print(f"liens audio vérifiés  : {c['liens']}")
        print(f"  fichiers manquants  : {c['manquants']}")
        print(f"  reproduits          : {c['produits']}")
        return

    if args.tout:
        resultats = lier_tout(args)
        total = collections.Counter()
        for c in resultats.values():
            total.update(c)
        print(f"\ndocuments parcourus         : {len(resultats)}")
        print(f"  hangul liés               : {total['reemploi'] + total['propre']}")
        print(f"    réemploi d'un audio     : {total['reemploi']}")
        print(f"    audio propre            : {total['propre']}")
        print(f"  audio à produire          : {total['audio']}")
        print(f"  hangul déjà liés          : {total['deja']}")
    else:
        for nom, (relatif, sous_dossier) in DOCUMENTS.items():
            if not getattr(args, nom):
                continue
            # un motif (« Combat/*.md ») désigne tous les documents d'un dossier
            for chemin in sorted(RACINE.glob(relatif)):
                c = lier_document(chemin, sous_dossier, args)
                print(f"\n{chemin.relative_to(RACINE)}")
                print(f"  hangul liés               : {c['reemploi'] + c['propre']}")
                print(f"    réemploi d'un audio     : {c['reemploi']}")
                print(f"    audio propre            : {c['propre']}")
                print(f"  audio à produire          : {c['audio']}")
                print(f"  hangul déjà liés          : {c['deja']}")
    if attente:
        print(f"\nhangul en attente d'audio (macOS) : {len(attente)} textes, "
              f"{sum(attente.values())} occurrences")


if __name__ == "__main__":
    main()

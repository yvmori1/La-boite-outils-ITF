#!/usr/bin/env python3
"""Romanise un texte coréen pour nommer son fichier audio.

  from romanisation import romaniser
  romaniser("옆차 뚫기")   # « yopcha-tulgi »

Chaque mot est d'abord découpé en termes connus du vocabulaire ITF et rendu
dans la romanisation du site (Tulgi, Nopunde, Sonkal…). Un mot que ce
vocabulaire ne couvre pas suit la romanisation révisée officielle, syllabe par
syllabe, sans les règles d'assimilation. Le résultat ne contient que des
minuscules ASCII, des chiffres et des tirets.
"""

import re

# romanisation ITF d'un mot -> graphies hangul qu'elle désigne
ITF = {
    "a": ["a"], "an": ["안"], "annun": ["앉은"], "anuro": ["안으로"], "ap": ["앞"],
    "apcha": ["앞차"], "apun": ["아픈"], "b": ["b", "비"], "badak": ["바닥"],
    "bakat": ["바깥", "밖"], "bakuro": ["바깥으로", "밖으로"], "bakwo": ["바꿔"],
    "bal": ["발"], "balkal": ["발칼"], "bandae": ["반대"], "bandal": ["반달"],
    "bandalson": ["반달손"], "bandol": ["반돌"], "bang": ["방"], "baro": ["바로"],
    "bituro": ["비틀어"], "busigi": ["부시기"], "butjaba": ["붙잡아"], "c": ["c", "씨"],
    "cha": ["차"], "chagi": ["차기"], "chookyo": ["추켜"], "d": ["d", "디"],
    "daebi": ["대비"], "deuro": ["들어"], "digutja": ["디귿자", "ㄷ자"], "do": ["도"],
    "dollimyo": ["돌리며"], "dollyo": ["돌려"], "dolmyo": ["돌며"],
    "dolymyo": ["돌며", "돌리며"], "doo": ["두"], "dora": ["돌아"], "doro": ["도로"],
    "dung": ["등"], "dungpalmok": ["등팔목"], "duro": ["들어"], "dwijibo": ["뒤집어"],
    "dwijibun": ["뒤집은"], "dwit": ["뒤", "뒷"], "dwitbal": ["뒷발"],
    "dwitcha": ["뒤차"], "dwitchuk": ["뒤축"], "euhkallin": ["엇갈린"], "ghin": ["긴"],
    "ghutgi": ["긋기"], "giokja": ["기역자", "ㄱ자"], "gojung": ["고정"],
    "gokaeng": ["곡괭이"], "golcho": ["걸쳐"], "goro": ["걸어"],
    "gorochagi": ["걸어차기"], "guburyo": ["구부려"], "gunnun": ["걷는"],
    "gutja": ["구자"], "hanulson": ["하늘손"], "hechyo": ["헤쳐"], "homi": ["호미"],
    "hon": ["혼"], "hopi": ["호미"], "hori": ["허리"], "i": ["이"],
    "ijung": ["이중"], "inji": ["인지"], "japgi": ["잡기"],
    "japgo": ["잡고"], "jappyosul": ["잡혔을"], "jirugi": ["지르기"], "joomuk": ["주먹"],
    "joongji": ["중지"], "junbi": ["준비"], "kaunde": ["가운데"],
    "kiokja": ["기역자", "ㄱ자"], "kumchi": ["꿈치"], "kyocha": ["교차"],
    "makgi": ["막기"], "mikulgi": ["미끌기"], "milgi": ["밀기"], "miro": ["밀어"],
    "mit": ["밑"], "moa": ["모아"], "momchau": ["멈춰"], "momchugi": ["멈추기"],
    "mongdung": ["몽둥이"], "moorup": ["무릎"], "nachuo": ["낮추어"], "naeryo": ["내려"],
    "najunde": ["낮은데"], "narani": ["나란히"], "niunja": ["니은자", "ㄴ자"],
    "noollo": ["눌러"], "nopi": ["높이"], "nopun": ["높은"], "nopunde": ["높은데"],
    "nullo": ["눌러"], "olligi": ["올리기"], "ollyo": ["올려"], "opun": ["엎은"],
    "orun": ["오른"], "palkup": ["팔굽"], "palmok": ["팔목"], "pihamyo": ["피하며"],
    "pyon": ["편"], "san": ["산"], "sang": ["쌍"], "sangbal": ["쌍발"],
    "sasun": ["사선"], "sewo": ["세워"], "shik": ["식"], "so": ["서"],
    "sogi": ["서기"], "son": ["손"], "sonbadak": ["손바닥"], "sondung": ["손등"],
    "songarak": ["손가락"], "sonkal": ["손칼"], "sonkut": ["손끝"], "sonmok": ["손목"],
    "soojik": ["수직"], "soopyong": ["수평"], "sun": ["선"], "suroh": ["쓸어"],
    "tae": ["태"], "taerigi": ["때리기"], "tulgi": ["뚫기"], "twigi": ["뛰기"],
    "twimyo": ["뛰며"], "twio": ["뛰어"], "wa": ["와"], "waebal": ["외발"],
    "wen": ["왼"], "wi": ["위"], "yobap": ["옆앞"], "yonsok": ["연속"], "yop": ["옆"],
    "yopap": ["옆앞"], "yopcha": ["옆차"], "yopdwi": ["옆뒤"],
}

# jamo isolés et syllabes : romanisation révisée
CHO = ["g", "kk", "n", "d", "tt", "r", "m", "b", "pp", "s", "ss", "", "j", "jj",
       "ch", "k", "t", "p", "h"]
JUNG = ["a", "ae", "ya", "yae", "eo", "e", "yeo", "ye", "o", "wa", "wae", "oe",
        "yo", "u", "wo", "we", "wi", "yu", "eu", "ui", "i"]
JONG = ["", "k", "k", "k", "n", "n", "n", "t", "l", "k", "m", "l", "l", "l",
        "p", "l", "m", "p", "p", "t", "t", "ng", "t", "t", "k", "t", "p", "t"]
JAMO = {"ㄱ": "giyeok", "ㄴ": "nieun", "ㄷ": "digeut", "ㄹ": "rieul",
        "ㅁ": "mieum", "ㅂ": "bieup", "ㅅ": "siot", "ㅇ": "ieung", "ㅈ": "jieut",
        "ㅊ": "chieut", "ㅋ": "kieuk", "ㅌ": "tieut", "ㅍ": "pieup", "ㅎ": "hieut"}

# graphie hangul -> romanisation ITF ; la première romanisation l'emporte,
# PREFERE tranche quand plusieurs conviennent
HANGUL_VERS_ITF = {}
for _rom, _graphies in ITF.items():
    if len(_rom) == 1:
        continue
    for _h in _graphies:
        HANGUL_VERS_ITF.setdefault(_h, _rom)
PREFERE = {"뒤": "dwi", "뒷": "dwit", "밖": "bak", "바깥": "bakat",
           "밖으로": "bakuro", "ㄱ자": "kiokja", "ㄴ자": "niunja",
           "ㄷ자": "digutja", "구자": "gutja", "서": "so", "들어": "duro",
           "눌러": "noollo", "선": "sun", "곡괭이": "gokaeng-i",
           "몽둥이": "mongdung-i"}
HANGUL_VERS_ITF.update(PREFERE)


def revisee(mot):
    """Romanisation révisée, syllabe par syllabe."""
    sortie = []
    for c in mot:
        o = ord(c) - 0xAC00
        if 0 <= o < 11172:
            sortie.append(CHO[o // 588] + JUNG[(o % 588) // 28] + JONG[o % 28])
        elif c in JAMO:
            sortie.append(JAMO[c])
        elif c.isascii() and c.isalnum():
            sortie.append(c.lower())
    return "".join(sortie)


def termes_itf(mot):
    """Découpe le mot en termes ITF connus, le moins de termes possible.

    Rend la liste de leurs romanisations, ou None si le mot ne se découpe pas.
    """
    meilleur = {0: []}
    for i in range(len(mot)):
        if i not in meilleur:
            continue
        for j in range(len(mot), i, -1):
            terme = HANGUL_VERS_ITF.get(mot[i:j])
            if terme and (j not in meilleur
                          or len(meilleur[j]) >= len(meilleur[i]) + 1):
                meilleur[j] = meilleur[i] + [terme]
    return meilleur.get(len(mot))


def romaniser(texte):
    """« 옆차 뚫기 » -> « yopcha-tulgi » : nom de fichier ASCII en minuscules."""
    mots = []
    for mot in texte.split():
        mots.extend(termes_itf(mot) or [revisee(mot)])
    nom = "-".join(mots).lower()
    return re.sub(r"[^a-z0-9]+", "-", nom).strip("-") or "terme"

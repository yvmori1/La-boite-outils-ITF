"""Fait trouver les fiches quand on tape une autre romanisation du coréen.

Le site écrit « Dollyo », « Jirugi », « Joomuk »… mais beaucoup de livres et
de clubs écrivent « Dolyo », « Chirugi », « Jumeok ». Après la construction,
ce hook ajoute au texte indexé de chaque page les variantes des mots qu'elle
contient : chercher « dolyo chagi » trouve alors les pages de « Dollyo Chagi ».
Seul l'index de recherche change, pas les pages.

Pour ajouter une variante : une ligne dans VARIANTES (graphie du site, puis
graphies équivalentes, en minuscules).
"""

import json
import os
import re

VARIANTES = {
    "dollyo": ["dolyo", "dolryo", "tollyo"],
    "jirugi": ["chirugi", "jireugi", "jiruki"],
    "makgi": ["makki", "maki", "makgui"],
    "chagi": ["tchagi", "chaki", "chagui"],
    "sogi": ["seogi", "sohgi"],
    "joomuk": ["jumeok", "jumuk", "chumok"],
    "sonkal": ["sonnal", "son kal"],
    "palkup": ["palkoop", "palgup"],
    "palmok": ["palmock"],
    "kaunde": ["gaunde", "kaundae", "gawoonde"],
    "najunde": ["najeunde", "nachunde"],
    "nopunde": ["nopeunde", "nopundae"],
    "gunnun": ["gunnun", "kunnun", "geonneun"],
    "niunja": ["nieunja", "niunjia"],
    "annun": ["anjun", "anneun"],
    "dwitbal": ["dwitbaal", "duitbal"],
    "taerigi": ["taeregi", "taeryigi"],
    "tulgi": ["ttulgi", "tulki"],
    "yopcha": ["yeopcha", "yop cha"],
    "apcha": ["ap cha", "apchagi"],
    "dwitcha": ["dwit cha", "dwichagi"],
    "twimyo": ["twimyeo", "twiyo"],
    "daebi": ["daebee", "taebi"],
    "sonbadak": ["sonbadag"],
    "sonkut": ["sonkeut", "son kut"],
    "dobok": ["dobuk"],
    "dojang": ["dojeong", "dojan"],
    "hosinsul": ["hoshinsul"],
    "kyokpa": ["kyukpa", "gyeokpa"],
    "matsogi": ["matseogi"],
    "taekwon-do": ["taekwondo", "tae kwon do"],
}
MOT = re.compile(r"[a-zà-ÿ-]+")


def on_post_build(config, **kwargs):
    chemin = os.path.join(config["site_dir"], "search", "search_index.json")
    if not os.path.exists(chemin):
        return
    with open(chemin, encoding="utf-8") as f:
        index = json.load(f)
    for doc in index.get("docs", []):
        texte = (doc.get("title", "") + " " + doc.get("text", "")).lower()
        mots = set(MOT.findall(texte))
        ajouts = [v for k, vs in VARIANTES.items() if k in mots for v in vs]
        if ajouts:
            doc["text"] = doc.get("text", "") + " " + " ".join(ajouts)
    donnees = json.dumps(index, ensure_ascii=False, separators=(",", ":"))
    with open(chemin, "w", encoding="utf-8") as f:
        f.write(donnees)
    # version hors ligne : le greffon « offline » a déjà copié l'index en .js
    chemin_js = chemin[:-len(".json")] + ".js"
    if os.path.exists(chemin_js):
        with open(chemin_js, "w", encoding="utf-8") as f:
            f.write("var __index = " + donnees)

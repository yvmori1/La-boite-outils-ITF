"""Range le menu principal selon le plan du Manuel (menu.yml).

awesome-pages construit d'abord le menu dossier par dossier (docs/.pages et
les .pages des sections). Ce hook reprend ces sections et ces pages telles
quelles, avec leurs titres et leur ordre, et les replace dans l'arborescence
décrite par menu.yml : chaque partie du Manuel suivie des fiches qui la
mettent en pratique. Aucun fichier ne bouge, les adresses restent les mêmes.

awesome-pages ne sait pas mettre un dossier dans la section d'un autre
dossier (« Nav entry not found ») : d'où ce hook, qui passe après lui.

Le hook refait aussi les liens « Précédent / Suivant » et les parents des
pages, puisque l'ordre de lecture suit maintenant le plan.
"""

import logging
import pathlib
import posixpath

import yaml
from mkdocs.exceptions import PluginError
from mkdocs.structure.nav import Navigation, Section
from mkdocs.structure.pages import Page

PLAN = pathlib.Path(__file__).resolve().parents[1] / "menu.yml"

# Pages publiées volontairement hors du menu (on y arrive par des liens).
HORS_MENU = set()

log = logging.getLogger("mkdocs.hooks.menu_manuel")


def _dossier_de(section):
    """Dossier d'une section : celui de ses pages directes (None si virtuelle
    et sans page directe)."""
    for enfant in section.children:
        if isinstance(enfant, Page):
            return posixpath.dirname(enfant.file.src_uri)
    return None


def _inventaire(items, pages, sections):
    """Remplit pages (chemin -> Page) et sections (dossier -> Section). La
    première section rencontrée pour un dossier est la section du dossier ;
    les groupes virtuels de son .pages, rencontrés après, ne la remplacent
    pas."""
    for item in items:
        if isinstance(item, Page):
            pages[item.file.src_uri] = item
        elif isinstance(item, Section):
            dossier = _dossier_de(item)
            if dossier is not None and dossier not in sections:
                sections[dossier] = item
            _inventaire(item.children, pages, sections)


def _references(entrees, refs):
    """Chemins (pages et dossiers) nommés dans le plan."""
    for entree in entrees:
        if isinstance(entree, dict):
            ((_, valeur),) = entree.items()
            if isinstance(valeur, list):
                _references(valeur, refs)
            else:
                refs.add(valeur.rstrip("/"))
        else:
            refs.add(entree.rstrip("/"))


def _filtrer(enfants, dossier, refs):
    """Enfants d'une section, moins ce que le plan place ailleurs."""
    garde = []
    for enfant in enfants:
        if isinstance(enfant, Page):
            if enfant.file.src_uri not in refs:
                garde.append(enfant)
        elif isinstance(enfant, Section):
            sous = _dossier_de(enfant)
            if sous is not None and sous != dossier and sous in refs:
                continue
            enfant.children = _filtrer(enfant.children, dossier, refs)
            if enfant.children:
                garde.append(enfant)
        else:
            garde.append(enfant)
    return garde


def _construire(entrees, pages, sections, refs):
    items = []
    for entree in entrees:
        titre = None
        if isinstance(entree, dict):
            ((titre, valeur),) = entree.items()
        else:
            valeur = entree
        if isinstance(valeur, list):
            items.append(Section(titre, _construire(valeur, pages, sections, refs)))
            continue
        chemin = valeur.rstrip("/")
        if chemin.endswith(".md"):
            if chemin not in pages:
                raise PluginError(f"menu.yml : page absente du site : {chemin}")
            page = pages[chemin]
            if titre:
                page.title = titre
            items.append(page)
            continue
        if chemin not in sections:
            raise PluginError(f"menu.yml : dossier absent du menu : {chemin}")
        section = sections[chemin]
        enfants = _filtrer(section.children, chemin, refs - {chemin})
        if titre:
            items.append(Section(titre, enfants))
        else:
            items.extend(enfants)
    return items


def _pages_dans_l_ordre(items, sortie):
    for item in items:
        if isinstance(item, Page):
            sortie.append(item)
        elif isinstance(item, Section):
            _pages_dans_l_ordre(item.children, sortie)
    return sortie


def _parents(items, parent):
    for item in items:
        item.parent = parent
        if isinstance(item, Section):
            _parents(item.children, item)


def on_nav(nav, config, files, **kwargs):
    entrees = yaml.safe_load(PLAN.read_text(encoding="utf-8"))
    pages, sections = {}, {}
    _inventaire(nav.items, pages, sections)
    refs = set()
    _references(entrees, refs)

    items = _construire(entrees, pages, sections, refs)
    _parents(items, None)
    ordre = _pages_dans_l_ordre(items, [])

    places = {p.file.src_uri for p in ordre}
    oubliees = sorted(set(pages) - places - HORS_MENU)
    for chemin in oubliees:
        log.warning("menu.yml : page sans place dans le menu : %s", chemin)

    for i, page in enumerate(ordre):
        page.previous_page = ordre[i - 1] if i else None
        page.next_page = ordre[i + 1] if i + 1 < len(ordre) else None
    for chemin in set(pages) - places:
        pages[chemin].previous_page = pages[chemin].next_page = None
        pages[chemin].parent = None

    return Navigation(items, ordre)

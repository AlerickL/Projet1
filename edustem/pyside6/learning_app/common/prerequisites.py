"""Lecture de la liste commune des prérequis (`learning_app/assets/prerequis.md`).

Plomberie : le moteur en tire la page « Prérequis » d'une application, et
les tests la liste des classes supposées connues. Le document reste la
seule source : aucune entrée n'est recopiée dans le code.
"""

from __future__ import annotations

import html
import re
from collections.abc import Sequence
from functools import cache
from pathlib import Path
from typing import NamedTuple

from .annex_style import AnnexTableClass, SectionRowClass

PrerequisitesPath = Path(__file__).resolve().parents[1] / "assets" / "prerequis.md"


def prerequisiteEntries() -> dict[str, str]:
    """Toutes les entrées du document, dans l'ordre : clé → description (Markdown).

    La clé est le texte en gras de la puce, sans accents graves
    (« QSlider », « signaux et slots »).
    """
    return {key: entry.description for key, entry in _entries().items()}


def prerequisitesTableHtml(chapterPrerequisites: Sequence[tuple[str, Sequence[str]]]) -> str:
    """La grille de la page « Prérequis », en HTML simple ; vide sans aucune clé.

    Une rangée par prérequis : son nom, sa description, et le chapitre qui
    l'emploie en premier. Les rangées sont groupées par catégorie du
    document (Python, Qt : classes…), dans l'ordre du document ; dans une
    catégorie, par chapitre, puis dans l'ordre du document. Le tableau ne
    porte que des classes : sa mise en forme vient de
    `annex_style.annexStyleSheet`.

    Args:
        chapterPrerequisites: Pour chaque chapitre, dans l'ordre : son
            libellé dans la grille, et les clés qu'il déclare.

    Raises:
        KeyError: Une clé n'est pas dans le document.
    """
    entries = _entries()
    keyOrder = list(entries)
    rows: list[tuple[int, int, str, str]] = []
    for chapterIndex, (chapterLabel, keys) in enumerate(chapterPrerequisites):
        for key in keys:
            entries[key]  # KeyError on an unknown key
            rows.append((chapterIndex, keyOrder.index(key), key, chapterLabel))
    if not rows:
        return ""

    sectionOrder = list(dict.fromkeys(entry.section for entry in entries.values()))
    rows.sort(key=lambda row: (sectionOrder.index(entries[row[2]].section), row[0], row[1]))
    cells = []
    currentSection = None
    for _chapterIndex, _keyIndex, key, chapterLabel in rows:
        entry = entries[key]
        if entry.section != currentSection:
            currentSection = entry.section
            cells.append(f"<tr class='{SectionRowClass}'><td colspan='3'>{html.escape(currentSection)}</td></tr>")
        cells.append(f"<tr><td><b>{_inlineHtml(entry.written)}</b></td>"
                     f"<td>{_inlineHtml(entry.description)}</td>"
                     f"<td>{html.escape(chapterLabel)}</td></tr>")
    header = "<tr><th>Prérequis</th><th>Ce qu'il faut savoir</th><th>À partir du chapitre</th></tr>"
    return f"<table class='{AnnexTableClass}' width='100%' cellspacing='0'>{header}{''.join(cells)}</table>"


def checkPrerequisiteKeys(keys: Sequence[str]) -> None:
    """Vérifie que chaque clé existe dans le document, et n'y figure qu'une fois dans `keys`.

    Raises:
        KeyError: Une clé est inconnue.
        ValueError: Une clé est répétée.
    """
    entries = _entries()
    for key in keys:
        if key not in entries:
            raise KeyError(f"unknown prerequisite {key!r}: add it to {PrerequisitesPath.name}")
    repeated = sorted({key for key in keys if list(keys).count(key) > 1})
    if repeated:
        raise ValueError(f"prerequisites declared twice: {repeated}")


# ====== Private ======

class _Entry(NamedTuple):
    """Une entrée du document : sa clé telle qu'écrite, sa description, sa catégorie."""

    written: str
    description: str
    section: str


_EntryPattern = re.compile(r"^- \*\*(.+?)\*\*\s*:\s*(.*)$")
_SectionPattern = re.compile(r"^## (.+)$")

@cache
def _entries() -> dict[str, _Entry]:
    """Clé → entrée, lues une fois dans le document."""
    entries: dict[str, _Entry] = {}
    currentKey = ""
    currentSection = ""
    for line in PrerequisitesPath.read_text(encoding="utf-8").splitlines():
        sectionMatch = _SectionPattern.match(line)
        if sectionMatch:
            currentSection = sectionMatch.group(1).strip()
            currentKey = ""
            continue
        match = _EntryPattern.match(line)
        if match:
            written, description = match.groups()
            currentKey = written.replace("`", "")
            if currentKey in entries:
                raise ValueError(f"duplicate prerequisite {currentKey!r} in {PrerequisitesPath.name}")
            entries[currentKey] = _Entry(written, description.strip(), currentSection)
        elif currentKey and line.startswith("  ") and line.strip():
            entry = entries[currentKey]
            entries[currentKey] = entry._replace(description=f"{entry.description} {line.strip()}")
        else:
            currentKey = ""
    return entries


def _inlineHtml(markdown: str) -> str:
    """Le Markdown d'une entrée en HTML : les accents graves deviennent `<code>`."""
    return re.sub(r"`([^`]+)`", r"<code>\1</code>", html.escape(markdown, quote=False))

"""Extraction du contenu visible d'une application d'apprentissage, pour la relecture (règle I6).

Produit, en Markdown, exactement ce que l'étudiant voit dans le panneau de
droite : l'introduction de l'application ; pour chaque chapitre, son
introduction ; pour chaque notion, chaque étape dans l'ordre, avec son titre, son explication, ses références et son
code affiché ; la synthèse du chapitre ; enfin les annexes, prérequis et glossaire. Rien d'autre : aucun code caché, aucun nom de fichier. C'est
le texte à remettre à l'agent étudiant et à l'agent enseignant (skill
`interactive-walkthrough-app`, §12.5).

L'option `--text-only` remplace chaque bloc de code par ses métadonnées
(nombre de lignes, fonctions et classes définies) : c'est le texte remis à
un relecteur qui juge la démarche et non le code.

Ligne de commande (depuis `new/sf3`) :
    python -m edustem.pyside6.learning_app.common.visible_content qpainter 1.3
    python -m edustem.pyside6.learning_app.common.visible_content qpainter 2.S   (synthèse du chapitre 2)
    python -m edustem.pyside6.learning_app.common.visible_content qpainter all -o qpainter.md
    python -m edustem.pyside6.learning_app.common.visible_content qpainter all --text-only -o qpainter-texte.md

Plomberie : jamais montrée à l'étudiant.
"""

from __future__ import annotations

import argparse
import html
import importlib
import os
import re
import sys

from PySide6.QtWidgets import QApplication

from .q_step_walkthrough import (
    QImageCaption, QChapterIntroTab, QChapterSynthesisPage, QGlossaryPage, QIntroductionPage, QPrerequisitesPage,
    QStepWalkthrough, shownCode,
)
from .q_walkthrough_app import QWalkthroughWindow


def _numberListItems(match: re.Match) -> str:
    """Numérote les éléments d'une liste `<ol>` : « 1. », « 2. »…"""
    items = re.findall(r"<li>(.*?)</li>", match.group(1), flags=re.DOTALL)
    return "\n\n" + "".join(f"\n{rank}. {item}" for rank, item in enumerate(items, start=1)) + "\n\n"


def htmlToText(fragment: str) -> str:
    """Convertit le HTML simple d'une explication en Markdown lisible.

    `<code>` devient des accents graves, `<pre>` un bloc de code, un lien
    devient `[texte](url)`, une liste devient des puces ; les autres balises
    disparaissent.
    """
    text = re.sub(r"<pre(\s[^>]*)?>(.*?)</pre>", r"\n\n```\n\2\n```\n\n", fragment, flags=re.DOTALL)
    text = re.sub(r"<ol>(.*?)</ol>", _numberListItems, text, flags=re.DOTALL)
    text = re.sub(r"<br\s*/?>", "\n", text)
    text = re.sub(r"</?(p|ul|ol|table)(\s[^>]*)?>", "\n\n", text)
    text = re.sub(r"</t[dh]>", " | ", text)
    text = re.sub(r"</tr>", "\n", text)
    text = re.sub(r'<a\s+href="([^"]+)"\s*>(.*?)</a>', r"[\2](\1)", text, flags=re.DOTALL)
    text = re.sub(r"<code>(.*?)</code>", r"`\1`", text, flags=re.DOTALL)
    text = re.sub(r"<li>(.*?)</li>", r"\n- \1", text, flags=re.DOTALL)
    text = re.sub(r"<(b|strong)>(.*?)</\1>", r"**\2**", text, flags=re.DOTALL)
    text = re.sub(r"<sup>(.*?)</sup>", r"^\1", text, flags=re.DOTALL)
    text = re.sub(r"<[^>]+>", "", text)
    return html.unescape(text).strip()


def stepContent(step: QStepWalkthrough.Step, number: int, count: int) -> str:
    """Le contenu visible d'une étape, en Markdown."""
    lines = [f"### Étape {number} / {count} : {step.title}", "", htmlToText(step.explanation), ""]
    if step.references:
        links = " · ".join(f"[{text}]({url})" for text, url in step.references)
        lines += [f"Documentation : {links}", ""]
    code = shownCode(step)
    if code.strip():
        lines += ["Code de cette étape :", "", "```python", code.rstrip(), "```", ""]
    return "\n".join(lines)


def topicContent(walkthrough: QStepWalkthrough) -> str:
    """Le contenu visible d'une notion : son en-tête, puis chacune de ses étapes."""
    steps = walkthrough.steps()
    parts = [f"## {walkthrough.topicHeading()}", ""]
    parts += [stepContent(step, index + 1, len(steps)) for index, step in enumerate(steps)]
    return "\n".join(parts)


def captionText(caption: QImageCaption) -> str:
    """La légende d'une image, en Markdown : ses sections, une par ligne."""
    lines = [htmlToText(part) for part in (caption.title, caption.author, caption.source, caption.note) if part]
    return "Image d'illustration :\n\n" + "\n".join(f"> {line}  " for line in lines)


def chapterContent(introduction: QChapterIntroTab) -> str:
    """Le contenu visible de la page d'introduction d'un chapitre."""
    toc = "\n".join(f"- {title}" for title in introduction.topicTitles())
    content = f"# {introduction.chapterTitle()}\n\n{htmlToText(introduction.introduction())}\n\n" \
              f"Dans ce chapitre :\n\n{toc}\n"
    if introduction.imageCaption() is not None:
        content += f"\n{captionText(introduction.imageCaption())}\n"
    return content


def synthesisContent(page: QChapterSynthesisPage) -> str:
    """Le contenu visible de la page de synthèse d'un chapitre."""
    return (f"# {QChapterSynthesisPage.Title} : {page.chapterTitle()}\n\n"
            f"{captionText(page.imageCaption())}\n\n"
            f"{htmlToText(page.synthesis())}\n")


def introductionContent(page: QIntroductionPage) -> str:
    """Le contenu visible de la page « Introduction »."""
    content = f"# {QIntroductionPage.Title}\n\n{htmlToText(page.hook())}\n\n"
    if page.imageCaption() is not None:
        content += f"{captionText(page.imageCaption())}\n\n"
    return content + f"{_headingsToMarkdown(page.html())}\n"


def prerequisitesContent(page: QPrerequisitesPage) -> str:
    """Le contenu visible de la page « Prérequis »."""
    return f"# {QPrerequisitesPage.Title}\n\n{htmlToText(QPrerequisitesPage.Introduction)}\n\n" \
           f"{htmlToText(page.prerequisitesHtml())}\n"


def glossaryContent(glossary: QGlossaryPage) -> str:
    """Le contenu visible de la page « Glossaire »."""
    return f"# {QGlossaryPage.Title}\n\n{htmlToText(glossary.glossary())}\n"


def applicationContent(window: QWalkthroughWindow, topicNumber: str = "all") -> str:
    """Le contenu visible de toute l'application, d'une seule notion (ex. « 1.3 »), ou d'une synthèse (« 2.S »).

    Dans l'ordre de l'arbre : l'introduction, les chapitres, leurs notions
    et leur synthèse, puis les annexes.
    """
    parts = []
    introductionItem = window.introductionItem()
    if topicNumber == "all" and introductionItem is not None:
        introductionPage = window.pageOf(introductionItem)
        assert isinstance(introductionPage, QIntroductionPage)
        parts.append(introductionContent(introductionPage))
    for chapterNumber, chapterItem in enumerate(window.chapterItems(), start=1):
        chapterPage = window.pageOf(chapterItem)
        assert isinstance(chapterPage, QChapterIntroTab)
        if topicNumber == "all":
            parts.append(chapterContent(chapterPage))
        for topicItem in window.topicItems(chapterItem):
            if topicNumber in ("all", topicItem.text(0).split(" ", 1)[0]):
                parts.append(topicContent(window.pageOf(topicItem).walkthrough))
        synthesisItem = window.synthesisItem(chapterItem)
        if synthesisItem is not None and topicNumber.upper() in ("ALL", f"{chapterNumber}.S"):
            synthesisPage = window.pageOf(synthesisItem)
            assert isinstance(synthesisPage, QChapterSynthesisPage)
            parts.append(synthesisContent(synthesisPage))
    prerequisitesItem = window.prerequisitesItem()
    if topicNumber == "all" and prerequisitesItem is not None:
        prerequisitesPage = window.pageOf(prerequisitesItem)
        assert isinstance(prerequisitesPage, QPrerequisitesPage)
        parts.append(prerequisitesContent(prerequisitesPage))
    glossaryItem = window.glossaryItem()
    if topicNumber == "all" and glossaryItem is not None:
        glossaryPage = window.pageOf(glossaryItem)
        assert isinstance(glossaryPage, QGlossaryPage)
        parts.append(glossaryContent(glossaryPage))
    if not parts:
        raise ValueError(f"no topic numbered {topicNumber!r}")
    return "\n".join(parts)


def textOnly(content: str) -> str:
    """Remplace chaque bloc de code du Markdown par une ligne de métadonnées.

    Ex. : « [code : 12 lignes ; définit `drawHouse`] ». Le code en ligne
    (entre accents graves simples) reste : il fait partie de la phrase.
    """
    return re.sub(r"^```[a-z]*\n(.*?)^```$", _codeSummary, content, flags=re.DOTALL | re.MULTILINE)


def main(arguments: list[str] | None = None) -> int:
    """Point d'entrée de la ligne de commande : écrit le contenu visible demandé."""
    parser = argparse.ArgumentParser(description="Contenu visible d'une application d'apprentissage.")
    parser.add_argument("application", help="nom du dossier de l'application dans learning_app (ex. qpainter)")
    parser.add_argument("topic", nargs="?", default="all",
                        help="numéro de notion (ex. 1.3), synthèse d'un chapitre (ex. 2.S), ou all")
    parser.add_argument("-o", "--output", help="fichier de sortie (sinon la sortie standard)")
    parser.add_argument("--text-only", action="store_true", help="remplacer le code par ses métadonnées")
    options = parser.parse_args(arguments)

    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    _app = QApplication.instance() or QApplication(sys.argv[:1])
    buildWindow = importlib.import_module(f"..{options.application}.main", __package__).buildWindow
    content = applicationContent(buildWindow(), options.topic)
    if options.text_only:
        content = textOnly(content)
    if options.output:
        with open(options.output, "w", encoding="utf-8") as file:
            file.write(content)
    else:
        sys.stdout.reconfigure(encoding="utf-8")
        print(content)
    return 0


# ====== Privé ======

def _headingsToMarkdown(fragment: str) -> str:
    """Comme `htmlToText`, en gardant les titres de section `<h3>` comme titres Markdown."""
    text = htmlToText(re.sub(r"<h3>(.*?)</h3>", r"<p>## \1</p>", fragment, flags=re.DOTALL))
    return re.sub(r"\n{3,}", "\n\n", text)


def _codeSummary(match: re.Match) -> str:
    lines = [line for line in match.group(1).splitlines() if line.strip()]
    names = re.findall(r"^\s*(?:def|class)\s+(\w+)", match.group(1), flags=re.MULTILINE)
    summary = f"[code : {len(lines)} ligne{'s' if len(lines) > 1 else ''}"
    if names:
        summary += " ; définit " + ", ".join(f"`{name}`" for name in names)
    return summary + "]"


if __name__ == "__main__":
    sys.exit(main())

"""Notation d'un intervalle de nombres : `QIntervalFormat`.

Une classe valeur, comme `QFont` ou `QTextOption`, que les widgets à intervalle partagent
(`QRangeSlider`, `QRangeSpinBox` et leurs versions réelles). Elle fixe les délimiteurs et le
séparateur, écrit un intervalle et le relit.

    fmt = box.intervalFormat()          # a copy
    fmt.setOpeningDelimiter("]")
    fmt.setClosingDelimiter("[")
    box.setIntervalFormat(fmt)          # ]-2,50 ; 3,75[ in French

Elle n'importe que `QLocale` : les nombres s'écrivent et se lisent dans la langue donnée.
"""

from __future__ import annotations

import math
from typing import NamedTuple, override

from PySide6.QtCore import QLocale


class QIntervalFormat:
    """La notation d'un intervalle : délimiteur ouvrant, séparateur, délimiteur fermant.

    Par défaut, un intervalle s'écrit `[a, b]`. Quand la virgule est la marque décimale de
    la langue, le séparateur automatique devient le point-virgule : `[a; b]`.

    Classe valeur
    -------------
    Comme `QFont`, un widget rend une copie de son format et en reçoit une copie :

        fmt = slider.intervalFormat()
        fmt.setSeparator(" to ")
        slider.setIntervalFormat(fmt)

    Deux formats sont égaux quand leurs délimiteurs et leur séparateur le sont.

    Délimiteurs et séparateur
    -------------------------
    - **Délimiteurs** (`openingDelimiter`, `closingDelimiter`) : `[` et `]` par défaut. Ils
      peuvent être vides. Ce sont des signes d'écriture, pas de sens : `]a ; b[` n'exclut
      pas les bornes de l'intervalle.
    - **Séparateur** (`separator`) : automatique par défaut (`separator()` rend None), il vaut
      alors `", "`, ou `"; "` quand la virgule est la marque décimale (`separatorFor`). Le
      fixer le rend explicite ; `resetSeparator()` revient à l'automatique.
    - Aucun ne peut contenir un chiffre, un signe ni `±` : il commencerait ou couperait un
      nombre. Le séparateur ne peut pas non plus être vide. Un séparateur qui contient la
      marque décimale d'une langue ne convient pas à cette langue (`isValidFor`) :
      `separatorFor` y rend le séparateur automatique. C'est le cas de `", "` en français.

    Écrire et lire
    --------------
    - `toString` assemble deux nombres déjà écrits ; `textFromNumber` en écrit un.
    - `structuredParts` découpe un texte écrit exactement dans ce format, sections comprises.
    - `freeParts` lit aussi les autres notations : séparateurs `,` (sauf si la virgule est la
      marque décimale), `;`, `..`, `…`, des espaces, ou un centre et une demi-longueur
      (`c ± h`, `c +/- h`, `c +- h`), avec ou sans délimiteurs.

    Exemple :
        >>> fmt = QIntervalFormat()
        >>> fmt.toString("-2.50", "3.75", QLocale.c())
        '[-2.50, 3.75]'
        >>> fmt.freeParts("0.625 ± 3.125", QLocale.c())[:3]
        ('0.625', '3.125', True)
    """

    class Parts(NamedTuple):
        """Les deux nombres d'un intervalle écrit, tels quels, et leur place dans le texte.

        Attributs:
            lower: Le texte du premier nombre (le centre, pour `c ± h`).
            upper: Le texte du second nombre (la demi-longueur, pour `c ± h`).
            centered: Vrai pour la notation `c ± h`.
            lowerSpan: `(début, fin)` du premier nombre dans le texte lu.
            upperSpan: `(début, fin)` du second nombre dans le texte lu.
        """

        lower: str
        upper: str
        centered: bool
        lowerSpan: tuple[int, int]
        upperSpan: tuple[int, int]

    def __init__(self, openingDelimiter: str = "[", closingDelimiter: str = "]", separator: str | None = None) -> None:
        """Construit un format.

        Args:
            openingDelimiter: Le délimiteur ouvrant (`[` par défaut).
            closingDelimiter: Le délimiteur fermant (`]` par défaut).
            separator: Le séparateur, ou None pour le séparateur automatique.

        Lève:
            ValueError: Si un délimiteur ou le séparateur n'est pas permis.
        """
        self.__opening: str = ""
        self.__closing: str = ""
        self.__separator: str | None = None
        self.setOpeningDelimiter(openingDelimiter)
        self.setClosingDelimiter(closingDelimiter)
        if separator is not None:
            self.setSeparator(separator)

    # ============================================================= delimiters

    def openingDelimiter(self) -> str:
        """Le délimiteur ouvrant (`[` par défaut)."""
        return self.__opening

    def setOpeningDelimiter(self, delimiter: str) -> None:
        """Fixe le délimiteur ouvrant ; il peut être vide.

        Lève:
            ValueError: S'il contient un caractère d'un nombre.
        """
        self.__opening = _checkedText(delimiter, "opening delimiter", allowEmpty=True)

    def closingDelimiter(self) -> str:
        """Le délimiteur fermant (`]` par défaut)."""
        return self.__closing

    def setClosingDelimiter(self, delimiter: str) -> None:
        """Fixe le délimiteur fermant ; il peut être vide.

        Lève:
            ValueError: S'il contient un caractère d'un nombre.
        """
        self.__closing = _checkedText(delimiter, "closing delimiter", allowEmpty=True)

    # ============================================================== separator

    def separator(self) -> str | None:
        """Le séparateur explicite, ou None s'il est automatique (voir `separatorFor`)."""
        return self.__separator

    def setSeparator(self, separator: str) -> None:
        """Fixe un séparateur explicite.

        Lève:
            ValueError: S'il est vide ou contient un caractère d'un nombre.
        """
        self.__separator = _checkedText(separator, "separator", allowEmpty=False)

    def resetSeparator(self) -> None:
        """Revient au séparateur automatique, qui suit la langue."""
        self.__separator = None

    def isSeparatorAutomatic(self) -> bool:
        """Indique si le séparateur suit la langue (vrai par défaut)."""
        return self.__separator is None

    def separatorFor(self, locale: QLocale) -> str:
        """Le séparateur employé dans une langue.

        Le séparateur explicite s'il convient à la langue (`isValidFor`), sinon le séparateur
        automatique : `"; "` si la virgule est la marque décimale, `", "` sinon.
        """
        if self.__separator is not None and self.isValidFor(locale):
            return self.__separator
        return "; " if locale.decimalPoint() == "," else ", "

    def isValidFor(self, locale: QLocale) -> bool:
        """Indique si le format se lit sans ambiguïté dans une langue.

        Un séparateur explicite ne doit pas contenir la marque décimale de la langue.
        """
        return self.__separator is None or locale.decimalPoint() not in self.__separator

    # ======================================================= writing, reading

    def toString(self, lowerText: str, upperText: str, locale: QLocale) -> str:
        """Écrit un intervalle dont les deux nombres sont déjà écrits : `[a, b]`."""
        return f"{self.__opening}{lowerText}{self.separatorFor(locale)}{upperText}{self.__closing}"

    def structuredParts(self, text: str, locale: QLocale) -> Parts | None:
        """Découpe un texte écrit exactement dans ce format.

        Les délimiteurs doivent être aux deux bouts, et le séparateur une seule fois entre
        les deux. Les nombres peuvent être incomplets, ou vides.

        Retourne:
            Les deux nombres et leur place dans `text`, ou None si la structure est rompue.
        """
        opening, closing, separator = self.__opening, self.__closing, self.separatorFor(locale)
        if len(text) < len(opening) + len(closing) or not text.startswith(opening) or not text.endswith(closing):
            return None
        start, stop = len(opening), len(text) - len(closing)
        inner = text[start:stop]
        if inner.count(separator) != 1:
            return None
        index = inner.index(separator)
        lowerSpan = (start, start + index)
        upperSpan = (start + index + len(separator), stop)
        return QIntervalFormat.Parts(text[slice(*lowerSpan)], text[slice(*upperSpan)], False, lowerSpan, upperSpan)

    def freeParts(self, text: str, locale: QLocale) -> Parts | None:
        """Lit un intervalle tapé dans l'une des notations acceptées (voir « Écrire et lire »).

        Retourne:
            Les deux nombres, sans espaces autour, et leur place dans `text`, ou None si le
            texte ne se coupe pas en deux.
        """
        surrounding = set(" \t[]()") | set(self.__opening) | set(self.__closing)
        start, stop = 0, len(text)
        while start < stop and text[start] in surrounding:
            start += 1
        while stop > start and text[stop - 1] in surrounding:
            stop -= 1
        body = text[start:stop]
        found = self.__splitIn(body, locale)
        if found is None:
            return None
        cut, resume, centered = found
        lowerText, upperText = body[:cut], body[resume:]
        lowerSpan = (start, start + len(lowerText.rstrip()))
        upperStart = start + resume + len(upperText) - len(upperText.lstrip())
        upperSpan = (upperStart, stop)
        if lowerSpan[0] == lowerSpan[1] or upperSpan[0] == upperSpan[1]:
            return None
        return QIntervalFormat.Parts(text[slice(*lowerSpan)], text[slice(*upperSpan)], centered, lowerSpan, upperSpan)

    # ================================================================ numbers

    @staticmethod
    def textFromNumber(value: float, locale: QLocale, decimals: int | None) -> str:
        """Écrit un nombre dans une langue, sans séparateur de milliers.

        Args:
            value: Le nombre.
            locale: La langue.
            decimals: Le nombre de décimales, ou None pour un entier.
        """
        written = QLocale(locale)
        written.setNumberOptions(QLocale.NumberOption.OmitGroupSeparator)
        if decimals is None:
            return written.toString(int(value))
        return written.toString(float(value), "f", decimals)

    @staticmethod
    def numberFromText(text: str, locale: QLocale, decimals: int | None) -> float | int | None:
        """Lit un nombre écrit dans une langue, ou avec un point décimal.

        Args:
            text: Le texte du nombre, sans espaces autour.
            locale: La langue.
            decimals: None pour lire un entier, un nombre de décimales pour lire un réel (le
                nombre n'est pas arrondi ici).

        Retourne:
            Le nombre, ou None si le texte ne se lit pas.
        """
        for reader in (QLocale(locale), QLocale.c()):
            reader.setNumberOptions(QLocale.NumberOption.RejectGroupSeparator)
            if decimals is None:
                integer, ok = reader.toLongLong(text)
                if ok:
                    return integer
            else:
                real, ok = reader.toDouble(text)
                if ok and math.isfinite(real):
                    return real
        return None

    @staticmethod
    def isNumberCharacter(character: str, locale: QLocale) -> bool:
        """Indique si un caractère peut faire partie d'un nombre écrit, même incomplet."""
        return character.isdigit() or character in _NumberCharacters or character in (
            locale.decimalPoint(), locale.negativeSign(), locale.positiveSign(), locale.exponential())

    # ================================================================== value

    @override
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, QIntervalFormat):
            return NotImplemented
        return (self.__opening, self.__closing, self.__separator) == (
            other.openingDelimiter(), other.closingDelimiter(), other.separator())

    @override
    def __hash__(self) -> int:
        return hash((self.__opening, self.__closing, self.__separator))

    @override
    def __repr__(self) -> str:
        return (f"QIntervalFormat({self.__opening!r}, {self.__closing!r}"
                f"{'' if self.__separator is None else f', {self.__separator!r}'})")

    # ================================================================ private

    def __splitIn(self, body: str, locale: QLocale) -> tuple[int, int, bool] | None:
        """Where the two numbers of a body split: `(cut, resume, centered)`."""
        for token in ("±", "+/-", "+-"):
            index = body.find(token, 1)
            if index > 0:
                return index, index + len(token), True
        tokens = [self.separatorFor(locale).strip(), ";", "..", "…"]
        if locale.decimalPoint() != ",":
            tokens.append(",")
        for token in tokens:
            index = body.find(token) if token else -1
            if index > 0:
                return index, index + len(token), False
        if " " in body:
            index = body.index(" ")
            return index, index + 1, False
        return None


_NumberCharacters = frozenset("+-.,eE")     # besides digits and the characters of the locale
_ForbiddenCharacters = frozenset("+-±")      # besides digits: they would start or split a number


def _checkedText(text: str, name: str, allowEmpty: bool) -> str:
    if not isinstance(text, str): # pyright: ignore[reportUnnecessaryIsInstance]
        raise TypeError(f"The {name} must be a str, got {type(text).__name__}.")
    if not text and not allowEmpty:
        raise ValueError(f"The {name} cannot be empty.")
    if any(c.isdigit() or c in _ForbiddenCharacters for c in text):
        raise ValueError(f"The {name} {text!r} cannot contain a digit, a sign or '±'.")
    return text

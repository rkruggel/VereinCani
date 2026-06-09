import ast
from datetime import date, datetime
from typing import Any, TypedDict

from dateutil.relativedelta import relativedelta


class Datumsdifferenz(TypedDict):
    jahre: int
    monate: int
    tage: int
    negativ: bool
    text: str


def _to_date(value: date | datetime | str) -> date:
    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    if isinstance(value, str):
        return date.fromisoformat(value)

    raise TypeError("Datum muss date, datetime oder ein String im Format YYYY-MM-DD sein.")


def _datumsdifferenz(
    von: date | datetime | str,
    bis: date | datetime | str,
) -> Datumsdifferenz:
    start = _to_date(von)
    ende = _to_date(bis)

    negativ = False

    if ende < start:
        start, ende = ende, start
        negativ = True

    diff = relativedelta(ende, start)

    text = (
        f"{diff.years} Jahr{'e' if diff.years != 1 else ''}, "
        f"{diff.months} Monat{'e' if diff.months != 1 else ''}, "
        f"{diff.days} Tag{'e' if diff.days != 1 else ''}"
    )

    if negativ:
        text = "-" + text

    return {
        "jahre": diff.years,
        "monate": diff.months,
        "tage": diff.days,
        "negativ": negativ,
        "text": text,
    }


def _werte_ausdruck_aus(
    ausdruck: ast.AST,
    namen: dict[str, Any],
    funktionen: dict[str, Any],
) -> Any:
    if isinstance(ausdruck, ast.Name):
        if ausdruck.id not in namen:
            raise ValueError(f"Unbekanntes Feld in Formel: {ausdruck.id}")
        return namen[ausdruck.id]

    if isinstance(ausdruck, ast.Constant):
        return ausdruck.value

    if isinstance(ausdruck, ast.Call) and isinstance(ausdruck.func, ast.Name):
        funktion = funktionen.get(ausdruck.func.id)
        if funktion is None:
            raise ValueError(f"Unbekannte Funktion in Formel: {ausdruck.func.id}")
        if ausdruck.keywords:
            raise ValueError("Benannte Argumente sind in Formeln nicht erlaubt.")

        argumente = [
            _werte_ausdruck_aus(argument, namen, funktionen)
            for argument in ausdruck.args
        ]
        return funktion(*argumente)

    raise ValueError("Dieser Ausdruck ist in Formeln nicht erlaubt.")


def berechne(formel: str, werte: dict[str, Any], heute: date | None = None) -> Any:
    """Wertet eine eingeschränkte Formel aus der YAML-Konfiguration aus."""

    namen = {**werte, "today": heute or date.today()}
    funktionen = {"datumDiff": datumDiff}

    try:
        ausdruck = ast.parse(formel, mode="eval").body
    except SyntaxError as error:
        raise ValueError(f"Ungültige Formel: {formel}") from error

    return _werte_ausdruck_aus(ausdruck, namen, funktionen)


def datumDiff(von, bis):
    if von in (None, "") or bis in (None, ""):
        return ""

    return _datumsdifferenz(von, bis)["text"]

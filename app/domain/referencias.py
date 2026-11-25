"""Reglas puras sobre referencias legales: detectar "artículo 14, fracción I, inciso a)"
en una pregunta o en una respuesta del modelo, y normalizar texto para búsqueda léxica."""

from __future__ import annotations

import re
import unicodedata

from app.domain.models import ReferenciaLegal

_ROMANOS = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100}

# "art. 14", "artículo 14", "articulo 14 bis"; la fracción y el inciso son opcionales.
_PATRON_ARTICULO = re.compile(
    r"\b(?:art[íi]culos?|art\.?|arts\.?)\s*(?P<num>\d{1,3})"
    r"(?:\s*(?:,|\s)\s*(?:fracci[óo]n|fracc?\.?|fr\.?)\s*(?P<fr>[IVXLC]+(?:\s+(?:bis|ter|qu[aá]ter))?)\b)?"
    r"(?:\s*(?:,|\s)\s*(?:inciso|inc\.?)\s*(?P<inc>[a-zñ])\)?)?",
    re.IGNORECASE,
)

_STOPWORDS = frozenset(
    """a al algo algun alguna algunas alguno algunos ante antes como con contra cual cuales
    cuando de del desde donde dos e el ella ellas ellos en entre era es esa esas ese eso esos
    esta estas este esto estos fue ha han hasta hay la las le les lo los mas me mi mis muy
    ni no nos o os otra otro para pero por porque que quien se ser si sin sobre son su sus
    tambien te tiene tu tus un una uno unos y ya yo puedo puede pueden debo debe deben hacer
    cuanto cuanta cuantos dice segun reglamento transito cdmx""".split()
)


def romano_a_entero(romano: str) -> int:
    total, previo = 0, 0
    for letra in reversed(romano.upper()):
        valor = _ROMANOS.get(letra, 0)
        total = total - valor if valor < previo else total + valor
        previo = max(previo, valor)
    return total


def normalizar(texto: str) -> str:
    """Minúsculas y sin acentos (conserva la ñ)."""
    texto = texto.lower().replace("ñ", "\0")
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return texto.replace("\0", "ñ")


def tokenizar(texto: str) -> list[str]:
    """Tokens para la búsqueda por palabras clave. Conserva números (artículos, km/h)
    y aplica un recorte muy simple de plurales."""
    tokens: list[str] = []
    for tok in re.findall(r"[a-zñ0-9]+", normalizar(texto)):
        if tok in _STOPWORDS or (len(tok) < 2 and not tok.isdigit()):
            continue
        if not tok.isdigit() and len(tok) > 4:
            if tok.endswith("es") and not tok.endswith("ces"):
                tok = tok[:-2]
            elif tok.endswith("s"):
                tok = tok[:-1]
        tokens.append(tok)
    return tokens


def extraer_referencias(texto: str) -> list[ReferenciaLegal]:
    """Detecta referencias explícitas a artículos. Devuelve sin duplicados y en orden."""
    vistas: set[tuple[int, str | None, str | None]] = set()
    refs: list[ReferenciaLegal] = []
    for m in _PATRON_ARTICULO.finditer(texto):
        num = int(m.group("num"))
        fr = m.group("fr")
        fr = " ".join(p.capitalize() if i else p.upper() for i, p in enumerate(fr.split())) if fr else None
        inc = m.group("inc").lower() if m.group("inc") else None
        clave = (num, fr, inc)
        if clave not in vistas:
            vistas.add(clave)
            refs.append(ReferenciaLegal(articulo_num=num, fraccion=fr, inciso=inc))
    return refs


def articulos_mencionados(texto: str) -> set[int]:
    return {r.articulo_num for r in extraer_referencias(texto)}

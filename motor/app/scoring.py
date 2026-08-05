"""Scoring ponderado: convierte los hits de las capas de deteccion en un
veredicto unico. Es comun a toda la cascada L1-L5, no solo a L1: cada capa
aporta sus HeuristicResult y aca se suman en un unico score 0-100.
"""

from collections.abc import Iterable
from typing import Literal

from app.detectors.l1_heuristics import HeuristicResult

Verdict = Literal["green", "yellow", "red"]

SCORE_MAX = 100
RED_THRESHOLD = 60

# ponytail: suma lineal con tope, sin pesos por combinacion ni decaimiento.
# Techo conocido: al saturar en 100 se pierde el "cuan rojo" cuando disparan
# muchas senales, y dos senales debiles pesan igual que una fuerte del mismo
# total. Alcanza mientras las capas sean independientes entre si; el camino de
# upgrade, si el benchmark de validacion muestra falsos positivos, es ponderar
# por capa (L4/L5 confirman, L1 solo sospecha) en vez de sumar plano.


def evaluate(hits: Iterable[HeuristicResult]) -> tuple[int, Verdict]:
    """Devuelve (score, veredicto) para los hits que dispararon.

    Umbrales: 0 -> green, 1..59 -> yellow, >=60 -> red. El corte en 60 exige
    que se acumulen al menos dos senales para llegar a rojo: la heuristica L1
    mas fuerte (punycode, 50) no basta por si sola, porque un dominio IDN
    legitimo la dispara igual.
    """
    score = min(sum(h.score for h in hits), SCORE_MAX)
    if score >= RED_THRESHOLD:
        return score, "red"
    return score, ("yellow" if score else "green")

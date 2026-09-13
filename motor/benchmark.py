"""Benchmark A/B del motor (Objetivo Especifico 4, RF-008, RF-009).

Pasa un dataset etiquetado por la cascada dos veces, con y sin trazabilidad de
redirecciones, y calcula precision, exhaustividad, tiempos por capa y la
diferencia entre las dos corridas. Esa diferencia es la evidencia del aporte
del modulo de trazabilidad.

Uso (desde motor/, con el venv activo y las variables del .env exportadas):

    python benchmark.py dataset --phishing PHISHTANK.csv --legit TRANCO.csv \\
        --n 500 --seed 42 --out dataset.csv
    python benchmark.py run --dataset dataset.csv --out resultados/

Decisiones de metodologia (van tambien al reporte):
- Las dos corridas ocurren en el mismo proceso, sobre el mismo snapshot del
  feed L3: con dos procesos cada uno descargaria su propio feed, y la diferencia
  entre corridas mezclaria el efecto de la trazabilidad con el del feed.
- La cache L2 se apaga: la corrida sin trazabilidad serviria desde la cache los
  veredictos que calculo la otra, y L2 no cambia la deteccion, solo la latencia.
- La fuente maliciosa no puede ser URLhaus: es el feed de L3 y la deteccion
  saldria circular. Se usa PhishTank.
"""

import argparse
import csv
import hashlib
import json
import logging
import math
import os
import random
import sys
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path

MALICIOUS, LEGIT = "malicious", "legit"
# Criterio estricto: solo el rojo cuenta como deteccion. Amplio: tambien el
# amarillo, que en el cliente ya se muestra como advertencia al usuario.
CRITERIA = {"estricto": {"red"}, "amplio": {"yellow", "red"}}


# --- Construccion del dataset ---


def _valid_urls(urls, validate) -> list[str]:
    vistas, validas = set(), []
    for url in urls:
        url = url.strip()
        if not url or url in vistas:
            continue
        vistas.add(url)
        try:
            validate(url)
        except ValueError:
            continue
        validas.append(url)
    return validas


def build_dataset(phishing_csv: Path, legit_csv: Path, n: int, seed: int) -> list[dict]:
    """Muestra `n` URLs por clase con semilla fija, para que el dataset se
    pueda reconstruir identico a partir de los mismos archivos crudos."""
    from pydantic import HttpUrl, TypeAdapter

    # Se valida con el mismo tipo que el endpoint: una URL que el API rechaza
    # con 422 no mide nada de la cascada.
    validate = TypeAdapter(HttpUrl).validate_python

    with phishing_csv.open(encoding="utf-8", errors="replace", newline="") as f:
        filas = csv.DictReader(f)
        phishing = _valid_urls(
            (r["url"] for r in filas if r.get("verified", "yes") == "yes"), validate
        )
    # Tranco no trae cabecera: rank,dominio. Se analiza la portada del dominio.
    with legit_csv.open(encoding="utf-8", newline="") as f:
        legit = _valid_urls((f"https://{r[1]}/" for r in csv.reader(f) if len(r) > 1), validate)

    rng = random.Random(seed)
    dataset = []
    for label, urls in ((MALICIOUS, phishing), (LEGIT, legit)):
        if len(urls) < n:
            raise SystemExit(f"{label}: se pidieron {n} URLs y hay {len(urls)} validas")
        dataset += [{"url": u, "label": label} for u in rng.sample(urls, n)]
    return dataset


# --- Metricas ---


def _ratio(num: int, den: int) -> float | None:
    return round(num / den, 4) if den else None


def percentile(values: list[float], q: float) -> float | None:
    """Percentil por rango mas cercano: siempre devuelve un valor observado."""
    if not values:
        return None
    ordenados = sorted(values)
    return ordenados[max(math.ceil(q / 100 * len(ordenados)) - 1, 0)]


def mcnemar_p(b: int, c: int) -> float:
    """p-valor exacto (binomial, dos colas) de la prueba de McNemar.

    Compara dos clasificadores sobre las mismas muestras usando solo los pares
    discordantes: `b` detectadas solo por uno, `c` solo por el otro. Es la
    prueba que corresponde a un A/B pareado; comparar las dos tasas como si
    fueran muestras independientes ignoraria el emparejamiento.
    """
    n = b + c
    if n == 0:
        return 1.0
    cola = sum(math.comb(n, i) for i in range(min(b, c) + 1)) / 2**n
    return min(1.0, 2 * cola)


def confusion(rows: list[dict], positivos: set[str]) -> dict:
    tp = sum(r["label"] == MALICIOUS and r["verdict"] in positivos for r in rows)
    fn = sum(r["label"] == MALICIOUS and r["verdict"] not in positivos for r in rows)
    fp = sum(r["label"] == LEGIT and r["verdict"] in positivos for r in rows)
    tn = sum(r["label"] == LEGIT and r["verdict"] not in positivos for r in rows)
    precision, recall = _ratio(tp, tp + fp), _ratio(tp, tp + fn)
    if precision is None or recall is None:
        f1 = None
    else:
        f1 = round(2 * precision * recall / (precision + recall), 4) if precision + recall else 0.0
    return {
        "tp": tp, "fp": fp, "tn": tn, "fn": fn,
        "precision": precision, "recall": recall, "f1": f1,
        "fpr": _ratio(fp, fp + tn), "accuracy": _ratio(tp + tn, len(rows)),
    }  # fmt: skip


def summarize_mode(rows: list[dict]) -> dict:
    ok = [r for r in rows if r["verdict"] != "error"]
    tiempos_capa: dict[str, list[float]] = {}
    for r in ok:
        for capa in r["layers"]:
            tiempos_capa.setdefault(capa["layer"], []).append(capa["duration_ms"])
    detectadas = [r for r in ok if r["label"] == MALICIOUS and r["verdict"] in CRITERIA["amplio"]]
    return {
        "analizadas": len(ok),
        "errores": len(rows) - len(ok),
        "criterios": {nombre: confusion(ok, pos) for nombre, pos in CRITERIA.items()},
        "latencia_ms": {
            "total": {
                "p50": percentile([r["total_ms"] for r in ok], 50),
                "p95": percentile([r["total_ms"] for r in ok], 95),
                "max": max((r["total_ms"] for r in ok), default=None),
            },
            **{
                capa: {"p50": percentile(v, 50), "p95": percentile(v, 95)}
                for capa, v in tiempos_capa.items()
            },
        },
        # Sobre las maliciosas detectadas: que capa emitio cada deteccion.
        "capa_responsable": dict(Counter(r["deciding_layer"] for r in detectadas)),
        "trazabilidad": {
            "resueltas": _ratio(sum(r["resolved"] for r in ok), len(ok)),
            "reescribieron_url": _ratio(sum(r["rewrote_url"] for r in ok), len(ok)),
        },
    }


def compare(con: list[dict], sin: list[dict]) -> dict:
    """A/B pareado: misma URL en las dos corridas, excluyendo las que fallaron
    en alguna de las dos."""
    sin_por_url = {r["url"]: r for r in sin if r["verdict"] != "error"}
    pares = [
        (a, sin_por_url[a["url"]])
        for a in con
        if a["verdict"] != "error" and a["url"] in sin_por_url
    ]
    resultado = {"pares": len(pares)}
    for nombre, pos in CRITERIA.items():
        por_clase = {}
        for label in (MALICIOUS, LEGIT):
            clase = [(a, b) for a, b in pares if a["label"] == label]
            solo_con = sum(a["verdict"] in pos and b["verdict"] not in pos for a, b in clase)
            solo_sin = sum(b["verdict"] in pos and a["verdict"] not in pos for a, b in clase)
            por_clase[label] = {
                "marcadas_solo_con_trazabilidad": solo_con,
                "marcadas_solo_sin_trazabilidad": solo_sin,
                "mcnemar_p": round(mcnemar_p(solo_con, solo_sin), 6),
            }
        # Subconjunto donde la trazabilidad tuvo algo que hacer: la URL del QR
        # no era el destino. En el resto las dos corridas analizan lo mismo.
        redirigidas = [(a, b) for a, b in pares if a["label"] == MALICIOUS and a["rewrote_url"]]
        por_clase["maliciosas_redirigidas"] = {
            "n": len(redirigidas),
            "recall_con": _ratio(
                sum(a["verdict"] in pos for a, _ in redirigidas), len(redirigidas)
            ),
            "recall_sin": _ratio(
                sum(b["verdict"] in pos for _, b in redirigidas), len(redirigidas)
            ),
        }
        resultado[nombre] = por_clase
    return resultado


# --- Corrida ---


def _analyze_rows(dataset: list[dict], tracing: bool, workers: int) -> list[dict]:
    from fastapi import BackgroundTasks

    from app import telemetry
    from app.api.v1 import analyze as endpoint

    # El flag se lee al importar la config y cada modulo guarda su copia: hay
    # que cambiar las dos. La verificacion de hops mas abajo detecta si algun
    # modulo nuevo empieza a leerlo y queda sin cambiar.
    endpoint.REDIRECT_TRACING_ENABLED = tracing
    telemetry.REDIRECT_TRACING_ENABLED = tracing

    def uno(fila: dict) -> dict:
        base = {"url": fila["url"], "label": fila["label"], "tracing": tracing}
        try:
            resp = endpoint.analyze(endpoint.AnalyzeRequest(url=fila["url"]), BackgroundTasks())
        except Exception as exc:
            # Una URL que revienta el analisis se cuenta aparte, no como verde.
            return {**base, "verdict": "error", "error": type(exc).__name__, "layers": []}
        return {
            **base,
            "verdict": resp.verdict,
            "score": resp.score,
            "deciding_layer": resp.metrics.deciding_layer,
            "total_ms": resp.metrics.total_ms,
            "hops": resp.redirects.hops,
            "resolved": resp.redirects.resolved,
            "rewrote_url": resp.redirects.rewrote_url,
            "final_url": resp.final_url,
            "layers": [c.model_dump() for c in resp.metrics.layers],
        }

    # ponytail: hilos de la stdlib. Techo conocido: con muchos workers las
    # peticiones de la trazabilidad compiten por red y su latencia medida sube;
    # por eso `workers` queda en el reporte. Para latencias de referencia,
    # correr con --workers 1.
    with ThreadPoolExecutor(max_workers=workers) as pool:
        filas = list(pool.map(uno, dataset))

    if not tracing and any(f.get("hops") for f in filas):
        raise SystemExit("la corrida sin trazabilidad siguio redirecciones: el flag no se aplico")
    return filas


def run(dataset_path: Path, out: Path, workers: int) -> dict:
    # Antes de importar el motor: la config se lee del entorno al importar.
    os.environ["DATABASE_URL"] = ""
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")

    from app import config, urlhaus
    from app.main import app

    with dataset_path.open(encoding="utf-8", newline="") as f:
        dataset = list(csv.DictReader(f))

    if urlhaus.enabled():
        urlhaus.refresh()
    if not urlhaus.ready():
        print("aviso: sin feed de URLhaus, la corrida no incluye L3", file=sys.stderr)

    inicio = time.monotonic()
    con = _analyze_rows(dataset, tracing=True, workers=workers)
    sin = _analyze_rows(dataset, tracing=False, workers=workers)

    reporte = {
        "fecha": datetime.now(UTC).isoformat(timespec="seconds"),
        "motor_version": app.version,
        "dataset": {
            "archivo": dataset_path.name,
            "sha256": hashlib.sha256(dataset_path.read_bytes()).hexdigest(),
            "por_clase": dict(Counter(r["label"] for r in dataset)),
        },
        "configuracion": {
            "workers": workers,
            "capas": ["L1"] + (["L3"] if urlhaus.ready() else []),
            "cache_l2": "desactivada (ver metodologia)",
            "redirect_max_hops": config.REDIRECT_MAX_HOPS,
            "redirect_timeout_s": config.REDIRECT_TIMEOUT_SECONDS,
            "redirect_total_timeout_s": config.REDIRECT_TOTAL_TIMEOUT_SECONDS,
        },
        "duracion_s": round(time.monotonic() - inicio, 1),
        "con_trazabilidad": summarize_mode(con),
        "sin_trazabilidad": summarize_mode(sin),
        "comparacion": compare(con, sin),
    }

    out.mkdir(parents=True, exist_ok=True)
    columnas = [
        "tracing", "label", "verdict", "score", "deciding_layer", "total_ms",
        "hops", "resolved", "rewrote_url", "error", "url", "final_url", "layers",
    ]  # fmt: skip
    with (out / "resultados.csv").open("w", encoding="utf-8", newline="") as f:
        escritor = csv.DictWriter(f, fieldnames=columnas, extrasaction="ignore")
        escritor.writeheader()
        for fila in con + sin:
            escritor.writerow({**fila, "layers": json.dumps(fila["layers"])})
    (out / "reporte.json").write_text(json.dumps(reporte, indent=2, ensure_ascii=False))
    (out / "reporte.md").write_text(render_markdown(reporte))
    return reporte


# --- Reporte legible ---


def _fmt(valor) -> str:
    if valor is None:
        return "-"
    return f"{valor:.1%}" if isinstance(valor, float) and valor <= 1 else str(valor)


def render_markdown(rep: dict) -> str:
    modos = (
        ("Con trazabilidad", rep["con_trazabilidad"]),
        ("Sin trazabilidad", rep["sin_trazabilidad"]),
    )
    lineas = [
        f"# Benchmark A/B del motor {rep['motor_version']}",
        "",
        f"- Fecha: {rep['fecha']}",
        f"- Dataset: `{rep['dataset']['archivo']}` (sha256 `{rep['dataset']['sha256'][:16]}`), "
        + ", ".join(f"{k}: {v}" for k, v in rep["dataset"]["por_clase"].items()),
        f"- Capas: {', '.join(rep['configuracion']['capas'])}; cache L2 desactivada; "
        f"workers: {rep['configuracion']['workers']}; duracion: {rep['duracion_s']} s",
        "",
    ]
    for nombre in CRITERIA:
        lineas += [
            f"## Deteccion, criterio {nombre} ({' o '.join(sorted(CRITERIA[nombre]))})",
            "",
            "| Corrida | Precision | Recall | F1 | FPR | TP | FP | TN | FN |",
            "|---|---|---|---|---|---|---|---|---|",
        ]
        for titulo, modo in modos:
            c = modo["criterios"][nombre]
            lineas.append(
                f"| {titulo} | {_fmt(c['precision'])} | {_fmt(c['recall'])} | {_fmt(c['f1'])} "
                f"| {_fmt(c['fpr'])} | {c['tp']} | {c['fp']} | {c['tn']} | {c['fn']} |"
            )
        comp = rep["comparacion"][nombre]
        red = comp["maliciosas_redirigidas"]
        mal = comp[MALICIOUS]
        lineas += [
            "",
            f"- Maliciosas marcadas solo con trazabilidad: "
            f"{mal['marcadas_solo_con_trazabilidad']}; solo sin ella: "
            f"{mal['marcadas_solo_sin_trazabilidad']} (McNemar p = {mal['mcnemar_p']})",
            f"- Legitimas marcadas solo con trazabilidad: "
            f"{comp[LEGIT]['marcadas_solo_con_trazabilidad']}; solo sin ella: "
            f"{comp[LEGIT]['marcadas_solo_sin_trazabilidad']}",
            f"- Maliciosas cuyo destino difiere de la URL del QR (n = {red['n']}): recall "
            f"{_fmt(red['recall_con'])} con trazabilidad, {_fmt(red['recall_sin'])} sin ella",
            "",
        ]
    lineas += ["## Latencia (ms)", "", "| Corrida | Medida | p50 | p95 |", "|---|---|---|---|"]
    for titulo, modo in modos:
        for medida, v in modo["latencia_ms"].items():
            lineas.append(f"| {titulo} | {medida} | {v['p50']} | {v['p95']} |")
    lineas += ["", "## Capa responsable de las detecciones (criterio amplio)", ""]
    for titulo, modo in modos:
        lineas.append(f"- {titulo}: {modo['capa_responsable'] or '-'}; errores: {modo['errores']}")
    return "\n".join(lineas) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="comando", required=True)

    ds = sub.add_parser("dataset", help="muestrea el dataset etiquetado")
    ds.add_argument("--phishing", type=Path, required=True, help="CSV de PhishTank (columna url)")
    ds.add_argument("--legit", type=Path, required=True, help="CSV de Tranco (rank,dominio)")
    ds.add_argument("--n", type=int, default=500, help="URLs por clase")
    ds.add_argument("--seed", type=int, default=42)
    ds.add_argument("--out", type=Path, required=True)

    rn = sub.add_parser("run", help="corre las dos pasadas y escribe el reporte")
    rn.add_argument("--dataset", type=Path, required=True)
    rn.add_argument("--out", type=Path, required=True)
    rn.add_argument("--workers", type=int, default=8)

    args = parser.parse_args()
    if args.comando == "dataset":
        filas = build_dataset(args.phishing, args.legit, args.n, args.seed)
        with args.out.open("w", encoding="utf-8", newline="") as f:
            escritor = csv.DictWriter(f, fieldnames=["url", "label"])
            escritor.writeheader()
            escritor.writerows(filas)
        print(f"{len(filas)} URLs escritas en {args.out}")
    else:
        print(render_markdown(run(args.dataset, args.out, args.workers)))


if __name__ == "__main__":
    main()

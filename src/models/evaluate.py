"""Strategy evaluation over history with descriptive metrics (T-004).

Metrics describe past overlap (hits against drawn concursos),
coverage and jogo shape. They do not predict future concursos:
lottery draws are random and independent.
"""

from __future__ import annotations

from collections.abc import Sequence

import pandas as pd  # type: ignore[import-untyped]

import config
from src.models import generate

DEZENA_COLS: tuple[str, ...] = tuple(config.DEZENA_COLS)

COMPARE_COLUMNS: tuple[str, ...] = (
    "strategy",
    "n_palmites",
    "cobertura",
    "soma_media",
    "pares_medio",
    "acertos_medio",
    "acertos_max",
)


def _require_dezena_frame(df: pd.DataFrame, label: str) -> pd.DataFrame:
    missing = [col for col in DEZENA_COLS if col not in df.columns]
    if missing:
        raise ValueError(
            f"CSV inválido: colunas ausentes {missing} em {label}. "
            f"Esperado: {', '.join(DEZENA_COLS)}."
        )
    if df.empty:
        raise ValueError(f"Dado vazio: sem {label} para avaliar.")
    return df


def count_hits(palpite: Sequence[int], concurso: Sequence[int]) -> int:
    """Count shared dezenas between one palpite and one concurso."""
    return len({int(v) for v in palpite} & {int(v) for v in concurso})


def evaluate_palmites(
    history: pd.DataFrame, palpites: pd.DataFrame
) -> dict[str, float]:
    """Describe palpites against history (deterministic, no prediction).

    Returns n_palmites, cobertura (distinct dezenas / 60), soma_media,
    pares_medio, acertos_medio (mean hits over every palpite x concurso
    pair) and acertos_max. Raises ValueError on empty input.
    """
    _require_dezena_frame(history, "concursos")
    _require_dezena_frame(palpites, "palpites")
    history_jogos = history[list(DEZENA_COLS)].to_numpy(dtype=int).tolist()
    palpite_jogos = palpites[list(DEZENA_COLS)].to_numpy(dtype=int).tolist()
    total_hits = 0
    max_hits = 0
    pairs = 0
    for palpite in palpite_jogos:
        for concurso in history_jogos:
            hits = count_hits(palpite, concurso)
            total_hits += hits
            max_hits = max(max_hits, hits)
            pairs += 1
    distinct = {int(v) for jogo in palpite_jogos for v in jogo}
    somas = [sum(int(v) for v in jogo) for jogo in palpite_jogos]
    pares = [sum(1 for v in jogo if int(v) % 2 == 0) for jogo in palpite_jogos]
    span = config.MAX_DEZENA - config.MIN_DEZENA + 1
    return {
        "n_palmites": float(len(palpite_jogos)),
        "cobertura": float(len(distinct) / span),
        "soma_media": float(sum(somas) / len(somas)),
        "pares_medio": float(sum(pares) / len(pares)),
        "acertos_medio": float(total_hits / pairs) if pairs else 0.0,
        "acertos_max": float(max_hits),
    }


def compare_strategies(
    history: pd.DataFrame,
    n: int = config.NUM_GUESSES,
    seed: int | None = config.RANDOM_SEED,
    strategies: Sequence[str] = ("frequencia", "atraso", "combinada", "aleatoria"),
) -> pd.DataFrame:
    """Generate n palpites per strategy and evaluate each (deterministic).

    The "aleatoria" entry uses the uniform random baseline; any other
    entry must be a ranking strategy accepted by rank.rank_dezenas.
    Returns one row per strategy with descriptive metrics.
    """
    if history.empty:
        raise ValueError("Dado vazio: sem concursos para comparar estratégias.")
    if not strategies:
        raise ValueError("Sem estratégias: informe ao menos uma estratégia.")
    rows: list[dict[str, object]] = []
    for strategy in strategies:
        if strategy == "aleatoria":
            palpites = generate.generate_random_palmites(n=n, seed=seed)
        else:
            palpites = generate.generate_ranked_palmites(
                history, n=n, seed=seed, strategy=strategy
            )
        metrics = evaluate_palmites(history, palpites)
        rows.append({"strategy": strategy, **metrics})
    table = pd.DataFrame(rows, columns=list(COMPARE_COLUMNS))
    return table.reset_index(drop=True)

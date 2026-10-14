"""Jogo validation and per-concurso feature derivation."""

from __future__ import annotations

import numbers

import pandas as pd  # type: ignore[import-untyped]

import config

CONTEST_COL = config.CONTEST_COL
DEZENA_COLS: tuple[str, ...] = tuple(config.DEZENA_COLS)
MIN_DEZENA = config.MIN_DEZENA
MAX_DEZENA = config.MAX_DEZENA
NUMBERS_PER_GAME = config.NUMBERS_PER_GAME

PROCESSED_COLUMNS: tuple[str, ...] = (
    config.CONTEST_COL,
    config.DATE_COL,
    *config.DEZENA_COLS,
    "soma",
    "n_pares",
    "n_impares",
)


def _coerce_dezena(value: object, contest_id: object) -> int:
    """Coerce one dezena to int or raise an explanatory error."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        raise ValueError(
            f"concurso {contest_id} tem dezena ausente/nula: "
            f"o jogo precisa de {NUMBERS_PER_GAME} dezenas válidas."
        )
    if isinstance(value, bool):
        raise ValueError(  # noqa: TRY004 - domain contract is ValueError with message
            f"concurso {contest_id} tem dezena inválida ({value!r}): "
            "use inteiros de 1 a 60."
        )
    if isinstance(value, str):
        try:
            number = int(value.strip())
        except ValueError as exc:
            raise ValueError(
                f"concurso {contest_id} tem dezena inválida ({value!r}): "
                "use inteiros de 1 a 60."
            ) from exc
    elif isinstance(value, numbers.Integral):
        number = int(value)
    elif isinstance(value, numbers.Real):
        if not float(value).is_integer():
            raise ValueError(
                f"concurso {contest_id} tem dezena inválida ({value!r}): "
                "use inteiros de 1 a 60."
            )
        number = int(float(value))
    else:
        raise ValueError(  # noqa: TRY004 - domain contract is ValueError with message
            f"concurso {contest_id} tem dezena inválida ({value!r}): "
            "use inteiros de 1 a 60."
        )
    if number < MIN_DEZENA or number > MAX_DEZENA:
        raise ValueError(
            f"concurso {contest_id}: dezena {number} fora do intervalo "
            f"{MIN_DEZENA}-{MAX_DEZENA} "
            f"(o jogo deve ter {NUMBERS_PER_GAME} dezenas distintas de 1 a 60)."
        )
    return number


def validate_concursos(df: pd.DataFrame) -> None:
    """Validate the canonical per-concurso frame; raise ValueError if invalid."""
    required = [CONTEST_COL, config.DATE_COL, *DEZENA_COLS]
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(
            f"CSV inválido: colunas ausentes {missing}. Esperado: {', '.join(required)}."
        )
    if df.empty:
        raise ValueError("Dado vazio: nenhum concurso para processar.")
    if df[CONTEST_COL].isna().any():
        raise ValueError("concurso ausente/nulo: todo sorteio precisa de número.")
    duplicated = df[CONTEST_COL][df[CONTEST_COL].duplicated(keep=False)]
    if not duplicated.empty:
        dup_ids = sorted({str(v) for v in duplicated.tolist()})
        raise ValueError(
            f"concurso duplicado: {dup_ids}. O processado exige um registro por concurso."
        )
    for _, row in df.iterrows():
        contest_id = row[CONTEST_COL]
        dezenas: list[int] = []
        for col in DEZENA_COLS:
            raw_value = row[col]
            if pd.isna(raw_value):
                raise ValueError(
                    f"concurso {contest_id} tem dezena ausente/nula em {col}: "
                    f"o jogo precisa de {NUMBERS_PER_GAME} dezenas válidas."
                )
            dezenas.append(_coerce_dezena(raw_value, contest_id))
        if len(dezenas) != NUMBERS_PER_GAME:
            raise ValueError(
                f"concurso {contest_id} tem {len(dezenas)} dezenas: "
                f"o jogo precisa de {NUMBERS_PER_GAME} dezenas."
            )
        if len(set(dezenas)) != NUMBERS_PER_GAME:
            raise ValueError(
                f"concurso {contest_id} tem dezenas repetidas: {dezenas}. "
                "Cada jogo precisa de 6 dezenas distintas."
            )


def process_concursos(df: pd.DataFrame) -> pd.DataFrame:
    """Validate, sort and derive per-concurso features (deterministic).

    Normalizes dezenas ascending within each jogo, sorts by concurso and
    derives soma, n_pares and n_impares. Never mutates the input.
    """
    validate_concursos(df)
    work = df.copy()
    normalized: list[list[int]] = []
    for _, row in work.iterrows():
        dezenas = sorted(
            _coerce_dezena(row[col], row[CONTEST_COL]) for col in DEZENA_COLS
        )
        normalized.append(dezenas)
    for i, col in enumerate(DEZENA_COLS):
        work[col] = [row[i] for row in normalized]
    work = work.sort_values(by=CONTEST_COL, kind="mergesort").reset_index(drop=True)
    dezenas_frame = work[list(DEZENA_COLS)]
    work["soma"] = dezenas_frame.sum(axis=1).astype(int)
    work["n_pares"] = (dezenas_frame % 2 == 0).sum(axis=1).astype(int)
    work["n_impares"] = (NUMBERS_PER_GAME - work["n_pares"]).astype(int)
    ordered_cols = [
        CONTEST_COL,
        config.DATE_COL,
        *DEZENA_COLS,
        "soma",
        "n_pares",
        "n_impares",
    ]
    return work[ordered_cols].reset_index(drop=True)


def compute_frequencia(df: pd.DataFrame) -> pd.DataFrame:
    """Count appearances per dezena (1-60) over the given concursos."""
    if df.empty:
        raise ValueError("Dado vazio: sem concursos para calcular frequência.")
    stacked = df[list(DEZENA_COLS)].melt(value_name="dezena")["dezena"]
    counts = stacked.value_counts()
    rows = [
        {"dezena": dezena, "frequencia": int(counts.get(dezena, 0))}
        for dezena in range(MIN_DEZENA, MAX_DEZENA + 1)
    ]
    return pd.DataFrame(rows, columns=["dezena", "frequencia"])


def compute_atraso(df: pd.DataFrame) -> pd.DataFrame:
    """Count concursos since the last appearance per dezena.

    Atraso is positional: 0 when the dezena was drawn in the last concurso,
    1 when last seen one concurso before, and len(df) when never drawn.
    """
    if df.empty:
        raise ValueError("Dado vazio: sem concursos para calcular atraso.")
    ordered = df.sort_values(by=CONTEST_COL, kind="mergesort").reset_index(drop=True)
    n = len(ordered)
    last_seen: dict[int, int] = {}
    for pos, (_, row) in enumerate(ordered.iterrows()):
        for col in DEZENA_COLS:
            last_seen[int(row[col])] = pos
    rows = [
        {
            "dezena": dezena,
            "atraso": (n - 1 - last_seen[dezena]) if dezena in last_seen else n,
        }
        for dezena in range(MIN_DEZENA, MAX_DEZENA + 1)
    ]
    return pd.DataFrame(rows, columns=["dezena", "atraso"])

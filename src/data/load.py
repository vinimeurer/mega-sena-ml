"""Raw concurso CSV loading with explicit schema validation."""

from __future__ import annotations

import csv
from pathlib import Path

import pandas as pd  # type: ignore[import-untyped]

import config

REQUIRED_COLUMNS: tuple[str, ...] = (
    config.CONTEST_COL,
    config.DATE_COL,
    *config.DEZENA_COLS,
)

# Official Caixa header aliases (normalized lowercase -> canonical).
# Accepts the Caixa file as-is: UTF-8 with BOM, ';' separator,
# "Concurso;Data do Sorteio;Bola1..Bola6" plus extra payout columns.
_CAIXA_ALIASES: dict[str, str] = {
    "concurso": config.CONTEST_COL,
    "data": config.DATE_COL,
    "data do sorteio": config.DATE_COL,
    **{f"bola{i}": col for i, col in enumerate(config.DEZENA_COLS, start=1)},
    **{
        col.lower(): col
        for col in (config.CONTEST_COL, config.DATE_COL, *config.DEZENA_COLS)
    },
}


def _canonicalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Rename official Caixa headers to the canonical schema in a copy."""
    rename: dict[str, str] = {}
    for col in df.columns:
        normalized = str(col).lstrip("\ufeff").strip().lower()
        canonical = _CAIXA_ALIASES.get(normalized)
        if canonical is not None and col != canonical:
            rename[col] = canonical
    if rename:
        df = df.rename(columns=rename)
    return df


def load_raw_csv(path: str | Path) -> pd.DataFrame:
    """Load the per-concurso raw CSV without modifying it.

    Accepts both the simple comma format
    (``concurso,data,dezena_1..dezena_6``) and the official Caixa file
    as-is (UTF-8 with BOM, ``;`` separator,
    ``Concurso;Data do Sorteio;Bola1..Bola6`` plus extra payout columns,
    which are ignored). Dates are kept as-is (``DD/MM/YYYY`` or ISO).

    Raises:
        FileNotFoundError: when the file does not exist.
        ValueError: when the CSV is malformed, has missing columns or no rows.
    """
    csv_path = Path(path)
    if not csv_path.is_file():
        raise FileNotFoundError(
            f"CSV bruto não encontrado: {csv_path}. "
            "Coloque o histórico por concurso em data/raw/ "
            "(ver README, seção Dados brutos)."
        )
    try:
        df = pd.read_csv(csv_path, encoding="utf-8-sig", sep=None, engine="python")
    except (
        pd.errors.EmptyDataError,
        pd.errors.ParserError,
        UnicodeDecodeError,
        OSError,
        csv.Error,
    ) as exc:
        raise ValueError(
            f"CSV malformado: {csv_path} não pôde ser lido ({exc})."
        ) from exc
    df = _canonicalize_columns(df)
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(
            f"CSV inválido: colunas ausentes {missing} em {csv_path}. "
            f"Esperado: {', '.join(REQUIRED_COLUMNS)}."
        )
    if df.empty:
        raise ValueError(
            f"CSV vazio: {csv_path} não tem registros (só cabeçalho, sem concursos)."
        )
    return df

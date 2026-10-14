"""Single entry point for mega-sena-ml (T-002 historical pipeline)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd  # type: ignore[import-untyped]

import config
import init_project
from src.data import load, process, save

PROCESSED_FILENAME = "mega_sena_processed.csv"


def find_raw_files() -> list[str]:
    """List raw CSV files under the configured raw data directory."""
    if not config.DATA_RAW_DIR.is_dir():
        return []
    return sorted(str(p) for p in config.DATA_RAW_DIR.glob("*.csv"))


def process_first_usable(raw_files: list[str]) -> tuple[str, pd.DataFrame]:
    """Load and process the first usable raw CSV.

    Returns the source path and the processed frame. Raises ValueError when
    no file is usable, chaining the last error for a clear message.
    """
    last_error: Exception | None = None
    for raw_path in raw_files:
        try:
            raw_df = load.load_raw_csv(raw_path)
            return raw_path, process.process_concursos(raw_df)
        except (FileNotFoundError, ValueError) as exc:
            last_error = exc
            continue
    detail = f": {last_error}" if last_error is not None else ""
    raise ValueError(
        "Nenhum CSV utilizável em data/raw/. "
        "Coloque o histórico por concurso "
        "(colunas: concurso,data,dezena_1..dezena_6) em data/raw/ "
        "e rode `python main.py` de novo"
        f"{detail}"
    )


def run_pipeline() -> tuple[str, Path, pd.DataFrame]:
    """Run load -> process -> save for the first usable raw CSV."""
    raw_files = find_raw_files()
    source, processed = process_first_usable(raw_files)
    target = Path(config.DATA_PROCESSED_DIR) / PROCESSED_FILENAME
    save.save_processed(processed, target)
    return source, target, processed


def main() -> int:
    """Ensure dirs, process the historical concursos and report the result."""
    init_project.ensure_directories()

    raw_files = find_raw_files()
    if not raw_files:
        print("[mega-sena-ml] Nenhum dado bruto encontrado em data/raw/.")
        print("[mega-sena-ml] Falta o histórico completo por concurso em CSV")
        print("[mega-sena-ml] (colunas: concurso,data,dezena_1..dezena_6).")
        print("[mega-sena-ml] Como seguir: baixe o resultado oficial da Caixa")
        print("[mega-sena-ml] (Portal Loterias > Mega-Sena > Download de resultados,")
        print(
            "[mega-sena-ml] https://loterias.caixa.gov.br/Paginas/Download-Resultados.aspx),"
        )
        print("[mega-sena-ml] converta para CSV por concurso e coloque em data/raw/")
        print("[mega-sena-ml] (ver README, seção Dados brutos).")
        return 0

    print(f"[mega-sena-ml] Encontrados {len(raw_files)} arquivo(s) em data/raw/:")
    for path in raw_files:
        print(f"  - {path}")
    try:
        source, target, processed = run_pipeline()
    except (FileNotFoundError, ValueError) as exc:
        print(f"[mega-sena-ml] Erro nos dados brutos: {exc}")
        print("[mega-sena-ml] Nenhum CSV utilizável em data/raw/.")
        print("[mega-sena-ml] Esperado: um CSV por concurso com")
        print("[mega-sena-ml] (colunas: concurso,data,dezena_1..dezena_6).")
        print(
            "[mega-sena-ml] Baixe o resultado oficial da Caixa e coloque em data/raw/"
        )
        print("[mega-sena-ml] (ver README, seção Dados brutos).")
        return 2

    print(f"[mega-sena-ml] Fonte usada: {source}")
    print(
        f"[mega-sena-ml] Processados {len(processed)} concursos "
        f"-> {target} (soma, pares/ímpares; frequência e atraso via src/data/process.py)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

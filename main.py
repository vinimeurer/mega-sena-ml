"""Single entry point for mega-sena-ml (skeleton, T-001)."""

from __future__ import annotations

import config
import init_project


def find_raw_files() -> list[str]:
    """List raw CSV files under the configured raw data directory."""
    if not config.DATA_RAW_DIR.is_dir():
        return []
    return sorted(str(p) for p in config.DATA_RAW_DIR.glob("*.csv"))


def main() -> int:
    """Ensure skeleton dirs and report what is missing to run the pipeline."""
    init_project.ensure_directories()

    raw_files = find_raw_files()
    if not raw_files:
        print("[mega-sena-ml] Nenhum dado bruto encontrado em data/raw/.")
        print("[mega-sena-ml] Falta o histórico completo por concurso em CSV")
        print("[mega-sena-ml] (colunas: concurso,data,dezena_1..dezena_6).")
        print("[mega-sena-ml] Como seguir: coloque o CSV oficial da Caixa em data/raw/")
        print(
            "[mega-sena-ml] e rode `python main.py` de novo. Pipeline completo chega nos tickets T-002+."
        )
        return 0

    print(f"[mega-sena-ml] Encontrados {len(raw_files)} arquivo(s) em data/raw/:")
    for path in raw_files:
        print(f"  - {path}")
    print(
        "[mega-sena-ml] Esqueleto T-001 OK. Pipeline de EDA/modelos chega nos próximos tickets."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

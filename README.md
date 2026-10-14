# mega-sena-ml

Estudo estatístico dos concursos da Mega-Sena com geração de palpites. Projeto pessoal espelhado no `employment-balance-predictor`.

Vocabulário (ver `GLOSSARY.md` no vault): **concurso** (sorteio com 6 dezenas), **dezena** (1–60), **jogo** (6 dezenas), **palpite** (jogo sugerido sem garantia), **frequência** e **atraso**.

## Pré-requisitos

- Python 3.10+

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

O `requirements.txt` tem versões pinadas de pandas, matplotlib, seaborn, scikit-learn, xgboost, jupyter e pytest.

Configuração opcional (tudo tem padrão em `config.py`):

```bash
cp .env.example .env
```

## Execução

```bash
python init_project.py   # cria data/raw,processed,outputs, notebooks/, src/data, src/models, tests/, models/ (idempotente)
python main.py           # roda de ponta a ponta
```

Sem dados reais o `main.py` termina com exit 0 e explica o que falta: colocar o histórico completo por concurso (CSV com `concurso,data,dezena_1..dezena_6`) em `data/raw/`. O CSV atual `mega_sena_resultados_2009_2023.csv` (1 jogo por ano) é só referência histórica; a fonte principal (T-002) será o CSV oficial da Caixa. O pipeline de EDA e modelos chega nos tickets T-002+.

## Estrutura

- `data/raw/` — CSV bruto intocado; `data/processed/` — derivados; `data/outputs/` — palpites em CSV
- `notebooks/` — EDA e tuning (lógica testável fica em `src/`)
- `src/data/` — carga e processamento; `src/models/` — ranqueador/gerador de palpites
- `config.py` — caminhos, colunas, quantidade de palpites, semente e parâmetros
- `main.py` — ponto de entrada único; `init_project.py` — inicialização idempotente
- `tests/` — pytest por módulo (`pytest -q`); `models/` — artefatos treinados

## Testes

```bash
pytest -q
```

## Limitação importante

Loteria é aleatória. Este projeto é educacional e estatístico: mostra frequência, atraso e compara estratégia contra baseline aleatório, mas **não promete acerto nem recomenda aposta**. Não use como aconselhamento financeiro.

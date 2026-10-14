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

## Dados brutos

Fonte oficial (única fonte aceita): Portal Loterias da Caixa, página
`Mega-Sena > Download de resultados` em
<https://loterias.caixa.gov.br/Paginas/Download-Resultados.aspx>
(atalho: <https://loterias.caixa.gov.br/Paginas/Mega-Sena.aspx>).
Baixe o arquivo da Mega-Sena (ZIP com HTML/XLS de todos os concursos já sorteados).

Como preparar (manual, uma vez):

1. Extraia o arquivo baixado e exporte para CSV UTF-8 com exatamente este cabeçalho:
   `concurso,data,dezena_1,dezena_2,dezena_3,dezena_4,dezena_5,dezena_6`
2. Um registro por concurso, ordenado por `concurso` crescente. Exemplo:
   ```csv
   concurso,data,dezena_1,dezena_2,dezena_3,dezena_4,dezena_5,dezena_6
   1,1996-03-11,4,5,30,33,41,52
   2,1996-03-18,1,2,3,4,5,60
   ```
3. Salve como `data/raw/mega_sena_concursos.csv` (qualquer `*.csv` dentro de
   `data/raw/` vale; o pipeline usa o primeiro utilizável em ordem alfabética).
4. Rode `python main.py`: ele valida cada jogo (6 dezenas inteiras 1–60,
   distintas, sem nulo), ordena dezenas e concursos, deriva `soma`,
   `n_pares`/`n_impares` e salva
   `data/processed/mega_sena_processed.csv` sem coluna de índice
   (reprocessar gera bytes idênticos). Frequência e atraso por dezena saem de
   `src/data/process.py:compute_frequencia/compute_atraso`.
   CSV ausente ou malformado, ou dezena inválida, falha com erro explicativo
   (exit 2 no `main.py`).

Nota sobre o legado: `mega_sena_resultados_2009_2023.csv` na raiz (17 linhas,
1 jogo por ano, colunas `ano,dezena_1..6`) é mantido como referência histórica
e **não** é lido pelo pipeline (não está em `data/raw/` e não tem as colunas
`concurso,data`). Não o apague; também não o coloque em `data/raw/`.

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

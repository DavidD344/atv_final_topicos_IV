# SPL NFP Sampling

Este projeto compara estrategias de **sampling de variantes** para predicao de propriedades nao funcionais (NFPs) em Software Product Lines (SPLs).

O foco principal e avaliar se **K-means pode ser usado como metodo de sampling**. Nao buscamos encontrar automaticamente o K otimo; testamos uma ampla faixa de valores de K para observar o potencial do metodo em diferentes cenarios.

## O que e comparado

Metodos avaliados:

- **Random:** seleciona variantes aleatoriamente.
- **Diversity:** seleciona variantes distantes entre si usando distancia de Hamming normalizada.
- **K-means default:** usa K-means padrao com distancia Euclidiana, agrupa variantes e alterna entre clusters.
- **K-means Hamming:** usa o mesmo K-means, mas ordena variantes dentro de cada cluster por diversidade Hamming.

Todos os metodos treinam o mesmo modelo de predicao.

## Configuracao do experimento

- Datasets reais: Apache, BDBC, BDBJ e LLVM.
- Alvo: `Measured_Value`.
- Modelo: Linear Regression.
- Metrica: MAPE.
- Percentuais analisados: 10% a 70%.
- Valores de K: 5 a 50.
- Metodos estocasticos: 30 repeticoes.
- Teste: variantes nao selecionadas para treino.

## Como rodar

Instale/execute com `uv`.

Rodar os experimentos:

```bash
uv run python run_experiments.py
```

Rodar em paralelo:

```bash
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 uv run python run_experiments.py --jobs 8
```

Gerar tabelas a partir dos resultados:

```bash
uv run python generate_tables.py
```

Gerar graficos sem rodar os experimentos novamente:

```bash
uv run python generate_plots.py
```

## Saidas

- `results/raw_results.csv`: resultados por execucao.
- `results/summary_results.csv`: medias e desvios por metodo.
- `results/tables/`: tabelas em CSV/Markdown.
- `results/table_images/`: tabelas renderizadas como PNG/PDF.
- `results/plots/`: graficos em PNG.

## Documentos uteis

- `METODOLOGIA_EXPERIMENTO.md`: detalhes metodologicos.
- `ROTEIRO_APRESENTACAO.md`: guia para apresentacao.
- `INSIGHTS_REUNIAO.md`: principais interpretacoes dos resultados.

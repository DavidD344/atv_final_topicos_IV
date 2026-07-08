# Projeto Final

Encontramos o paper **"Efficient Product-Line Testing using Cluster-Based Product Prioritization"**. Ele propõe usar **K-means** para agrupar variantes de uma linha de produto e depois priorizar os testes dentro desses grupos.

A ideia central do paper é reduzir o custo de teste explorando similaridade entre variantes. Porém, os próprios resultados mostram uma fragilidade importante: quanto mais clusters são usados, pior tende a ser o resultado médio. Além disso, a abordagem fica abaixo da priorização puramente baseada em similaridade e a avaliação usa falhas sintéticas, não dados reais de performance. Ou seja, o uso de clusters como priorização de testes não parece ser a parte mais forte da proposta.

Nossa ideia é trazer essa intuição para nossa área de pesquisa: **predição de propriedades não funcionais em linhas de produto de software**. Em vez de usar K-means apenas para priorizar testes, vamos investigar o K-means como método de **sampling** para escolher variantes a serem medidas/treinadas.

Nosso objetivo principal é testar e validar se o **K-means pode ser viável como método de sampling**. Por isso, testamos muitos valores de K. Descobrir automaticamente o melhor K para cada dataset ou tamanho de amostra não é o foco deste trabalho; isso fica como limitação e possível trabalho futuro.

A hipótese é simples: se alternarmos entre grupos gerados pelo K-means, escolhendo variantes de clusters diferentes, podemos obter uma amostra mais diversa do espaço de configurações. Essa diversidade pode melhorar a predição de propriedades não funcionais quando comparada a uma seleção aleatória de variantes.

No K-means, a estratégia central é alternar entre clusters até atingir o orçamento de amostras. Para a apresentação principal, usamos duas variações. O agrupamento é o mesmo; o que muda é como a fila de variantes dentro de cada cluster é organizada antes de pular de grupo em grupo.

| Variante | Como funciona |
| --- | --- |
| **K-means default** | Usa a ordem natural das variantes em cada cluster, sem embaralhar e sem priorização extra. Serve como versão mais simples: agrupa e alterna entre clusters. |
| **K-means Hamming** | Ordena as variantes dentro de cada cluster por distância de Hamming, escolhendo variantes mais diferentes entre si. É a versão mais próxima da ideia de priorização por similaridade do paper. |

Tambem testamos uma variante exploratoria chamada `kmeans_random`, que embaralha as variantes dentro dos clusters. Como ela nao trouxe ganhos consistentes e poderia confundir com o baseline `random sampling`, ela foi removida das tabelas e graficos principais.

Para o clustering, seguimos a escolha prática do paper: K-means padrão. O paper usa Weka Simple K-means, cuja distância padrão é Euclidiana; nosso experimento usa `sklearn.KMeans`, também com distância Euclidiana. Para o diversity-based sampling e para a variação K-means com priorização interna, usamos distância de Hamming normalizada entre vetores binários de features.

Euclidiana e Hamming ficam relacionadas porque nossas features sao binarias: quanto mais features diferem, maior fica a distancia nas duas metricas. Mesmo assim, elas nao sao usadas no mesmo lugar. A Euclidiana forma os clusters comparando variantes com centroides do K-means; a Hamming ordena variantes binarias diretamente no diversity e no K-means Hamming.

O K-means nao escolhe diretamente as variantes de teste. Ele escolhe as variantes de treino; o teste e simplesmente formado pelas variantes restantes. Assim, cada sampling afeta o teste apenas indiretamente, pelo complemento do conjunto selecionado para treino.

Para testar isso, vamos comparar o K-means com métodos de sampling independentes de um tamanho fixo gerado por cobertura combinatória: **sampling aleatório** e **diversity-based sampling**, que escolhe uma variante inicial, depois a mais diferente dela, depois a mais diferente das anteriores, e assim por diante.

Em vez de usar pairwise ou 3-wise como orçamento, vamos avaliar diferentes tamanhos relativos de amostra. Os resultados brutos foram calculados de **10% até 100%**, mas a análise principal, tabelas e gráficos focam **10%, 20%, ..., 70%**. Percentuais muito altos deixam poucas variantes para teste; no caso de 100%, mantemos apenas uma variante fora do treino para ainda ser possível calcular MAPE, então esse ponto é instável.

Também vamos testar o K-means com vários valores de **K**, variando a quantidade de clusters usados no processo de sampling. A grade será **K = {5, 6, ..., 50}**. Essa expansão foi feita porque, na rodada anterior com K até 20, o maior K testado apareceu muitas vezes como melhor. Diferente do paper, nossa avaliação será feita em **4 datasets reais**, amplamente utilizados na literatura para avaliar performance em predição de propriedades não funcionais.

Uma limitação importante é que a escolha de **K** pode influenciar fortemente o resultado do K-means. Portanto, um desempenho ruim do K-means pode estar relacionado não apenas à ideia de clustering, mas também à escolha inadequada de K para um dataset ou tamanho de amostra específico. Quando mostramos o melhor K-means para cada cenário, essa é uma análise otimista; escolher K automaticamente continua sendo uma limitação e uma possibilidade de trabalho futuro.

Para avaliar os modelos, vamos usar **MAPE** como métrica principal e modelos de regressão simples. Como o objetivo do trabalho é medir o impacto do sampling, o mesmo modelo de regressão será usado para todos os métodos, de forma propositalmente simples.

Em resumo: o paper usa clusters para priorização de testes; nós queremos usar clusters para sampling em predição de propriedades não funcionais. A aposta é que pular de grupo em grupo force maior diversidade nas variantes escolhidas. Ao comparar K-means default e K-means Hamming, conseguimos observar se o ganho vem apenas do agrupamento ou tambem da priorizacao dentro dos clusters.

## Como rodar os experimentos

Os experimentos foram implementados de forma independente do projeto antigo. O código antigo em `AutoML-SPL-Datasets` é usado apenas como fonte dos quatro CSVs de entrada.

Para executar:

```bash
uv run python run_experiments.py
```

Para executar mais rapido em uma CPU com varios cores, use `--jobs`. Em um Ryzen 7 5700G com 64 GB de RAM, uma configuracao recomendada e:

```bash
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 uv --cache-dir /tmp/uv-cache run python run_experiments.py --jobs 8
```

O `--jobs 8` roda repeticoes em paralelo. As variaveis `OMP_NUM_THREADS`, `OPENBLAS_NUM_THREADS` e `MKL_NUM_THREADS` evitam que cada processo tente usar todos os cores ao mesmo tempo.

Para gerar tabelas derivadas dos resultados:

```bash
uv run python generate_tables.py
```

Para gerar ou alterar apenas os gráficos, sem rodar novamente os experimentos:

```bash
uv run python generate_plots.py
```

As saídas são geradas em:

- `results/raw_results.csv`: resultados por dataset, método, repetição e valor de K.
- `results/summary_results.csv`: média e desvio padrão do MAPE por dataset e método.
- `results/tables/`: tabelas em CSV e Markdown para análise, relatório e apresentação.
- `results/plots/`: gráficos em PNG para relatório e apresentação.

Os resultados antigos com `K = 5, 6, ..., 20` foram preservados em `results/snapshots/k_5_20/`.

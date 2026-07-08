# Metodologia do Experimento

Este documento descreve exatamente como os experimentos foram executados, com foco nos metodos de sampling, no uso do K-means, no diversity-based sampling e na metrica de avaliacao.

## Objetivo

O objetivo do experimento e comparar metodos de **sampling de variantes** para predicao de propriedades nao funcionais em linhas de produto de software.

Mais especificamente, queremos testar e validar se o **K-means pode ser viavel como metodo de sampling**. Por isso, testamos muitos valores de K. A intencao nao e resolver o problema de descobrir automaticamente o melhor K para cada caso, mas sim avaliar se existe algum cenario em que K-means, com uma escolha adequada de K, consegue competir com random sampling e diversity-based sampling.

Cada dataset possui:

- colunas binarias representando features/configuracoes;
- uma coluna alvo chamada `Measured_Value`, representando a propriedade nao funcional medida.

Para cada metodo de sampling, selecionamos uma parte das variantes para treino e usamos o restante para teste.

## Datasets

Foram usados 4 datasets reais do projeto `AutoML-SPL-Datasets`:

- Apache;
- BDBC;
- BDBJ;
- LLVM.

O codigo antigo do projeto original foi ignorado. Apenas os CSVs preparados foram usados como entrada.

## Tamanhos de Amostra

Os metodos sao comparados usando os mesmos orcamentos de amostragem.

Foram usados os seguintes percentuais de cada dataset:

- 10%;
- 20%;
- 30%;
- 40%;
- 50%;
- 60%;
- 70%;
- 80%;
- 90%;
- 100%.

No caso de 100%, o codigo seleciona todas as variantes menos uma. Isso e necessario porque precisamos manter pelo menos uma variante fora do treino para calcular o erro no conjunto de teste.

Apesar de os resultados brutos existirem ate 100%, a **analise principal** usa apenas **10% ate 70%**. Percentuais acima de 70% deixam poucas variantes para teste e tornam o MAPE menos estavel, especialmente no caso de 100%, em que apenas uma variante fica fora do treino.

## Modelo de Predicao

O modelo usado em todos os experimentos e **Linear Regression**.

Essa escolha foi propositalmente simples. O objetivo nao e encontrar o melhor modelo de machine learning, mas sim comparar o efeito dos diferentes metodos de sampling.

Assim, todos os metodos usam o mesmo modelo, mudando apenas as variantes escolhidas para treino.

## Metrica de Avaliacao

A metrica principal e **MAPE** (*Mean Absolute Percentage Error*).

Ela mede o erro percentual medio entre o valor real e o valor previsto:

```text
MAPE = mean(abs(y_real - y_predito) / abs(y_real))
```

Quanto menor o MAPE, melhor o resultado.

Como todos os valores de `Measured_Value` nos datasets sao positivos, o MAPE pode ser usado diretamente.

Nos arquivos de tabela, o MAPE e apresentado em porcentagem.

## Random Sampling

O random sampling seleciona variantes aleatoriamente.

Para cada percentual de amostra:

1. Calculamos o numero de variantes que devem ser selecionadas.
2. Sorteamos essa quantidade de variantes sem reposicao.
3. Treinamos o modelo com essas variantes.
4. Testamos nas variantes restantes.

Como esse metodo e aleatorio, ele e repetido 30 vezes.

O resultado final reportado e a media e o desvio padrao do MAPE nas 30 repeticoes.

## Diversity-Based Sampling

O diversity-based sampling busca selecionar variantes diferentes entre si.

O funcionamento e:

1. A primeira variante escolhida e a variante de indice 0 do dataset.
2. Depois, o algoritmo calcula a distancia entre as variantes ainda nao escolhidas e o conjunto de variantes ja selecionadas.
3. A proxima variante escolhida e aquela cuja menor distancia ate as variantes selecionadas e a maior possivel.
4. Esse processo continua ate atingir o tamanho de amostra desejado.

Essa estrategia e conhecida como **farthest-first traversal**.

### Metrica de Distancia no Diversity

A distancia usada e a **distancia de Hamming normalizada**.

Como cada variante e representada por um vetor binario de features, a distancia entre duas variantes e a proporcao de features em que elas diferem.

Exemplo:

```text
v1 = [1, 0, 1, 1]
v2 = [1, 1, 0, 1]
```

Elas diferem em 2 de 4 features, entao:

```text
distancia = 2 / 4 = 0.5
```

No codigo, isso e calculado como:

```python
np.mean(features != variant, axis=1)
```

O diversity-based sampling e deterministico na implementacao atual, pois sempre comeca pela variante de indice 0.

## K-means Sampling

O K-means sampling usa clustering para agrupar variantes semelhantes e depois selecionar variantes alternando entre clusters.

O funcionamento e:

1. O algoritmo recebe todas as variantes do dataset.
2. Usa apenas as colunas de features, nao o `Measured_Value`.
3. Executa K-means com um valor de K.
4. Cada variante recebe um rotulo de cluster.
5. As variantes dentro de cada cluster sao ordenadas conforme a variante do metodo.
6. A selecao e feita em round-robin: o algoritmo pega uma variante de um cluster, depois passa para o proximo cluster, e assim por diante.
7. O processo continua ate atingir o tamanho de amostra desejado.

A ideia e forcar a amostra a passar por diferentes regioes do espaco de configuracoes, em vez de escolher variantes concentradas em apenas uma regiao.

Para a analise principal, foram usadas duas variantes de K-means:

- **K-means default**: usa a organizacao natural gerada pelo K-means, sem embaralhar e sem aplicar priorizacao dentro do cluster.
- **K-means Hamming**: alterna entre clusters e, dentro de cada cluster, ordena as variantes por diversidade usando distancia de Hamming normalizada.

Tambem foi executada uma variante exploratoria, **K-means random**, que embaralha as variantes dentro de cada cluster. Ela permanece nos resultados brutos, mas foi removida das tabelas e graficos principais porque nao trouxe ganhos consistentes e poderia confundir com o baseline **random sampling**.

Em todas as variantes, a parte de clustering e igual: o K-means e treinado com as features binarias e separa as variantes em K grupos. Depois disso, cada grupo vira uma fila de variantes. A diferenca entre as variantes esta exatamente em como essa fila e montada:

| Variante | Fila dentro do cluster | O que ela testa |
| --- | --- | --- |
| **K-means default** | Mantem a ordem natural das variantes pertencentes ao cluster. | Testa o efeito puro de agrupar e alternar entre clusters, sem priorizacao interna. |
| **K-means Hamming** | Reordena as variantes do cluster por farthest-first usando distancia de Hamming normalizada. | Testa se combinar clusters com diversidade interna melhora o sampling. |

Depois que as filas sao criadas, todas as variantes usam o mesmo processo de selecao: pegar uma variante do primeiro cluster, depois uma do segundo, depois uma do terceiro, e assim por diante, voltando ao inicio quando necessario. Esse processo e o round-robin entre clusters.

O **K-means Hamming** e a variante mais proxima da intuicao do paper, porque combina agrupamento com uma etapa de priorizacao por diferenca entre configuracoes dentro dos grupos.

Na variante Hamming, a primeira variante de cada cluster e a que possui mais features ativas. Depois disso, escolhemos iterativamente a variante cuja menor distancia para as variantes ja escolhidas no mesmo cluster seja a maior possivel. Em outras palavras, e uma ordenacao farthest-first dentro de cada cluster.

### Por que o K-means default pode ser melhor que o random?

O **K-means default** nao significa uma ordem teorica especial do algoritmo K-means. Ele significa: depois de formar os clusters, mantemos as variantes dentro de cada cluster na ordem em que aparecem no dataset.

Isso pode ser melhor que o random por alguns motivos:

- a ordem original do dataset pode carregar alguma estrutura da geracao das variantes;
- manter uma ordem deterministica evita sorteios ruins dentro dos clusters;
- o round-robin entre clusters ja introduz diversidade entre grupos, entao embaralhar dentro do cluster nem sempre ajuda;
- o random pode escolher cedo variantes redundantes ou pouco representativas dentro de um mesmo cluster.

Portanto, quando o default vence, a interpretacao correta nao e que existe uma "ordem padrao magica" do K-means. A interpretacao e que **clusterizar e alternar entre clusters, sem adicionar aleatoriedade intra-cluster, foi mais estavel naquele cenario**.

### O K-means escolhe o teste?

Nao diretamente. O K-means escolhe apenas as variantes de **treino**.

Depois que o sampling seleciona as variantes de treino, o conjunto de teste e formado automaticamente pelas variantes restantes, ou seja, pelo complemento do treino.

Exemplo:

```text
dataset = 100 variantes
sampling = 30 variantes para treino
teste = 70 variantes restantes
```

Assim, o K-means afeta o teste apenas indiretamente: ao escolher quais variantes entram no treino, ele tambem determina quais variantes sobram para teste.

## Valores de K

Os valores de K testados sao:

```text
K = 5, 6, 7, ..., 50
```

Se `K` for maior que o tamanho da amostra, esse valor de K e ignorado naquele caso. Isso evita criar mais clusters do que variantes selecionadas.

A grade foi expandida ate 50 porque, na rodada anterior com `K = 5, 6, ..., 20`, o valor `K=20` apareceu muitas vezes como o melhor K-means. Como 20 era a borda superior da busca, isso sugeria que valores maiores poderiam melhorar os resultados em alguns datasets.

## Metrica de Distancia no K-means

No paper base, os autores usam **Weka Simple K-means** para fazer o agrupamento. O artigo nao explicita uma formula de distancia para o clustering, mas o Simple K-means do Weka usa **distancia Euclidiana** por padrao.

Para manter o experimento alinhado ao paper, usamos o `KMeans` do scikit-learn, que tambem usa **distancia Euclidiana** internamente.

Como nossas features sao binarias, a distancia Euclidiana entre duas variantes esta relacionada ao numero de features diferentes entre elas.

Para vetores binarios:

- a distancia de Hamming conta quantas features diferem;
- a distancia Euclidiana e proporcional a raiz quadrada desse numero.

Ou seja, embora K-means use Euclidiana, ela ainda reflete diferencas nas features binarias.

Elas parecem muito parecidas em vetores binarios porque as duas aumentam quando mais features diferem. A diferenca pratica no nosso experimento e onde cada uma e usada:

- **Euclidiana**: usada pelo K-means para formar os clusters e recalcular centroides.
- **Hamming**: usada pelo diversity-based sampling e pela variante K-means Hamming para ordenar variantes por diferenca.

Elas nao precisam produzir exatamente o mesmo comportamento porque o K-means nao compara apenas pares de variantes. Ele compara variantes com **centroides**, que podem ter valores fracionarios como `[0.2, 0.8, 0.5]`. Ja a Hamming compara diretamente vetores binarios de variantes.

Ja para a estrategia de diversity-based sampling e para a variante **K-means Hamming**, usamos Hamming normalizada. Essa e a mesma nocao de diferenca entre configuracoes usada na etapa de priorizacao por similaridade do paper.

## Aleatoriedade no K-means

O K-means pode ter aleatoriedade em dois pontos:

1. inicializacao dos centroides;
2. ordenacao interna dos clusters, dependendo da variante.

Por isso, cada configuracao de K, percentual de amostra e variante de K-means e repetida 30 vezes.

Cada repeticao usa uma seed diferente.

## Interpretacao dos Resultados

As tabelas mostram:

- MAPE medio;
- desvio padrao;
- melhor K-means para cada dataset e percentual;
- comparacao com random e diversity.

Quando mostramos o **melhor K-means**, estamos mostrando uma analise otimista, pois escolhemos o melhor K depois de testar varios valores.

Isso e util para responder:

> Se o K fosse bem escolhido, K-means poderia ser competitivo?

Mas isso tambem revela uma limitacao:

> Escolher K automaticamente e uma parte importante do problema e nao foi resolvida neste trabalho.

Para apoiar essa discussao, tambem geramos uma tabela de comparacao entre valores de K. Ela mostra, para cada dataset e percentual de amostra:

- o MAPE medio de cada K;
- o ranking daquele K dentro da rodada;
- a diferenca absoluta em relacao ao melhor K da rodada;
- a diferenca percentual em relacao ao melhor K da rodada.

Essa tabela ajuda a observar se existe uma faixa de K consistentemente boa ou se o desempenho do K-means e muito sensivel ao valor escolhido.

Tambem geramos heatmaps de sensibilidade ao K. Nesses graficos:

- o eixo X representa o valor de K;
- o eixo Y representa o percentual de amostra;
- cada linha compara valores de K mantendo o mesmo tamanho de amostra;
- a cor representa quanto aquele K ficou pior que o melhor K da mesma linha.

Esse grafico e importante porque a relacao `K x MAPE` pode ficar enviesada quando analisada de forma agregada. Valores maiores de K podem parecer melhores simplesmente porque estao misturados com certos tamanhos de amostra, e o tamanho da amostra tambem afeta diretamente o erro. Portanto, os graficos agregados de `K x MAPE` devem ser lidos como resumo exploratorio. O heatmap de delta e mais adequado para discutir a influencia de K, porque normaliza a comparacao dentro de cada percentual de amostra.

## Limitacoes

Principais limitacoes do desenho experimental:

- o modelo usado e simples, apenas Linear Regression;
- o diversity-based sampling comeca sempre pela variante de indice 0;
- o melhor K-means e uma analise otimista;
- nao ha selecao automatica de K;
- a comparacao entre valores de K pode ser confundida pelo tamanho da amostra, por isso tambem usamos heatmaps que comparam K apenas dentro do mesmo percentual de amostra;
- o caso de 100% usa apenas uma variante no teste, portanto pode ser instavel;
- os resultados podem variar se outro modelo de regressao for usado.

## Comandos

Para rodar os experimentos:

```bash
uv run python run_experiments.py
```

Para gerar tabelas e graficos:

```bash
uv run python generate_tables.py
uv run python generate_plots.py
```

As saidas principais ficam em:

- `results/raw_results.csv`;
- `results/summary_results.csv`;
- `results/tables/`;
- `results/plots/`.

# Insights para a Reuniao

> Estes insights usam a rodada atual com `K = 5, 6, ..., 50`, mas a analise principal considera apenas amostras de **10% ate 70%**. Os resultados brutos ate 100% continuam salvos em `results/raw_results.csv` e `results/summary_results.csv`.

## Mensagem Principal

O resultado mais forte continua sendo que **K-means e viavel como metodo de sampling**, mas nao como solucao universal.

A decisao de focar ate 70% deixa a avaliacao mais defensavel, porque o MAPE e calculado apenas nas variantes que ficaram fora do treino. Acima de 70%, o conjunto de teste fica pequeno demais; em 100%, sobra apenas uma variante para testar.

Com esse recorte, a expansao para `K=50` ainda mostra algo importante: em **14 dos 28 cenarios**, o melhor K-means usa `K > 20`. Ou seja, limitar a busca ate 20 realmente podia esconder bons resultados.

## Resultado Geral

Foram avaliados 28 cenarios principais:

- 4 datasets;
- 7 tamanhos de amostra, de 10% ate 70%;
- comparacao entre random, diversity e duas variantes principais de K-means;
- K-means testado com `K = 5, 6, ..., 50`.

Melhores metodos por cenario:

- **Diversity** venceu em 14 cenarios.
- **K-means default** venceu em 11 cenarios.
- **K-means Hamming** venceu em 3 cenarios.

Ou seja, o K-means venceu em **14 dos 28 cenarios** considerando suas variantes principais. Isso e um resultado bom: K-means empata com diversity em numero de vitorias no recorte principal, mas o comportamento varia bastante por dataset.

## Melhor Insight para Defender

O melhor argumento para a reuniao:

> K-means e competitivo como metodo de sampling, especialmente em datasets onde o agrupamento parece capturar regioes importantes do espaco de configuracoes. No recorte principal ate 70%, ele vence metade dos cenarios. Ao mesmo tempo, a escolha de K e critica, porque muitos melhores resultados aparecem acima de K=20.

Essa narrativa e forte porque mostra viabilidade sem vender uma conclusao exagerada.

## Achados por Dataset

### Apache

No Apache, o **diversity-based sampling** foi claramente mais forte.

K-means venceu apenas em:

- 20%: K-means Hamming, K=5.

Nos demais tamanhos ate 70%, diversity venceu.

Interpretacao: no Apache, diversidade global parece representar melhor o espaco do que agrupamento por K-means.

### BDBC

BDBC e o melhor caso para defender K-means.

K-means venceu em todos os tamanhos de amostra de 10% ate 70%, sempre com **K-means default**:

- 10%: K=20;
- 20%: K=29;
- 30%: K=20;
- 40%: K=32;
- 50%: K=50;
- 60%: K=20;
- 70%: K=24.

Esse e o principal resultado positivo: no BDBC, alternar entre clusters parece capturar regioes do espaco de configuracoes que random e diversity nao capturam tao bem.

### BDBJ

BDBJ favorece mais o diversity.

K-means venceu apenas em:

- 10%: K-means default, K=6.

De 20% ate 70%, diversity venceu todos os cenarios.

Interpretacao: nesse dataset, o agrupamento nao trouxe vantagem consistente no recorte principal.

### LLVM

LLVM mostra um caso intermediario interessante.

K-means venceu em:

- 20%: K-means default, K=22;
- 40%: K-means Hamming, K=25;
- 50%: K-means Hamming, K=40;
- 60%: K-means default, K=36;
- 70%: K-means default, K=28.

Diversity venceu em 10% e 30%.

Interpretacao: em LLVM, K-means ajuda principalmente em amostras intermediarias, e varios melhores K ficam acima de 20.

## Sobre as Variantes de K-means

As duas variantes principais usam o mesmo K-means para formar os clusters. A diferenca nao esta no agrupamento, mas na forma de escolher as variantes dentro de cada cluster antes de alternar entre grupos:

- **K-means default**: usa a ordem natural das variantes dentro do cluster.
- **K-means Hamming**: ordena as variantes dentro do cluster por distancia de Hamming, tentando escolher variantes mais diferentes entre si.

Uma forma simples de explicar:

> Todos pulam de cluster em cluster; o default segue a fila original, e o Hamming organiza a fila por diversidade.

Dentro do K-means, no recorte ate 70%, as melhores variantes foram:

- **K-means default**: melhor em 17 cenarios;
- **K-means Hamming**: melhor em 11 cenarios.

Isso sugere que Hamming ajuda em alguns casos, especialmente BDBJ e LLVM, mas a variante default foi a mais consistente.

A variante exploratoria `kmeans_random`, que embaralha a fila dentro dos clusters, foi mantida nos resultados brutos, mas removida das tabelas e graficos principais porque nao trouxe uma mensagem forte e poderia confundir com o baseline random sampling.

Por que o default pode ser melhor que o random?

- O default preserva a ordem original das variantes dentro de cada cluster.
- Essa ordem pode carregar alguma estrutura da geracao do dataset.
- O round-robin entre clusters ja cria diversidade entre grupos.
- O random pode introduzir ruido e selecionar cedo variantes menos representativas dentro de um cluster.

Entao a leitura correta e: **o agrupamento por K-means ja ajuda em alguns casos, e adicionar aleatoriedade dentro dos clusters nem sempre melhora**.

## Distancias e Conjunto de Teste

No clustering, o K-means usa distancia Euclidiana. Como as features sao binarias, essa distancia cresce conforme aumenta o numero de features diferentes entre variantes. Por isso, ela se aproxima da ideia da Hamming.

Mas elas nao sao exatamente iguais no uso:

- **Euclidiana** forma os clusters e compara variantes com centroides, que podem ter valores fracionarios.
- **Hamming** compara diretamente variantes binarias e e usada no diversity e na ordenacao intra-cluster do K-means Hamming.

O K-means tambem nao escolhe diretamente as variantes de teste. Ele escolhe o conjunto de treino; o teste e formado pelas variantes restantes. Portanto, o sampling afeta o teste apenas indiretamente, pelo complemento do treino.

## Sobre o Valor de K

A expansao ate `K=50` foi util mesmo no recorte principal.

Resumo dos melhores K dentro do K-means:

- `K > 20` foi melhor em **14 dos 28 cenarios**.
- `K = 50` foi melhor em **2 dos 28 cenarios**.
- `K=20`, `K=10` e `K=8` ainda aparecem varias vezes.
- Valores como `K=24`, `K=25`, `K=28`, `K=29`, `K=32`, `K=36`, `K=40` e `K=44` tambem aparecem.

Interpretacao:

> O problema nao e simplesmente usar K maior sempre. O ponto e que uma grade limitada ate 20 era pequena para alguns datasets e tamanhos de amostra.

## Comparacao com a Rodada K=5..20

Comparando o melhor K-means da rodada antiga com a nova, considerando apenas 10% ate 70%:

- K-means melhorou em **15 dos 28 cenarios**.
- Os maiores ganhos ocorreram em BDBC 40%, 50% e 70%.
- LLVM teve pequenas melhoras em varios tamanhos intermediarios.
- Apache mudou pouco.
- BDBJ teve comportamento misto.

Isso justifica a expansao de K, mas tambem reforca que o impacto depende do dataset.

## Comparacao com Baselines

No recorte principal ate 70%, o melhor K-means venceu o melhor baseline em **14 de 28 cenarios**.

Por dataset:

- Apache: K-means venceu 1 de 7 cenarios.
- BDBC: K-means venceu 7 de 7 cenarios.
- BDBJ: K-means venceu 1 de 7 cenarios.
- LLVM: K-means venceu 5 de 7 cenarios.

Esse e um numero bom para reuniao porque mostra que K-means nao ganhou apenas por causa dos pontos instaveis de 80%, 90% ou 100%.

## Ressalvas Importantes

Alguns cuidados para falar dos resultados:

- O MAPE e calculado apenas nas variantes nao usadas no treino.
- A analise principal para em 70% para manter um conjunto de teste razoavel.
- O melhor K-means e uma analise otimista, porque escolhemos o melhor K depois de testar muitos valores.
- A busca ate K=50 reforca que selecao automatica de K e um problema aberto.
- O modelo usado foi Linear Regression, propositalmente simples.
- O objetivo nao foi otimizar o preditor, mas comparar o impacto do sampling.
- Random e K-means foram repetidos 30 vezes; diversity e deterministico na implementacao atual.

## Frase de Fechamento

Uma boa conclusao para a reuniao:

> Os resultados indicam que K-means pode ser usado como metodo de sampling para predicao de propriedades nao funcionais. No recorte principal ate 70%, ele vence metade dos cenarios e domina o BDBC, mas nao substitui diversity em todos os datasets. A contribuicao principal e mostrar que K-means e uma alternativa viavel, desde que a escolha de K e a estrategia de selecao dentro dos clusters sejam tratadas com cuidado.

# Fluxo da Apresentacao

## 1. Contexto

Comecar explicando o que e uma **Software Product Line (SPL)**.

Uma SPL e uma familia de sistemas relacionados que compartilham funcionalidades comuns, mas tambem possuem variacoes. Cada produto da linha e formado por uma combinacao diferente de features.

Exemplo simples: um sistema pode ter ou nao cache, compressao, logs, criptografia, diferentes bancos de dados ou diferentes estrategias de execucao. Cada combinacao dessas escolhas gera uma variante.

## 2. Problema das SPLs

O grande desafio e que o numero de variantes cresce rapidamente conforme novas features sao adicionadas.

Por isso, medir, testar ou avaliar todas as variantes costuma ser inviavel. Precisamos escolher apenas um subconjunto representativo de variantes.

Esse processo de escolha e chamado de **sampling**.

## 3. Propriedades Nao Funcionais

Depois, explicar o que sao **Non-Functional Properties (NFPs)**.

NFPs sao propriedades que descrevem como o sistema se comporta, e nao apenas o que ele faz. Exemplos:

- desempenho;
- tempo de execucao;
- consumo de memoria;
- uso de CPU;
- tamanho do binario;
- consumo de energia.

Essas propriedades sao importantes porque diferentes variantes de uma SPL podem ter comportamentos muito diferentes. Uma configuracao pode ser rapida, mas consumir muita memoria; outra pode ser mais lenta, mas mais economica.

## 4. Predicao de NFPs

Como medir todas as variantes e caro, uma estrategia comum e medir apenas algumas variantes e treinar modelos para prever o comportamento das demais.

Assim, a qualidade do modelo depende muito das variantes escolhidas para treinamento.

Logo, o problema central do trabalho e: **como escolher boas variantes para medir e treinar modelos de predicao de NFPs?**

## 5. Metodos Tradicionais de Sampling

Apresentar os metodos que ja sao usados na literatura:

- **Random sampling**: escolhe variantes aleatoriamente.
- **Diversity-based sampling**: escolhe uma variante inicial, depois a mais diferente dela, depois a mais diferente das anteriores, e assim por diante.
- **K-means sampling**: agrupa as variantes e seleciona exemplos alternando entre clusters.

Esses metodos buscam representar bem o espaco de configuracoes sem medir tudo.

## 6. Paper Base

Apresentar o paper **"Efficient Product-Line Testing using Cluster-Based Product Prioritization"**.

O paper usa **K-means** para agrupar variantes semelhantes de uma SPL. A ideia dos autores e usar esses grupos para priorizar testes.

Ou seja, o foco do paper e teste de SPLs, nao predicao de propriedades nao funcionais.

## 7. Critica ao Paper

Nossa leitura e que a ideia do paper tem limitacoes importantes:

- a avaliacao usa falhas sinteticas;
- os resultados mostram que aumentar o numero de clusters piora o desempenho medio;
- a abordagem com clusters fica abaixo da priorizacao puramente baseada em similaridade;
- o uso de K-means para priorizacao de testes nao parece ser o ponto mais forte da proposta.

## 8. Nossa Ideia

Apesar disso, a intuicao de usar clusters continua interessante.

Nossa proposta e trazer o K-means para outro problema: **sampling para predicao de propriedades nao funcionais**.

Em vez de usar clusters para priorizar testes, vamos usar clusters para escolher variantes de treinamento.

O objetivo nao e descobrir automaticamente o melhor K para cada caso. O objetivo e testar se K-means pode ser viavel como metodo de sampling quando avaliamos varios valores de K.

## 9. Hipotese

A hipotese e que escolher variantes pulando de cluster em cluster pode gerar uma amostra mais diversa do espaco de configuracoes.

Essa diversidade pode ajudar o modelo a aprender melhor o comportamento da SPL e melhorar a predicao de NFPs.

No K-means, a estrategia sera alternar entre clusters ate atingir o orcamento de amostras. Vamos comparar duas formas de organizar a selecao dentro dos clusters:

- **K-means default**: depois de formar os clusters, usa a ordem natural das variantes dentro de cada cluster.
- **K-means Hamming**: depois de formar os clusters, ordena as variantes dentro de cada cluster pela distancia de Hamming, aproximando a ideia de priorizacao por similaridade usada no paper.

A frase simples para apresentar e: todos os K-means pulam de grupo em grupo; o que muda e como escolhemos a proxima variante dentro de cada grupo.

Tambem vale explicar que o **K-means default** nao e uma priorizacao especial do algoritmo. Ele apenas mantem, dentro de cada cluster, a ordem original das variantes no dataset. Isso pode vencer o random porque evita sorteios ruins e porque o proprio round-robin entre clusters ja traz diversidade.

Nos resultados brutos tambem existe uma variante K-means random, mas ela fica fora da apresentacao principal porque nao trouxe ganhos consistentes e pode confundir com o baseline random sampling.

## 10. Experimento

Vamos comparar o K-means com metodos tradicionais de sampling:

- random sampling;
- diversity-based sampling.

Tambem vamos testar diferentes valores de **K**, variando a quantidade de clusters. A grade sera **K = {5, 6, ..., 50}**.

A motivacao para expandir ate 50 e que, na rodada anterior, `K=20` apareceu muitas vezes como melhor resultado e era justamente o maior valor testado. Isso indica que talvez a faixa inicial estivesse pequena.

Dentro do K-means, a apresentacao principal tera duas variantes: **K-means default** e **K-means Hamming**. Assim conseguimos separar melhor duas perguntas: se alternar entre clusters ajuda, e se ordenar as variantes dentro dos clusters por Hamming melhora a selecao em relacao a uma ordem simples.

Um ponto importante para discutir e que a escolha correta de **K** pode ser um problema. Se o K-means tiver desempenho ruim, isso pode acontecer porque clustering nao ajuda naquele caso, mas tambem pode acontecer porque o valor de K escolhido nao foi adequado para aquele dataset ou tamanho de amostra. Quando mostramos o melhor K-means, essa e uma analise otimista; escolher K automaticamente continua como limitacao e trabalho futuro.

Para deixar a comparacao justa e facilitar graficos, vamos usar tamanhos relativos de amostra. A analise principal vai focar em **10%, 20%, ..., 70%** de cada dataset. Os resultados acima de 70% ficam como complemento, porque deixam poucas variantes para teste e podem tornar o MAPE instavel, principalmente em 100%.

A avaliacao sera feita em **4 datasets reais**, amplamente utilizados na literatura para avaliar performance em predicao de propriedades nao funcionais.

Para avaliar os modelos, vamos usar **MAPE** como metrica principal e modelos de regressao simples. A ideia e manter o modelo igual para todos os metodos, porque o objetivo nao e testar o melhor regressor, mas sim medir o impacto do sampling.

Importante: o sampling escolhe apenas as variantes de treino. As variantes de teste sao sempre as que sobraram. Entao o K-means nao escolhe diretamente o teste; ele afeta o teste apenas porque, ao escolher o treino, define automaticamente o complemento.

## 11. Resultado Esperado

Esperamos verificar se o K-means pode ser competitivo como metodo de sampling.

Mesmo que ele nao supere todos os baselines, o objetivo e entender em quais cenarios a estrategia baseada em clusters ajuda ou atrapalha.

## 12. Fechamento

Resumo da narrativa:

O paper usa K-means para priorizacao de testes em SPLs, mas apresenta limitacoes. Nosso trabalho reaproveita a intuicao de agrupamento para um problema diferente: escolher variantes para treinar modelos de predicao de NFPs. A ideia e avaliar se alternar entre clusters gera amostras mais diversas e melhora a qualidade da predicao.

# Roteiro da Apresentacao

Este documento e um guia para quem vai apresentar e nao conhece profundamente a area. A ideia e explicar **o que falar**, **por que aquilo importa** e **qual figura/tabela usar**. Nao precisa colocar todo este texto nos slides.

## Mensagem Central

Pergunta do trabalho:

```text
K-means pode ser usado como metodo de sampling para treinar modelos de predicao de propriedades nao funcionais em SPLs?
```

Resposta que guia a apresentacao:

- Sim, K-means mostrou potencial como metodo de sampling.
- Ele nao foi melhor em todos os casos, mas venceu metade dos cenarios principais.
- O melhor caso foi o dataset BDBC, onde K-means venceu todos os tamanhos de amostra analisados.
- A escolha de K importa muito.
- Nosso foco nao e achar o K perfeito automaticamente, mas avaliar se K-means e uma estrategia viavel.

## Termos Que Precisam Ficar Claros

**SPL:** Software Product Line. E uma familia de sistemas parecidos, mas com variacoes de features/configuracoes.

**Variante:** uma configuracao especifica de features. Exemplo: cache ligado, logs desligados, compressao ligada.

**NFP:** Non-Functional Property, ou propriedade nao funcional. Mede comportamento do sistema, como tempo, memoria, CPU, energia ou tamanho.

**Sampling:** escolher algumas variantes para medir/treinar, em vez de medir todas.

**MAPE:** erro percentual medio. Quanto menor, melhor.

**K:** numero de clusters do K-means.

## Slide 1: Titulo

**Titulo sugerido:**

```text
K-means as a Sampling Method for Non-Functional Property Prediction in Software Product Lines
```

**Fala curta:**

- "O trabalho investiga se K-means pode ajudar a escolher variantes representativas para treinar modelos de predicao de propriedades nao funcionais."

## Slide 2: Contexto: O que e uma SPL?

**No slide:**

- Familia de sistemas com features comuns e variaveis.
- Cada combinacao valida de features gera uma variante.
- O numero de variantes pode crescer muito rapido.

**Fala sugerida:**

- "Em uma SPL, nao analisamos um sistema unico. Analisamos um espaco de configuracoes. Cada configuracao possivel e uma variante."

**Visual sugerido:**

- Diagrama simples: `features -> variantes`.

## Slide 3: Por que Sampling Importa?

**No slide:**

- Medir todas as variantes pode ser inviavel.
- Precisamos escolher um subconjunto para treinar o modelo.
- A qualidade da amostra afeta a qualidade da predicao.

**Fala sugerida:**

- "Se temos muitas variantes, medir todas custa tempo. Entao o problema vira: quais variantes devemos escolher para representar bem o espaco?"

**Visual sugerido:**

- Funil: muitas variantes entrando, poucas variantes selecionadas.

## Slide 4: O que sao NFPs?

**No slide:**

- Propriedades nao funcionais medem como o sistema se comporta.
- Exemplos: tempo, memoria, CPU, energia, tamanho.

**Fala sugerida:**

- "NFPs nao dizem o que o sistema faz, mas como ele se comporta. Neste trabalho, queremos prever esses valores para variantes nao medidas."

## Slide 5: Fluxo da Predicao

**No slide:**

```text
Sampling -> Medicao -> Treino -> Predicao -> MAPE
```

**Fala sugerida:**

- "Selecionamos algumas variantes, treinamos um modelo de regressao com elas e avaliamos o erro nas variantes que ficaram fora do treino."
- "O conjunto de teste e sempre o complemento da amostra escolhida."

## Slide 6: Estudo Base

**No slide:**

- Paper: **Efficient Product-Line Testing using Cluster-Based Product Prioritization**.
- Usa K-means para agrupar variantes.
- Objetivo original: priorizacao de testes em SPLs.

**Defeitos/limitacoes que motivam nosso trabalho:**

- Usa falhas sinteticas.
- Nao foca em predicao de propriedades nao funcionais.
- Clustering nao foi consistentemente superior.
- A escolha de K continua sendo sensivel.

**Fala sugerida:**

- "O paper inspira a ideia de usar clusters, mas o objetivo dele e diferente. Eles priorizam testes; nos usamos clustering para escolher amostras de treino para predicao de NFPs."

## Slide 7: Nossa Ideia

**No slide:**

- Usar K-means como estrategia de sampling.
- Agrupar variantes semelhantes.
- Alternar entre clusters para diversificar a amostra.

**Fala sugerida:**

- "A intuicao e que, se alternarmos entre grupos diferentes, evitamos escolher variantes muito parecidas e cobrimos melhor o espaco de configuracoes."

**Visual sugerido:**

```text
variantes -> K-means -> clusters -> round-robin -> amostra de treino
```

## Slide 8: Objetivo e Setup Experimental

**Texto para o slide:**

- Nosso objetivo nao e encontrar o K otimo, mas avaliar se o K-means e viavel como estrategia de sampling.
- Por isso, usamos Regressao Linear simples e testamos uma ampla faixa de valores de K.
- Datasets reais: Apache, BDBC, BDBJ e LLVM.
- Metrica: MAPE.
- Percentuais analisados: 10% a 70%.
- Valores de K: 5 a 50.
- Metodos estocasticos: 30 repeticoes.

**Fala sugerida:**

- "O modelo foi mantido simples de proposito. Queremos isolar o efeito do sampling, nao otimizar o melhor preditor possivel."
- "Tambem paramos em 70% porque o erro e calculado nas variantes restantes. Acima disso, o conjunto de teste fica pequeno demais."

## Slide 9: Metodos Comparados

**No slide:**

- Random.
- Diversity.
- K-means default.
- K-means Hamming.

**Visual sugerido:**

- Use a imagem: [methods_summary_large.png](results/table_images/methods_summary_large.png)
- Alternativa menor: [methods_summary.png](results/table_images/methods_summary.png)

**Fala sugerida:**

- "Random sorteia variantes."
- "Diversity tenta escolher variantes diferentes entre si."
- "K-means default agrupa e alterna entre clusters."
- "K-means Hamming tambem alterna entre clusters, mas ordena variantes dentro de cada cluster por diversidade."

## Slide 10: Detalhe do K-means

**No slide:**

- Usamos K-means padrao.
- Distancia do clustering: Euclidiana.
- Features binarias.
- Selecionamos em round-robin entre clusters.

**Fala sugerida:**

- "O K-means forma os grupos usando distancia Euclidiana. Como as features sao binarias, essa distancia aumenta quando as variantes diferem em mais features."
- "No K-means Hamming, a Hamming nao forma os clusters; ela so ordena as variantes dentro de cada cluster."

## Slide 11: Randomness e Repeticoes

**No slide:**

- Diversity e deterministico na implementacao atual.
- Random muda por sorteio.
- K-means pode mudar pela inicializacao dos centroides.
- Por isso, metodos estocasticos usam 30 repeticoes.

**Fala sugerida:**

- "Random e K-means podem gerar resultados diferentes com seeds diferentes. Por isso repetimos 30 vezes e reportamos medias."

## Slide 12: Resultado Geral

**No slide:**

```text
Diversity: 14 vitorias
K-means default: 11 vitorias
K-means Hamming: 3 vitorias
```

**Mensagem principal:**

```text
K-means venceu 14 de 28 cenarios principais.
```

**Visual sugerido:**

- Use a tabela wide: [best_by_dataset_fraction_mape_wide.png](results/table_images/best_by_dataset_fraction_mape_wide.png)
- Alternativa vertical: [best_by_dataset_fraction_mape.png](results/table_images/best_by_dataset_fraction_mape.png)

**Fala sugerida:**

- "Considerando os melhores resultados de K-means, ele empata com Diversity em numero total de vitorias. Isso mostra que ele e competitivo, mas nao universal."

## Slide 13: Melhor Metodo por Dataset

**No slide:**

- Apache: Diversity.
- BDBC: K-means default.
- BDBJ: Diversity.
- LLVM: K-means default.

**Visual sugerido:**

- [best_method_by_dataset.png](results/table_images/best_method_by_dataset.png)

**Fala sugerida:**

- "O comportamento muda bastante por dataset. Esse e um ponto importante: K-means funciona muito bem em alguns espacos de configuracao, mas nao em todos."

## Slide 14: Melhor Caso: BDBC

**No slide:**

- K-means default venceu de 10% ate 70%.
- Foi o resultado mais forte da proposta.
- Indica que os clusters capturaram regioes importantes do dataset.

**Visual sugerido:**

- [bdbc_methods.png](results/plots/bdbc_methods.png)

**Fala sugerida:**

- "BDBC e o melhor argumento a favor do K-means. Nesse dataset, a estrategia de agrupar e alternar entre clusters foi claramente superior aos baselines."

## Slide 15: Casos Onde K-means Nao Dominou

**No slide:**

- Apache: Diversity foi melhor na maioria dos percentuais.
- BDBJ: Diversity tambem dominou.
- LLVM: caso intermediario; K-means venceu em varios percentuais.

**Visual sugerido:**

- [apache_methods.png](results/plots/apache_methods.png)
- [llvm_methods.png](results/plots/llvm_methods.png)
- [bdbj_methods.png](results/plots/bdbj_methods.png) como backup.

**Fala sugerida:**

- "Esses casos evitam uma conclusao exagerada. K-means e promissor, mas depende da estrutura do dataset."

## Slide 16: Influencia do K

**No slide:**

- Testamos K de 5 a 50.
- Muitos bons resultados aparecem acima de K=20.
- Escolher K automaticamente ainda e problema aberto.

**Visual sugerido:**

- Principal: [bdbc_k_delta_heatmap.png](results/plots/bdbc_k_delta_heatmap.png)
- Complementar: [llvm_k_delta_heatmap.png](results/plots/llvm_k_delta_heatmap.png)

**Como explicar o heatmap:**

- Cada linha fixa o percentual de amostra.
- Verde significa proximo do melhor K daquela linha.
- Vermelho significa pior que o melhor K daquela linha.
- Isso evita confundir o efeito de K com o efeito do tamanho da amostra.

**Fala sugerida:**

- "Esse grafico mostra que K importa. Nao basta dizer que K-means funciona; o valor de K pode mudar bastante o desempenho."

## Slide 17: Default vs Hamming

**No slide:**

- O clustering e o mesmo nas duas variantes.
- Default preserva a ordem original dentro do cluster.
- Hamming prioriza diversidade dentro do cluster.
- Default foi mais consistente no geral.

**Visual sugerido:**

- [kmeans_best_k.png](results/table_images/kmeans_best_k.png)

**Fala sugerida:**

- "A diferenca entre default e Hamming nao esta em como os clusters sao formados, mas em como escolhemos a ordem dos elementos dentro de cada cluster."

## Slide 18: Limitacoes Principais

**No slide:**

- O melhor K e escolhido apos os testes, entao a analise e otimista.
- Nao propomos selecao automatica de K.
- Usamos apenas Regressao Linear para isolar o efeito do sampling.
- Avaliamos apenas 4 datasets reais.
- O desempenho do K-means depende da estrutura de cada dataset.

**Fala sugerida:**

- "A principal limitacao e que ainda nao sabemos escolher K automaticamente. O trabalho mostra potencial, mas nao fecha esse problema."

## Slide 19: Conclusao

**No slide:**

- K-means e viavel como sampling para predicao de NFPs.
- Venceu metade dos cenarios principais.
- Foi muito forte no BDBC.
- Nao substitui Diversity em todos os datasets.
- A escolha de K e a estrategia intra-cluster sao pontos centrais.

**Frase final sugerida:**

```text
K-means nao resolve sozinho o problema de sampling, mas mostrou potencial suficiente para justificar estudos mais profundos.
```

## Slide 20: Proximos Passos

**No slide:**

- Selecionar K automaticamente.
- Testar outras estrategias para escolher representantes dos clusters.
- Medir a diversidade real das amostras.
- Avaliar outros modelos de regressao.
- Testar mais datasets reais.

## Versao Curta

Se o tempo for curto, apresente nesta ordem:

1. Contexto: SPL, NFP e sampling.
2. Estudo base e motivacao.
3. Nossa ideia: K-means como sampling.
4. Setup experimental.
5. Metodos comparados.
6. Resultado geral.
7. Melhor caso BDBC.
8. Influencia de K.
9. Limitacoes.
10. Conclusao.

## Arquivos Mais Importantes Para os Slides

- [methods_summary_large.png](results/table_images/methods_summary_large.png): tabela dos metodos.
- [best_by_dataset_fraction_mape_wide.png](results/table_images/best_by_dataset_fraction_mape_wide.png): melhor metodo por dataset e percentual, formato wide.
- [best_method_by_dataset.png](results/table_images/best_method_by_dataset.png): melhor metodo por dataset.
- [bdbc_methods.png](results/plots/bdbc_methods.png): melhor caso para K-means.
- [llvm_methods.png](results/plots/llvm_methods.png): caso intermediario.
- [apache_methods.png](results/plots/apache_methods.png): caso em que Diversity e mais forte.
- [bdbc_k_delta_heatmap.png](results/plots/bdbc_k_delta_heatmap.png): sensibilidade ao K no BDBC.
- [llvm_k_delta_heatmap.png](results/plots/llvm_k_delta_heatmap.png): sensibilidade ao K no LLVM.

## Observacoes Para Perguntas

**Por que Regressao Linear?**

Porque o foco e comparar sampling. Se usassemos modelos complexos, ficaria mais dificil saber se a melhora veio do sampling ou do modelo.

**Por que ate 70%?**

Porque o teste usa as variantes nao selecionadas. Acima de 70%, sobram poucas variantes para avaliar.

**O que e Std nas tabelas antigas?**

Std e o desvio padrao do MAPE entre repeticoes. Ele mostra quanto o resultado variou entre seeds diferentes.

**O K-means escolhe o teste?**

Nao diretamente. Ele escolhe o treino; o teste e formado pelas variantes restantes.

**Por que o K-means usa Euclidiana se as features sao binarias?**

Porque usamos K-means padrao, como no estudo base. Em features binarias, a Euclidiana ainda cresce quando mais features diferem, mas ela nao e igual a Hamming no uso pratico porque o K-means compara pontos com centroides.

**Qual conclusao nao devemos exagerar?**

Nao devemos dizer que K-means e sempre melhor. A conclusao correta e que ele e uma alternativa viavel e competitiva em alguns datasets, especialmente BDBC.

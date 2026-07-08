# Por que o K-means default foi melhor que o random?

Este documento explica a diferenca entre `kmeans_default` e `kmeans_random` e por que, nos nossos resultados, o default aparece melhor na maior parte dos casos.

## Resumo curto

O `kmeans_default` foi melhor que o `kmeans_random` porque ele preserva uma ordem deterministica dentro de cada cluster, enquanto o random adiciona aleatoriedade dentro dos clusters.

Como o nosso metodo ja alterna entre clusters em round-robin, a diversidade entre grupos ja esta garantida. Embaralhar dentro de cada cluster nem sempre adiciona informacao util; muitas vezes adiciona apenas ruido.

## O que e igual nos dois metodos

Tanto `kmeans_default` quanto `kmeans_random` usam exatamente o mesmo agrupamento:

1. Pegam todas as variantes do dataset.
2. Usam apenas as features binarias.
3. Executam K-means com distancia Euclidiana.
4. Atribuem cada variante a um cluster.
5. Selecionam variantes alternando entre clusters.

Ou seja, a diferenca nao esta no K-means em si. A diferenca esta apenas na **ordem das variantes dentro de cada cluster**.

## O que muda entre default e random

### K-means default

No default, depois que o cluster e formado, as variantes ficam na ordem em que aparecem no dataset.

No codigo:

```python
members = np.flatnonzero(labels == cluster_id).tolist()
default_clusters.append(members.copy())
```

Isso significa:

- nao embaralha;
- nao usa Hamming;
- nao reordena por distancia ao centroide;
- apenas mantem a ordem natural dos indices das variantes.

Depois disso, o algoritmo faz round-robin entre clusters.

### K-means random

No random, depois que o cluster e formado, as variantes daquele cluster sao embaralhadas:

```python
random_members = members.copy()
rng.shuffle(random_members)
random_clusters.append(random_members)
```

Depois, o algoritmo tambem faz round-robin entre clusters.

## Por que o default pode ganhar?

### 1. O round-robin ja traz diversidade entre clusters

A principal ideia do nosso K-means sampling e pular de cluster em cluster.

Isso ja evita selecionar muitas variantes de uma mesma regiao do espaco de configuracoes.

Entao, mesmo sem embaralhar dentro do cluster, o metodo ja tem uma fonte forte de diversidade: a alternancia entre grupos.

### 2. O random pode adicionar ruido

Dentro de um cluster, as variantes sao parecidas entre si. Embaralhar essas variantes pode fazer o algoritmo escolher cedo variantes menos representativas ou redundantes.

Isso pode prejudicar principalmente quando o orcamento e pequeno, porque as primeiras escolhas importam muito.

### 3. A ordem original pode carregar estrutura

Os datasets nao sao necessariamente arquivos em ordem completamente aleatoria.

Dependendo de como as variantes foram geradas ou salvas, a ordem original pode carregar alguma estrutura do espaco de configuracoes.

O default preserva essa estrutura. O random destrói essa ordem e troca por sorteio.

Isso nao significa que a ordem original seja sempre boa, mas pode explicar por que o default foi mais estavel em varios cenarios.

### 4. O default e mais estavel

O random depende do sorteio dentro de cada cluster. Mesmo com 30 repeticoes, ele pode ter mais variabilidade.

O default ainda varia por causa da inicializacao do K-means, mas nao adiciona uma segunda camada de aleatoriedade dentro dos clusters.

Essa menor aleatoriedade pode tornar o resultado medio mais consistente.

## O que os nossos resultados mostram

No recorte principal da analise, de 10% ate 70%:

- `kmeans_default` foi a melhor variante de K-means em **17 cenarios**.
- `kmeans_hamming` foi a melhor em **10 cenarios**.
- `kmeans_random` foi a melhor em **1 cenario**.

Comparando `kmeans_default` contra `kmeans_random` no mesmo dataset, mesmo percentual de amostra e mesmo K:

- default teve MAPE menor em **832 comparacoes**;
- random teve MAPE menor ou igual em **367 comparacoes**;
- default foi melhor em aproximadamente **69%** das comparacoes.

Por dataset, o default foi melhor que o random em:

- Apache: aproximadamente 84% das comparacoes;
- BDBC: aproximadamente 90% das comparacoes;
- BDBJ: aproximadamente 51% das comparacoes;
- LLVM: aproximadamente 52% das comparacoes.

Isso mostra que a vantagem do default nao e uniforme. Ela e muito forte em Apache e BDBC, mas bem menor em BDBJ e LLVM.

## Interpretacao correta

A conclusao correta nao e:

> A ordem original sempre e melhor.

A conclusao correta e:

> No nosso experimento, o agrupamento por K-means combinado com round-robin ja trouxe diversidade suficiente em varios cenarios. Adicionar aleatoriedade dentro dos clusters frequentemente nao ajudou e, em muitos casos, piorou a selecao.

## Como explicar na apresentacao

Uma forma simples de falar:

> O K-means default nao usa uma ordem especial do algoritmo. Ele apenas mantem a ordem original das variantes dentro de cada cluster. Como a selecao ja alterna entre clusters, a diversidade entre grupos ja esta presente. O random adiciona uma camada extra de sorteio dentro dos clusters, e essa aleatoriedade pode escolher variantes menos representativas, principalmente quando o orcamento de amostra e pequeno. Por isso, nos nossos resultados, o default foi mais estavel e apareceu como melhor variante de K-means na maioria dos cenarios.

## Ressalva importante

Essa explicacao e uma interpretacao dos resultados, nao uma prova absoluta.

Para confirmar completamente a causa, seria necessario fazer experimentos adicionais, por exemplo:

- testar ordem por distancia ao centroide;
- testar ordem por proximidade ao centroide;
- testar ordem por medoid;
- embaralhar previamente o dataset e ver se o default continua forte;
- medir a diversidade real das amostras geradas por cada variante.

Mesmo assim, para a reuniao, a interpretacao atual e suficiente e defensavel.

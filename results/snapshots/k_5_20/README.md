# Snapshot K=5..20

Este diretorio guarda os resultados antes de expandir a grade do K-means para K=50.

Configuracao desta rodada:

- K-means com `K = 5, 6, ..., 20`;
- amostras de 10% ate 100%;
- 30 repeticoes para metodos aleatorios;
- variantes: `kmeans_default`, `kmeans_random`, `kmeans_hamming`.

Arquivos preservados:

- `raw_results.csv`;
- `summary_results.csv`;
- `tables/`;
- `plots/`.

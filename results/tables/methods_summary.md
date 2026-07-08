| Method          | Summary                                                                                                                                              |
| --------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| Random          | Randomly selects variants without replacement.                                                                                                       |
| Diversity       | Iteratively selects variants that are farthest from the already selected set using normalized Hamming distance.                                      |
| K-means default | Uses standard K-means with Euclidean distance; samples by alternating between clusters and preserves the original order inside each cluster.         |
| K-means Hamming | Uses standard K-means with Euclidean distance; samples by alternating between clusters and orders variants inside each cluster by Hamming diversity. |

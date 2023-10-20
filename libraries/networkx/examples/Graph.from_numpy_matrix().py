import networkx as nx
import numpy as np

A = np.matrix([[0, 1, 1, 0, 0], [1, 0, 1, 1, 0], [1, 1, 0, 1, 1], [0, 1, 1, 0, 1], [0, 0, 1, 1, 0]])
G = nx.from_numpy_matrix(A)
print(G.edges)
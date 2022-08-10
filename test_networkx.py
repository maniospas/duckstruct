from duckstruct import TypeListener
import networkx as nx

graph = nx.DiGraph()
graph = TypeListener(graph)
graph.add_edge("a", "b")
graph.add_edge("b", "c")
nx.pagerank(graph)

print(graph.type())
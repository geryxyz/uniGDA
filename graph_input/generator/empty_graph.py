from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from gremlin_python.process import anonymous_traversal
from gremlin_python.process.graph_traversal import GraphTraversal
from gremlin_python.structure.graph import Vertex, Edge
import random

WEIGHT = 'weight'

class EmptyGraph(object):
    def __init__(self, server_url, traversal_source, vertex_count):
        self.output_graph = anonymous_traversal.traversal().withRemote(
            DriverRemoteConnection(server_url, traversal_source))
        self.output_graph.V().drop().toList()
        self.output_graph.E().drop().toList()
        for index in range(vertex_count):
            self.output_graph.addV().next()

    def add_random_edge(self, edge_count=1, weight=1):
        for index in range(edge_count):
            if weight is None:
                _weight = random.random()
            self.output_graph.addE('random').from_(self.output_graph.V().sample(1)).to(self.output_graph.V().sample(1)).property(WEIGHT, _weight).next()


if __name__ == '__main__':
    genrator = EmptyGraph('ws://localhost:8182/gremlin', 'g', 5)

import typing
from floatrange import floatrange
from PIL import Image, ImageDraw, ImageFont
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from gremlin_python.process import anonymous_traversal
from gremlin_python.process.graph_traversal import GraphTraversal
from gremlin_python.structure.graph import Vertex, Edge
from gremlin_python.process.graph_traversal import __
import math
from statistics import stdev
import logging


class ModifiedGauss(object):
    def __init__(self, height: float, offset: float, width: float):
        self.height = height
        self.offset = offset
        self.width = width

    def __call__(self, x: float):
        if self.width != 0:
            return self.height * math.e ** -((x - self.offset) ** 2 / (2 * self.width ** 2))
        else:
            if x == 0:
                return self.height
            else:
                return 0

    def __str__(self):
        return f'g(x, {self.height}, {self.offset}, {self.width})'


def sum_of_squares(values: typing.List[float]) -> float:
    return sum([value ** 2 for value in values])


class ContinuesNDD(list):
    def __init__(self, inspected: Vertex, graph: GraphTraversal,
                 neighbor_selector: typing.Callable[[Vertex], typing.List[Vertex]] = None,
                 weight_selector: typing.Callable[[Edge], typing.Union[int, float]] = None,
                 edge_selector: typing.Callable[[Vertex], typing.List[Edge]] = None):
        super().__init__({})
        self.inspected = inspected
        self.graph = graph
        if neighbor_selector is None:
            def neighbor_selector(node): return graph.V(node).both().toList()
        if edge_selector is None:
            def edge_selector(node): return graph.V(node).bothE().toList()
        if weight_selector is None:
            def weight_selector(edge): return float(graph.E(edge).properties('weight').value().limit(1).next())
        neighbors = neighbor_selector(inspected)
        for neighbor in neighbors:
            count_of_neighbor_adjacents = len(neighbor_selector(neighbor))
            stdev_of_neighbor_edges = stdev([weight_selector(edge) for edge in edge_selector(neighbor)])
            neighbor_edge = graph.V(inspected).bothE().filter(__.otherV().is_(neighbor)).limit(1).next()
            neighbor_weight = weight_selector(neighbor_edge)
            gauss = ModifiedGauss(height=neighbor_weight, offset=count_of_neighbor_adjacents, width=stdev_of_neighbor_edges)
            self.append(gauss)

    def value(self, x, aggregation: typing.Callable[[typing.List[float]], float] = sum_of_squares):
        return aggregation([gauss(x) for gauss in self])


if __name__ == '__main__':
    graph = anonymous_traversal.traversal().withRemote(DriverRemoteConnection('ws://localhost:8182/gremlin', 'g'))
    cndd = ContinuesNDD(graph.V().limit(1).next(), graph)
    with open('test.csv', 'w') as test:
        for x in floatrange(0, max([gauss.offset for gauss in cndd]), 1):
            print(x)
            test.write(f'{x};{cndd.value(x)}\n')
    pass

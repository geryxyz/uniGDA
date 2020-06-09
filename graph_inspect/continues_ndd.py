import typing
from floatrange import floatrange
from PIL import Image, ImageDraw, ImageFont
from gremlin_python.process.graph_traversal import GraphTraversal
from gremlin_python.structure.graph import Vertex, Edge
import math


class ModifiedGauss(object):
    def __init__(self, height, offset, width):
        self.height = height
        self.offset = offset
        self.width = width

    def __call__(self, x):
        if self.width != 0:
            return self.height * math.e ** -((x - self.offset) ** 2 / (2 * self.width ** 2))
        else:
            if x == 0:
                return self.height
            else:
                return 0


class ContinuesNDD(list):
    def __init__(self, inspected: Vertex, graph: GraphTraversal,
                 neighbor_selector: typing.Callable[[Vertex], typing.List[Edge]] = None,
                 weight_selector: typing.Callable[[Edge], typing.Union[int, float]] = None):
        super().__init__({})
        if neighbor_selector is None:
            def neighbor_selector(node): return graph.V(node).both().toList()
        if weight_selector is None:
            def weight_selector(edge): return graph.E(edge).properties('weight').value().limit(1).next()


if __name__ == '__main__':
    pass
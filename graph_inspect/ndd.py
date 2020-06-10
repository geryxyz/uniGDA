from PIL import Image, ImageDraw, ImageFont
from gremlin_python.process.graph_traversal import GraphTraversal
from gremlin_python.structure.graph import Vertex, Edge
import typing
from graph_inspect import DiscreteNDD, ContinuesNDD


class NDD(object):
    def __init__(self,
                 inspected: Vertex, graph: GraphTraversal,
                 neighbor_selector: typing.Callable[[Vertex], typing.List[Vertex]] = None,
                 weight_selector: typing.Callable[[Edge], typing.Union[int, float]] = None,
                 edge_selector: typing.Callable[[Vertex], typing.List[Edge]] = None):
        self.inspected = inspected
        self.graph = graph
        self.discrete = DiscreteNDD(inspected, graph, neighbor_selector)
        self.continues = ContinuesNDD(inspected, graph, neighbor_selector, weight_selector, edge_selector)

    def offset_maximum(self):
        return max(self.discrete.offset_maximum(), self.continues.offset_maximum())

    def strength_maximum(self, step_size: float = .5):
        return max(self.discrete.strength_maximum(), self.continues.strength_maximum(step_size))

    def visualize(self, path, title=None, width=900, height=100, offset_maximum=None, strength_maximum=None, top_margin_ratio=.3, bottom_margin_ratio=.2, tick_count=5):
        self.discrete.visualize(f'{path}.discrete', title, width, height, offset_maximum, strength_maximum, top_margin_ratio, bottom_margin_ratio, tick_count)
        self.continues.visualize(f'{path}.continues', title, width, height, offset_maximum, strength_maximum, top_margin_ratio, bottom_margin_ratio, tick_count)

    def __str__(self):
        return f'dNDD={self.discrete}, cNDD={self.continues}'

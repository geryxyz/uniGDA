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

    def strength_maximum(self):
        return max(self.discrete.strength_maximum(), self.continues.strength_maximum())

    def visualize(self,
                  path, title=None, discrete_title=None, continues_title=None,
                  width=900, height=200,
                  offset_maximum=None, strength_maximum=None,
                  top_margin_ratio=.3, bottom_margin_ratio=.2,
                  tick_count=5,
                  save: bool = True):
        if continues_title is None:
            continues_title = title
        if discrete_title is None:
            discrete_title = title
        image = Image.new('RGBA', (width, height), color=(255, 255, 255, 255))
        discrete_image = self.discrete.visualize(f'{path}.discrete', discrete_title,
                                                 width, int(height / 2),
                                                 offset_maximum, strength_maximum,
                                                 top_margin_ratio, bottom_margin_ratio,
                                                 tick_count, save=False)
        continues_image = self.continues.visualize(f'{path}.continues', continues_title,
                                                   width, int(height / 2),
                                                   offset_maximum, strength_maximum,
                                                   top_margin_ratio, bottom_margin_ratio,
                                                   tick_count, save=False)
        image.paste(discrete_image, (0, 0))
        image.paste(continues_image, (0, int(height / 2)))
        if save:
            image.save(f'{path}.png')
        else:
            return image

    def __str__(self):
        return f'dNDD={self.discrete}, cNDD={self.continues}'

    def is_alike(self, other):
        return isinstance(other, NDD) and self.continues.is_alike(other.continues) and self.discrete.is_alike(other.discrete)

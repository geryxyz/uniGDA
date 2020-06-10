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

import graph_input


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
        print(f'{inspected}... ', end='')
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
            print(".", end='')
            count_of_neighbor_adjacents = len(neighbor_selector(neighbor))
            weights = [weight_selector(edge) for edge in edge_selector(neighbor)]
            if len(weights) > 1:
                stdev_of_neighbor_edges = stdev(weights)
            else:
                stdev_of_neighbor_edges = 0
            neighbor_edge = graph.V(inspected).bothE().filter(__.otherV().is_(neighbor)).limit(1).next()
            neighbor_weight = weight_selector(neighbor_edge)
            gauss = ModifiedGauss(height=neighbor_weight, offset=count_of_neighbor_adjacents, width=stdev_of_neighbor_edges)
            self.append(gauss)
        print()

    def value(self, x, aggregation: typing.Callable[[typing.List[float]], float] = sum_of_squares):
        return aggregation([gauss(x) for gauss in self])

    def offset_maximum(self):
        return max([gauss.offset + gauss.width for gauss in self])

    def strength_maximum(self, step_size: float = .5):
        max_offset = self.offset_maximum()
        return max([self.value(x) for x in floatrange(0, max_offset, step_size)])

    def visualize(self, path, title=None, width=900, height=100, offset_maximum=None, strength_maximum=None, top_margin_ratio=.3, bottom_margin_ratio=.2, tick_count=5):
        if offset_maximum is None:
            offset_maximum = self.offset_maximum()
        if strength_maximum is None:
            strength_maximum = self.strength_maximum(offset_maximum / width)
        image = Image.new('RGBA', (width, height), color=(255, 255, 255, 255))
        draw = ImageDraw.Draw(image)
        title_font = ImageFont.truetype('arial', size=int(height * top_margin_ratio * .6))
        if top_margin_ratio > 0 and title is not None:
            text_width, text_height = title_font.getsize(title)
            draw.text((int(width / 2 - text_width / 2), 0), title, fill=(0, 0, 0, 255), font=title_font)
        for image_x in range(width):
            x = (image_x / width) * offset_maximum
            strength = int((1 - self.value(x) / strength_maximum) * 255)
            draw.line(
                [(image_x, height * top_margin_ratio), (image_x, height * (1 - bottom_margin_ratio))],
                fill=(strength, strength, strength, 255))
        rule_font = ImageFont.truetype('arial', size=int(height * bottom_margin_ratio * .6))
        for value in floatrange(0, offset_maximum, offset_maximum / tick_count):
            mark = f'{value:.2f}'
            text_width, text_height = rule_font.getsize(mark)
            offset = int((value / offset_maximum) * width)
            if offset_maximum - value < text_width:
                draw.line([(offset, height * (1 - bottom_margin_ratio) + 3), (offset, height)],
                          fill=(0, 0, 0, 255))
                draw.text((offset - text_width - 3, height - text_height), mark, fill=(0, 0, 0, 255), font=rule_font)
            elif value < text_width:
                draw.line([(offset, height * (1 - bottom_margin_ratio) + 3), (offset, height)],
                          fill=(0, 0, 0, 255))
                draw.text((offset + 3, height - text_height), mark, fill=(0, 0, 0, 255), font=rule_font)
            else:
                draw.line([(offset, height * (1 - bottom_margin_ratio) + 3), (offset, height - text_height - 2)],
                          fill=(0, 0, 0, 255))
                draw.text((offset - (text_width / 2), height - text_height), mark, fill=(0, 0, 0, 255), font=rule_font)
        draw.rectangle([(0, height * top_margin_ratio), (width - 1, height * (1 - bottom_margin_ratio))], outline=(0, 0, 0, 255))
        image.save(path)


if __name__ == '__main__':
    graph = anonymous_traversal.traversal().withRemote(DriverRemoteConnection('ws://localhost:8182/gremlin', 'g'))
    for node in graph.V().limit(3).toList():
        cndd = ContinuesNDD(node, graph)
        name = graph.V(node).properties(graph_input.ORIGINAL_ID).value().limit(1).next()
        cndd.visualize(f'{node.id}.png', title=name)
    pass

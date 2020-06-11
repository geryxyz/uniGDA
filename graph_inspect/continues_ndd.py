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
from graph_inspect import draw_ruler, text_with_boarder, EmptyGraph


class ModifiedGauss(object):
    def __init__(self, height: float, offset: float, width: float):
        self.height = height
        self.offset = offset
        self.width = width

    def __call__(self, x: float):
        if self.width != 0:
            return self.height * math.e ** -((x - self.offset) ** 2 / (2 * self.width ** 2))
        else:
            if x == self.offset:
                return self.height
            else:
                return 0.0

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
            weights = [weight_selector(edge) for edge in edge_selector(neighbor)]
            if len(weights) > 1:
                stdev_of_neighbor_edges = stdev(weights)
            else:
                stdev_of_neighbor_edges = 0
            neighbor_edge = graph.V(inspected).bothE().filter(__.otherV().is_(neighbor)).limit(1).next()
            neighbor_weight = weight_selector(neighbor_edge)
            gauss = ModifiedGauss(height=neighbor_weight, offset=count_of_neighbor_adjacents, width=stdev_of_neighbor_edges)
            self.append(gauss)

    def value(self, x, aggregation: typing.Callable[[typing.List[float]], float] = sum_of_squares):
        return aggregation([gauss(x) for gauss in self])

    def offset_maximum(self):
        if self:
            return max([gauss.offset + gauss.width for gauss in self])
        else:
            return 0

    def strength_maximum(self):
        if self:
            return max([self.value(gauss.offset) for gauss in self])
        else:
            return 0

    def visualize(self, path, title=None, width=900, height=100, offset_maximum=None, strength_maximum=None, top_margin_ratio=.3, bottom_margin_ratio=.2, tick_count=5):
        if offset_maximum is None:
            offset_maximum = self.offset_maximum()
        if strength_maximum is None:
            step_size = offset_maximum / width
            strength_maximum = self.strength_maximum()
        else:
            step_size = 0
        image = Image.new('RGBA', (width, height), color=(255, 255, 255, 255))
        draw = ImageDraw.Draw(image)
        title_font = ImageFont.truetype('arial', size=int(height * top_margin_ratio * .6))
        if top_margin_ratio > 0 and title is not None:
            text_width, text_height = title_font.getsize(title)
            draw.text((int(width / 2 - text_width / 2), 0), title, fill=(0, 0, 0, 255), font=title_font)
        if self:
            hint_font = ImageFont.truetype('arial', size=int(height * bottom_margin_ratio * .6))
            for image_x in range(width):
                x = (image_x / width) * offset_maximum
                strength = int((1 - self.value(x) / strength_maximum) * 255)
                draw.line(
                    [(image_x, height * top_margin_ratio), (image_x, height * (1 - bottom_margin_ratio))],
                    fill=(strength, strength, strength, 255))
            last_nearest_gauss = None
            for image_x in range(width):
                x = (image_x / width) * offset_maximum
                nearest_gauss: ModifiedGauss = min(self, key=lambda gauss: abs(gauss.offset - x))
                if last_nearest_gauss != nearest_gauss and abs(nearest_gauss.offset - x) <= step_size:
                    hint = f'{self.value(nearest_gauss.offset):.4f}'
                    text_width, text_height = hint_font.getsize(hint)
                    if text_width < image_x < width - text_width:
                        for y in range(int(height * top_margin_ratio), int(height * (1 - bottom_margin_ratio))):
                            is_dashing = y % 10 > 5
                            if is_dashing:
                                image.putpixel((image_x, y), (is_dashing, is_dashing, is_dashing, 255))
                        text_with_boarder(draw, (image_x, height * top_margin_ratio + text_height), hint, hint_font)
                        last_nearest_gauss = nearest_gauss
            draw_ruler(draw, width, height, bottom_margin_ratio, tick_count, offset_maximum)
        else:
            text_with_boarder(draw, (width / 2, height / 2), 'empty cNDD', font=title_font)
        draw.rectangle([(0, height * top_margin_ratio), (width - 1, height * (1 - bottom_margin_ratio))], outline=(0, 0, 0, 255))
        image.save(f'{path}.png')

    def __str__(self):
        gauss: ModifiedGauss
        return ', '.join([f'|{gauss.height:.4f}-{gauss.width:.4f}@{gauss.offset:.4f}' for gauss in sorted(self, key=lambda g: g.offset)])


if __name__ == '__main__':
    genrator = EmptyGraph('ws://localhost:8182/gremlin', 'g', 5)
    genrator.add_random_edge(50)
    for index, node in enumerate(genrator.output_graph.V().toList()):
        cndd = ContinuesNDD(node, genrator.output_graph)
        cndd.visualize(str(index))
    pass

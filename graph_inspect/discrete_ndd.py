import typing

from PIL import Image, ImageDraw, ImageFont
from floatrange import floatrange
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from gremlin_python.process import anonymous_traversal
from gremlin_python.process.graph_traversal import GraphTraversal
from gremlin_python.structure.graph import Vertex, Edge

import graph_input
from graph_input.generator import EmptyGraph
from graph_inspect import draw_ruler, text_with_boarder


class DiscreteNDD(dict):
    def __init__(self, inspected: Vertex, graph: GraphTraversal,
                 neighbor_selector: typing.Callable[[Vertex], typing.List[Vertex]] = None):
        super().__init__({})
        self.inspected = inspected
        self.graph = graph
        if neighbor_selector is None:
            def neighbor_selector(node): return graph.V(node).both().toList()
        neighbors = neighbor_selector(inspected)
        for neigbor in neighbors:
            count_of_neighbor_adjacents = len(neighbor_selector(neigbor))
            self[count_of_neighbor_adjacents] = self.get(count_of_neighbor_adjacents, 0) + 1

    def offset_maximum(self):
        if self:
            as_sorted = sorted(self.items(), key=lambda e: e[0])
            return as_sorted[-1][0]
        else:
            return 0

    def strength_maximum(self):
        if self:
            as_sorted = sorted(self.items(), key=lambda e: e[0])
            return max(as_sorted, key=lambda e: [1])[1]
        else:
            return 0

    def visualize(self, path, title=None, width=900, height=100, offset_maximum=None, strength_maximum=None, top_margin_ratio=.3, bottom_margin_ratio=.2, tick_count=5):
        as_sorted = sorted(self.items(), key=lambda e: e[0])
        if offset_maximum is None:
            offset_maximum = self.offset_maximum()
        if strength_maximum is None:
            strength_maximum = self.strength_maximum()
        image = Image.new('RGBA', (width, height), color=(255, 255, 255, 255))
        draw = ImageDraw.Draw(image)
        hint_font = ImageFont.truetype('arial', size=int(height * bottom_margin_ratio * .6))
        for entry in as_sorted:
            offset = (entry[0] / offset_maximum) * width
            strength = int((1 - entry[1] / strength_maximum) * 255)
            draw.line([(offset, height * top_margin_ratio), (offset, height * (1 - bottom_margin_ratio))], fill=(strength, strength, strength, 255))
            hint = str(entry[1])
            text_width, text_height = hint_font.getsize(hint)
            if text_width < offset < width - text_width:
                text_with_boarder(draw, (offset, height * top_margin_ratio), hint, hint_font)
        title_font = ImageFont.truetype('arial', size=int(height * top_margin_ratio * .6))
        if top_margin_ratio > 0 and title is not None:
            text_width, text_height = title_font.getsize(title)
            draw.text((int(width / 2 - text_width / 2), 0), title, fill=(0, 0, 0, 255), font=title_font)
        if offset_maximum > 0:
            draw_ruler(draw, width, height, bottom_margin_ratio, tick_count, offset_maximum)
        else:
            text_with_boarder(draw, (width / 2, height / 2), 'empty dNDD', font=title_font)
        image.save(f'{path}.png')

    def __str__(self):
        as_sorted = sorted(self.items(), key=lambda e: e[0])
        as_sorted.insert(0, (None, None))
        glyphs = []
        for prev, current in zip(as_sorted, as_sorted[1:]):
            if prev[0] is None:
                zero_count = current[0]
            else:
                zero_count = current[0] - prev[0] - 1
            if zero_count == 0:
                pass
            elif zero_count == 1:
                glyphs.append('0')
            else:
                glyphs.append(f'0{{{zero_count}}}')
            glyphs.append(str(current[1]))
        return f"[{'; '.join(glyphs)}]"


if __name__ == '__main__':
    genrator = EmptyGraph('ws://localhost:8182/gremlin', 'g', 5)
    genrator.add_random_edge(50)
    for index, node in enumerate(genrator.output_graph.V().toList()):
        cndd = DiscreteNDD(node, genrator.output_graph)
        cndd.visualize(str(index))
    pass

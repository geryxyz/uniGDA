import typing

from PIL import ImageDraw
from PIL import Image
from PIL import ImageFont
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from gremlin_python.process import anonymous_traversal
from gremlin_python.process.graph_traversal import GraphTraversal
from gremlin_python.structure.graph import Vertex

import graph_input
from graph_inspect import DiscreteNDD, ContinuesNDD, NDD
from graph_input.generator import EmptyGraph
import os.path


class NDDCollection(list):
    def visualize_single_image(self, title_extractor: typing.Callable[[Vertex, GraphTraversal], str] = None,
                               width=900, height=300, top_margin_ratio=.3, bottom_margin_ratio=.2, tick_count=5):
        if self:
            offset_maximum = max([ndd.offset_maximum() for ndd in self])
            strength_maximum = max([ndd.strength_maximum() for ndd in self])
            if title_extractor is None:
                def title_extractor(node, graph): return graph.V(node).properties(
                    graph_input.ORIGINAL_ID).value().limit(1).next()
            ndd: typing.Union[DiscreteNDD, ContinuesNDD, NDD]
            for index, ndd in enumerate(self):
                extracted_title = title_extractor(ndd.inspected, ndd.graph)
                image = ndd.visualize(title=extracted_title, width=width, height=height,
                                      offset_maximum=offset_maximum, strength_maximum=strength_maximum,
                                      top_margin_ratio=top_margin_ratio, bottom_margin_ratio=bottom_margin_ratio,
                                      tick_count=tick_count)
                yield ndd, image

    def visualize_collage(self, title_extractor: typing.Callable[[Vertex, GraphTraversal], str] = None,
                          max_count: int = None, max_kind: int = None,
                          ndd_width: int = 200, ndd_height: int = 100, inner_margin: int = 50):
        if title_extractor is None:
            def title_extractor(node, graph): return None
        groups: typing.List[typing.List[typing.Tuple[object, Image]]] = []
        for ndd, image in self.visualize_single_image(title_extractor=title_extractor, width=ndd_width,
                                                      height=ndd_height):
            for group in groups:
                if any([ndd.is_alike(candidate) for candidate, _ in group]):
                    group.append((ndd, image))
                    break
            else:
                groups.append([(ndd, image)])
        groups_by_count = {}
        for group in groups:
            count = len(group)
            groups_by_count[count] = groups_by_count.get(count, []) + [group]

        if max_count is None:
            max_count = max([len(g) for g in groups])
        if max_kind is None:
            max_kind = max([len(groups_of_count) for groups_of_count in groups_by_count.values()])
        image_width, image_height = groups[0][0][1].size
        y_label_size = int(image_height / 2)
        y_font = ImageFont.truetype('arial', size=int(y_label_size * .6))
        collage = Image.new('RGBA', (
            y_label_size + (image_width + inner_margin) * max_kind, (image_height + inner_margin) * max_count),
                            color=(255, 255, 255, 255))
        collage_draw: ImageDraw.ImageDraw = ImageDraw.Draw(collage)
        x_offset = {}
        for count in range(max_count + 1):
            text_width, text_height = y_font.getsize(str(count))
            collage_draw.text((int(y_label_size / 2 - text_width / 2),
                               int((image_height + inner_margin) * (
                                       max_count - count) + image_height / 2 - text_height / 2)),
                              str(count), fill=(100, 100, 100, 255), font=y_font)
        for group in groups:
            count = len(group)
            x_offset[count] = x_offset.get(count, -1) + 1
            collage.paste(group[0][1],
                          (y_label_size + (image_width + inner_margin) * x_offset[count],
                           (image_height + inner_margin) * (max_count - count) + inner_margin))
        return collage

    def add(self, new_ndd: typing.Union[DiscreteNDD, ContinuesNDD, NDD]):
        self.append(new_ndd)


if __name__ == "__main__":
    genrator = EmptyGraph('ws://localhost:8182/gremlin', 'g', 5)
    genrator.add_random_edge(50)

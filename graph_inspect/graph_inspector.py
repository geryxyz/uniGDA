import os
import typing

import PIL.Image as Image
import PIL.ImageFont
from PIL import ImageFont, ImageDraw
from gremlin_python.process.graph_traversal import GraphTraversal
from gremlin_python.structure.graph import Vertex, Edge
from matplotlib.axes import Axes
from matplotlib.figure import Figure
import matplotlib.pyplot as pyplot

from graph_input.generator import EmptyGraph
from graph_inspect import NDDCollection, NDD
import io


class DegreeDistribution(dict):
    def visualize(self, path: str, width=800, height=600, title=None, xmax=None, ymax=None, save: bool = True):
        as_list = sorted(self.items())  # sorted by key, return a list of tuples
        x, y = zip(*as_list)
        fig: Figure
        ax: Axes
        fig = pyplot.figure(0, figsize=(width / 100, height / 100), dpi=100)
        if xmax:
            pyplot.xlim(0, xmax)
        if ymax:
            pyplot.ylim(0, ymax)
        if title:
            pyplot.title(title)
        pyplot.xlabel('degree')
        pyplot.ylabel('count of nodes')
        pyplot.bar(x, y, color='lightgrey', edgecolor='black')
        if save:
            fig.savefig(f'{path}.png')
            fig.clf()
        else:
            buffer = io.BytesIO()
            fig.savefig(buffer, format='png')
            fig.clf()
            buffer.seek(0)
            image = Image.open(buffer)
            image.load()
            buffer.close()
            return image


class GraphInspector(object):
    def __init__(self, graph: GraphTraversal):
        self.graph = graph

    def all_ndds_of(self):
        nodes = self.graph.V().toList()
        ndds = NDDCollection()
        for ndd in [NDD(node, self.graph) for node in nodes]:
            ndds.add(ndd)
        return ndds

    def degree_distribution(self, edge_selector: typing.Callable[[Vertex], typing.List[Edge]] = None):
        if edge_selector is None:
            def edge_selector(node): return self.graph.V(node).bothE().toList()
        degrees = DegreeDistribution()
        for vertex in self.graph.V().toList():
            degree = len(edge_selector(vertex))
            degrees[degree] = degrees.get(degree, 0) + 1
        return degrees

    def visualize(self, title_extractor: typing.Callable[[Vertex, GraphTraversal], str] = None,
                  max_count: int = None, max_kind: int = None,
                  ndd_width: int = 200, ndd_height: int = 100, inner_margin: int = 50):
        ndds = self.all_ndds_of()
        if title_extractor is None:
            def title_extractor(node, graph): return None
        groups: typing.List[typing.List[typing.Tuple[object, Image]]] = []
        for ndd, image in ndds.visualize('.', title_extractor=title_extractor, width=ndd_width, height=ndd_height, save=False):
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
        collage = Image.new('RGBA', (y_label_size + (image_width + inner_margin) * max_kind, (image_height + inner_margin) * max_count), color=(255, 255, 255, 255))
        collage_draw: ImageDraw.ImageDraw = ImageDraw.Draw(collage)
        x_offset = {}
        for count in range(max_count + 1):
            text_width, text_height = y_font.getsize(str(count))
            collage_draw.text((int(y_label_size / 2 - text_width / 2),
                               int((image_height + inner_margin) * (max_count - count) + image_height / 2 - text_height / 2)),
                              str(count), fill=(100, 100, 100, 255), font=y_font)
        for group in groups:
            count = len(group)
            x_offset[count] = x_offset.get(count, -1) + 1
            collage.paste(group[0][1],
                          (y_label_size + (image_width + inner_margin) * x_offset[count],
                           (image_height + inner_margin) * (max_count - count) + inner_margin))
        return collage


if __name__ == "__main__":
    max_node_count = 5
    genrator = EmptyGraph('ws://localhost:8182/gremlin', 'g', max_node_count)
    inspector = GraphInspector(genrator.output_graph)
    max_edge_count = 25
    degree_distributions = []
    ndd_frames = []
    for count in range(max_edge_count):
        print(count)
        genrator.add_random_edge(weight=None)
        ndd_frames.append(inspector.visualize(max_count=max_node_count, max_kind=max_node_count))
        degree_distributions.append(inspector.degree_distribution())
    degree_frames = []
    xmax = max([max(dist.keys()) for dist in degree_distributions])
    ymax = max([max(dist.values()) for dist in degree_distributions])
    for index, distribution in enumerate(degree_distributions):
        degree_frames.append(
            distribution.visualize(f'frames/{index}_degree_dist',
                                   title=f'Degree distribution of {index} edges over {max_node_count} nodes',
                                   xmax=xmax, ymax=ymax, width=ndd_frames[0].size[0], height=int(ndd_frames[0].size[1] / 3), save=False))
    degree_frames[0].save('degree_dist.gif', save_all=True, append_images=degree_frames[1:], optimize=False, duration=250, loop=0)
    ndd_frames[0].save('ndd.gif', save_all=True, append_images=ndd_frames[1:], optimize=False, duration=1000, loop=0)
    collage_frames = []
    for index, (ndds, degrees) in enumerate(zip(ndd_frames, degree_frames)):
        collage = Image.new('RGBA', (ndds.size[0], ndds.size[1] + degrees.size[1]), color=(255, 255, 255, 255))
        collage.paste(degrees, (0, 0))
        collage.paste(ndds, (0, degrees.size[1]))
        collage_frames.append(collage)
        collage.save(f'{index}.png')
    collage_frames[0].save('inspection.gif', save_all=True, append_images=collage_frames[1:], optimize=False, duration=1000, loop=0)

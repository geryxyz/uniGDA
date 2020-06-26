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
    def visualize(self, width=800, height=600, title=None, xmax=None, ymax=None, save: bool = True):
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
        buffer = io.BytesIO()
        fig.savefig(buffer, format='png')
        fig.clf()
        buffer.seek(0)
        image = Image.open(buffer)
        image.load()
        buffer.close()
        return image


class InspectionReport(object):
    def __init__(self, ndds: NDDCollection, degrees: DegreeDistribution, graph: GraphTraversal):
        self.ndds = ndds
        self.degrees = degrees
        self.graph = graph

    def visualize(self, xmax: int, ymax: int, max_node_count: int = None, title: str = None, ndd_width: int = 600,
                  ndd_height: int = 200):
        if max_node_count is None:
            max_node_count = self.graph.V().count().next()
        ndd_image = self.ndds.visualize_collage(max_count=max_node_count, max_kind=max_node_count,
                                                ndd_width=ndd_width, ndd_height=ndd_height)
        degree_image = self.degrees.visualize(title=title,
                                              xmax=xmax, ymax=ymax, width=ndd_image.size[0],
                                              height=int(ndd_image.size[1] / 3))
        collage = Image.new('RGBA', (ndd_image.size[0], ndd_image.size[1] + degree_image.size[1]),
                            color=(255, 255, 255, 255))
        collage.paste(degree_image, (0, 0))
        collage.paste(ndd_image, (0, degree_image.size[1]))
        return collage


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

    def generate_report(self, edge_selector: typing.Callable[[Vertex], typing.List[Edge]] = None):
        return InspectionReport(self.all_ndds_of(), self.degree_distribution(edge_selector), self.graph)


if __name__ == "__main__":
    max_node_count = 10
    genrator = EmptyGraph('ws://localhost:8182/gremlin', 'g', max_node_count)
    inspector = GraphInspector(genrator.output_graph)
    max_edge_count = 25
    reports = []
    for count in range(max_edge_count):
        print(count)
        genrator.add_random_edge(weight=None)
        reports.append(inspector.generate_report())
    xmax = max([max(report.degrees.keys()) for report in reports])
    ymax = max([max(report.degrees.values()) for report in reports])
    for index, report in enumerate(reports):
        collage = report.visualize(xmax, ymax)
        collage.save(f'{index}.png')

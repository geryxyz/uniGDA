import os
import typing

import PIL.Image as Image
from gremlin_python.process.graph_traversal import GraphTraversal
from gremlin_python.structure.graph import Vertex, Edge
from matplotlib.axes import Axes
from matplotlib.figure import Figure
import matplotlib.pyplot as pyplot

from graph_input.generator import EmptyGraph
from graph_inspect import NDDCollection, NDD
import io


class DegreeDistribution(dict):
    def visualize(self, path: str, width=6, height=8, title=None, xmax=None, ymax=None, save: bool = True):
        as_list = sorted(self.items())  # sorted by key, return a list of tuples
        x, y = zip(*as_list)
        fig: Figure
        ax: Axes
        fig = pyplot.figure(0, figsize=(width, height))
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

    def visualize(self, title_extractor: typing.Callable[[Vertex, GraphTraversal], str] = None):
        ndds = self.all_ndds_of()
        if title_extractor is None:
            def title_extractor(node, graph): return node.id
        groups: typing.List[typing.List[typing.Tuple[object, Image]]] = []
        for ndd, image in ndds.visualize('.', title_extractor=title_extractor, save=False):
            for group in groups:
                if any([ndd.is_alike(candidate) for candidate in group]):
                    group.append(ndd)
                    break
            else:
                groups.append([ndd])
        print()


if __name__ == "__main__":
    max_node_count = 10
    genrator = EmptyGraph('ws://localhost:8182/gremlin', 'g', max_node_count)
    inspector = GraphInspector(genrator.output_graph)
    max_edge_count = 50
    degree_distributions = []
    for count in range(max_edge_count):
        print(count)
        genrator.add_random_edge(weight=None)
        count_dir = f'count_{count}'
        if not os.path.isdir(count_dir):
            os.mkdir(count_dir)
        inspector.visualize()
        degree_distributions.append(inspector.degree_distribution())
    frames = []
    xmax = max([max(dist.keys()) for dist in degree_distributions])
    ymax = max([max(dist.values()) for dist in degree_distributions])
    for index, distribution in enumerate(degree_distributions):
        frames.append(
            distribution.visualize(f'frames/{index}_degree_dist',
                                   title=f'Degree distribution of {index} edges over {max_node_count} nodes',
                                   xmax=xmax, ymax=ymax, save=False))
    frames[0].save('degree_dist.gif', save_all=True, append_images=frames[1:], optimize=False, duration=250, loop=0)
    print()

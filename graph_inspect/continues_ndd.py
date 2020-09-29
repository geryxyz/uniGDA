import typing
from statistics import stdev

import math
import matplotlib.pyplot as pyplot
from gremlin_python.process.graph_traversal import GraphTraversal
from gremlin_python.process.graph_traversal import __
from gremlin_python.structure.graph import Vertex, Edge
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from graph_inspect import EmptyGraph, set_axes_size, NDDVisualization
import floatrange


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

    def __eq__(self, other):
        return isinstance(other, ModifiedGauss) \
               and self.height == other.height and self.width == other.width and self.offset == other.offset

    def __hash__(self):
        return hash((self.offset, self.width, self.height))


def sum_of_squares(values: typing.List[float]) -> float:
    return sum([value ** 2 for value in values])


RESOLUTION = 1000


class ContinuesNDD:
    def __init__(self, inspected: Vertex, graph: GraphTraversal,
                 neighbor_selector: typing.Callable[[Vertex], typing.List[Vertex]] = None,
                 weight_selector: typing.Callable[[Edge], typing.Union[int, float]] = None,
                 edge_selector: typing.Callable[[Vertex], typing.List[Edge]] = None):
        self.inspected = inspected
        self.graph = graph
        if neighbor_selector is None:
            def neighbor_selector(node): return graph.V(node).both().toList()
        if edge_selector is None:
            def edge_selector(node): return graph.V(node).bothE().toList()
        if weight_selector is None:
            def weight_selector(edge):
                weight = graph.E(edge).properties('weight').value().limit(1).toList()
                if weight:
                    return float(weight[0])
                else:
                    return 1
        neighbors = neighbor_selector(inspected)
        curve = []
        for neighbor in neighbors:
            count_of_neighbor_adjacents = len(neighbor_selector(neighbor))
            weights = [weight_selector(edge) for edge in edge_selector(neighbor)]
            if len(weights) > 1:
                stdev_of_neighbor_edges = stdev(weights)
            else:
                stdev_of_neighbor_edges = 0
            neighbor_edge = graph.V(inspected).bothE().filter(__.otherV().is_(neighbor)).limit(1).next()
            neighbor_weight = weight_selector(neighbor_edge)
            gauss = ModifiedGauss(height=neighbor_weight, offset=count_of_neighbor_adjacents,
                                  width=stdev_of_neighbor_edges)
            curve.append(gauss)
        self._curve = tuple(curve)

    def value(self, x, aggregation: typing.Callable[[typing.List[float]], float] = sum_of_squares):
        return aggregation([gauss(x) for gauss in self._curve])

    def offset_maximum(self):
        if self._curve:
            return max([gauss.offset + gauss.width for gauss in self._curve])
        else:
            return 0

    def strength_maximum(self):
        if self._curve:
            return max([self.value(gauss.offset) for gauss in self._curve])
        else:
            return 0

    def visualize(self,
                  title=None,
                  width=900, height=200,
                  offset_maximum=None, strength_maximum=None) -> NDDVisualization:
        if offset_maximum is None:
            offset_maximum = self.offset_maximum()
        if strength_maximum is None:
            strength_maximum = self.strength_maximum()

        xs = list(floatrange.floatrange(0, offset_maximum, offset_maximum / RESOLUTION))
        xs += [g.offset for g in self._curve]
        xs = sorted(xs)
        ys = [self.value(x) for x in xs]

        fig: Figure
        ax: Axes
        fig, ax = pyplot.subplots()

        fig.set_dpi(100)
        fig.subplots_adjust(bottom=.2, left=.1, right=.95, top=.95)
        set_axes_size(width / 100, height / 100, ax)

        if title:
            ax.set_title(title)
            fig.subplots_adjust(top=.8)
        ax.set_xlabel('degree of neighbors (st.dev. of adj.connection)')
        ax.set_ylabel('strength of connection')

        ax.set_xlim(0, offset_maximum + 1)
        ax.set_ylim(0, strength_maximum + 1)
        ax.plot(
            xs, ys,
            linestyle='solid', linewidth=1,
            color='black',
            zorder=1)
        peaks = [(g.offset, self.value(g.offset)) for g in self._curve]
        ax.scatter(
            [p[0] for p in peaks], [p[1] for p in peaks],
            marker='^', c='lightgray', edgecolors='black',
            zorder=2)

        fig.show()
        return NDDVisualization(fig, ax)

    def __str__(self):
        gauss: ModifiedGauss
        return '(' + ', '.join([f'|{gauss.height:.4f}-{gauss.width:.4f}@{gauss.offset:.4f}' for gauss in
                                sorted(self._curve, key=lambda g: g.offset)]) + ')'

    def is_alike(self, other):
        return isinstance(other, ContinuesNDD) and self._curve == other._curve


if __name__ == '__main__':
    genrator = EmptyGraph('ws://localhost:8182/gremlin', 'g', 5)
    genrator.add_random_edge(500, weight=None)
    for index, node in enumerate(genrator.output_graph.V().toList()):
        cndd = ContinuesNDD(node, genrator.output_graph)
        cndd.visualize().image.save(f'cndd_{index}.png')
    pass

import io
import typing

from PIL import Image, ImageDraw, ImageFont
from floatrange import floatrange
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from gremlin_python.process import anonymous_traversal
from gremlin_python.process.graph_traversal import GraphTraversal
from gremlin_python.structure.graph import Vertex, Edge

import graph_input
from graph_input.generator import EmptyGraph
from matplotlib.axes import Axes
from matplotlib.figure import Figure
import matplotlib.pyplot as pyplot

from util import set_axes_size


class DiscreteNDD:
    def __init__(self, inspected: Vertex, graph: GraphTraversal,
                 neighbor_selector: typing.Callable[[Vertex], typing.List[Vertex]] = None):
        self.inspected = inspected
        self.graph = graph
        if neighbor_selector is None:
            def neighbor_selector(node): return graph.V(node).both().toList()
        neighbors = neighbor_selector(inspected)
        vector = {}
        for neigbor in neighbors:
            count_of_neighbor_adjacents = len(neighbor_selector(neigbor))
            vector[count_of_neighbor_adjacents] = vector.get(count_of_neighbor_adjacents, 0) + 1
        self._vector: typing.Tuple[typing.Tuple[int, int]] = tuple(vector.items())

    def offset_maximum(self):
        if self._vector:
            as_sorted = sorted(self._vector, key=lambda e: e[0])
            return as_sorted[-1][0]
        else:
            return 0

    def strength_maximum(self):
        if self._vector:
            as_sorted = sorted(self._vector, key=lambda e: e[0])
            return max(as_sorted, key=lambda e: [1])[1]
        else:
            return 0

    def visualize(self,
                  title=None,
                  width=900, height=100,
                  offset_maximum=None, strength_maximum=None):
        as_sorted = sorted(self._vector, key=lambda e: e[0])
        if offset_maximum is None:
            offset_maximum = self.offset_maximum()
        if strength_maximum is None:
            strength_maximum = self.strength_maximum()

        fig: Figure
        ax: Axes
        fig, ax = pyplot.subplots()

        fig.set_dpi(100)
        fig.subplots_adjust(bottom=0.2)
        set_axes_size(width / 100, height / 100, ax)

        if title:
            ax.set_title(title)
        ax.set_xlabel('degree')
        ax.set_ylabel('count')

        ax.set_xlim(0, offset_maximum + 1)
        ax.set_ylim(0, strength_maximum + 1)
        ax.bar(
            [item[0] for item in as_sorted], [item[1] for item in as_sorted],
            color='lightgrey', edgecolor='black')

        #fig.show()
        buffer = io.BytesIO()
        fig.savefig(buffer, format='png')
        fig.clf()
        buffer.seek(0)
        image = Image.open(buffer)
        image.load()
        buffer.close()
        return image


    def __str__(self):
        as_sorted: typing.List[typing.Union[typing.Tuple[int, int], typing.Tuple[None, None]]] = sorted(self._vector, key=lambda e: e[0])
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

    def is_alike(self, other):
        return isinstance(other, DiscreteNDD) and self._vector == other._vector


if __name__ == '__main__':
    genrator = EmptyGraph('ws://localhost:8182/gremlin', 'g', 5)
    genrator.add_random_edge(50)
    for index, node in enumerate(genrator.output_graph.V().toList()):
        dndd = DiscreteNDD(node, genrator.output_graph)
        dndd.visualize().save(f"{index}.png")
    pass

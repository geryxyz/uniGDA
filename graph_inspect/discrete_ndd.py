import typing

from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from gremlin_python.process import anonymous_traversal
from gremlin_python.process.graph_traversal import GraphTraversal
from gremlin_python.process.traversal import P
from gremlin_python.process.graph_traversal import __
from gremlin_python.structure.graph import Vertex, Edge

from PIL import Image, ImageDraw


class DiscreteNDD(dict):
    @staticmethod
    def from_node(
            inspected: Vertex,
            graph: GraphTraversal,
            neighbor_selector: typing.Callable[[Vertex], typing.List[Edge]] = None):
        if neighbor_selector is None:
            def neighbor_selector(node): return graph.V(node).both().toList()
        neighbors = neighbor_selector(inspected)
        dndd = DiscreteNDD()
        for neigbor in neighbors:
            count_of_neighbor_adjacents = len(neighbor_selector(neigbor))
            dndd[count_of_neighbor_adjacents] = dndd.get(count_of_neighbor_adjacents, 0) + 1
        return dndd

    def visualize(self, path, width=300, height=50, offset_maximum=None, strength_maximum=None):
        as_sorted = sorted(self.items(), key=lambda e: e[0])
        if offset_maximum is None:
            offset_maximum = as_sorted[-1][0]
        if strength_maximum is None:
            strength_maximum = max(as_sorted, key=lambda e: [1])[1]
        image = Image.new('RGBA', (width, height), color=(255, 255, 255, 255))
        draw = ImageDraw.Draw(image)
        for entry in as_sorted:
            offset = (entry[0] / offset_maximum) * width
            strength = int((1 - entry[1] / strength_maximum) * 255)
            draw.line([(offset, 0), (offset, width)], fill=(strength, strength, strength, 255))
        image.save(path)

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


if __name__ == "__main__":
    graph = anonymous_traversal.traversal().withRemote(DriverRemoteConnection('ws://localhost:8182/gremlin', 'g'))
    dndds = {}
    node: Vertex
    for node in graph.V().limit(10).toList():
        dndd = DiscreteNDD.from_node(node, graph)
        dndds[node] = dndd
        print(f"dNDD({node.id}) = {dndd}")
        dndd.visualize(f'{node.id}.png')
    pass

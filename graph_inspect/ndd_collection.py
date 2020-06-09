import typing
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from gremlin_python.process import anonymous_traversal

import graph_input
from graph_inspect import DiscreteNDD
import os.path


class NDDCollection(list):
    def visualize(self, path, title_extractor=None, width=900, height=100, top_margin_ratio=.3, bottom_margin_ratio=.2, tick_count=5):
        if self:
            offset_maximum = max([ndd.offset_maximum() for ndd in self])
            strength_maximum = max([ndd.strength_maximum() for ndd in self])
            if title_extractor is None:
                def title_extractor(node, graph): return graph.V(node).properties(graph_input.ORIGINAL_ID).value().limit(1).next()
            ndd: typing.Union[DiscreteNDD]
            for index, ndd in enumerate(self):
                ndd.visualize(
                    os.path.join(path, f'{index}.png'),
                    title=title_extractor(ndd.inspected, ndd.graph),
                    width=width, height=height,
                    offset_maximum=offset_maximum, strength_maximum=strength_maximum,
                    top_margin_ratio=top_margin_ratio, bottom_margin_ratio=bottom_margin_ratio,
                    tick_count=tick_count)


if __name__ == "__main__":
    graph = anonymous_traversal.traversal().withRemote(DriverRemoteConnection('ws://localhost:8182/gremlin', 'g'))
    dndds = NDDCollection([DiscreteNDD(node, graph) for node in graph.V().limit(30).toList()])
    dndds.visualize('.')

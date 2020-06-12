import typing
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from gremlin_python.process import anonymous_traversal
from gremlin_python.process.graph_traversal import GraphTraversal
from gremlin_python.structure.graph import Vertex

import graph_input
from graph_inspect import DiscreteNDD, ContinuesNDD, NDD
from graph_input.generator import EmptyGraph
import os.path


class NDDCollection(list):
    def visualize(self, path, title_extractor: typing.Callable[[Vertex, GraphTraversal], str]=None, width=900, height=300, top_margin_ratio=.3, bottom_margin_ratio=.2, tick_count=5):
        if self:
            offset_maximum = max([ndd.offset_maximum() for ndd in self])
            strength_maximum = max([ndd.strength_maximum() for ndd in self])
            if title_extractor is None:
                def title_extractor(node, graph): return graph.V(node).properties(graph_input.ORIGINAL_ID).value().limit(1).next()
            with open('toc.txt', 'w') as table_of_contents:
                ndd: typing.Union[DiscreteNDD, ContinuesNDD, NDD]
                for index, ndd in enumerate(self):
                    extracted_title = title_extractor(ndd.inspected, ndd.graph)
                    ndd.visualize(
                        os.path.join(path, str(index)),
                        title=extracted_title,
                        width=width, height=height,
                        offset_maximum=offset_maximum, strength_maximum=strength_maximum,
                        top_margin_ratio=top_margin_ratio, bottom_margin_ratio=bottom_margin_ratio,
                        tick_count=tick_count)
                    table_of_contents.write(f'{index}: {ndd}\n')

    @staticmethod
    def all_ndds_of(graph: GraphTraversal):
        nodes = graph.V().toList()
        ndds = NDDCollection()
        ndds.extend([NDD(node, graph) for node in nodes])
        return ndds


if __name__ == "__main__":
    genrator = EmptyGraph('ws://localhost:8182/gremlin', 'g', 5)
    genrator.add_random_edge(50)
    ndds = NDDCollection.all_ndds_of(genrator.output_graph)
    ndds.visualize('.', title_extractor=lambda node, graph: str(node.id))

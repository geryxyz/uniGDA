import pdb

import graph_inspect
import argparse
import logging

if __name__ == '__main__':
    clap = argparse.ArgumentParser(
        description='This script creates a scheme documentation for a graph hosted in a Apache TinkerPop Gremlin server.')
    clap.add_argument(
        '-is', '--input-server',
        dest='input_server',
        action='store',
        help='URL of the input Gremlin server',
        required=True)
    clap.add_argument(
        '-its', '--input-source',
        dest='input_source',
        action='store',
        help='name of the input Gremlin traversal source',
        required=True)
    clap.add_argument(
        "-l", "--log",
        default='INFO',
        dest="log_level",
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        help="set the logging level",
        required=False)
    clap.add_argument(
        "-np", "--node-property",
        default=None,
        dest="node_property",
        help="name of property for node type",
        required=False)
    clap.add_argument(
        "-ep", "--edge-property",
        default=None,
        dest="edge_property",
        help="name of property for edge type",
        required=False)

    clargs = clap.parse_args()
    logging.basicConfig(level=logging.getLevelName(clargs.log_level))

    discovery = graph_inspect.GremlinDiscovery(clargs.input_server, clargs.input_source)


    def node_extractor(graph, node):
        return graph.V(node).label().next()

    def edge_extractor(graph, edge):
        return graph.E(edge).label().next()

    if clargs.node_property:
        def node_extractor(graph, node):
            return '{}/{}'.format(
                graph.V(node).label().next(),
                ','.join(graph.V(node).properties(clargs.node_property).value().toList()))

    if clargs.edge_property:
        def edge_extractor(graph, edge):
            return '{}/{}'.format(
                graph.E(edge).label().next(),
                ','.join(graph.E(edge).properties(clargs.edge_property).value().toList()))

    discovery.discover(node_type_extractor=node_extractor, edge_type_extractor=edge_extractor)

import io
import json

import networkx as nx
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from gremlin_python.process import anonymous_traversal
import logging
import pdb


class GremlinDiscovery(object):
    def __init__(self, server_url, traversal_source):
        super().__init__()
        logging.info("subject Gremlin server: %s, %s" % (server_url, traversal_source))
        self.graph = anonymous_traversal.traversal().withRemote(
            DriverRemoteConnection(server_url, traversal_source))

    def _add_edge(self, in_id, out_id, props, edge_id, edge_label):
        logging.debug("processing edge: %s --> %s" % (out_id, in_id))
        for prop, value in props.items():
            pass

    def _add_node(self, id, props):
        logging.debug("processing node: %s\nwith data: %s" % (id, props))
        for prop, value in props.items():
            pass

    def discover(self, server_url, traversal_source):
        logging.info("input Gremlin server: %s, %s" % (server_url, traversal_source))
        graph = anonymous_traversal.traversal().withRemote(DriverRemoteConnection(server_url, traversal_source))
        for node in graph.V().toList():
            id = node.id
            props = {prop: value[0].value for prop, value in graph.V(node).propertyMap().next().items()}
            self._discover_node(id, props)
        for edge in graph.E().toList():
            id = edge.id
            edge_label = edge.label
            in_id = edge.inV.id
            out_id = edge.outV.id
            props = {prop: value.value for prop, value in graph.E(edge).propertyMap().next().items()}
            self._discover_edge(in_id, out_id, props, id, edge_label)

        logging.info("nodes count: %d" % graph.V().count().next())
        logging.info("edges count: %d" % graph.E().count().next())

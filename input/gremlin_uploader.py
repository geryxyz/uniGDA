import io
import json

import networkx as nx
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from gremlin_python.process import anonymous_traversal
import logging


class GremlinUploader(object):
    def __init__(self, server_url, traversal_source):
        super().__init__()
        logging.info("output Gremlin server: %s, %s" % (server_url, traversal_source))
        self.output_graph = anonymous_traversal.traversal().withRemote(
            DriverRemoteConnection(server_url, traversal_source))

    def _drop_graph(self):
        self.output_graph.V().drop().toList()
        self.output_graph.E().drop().toList()

    def from_d3js(self, json_graph, source_name, drop_graph=True, label=None):
        source_label = source_name
        if label:
            source_label = label
        input_graph = self._load_graph(json_graph)
        self.drop_if(drop_graph)

        for id, props in input_graph.nodes(data=True):
            logging.debug("processing node: %s\nwith data: %s" % (id, props))
            new_node = self.output_graph.addV('node_link_node').next()
            self.output_graph.V(new_node).property('original_id', id).toList()
            self.output_graph.V(new_node).property('source_name', source_label).toList()
            for prop, value in props.items():
                self.output_graph.V(new_node).property(prop, value).toList()
            logging.debug("added properties: %s" % self.output_graph.V(new_node).properties().toList())

        for out_id, in_id, props in input_graph.edges(data=True):
            logging.debug("processing edge: %s --> %s" % (out_id, in_id))
            out_node = self.output_graph.V().has('source_name', source_label).has('original_id', out_id).next()
            in_node = self.output_graph.V().has('source_name', source_label).has('original_id', in_id).next()
            new_edge = self.output_graph.addE('node_link_connection').from_(out_node).to(in_node).next()
            for prop, value in props.items():
                self.output_graph.E(new_edge).property(prop, value).toList()
            logging.debug("added properties: %s" % self.output_graph.E(new_edge).properties().toList())

        logging.info("total nodes added: %d" % self.output_graph.V().count().next())
        logging.info("total edges added: %d" % self.output_graph.E().count().next())

    def _load_graph(self, json_graph):
        if isinstance(json_graph, str):
            input_graph = nx.readwrite.json_graph.node_link_graph(json.loads(json_graph))
        elif isinstance(json_graph, io.TextIOBase):
            input_graph = nx.readwrite.json_graph.node_link_graph(json.load(json_graph))
        return input_graph

    def drop_if(self, drop_graph):
        if drop_graph:
            logging.warning("Clearing output graph...")
            self._drop_graph()
            logging.warning("done")

    def from_gremlin(self, server_url, traversal_source, drop_graph=True, label=None):
        source_label = server_url
        if label:
            source_label = label
        self.drop_if(drop_graph)

        logging.info("output Gremlin server: %s, %s" % (server_url, traversal_source))
        input_graph = anonymous_traversal.traversal().withRemote(DriverRemoteConnection(server_url, traversal_source))
        for node in input_graph.V().toList():
            id = node.id
            props = {prop: value[0].value for prop, value in input_graph.V(node).propertyMap().next()}
            logging.debug("processing node: %s\nwith data: %s" % (id, props))
            new_node = self.output_graph.addV('node_link_node').next()
            self.output_graph.V(new_node).property('original_id', id).toList()
            self.output_graph.V(new_node).property('source_name', source_label).toList()
            for prop, value in props.items():
                self.output_graph.V(new_node).property(prop, value).toList()
            logging.debug("added properties: %s" % self.output_graph.V(new_node).properties().toList())

        for edge in input_graph.E().toList():
            id = edge.id
            in_id = edge.inV.id
            out_id = edge.outV.id
            props = {prop: value.value for prop, value in input_graph.E(edge).propertyMap().next()}
            logging.debug("processing edge: %s --> %s" % (out_id, in_id))
            out_node = self.output_graph.V().has('source_name', source_label).has('original_id', out_id).next()
            in_node = self.output_graph.V().has('source_name', source_label).has('original_id', in_id).next()
            new_edge = self.output_graph.addE('node_link_connection').from_(out_node).to(in_node).next()
            self.output_graph.E(new_edge).property('original_id', id).toList()
            self.output_graph.E(new_edge).property('source_name', source_label).toList()
            for prop, value in props.items():
                self.output_graph.E(new_edge).property(prop, value).toList()
            logging.debug("added properties: %s" % self.output_graph.E(new_edge).properties().toList())

        logging.info("original nodes count: %d" % input_graph.V().count().next())
        logging.info("original edges count: %d" % input_graph.E().count().next())

        logging.info("total nodes added: %d" % self.output_graph.V().count().next())
        logging.info("total edges added: %d" % self.output_graph.E().count().next())

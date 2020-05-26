from __future__ import annotations

import io
import json
import typing
import networkx as nx
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from gremlin_python.process import anonymous_traversal
import logging
import pdb

SOURCE_NAME = 'source_name'

ORIGINAL_ID = 'original_id'

_allowed_id_type = typing.Union[int, str]
_allowed_propeties_type = typing.Dict[str, typing.AnyStr]


class GremlinUploader(object):
    def __init__(self, server_url, traversal_source):
        super().__init__()
        logging.info("output Gremlin server: %s, %s" % (server_url, traversal_source))
        self.output_graph = anonymous_traversal.traversal().withRemote(
            DriverRemoteConnection(server_url, traversal_source))

    def _check_original_edge_id(self, new_id):
        return new_id in self.output_graph.E().properties(ORIGINAL_ID).values().toList()

    def _check_original_node_id(self, new_id):
        return new_id not in self.output_graph.V().properties(ORIGINAL_ID).values().toList()

    def _add_edge(
            self,
            original_out_id: _allowed_id_type,
            original_in_id: _allowed_id_type,
            props: _allowed_propeties_type,
            label: typing.AnyStr,
            source_label: typing.AnyStr,
            original_id: _allowed_id_type = None):
        logging.debug("processing edge: %s --> %s" % (original_out_id, original_in_id))
        if original_id and not self._check_original_edge_id(original_id):
            raise AttributeError(f'duplicated edge id: {original_id}')
        out_node = self.output_graph.V().has(SOURCE_NAME, source_label).has(ORIGINAL_ID, original_out_id).next()
        in_node = self.output_graph.V().has(SOURCE_NAME, source_label).has(ORIGINAL_ID, original_in_id).next()
        new_edge = self.output_graph.addE(label).from_(out_node).to(in_node).next()
        if original_id:
            self.output_graph.E(new_edge).property(ORIGINAL_ID, original_id).toList()
        self.output_graph.E(new_edge).property(SOURCE_NAME, source_label).toList()
        for prop, value in props.items():
            self.output_graph.E(new_edge).property(prop, value).toList()
        logging.debug("added properties: %s" % self.output_graph.E(new_edge).properties().toList())

    def _add_node(
            self,
            original_id: _allowed_id_type,
            props: _allowed_propeties_type,
            node_label: typing.AnyStr,
            source_label: typing.AnyStr):
        logging.debug("processing node: %s\nwith data: %s" % (original_id, props))
        if not self._check_original_node_id(original_id):
            raise AttributeError(f'duplicated edge id: {original_id}')
        new_node = self.output_graph.addV(node_label).next()
        self.output_graph.V(new_node).property(ORIGINAL_ID, original_id).toList()
        self.output_graph.V(new_node).property(SOURCE_NAME, source_label).toList()
        for prop, value in props.items():
            self.output_graph.V(new_node).property(prop, value).toList()
        logging.debug("added properties: %s" % self.output_graph.V(new_node).properties().toList())

    def _load_graph(self, json_graph):
        if isinstance(json_graph, str):
            input_graph = nx.readwrite.json_graph.node_link_graph(json.loads(json_graph))
        elif isinstance(json_graph, io.TextIOBase):
            input_graph = nx.readwrite.json_graph.node_link_graph(json.load(json_graph))
        return input_graph

    def _drop_if(self, drop_graph):
        if drop_graph:
            logging.warning("Clearing output graph...")
            self.output_graph.V().drop().toList()
            self.output_graph.E().drop().toList()
            logging.warning("done")

    def from_d3js(
            self,
            json_graph: str,
            source_name: str,
            drop_graph: bool = True,
            label: str = None):
        source_label = source_name
        if label:
            source_label = label
        input_graph = self._load_graph(json_graph)
        self._drop_if(drop_graph)

        for id, props in input_graph.nodes(data=True):
            self._add_node(id, props, 'node', source_label)

        for out_id, in_id, props in input_graph.edges(data=True):
            self._add_edge(out_id, in_id, props, 'edge', source_label, -1)

    def from_gremlin(
            self,
            server_url: str,
            traversal_source: str,
            drop_graph: bool = True,
            label: str = None):
        source_label = server_url
        if label:
            source_label = label
        self._drop_if(drop_graph)

        logging.info("input Gremlin server: %s, %s" % (server_url, traversal_source))
        input_graph = anonymous_traversal.traversal().withRemote(DriverRemoteConnection(server_url, traversal_source))
        add_node_count = 0
        for node in input_graph.V().toList():
            id = node.id
            props = {prop: value[0].value for prop, value in input_graph.V(node).propertyMap().next().items()}
            self._add_node(id, props, node.label, source_label)
            add_node_count += 1

        add_edge_count = 0
        for edge in input_graph.E().toList():
            id = edge.id
            edge_label = edge.label
            in_id = edge.inV.id
            out_id = edge.outV.id
            props = {prop: value.value for prop, value in input_graph.E(edge).propertyMap().next().items()}
            self._add_edge(out_id, in_id, props, edge_label, source_label, id)
            add_edge_count += 1

        logging.info("original nodes count: %d" % input_graph.V().count().next())
        logging.info("original edges count: %d" % input_graph.E().count().next())

        logging.info("total nodes added: %d" % add_node_count)
        logging.info("total edges added: %d" % add_edge_count)

    class ParsedNode(object):
        def __init__(
                self,
                original_id: _allowed_id_type,
                label: str,
                props: _allowed_propeties_type = {}):
            self.props = props
            self.label = label
            self.original_id = original_id

    class ParsedEdge(object):
        def __init__(
                self,
                source: GremlinUploader.ParsedNode,
                target: GremlinUploader.ParsedNode,
                original_id: _allowed_id_type,
                label: str = "",
                props: _allowed_propeties_type = {}):
            self.props = props
            self.label = label
            self.original_id = original_id
            self.target = target
            self.source = source

    def edge_from_text(
            self,
            edge_list: typing.List[str],
            source_name: str,
            parse: typing.Callable[[str], ParsedEdge],
            drop_graph: bool = True,
            label: str = None):
        source_label = source_name
        if label:
            source_label = label
        self._drop_if(drop_graph)

        for line in edge_list:
            line = line.strip()
            if line == '':
                continue
            edge = parse(line)

            self._add_node(edge.source.original_id, edge.source.props, edge.source.label, source_label)
            self._add_node(edge.target.original_id, edge.target.props, edge.target.label, source_label)
            self._add_edge(edge.source.original_id, edge.target.original_id, edge.props, edge.label, source_label,
                           edge.original_id)
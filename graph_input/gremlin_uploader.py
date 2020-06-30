from __future__ import annotations

import io
import json
import typing
import networkx as nx
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from gremlin_python.process import anonymous_traversal
from gremlin_python.process.graph_traversal import GraphTraversal
import logging
import pdb
import time

from networkx import Graph, DiGraph, MultiGraph, MultiDiGraph

SOURCE_NAME = 'source_name'

ORIGINAL_ID = 'original_id'

_allowed_id_type = typing.Union[int, str]
_allowed_propeties_type = typing.Dict[str, typing.AnyStr]


class GremlinUploader(object):
    def __init__(self, server_url, traversal_source):
        super().__init__()
        logging.info("output Gremlin server: %s, %s" % (server_url, traversal_source))
        # travel = anonymous_traversal.traversal().withRemote(DriverRemoteConnection("ws://localhost:8182/gremlin", "g"))
        self.output_graph = anonymous_traversal.traversal().withRemote(
            DriverRemoteConnection(server_url, traversal_source))
        self._added_node_ids = []
        self._added_edge_ids = []

    def _edge_id_present(self, new_id):
        return new_id in self._added_edge_ids

    def _node_id_present(self, new_id):
        return new_id in self._added_node_ids

    def _add_edge(
            self,
            original_out_id: _allowed_id_type,
            original_in_id: _allowed_id_type,
            props: _allowed_propeties_type,
            label: typing.AnyStr,
            source_label: typing.AnyStr,
            original_id: _allowed_id_type = None,
            query: GraphTraversal = None) -> GraphTraversal:
        if query is None:
            query = self.output_graph
        logging.debug("processing edge: %s --> %s" % (original_out_id, original_in_id))
        out_node_query = self.output_graph.V().has(ORIGINAL_ID, original_out_id).has(SOURCE_NAME, source_label).limit(1)
        in_node_query = self.output_graph.V().has(ORIGINAL_ID, original_in_id).has(SOURCE_NAME, source_label).limit(1)
        query = query.addE(label).from_(out_node_query).to(in_node_query)
        if original_id:
            self._added_edge_ids.append(original_id)
            query = query.property(ORIGINAL_ID, original_id)
        query = query.property(SOURCE_NAME, source_label)
        for prop, value in props.items():
            query = query.property(prop, value)
        return query

    def _add_node(
            self,
            original_id: _allowed_id_type,
            props: _allowed_propeties_type,
            node_label: typing.AnyStr,
            source_label: typing.AnyStr,
            query: GraphTraversal = None) -> GraphTraversal:
        if query is None:
            query = self.output_graph
        logging.debug("processing node: %s\nwith data: %s" % (original_id, props))
        query = query.addV(node_label)
        self._added_node_ids.append(original_id)
        query = query.property(ORIGINAL_ID, original_id).property(SOURCE_NAME, source_label)
        for prop, value in props.items():
            query = query.property(prop, value).toList()
        return query

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

    def from_networkx(
            self,
            input_graph: typing.Union[Graph, DiGraph, MultiGraph, MultiDiGraph],
            source_name: str,
            drop_graph: bool = True,
            label: str = None):
        source_label = source_name
        if label:
            source_label = label
        self._drop_if(drop_graph)

        for id, props in input_graph.nodes(data=True):
            self._add_node(id, props, 'node', source_label).toList()

        for out_id, in_id, props in input_graph.edges(data=True):
            self._add_edge(out_id, in_id, props, 'edge', source_label, -1).toList()

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
            self._add_node(id, props, 'node', source_label).toList()

        for out_id, in_id, props in input_graph.edges(data=True):
            self._add_edge(out_id, in_id, props, 'edge', source_label, -1).toList()

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
            self._add_node(id, props, node.label, source_label).toList()
            add_node_count += 1

        add_edge_count = 0
        for edge in input_graph.E().toList():
            id = edge.id
            edge_label = edge.label
            in_id = edge.inV.id
            out_id = edge.outV.id
            props = {prop: value.value for prop, value in input_graph.E(edge).propertyMap().next().items()}
            self._add_edge(out_id, in_id, props, edge_label, source_label, id).toList()
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

    def edges_from_text(
            self,
            edge_list: typing.Union[typing.List[str], typing.TextIO],
            source_name: str,
            parse: typing.Callable[[str], ParsedEdge],
            drop_graph: bool = True,
            label: str = None,
            batch_size: int = 300):
        logging.info("loading edges from text list")
        source_label = source_name
        if label:
            source_label = label
        self._drop_if(drop_graph)

        processed_line_count = 0
        query = self.output_graph.V()
        start = time.perf_counter()
        for line in edge_list:
            line = line.strip()
            if line == '':
                continue
            logging.debug(f"processing: {line}")
            edge = parse(line)

            if processed_line_count % batch_size == 0:
                query.toList()
                query = self.output_graph
                duration = time.perf_counter() - start
                logging.info(f"flushing {batch_size} lines during {duration:.4f} seconds. {processed_line_count} lines are processed")
                start = time.perf_counter()
            if not self._node_id_present(edge.source.original_id):
                query = self._add_node(
                    edge.source.original_id,
                    edge.source.props,
                    edge.source.label,
                    source_label,
                    query=query)
            if not self._node_id_present(edge.target.original_id):
                query = self._add_node(
                    edge.target.original_id,
                    edge.target.props,
                    edge.target.label,
                    source_label,
                    query=query)
            query = self._add_edge(
                edge.source.original_id,
                edge.target.original_id,
                edge.props,
                edge.label,
                source_label,
                edge.original_id,
                query=query)
            processed_line_count += 1
        query.toList()
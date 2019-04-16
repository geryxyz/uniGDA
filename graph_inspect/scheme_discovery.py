import pdb

from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from gremlin_python.process import anonymous_traversal
import logging


class Property(object):
    def __init__(self):
        self.is_optional = False
        self.sample_values = set()

    def add_new_sample(self, value):
        self.sample_values.add(value)


class Description(object):
    def __init__(self):
        self.properties = {}
        self.count = 0


class NodeType(Description):
    def __init__(self):
        super().__init__()
        self.out_edges = {}


class EdgeType(Description):
    def __init__(self):
        super().__init__()
        self.target_types = set()


class GremlinDiscovery(object):
    def __init__(self, server_url, traversal_source):
        super().__init__()
        logging.info("subject Gremlin server: %s, %s" % (server_url, traversal_source))
        self.graph = anonymous_traversal.traversal().withRemote(
            DriverRemoteConnection(server_url, traversal_source))
        self._server_url = server_url

    def discover(self, file='scheme.html',
                 node_type_extractor=lambda graph, node: graph.V(node).label().next(),
                 edge_type_extractor=lambda graph, edge: graph.E(edge).label().next()):
        logging.info("discovering graph structure")
        nodes = {}
        edges = {}
        total_node_count = self.graph.V().count().next()
        for i, node in enumerate(self.graph.V().toList()):
            logging.debug("[{} {:.2f}%] {}".format(i, i/total_node_count*100, node))
            node_type_name = node_type_extractor(self.graph, node)
            node_type = nodes.get(node_type_name, NodeType())
            node_type.count += 1

            props = {prop: value[0].value for prop, value in self.graph.V(node).propertyMap().next().items()}
            for prop_name, value in props.items():
                node_property = node_type.properties.get(prop_name, Property())
                node_property.sample_values.add(value)
                node_type.properties[prop_name] = node_property

            for edge in self.graph.V(node).outE().toList():
                edge_type_name = edge_type_extractor(self.graph, edge)
                edge_type = edges.get(edge_type_name, EdgeType())
                edge_type.count += 1
                edge_type.target_types.add(node_type_extractor(self.graph, edge.inV))

                props = {prop: value.value for prop, value in self.graph.E(edge).propertyMap().next().items()}
                for prop_name, value in props.items():
                    edge_property = edge_type.properties.get(prop_name, Property())
                    edge_property.sample_values.add(value)
                    edge_type.properties[prop_name] = edge_property

                node_type.out_edges[edge_type_name] = edge_type
                edges[edge_type_name] = edge_type

            nodes[node_type_name] = node_type

        logging.info("%d nodes in %d types" % (self.graph.V().count().next(), len(nodes)))
        logging.info("%d edges in %d types" % (self.graph.E().count().next(), len(edges)))

        with open(file, 'w') as doc:
            doc.write("""<!DOCTYPE html>
                <html lang="en">
                  <head>
                    <meta charset="utf-8">
                    <title>{}</title>
                    <style>
                    table {{
                        border-collapse: collapse;
                    }}
                    
                    table, th, td {{
                        border: 1px solid black;
                    }}
                    td, th {{
                        padding: 5px;
                    }}
                    span {{
                        border: .3px solid gray;
                        margin: 0px 3px;
                        padding: 2px;
                        font-family: monospace
                    }}
                    </style>
                  </head>
                  <body>""".format(self._server_url))
            doc.write('<h1>Scheme Documentation for {}</h1>'.format(self._server_url))
            for node_type_name, node_type in sorted(nodes.items(), key=lambda item: item[0].lower()):
                doc.write('<h2>Node Type of <span>{}</span> ({} present)</h2>'.format(node_type_name, node_type.count))
                if node_type.properties:
                    doc.write('<h3>Properties</h3>')
                    doc.write('<table><tr><th>Name</th><th>Sample Values (max. 10)</th></tr>')
                    for property_name, value in sorted(node_type.properties.items(), key=lambda item: item[0].lower()):
                        doc.write(
                            '<tr><td>{}</td><td>{}</td></tr>'.format(
                                property_name,
                                '<br/>'.join(map(str, list(value.sample_values)[:10]))))
                    doc.write('</table>')
                else:
                    doc.write('<p>There are not any properties for node type <span>{}</span>.</p>'.format(node_type_name))
                if node_type.out_edges:
                    doc.write('<h3>Edges</h3>')
                    for edge_type_name, edge_type in sorted(node_type.out_edges.items(), key=lambda item: item[0].lower()):
                        doc.write('<h4>Edge Type of <span>{}</span> (outgoing) (altogether {} present)</h4>'.format(edge_type_name, edge_type.count))
                        if edge_type.properties:
                            doc.write('<h5>Properties</h5>')
                            doc.write('<table><tr><th>Name</th><th>Sample Values (max. 10)</th></tr>')
                            for property_name, value in sorted(edge_type.properties.items(), key=lambda item: item[0].lower()):
                                doc.write(
                                    '<tr><td>{}</td><td>{}</td></tr>'.format(
                                        property_name,
                                        '<br/>'.join(map(str, list(value.sample_values)[:10]))))
                            doc.write('</table>')
                        else:
                            doc.write('<p>There are not any properties for edge type <span>{}</span>.</p>'.format(edge_type_name))
                        doc.write('<p>Targets: {}</p>'.format(','.join(['<span>{}</span>'.format(t) for t in edge_type.target_types])))
                else:
                    doc.write('<p>There are not any outgoing edges for node type <span>{}</span>.</p>'.format(node_type_name))
            doc.write("</body></html>")

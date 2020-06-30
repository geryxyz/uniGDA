from floatrange import floatrange

from graph_input import GremlinUploader
import networkx
import sys

from graph_inspect import GraphInspector

if __name__ == '__main__':
    uploader = GremlinUploader('ws://localhost:8182/gremlin', 'g')
    inspector = GraphInspector(uploader.output_graph)
    max_vertex_count = 10
    min_vertex_count = 3
    max_edge_probability = 1
    min_edge_probability = .25
    reports = {}
    for edge_probability in floatrange(min_edge_probability, max_edge_probability, .25):
        for vertex_count in range(min_vertex_count, max_vertex_count):
            print(f"generate an Erdős-Rényi graph with {vertex_count} vertexes and {edge_probability} for edges")
            graph = networkx.generators.erdos_renyi_graph(vertex_count, edge_probability)
            networkx.write_graphml(graph, f'erdos_renyi_vertex_{vertex_count}_edgeprobability_{edge_probability:.4f}.graphml')
            uploader.from_networkx(graph, 'complete_graph')
            print("measuring the generated graph")
            reports[(vertex_count, edge_probability)] = inspector.generate_report()
    xmax = max([max(report.degrees.keys()) for report in reports.values()])
    ymax = max([max(report.degrees.values()) for report in reports.values()])
    for (vertex_count, edge_probability), report in sorted(reports.items(), key=lambda e: e[0]):
        title = f'Erdős-Rényi graph with {vertex_count} vertices and {edge_probability:.4f} edge probability'
        print(f"saving visual report #{(vertex_count, edge_probability)}")
        collage = report.visualize(xmax, ymax, title=title)
        collage.save(f'erdos_renyi_vertex_{vertex_count}_edgeprobability_{edge_probability:.4f}.png')

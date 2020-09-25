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
    min_neighbor_count = 3
    reports = {}
    for edge_probability in floatrange(min_edge_probability, max_edge_probability, .25):
        for vertex_count in range(min_vertex_count, max_vertex_count):
            for neighbor_count in range(vertex_count):
                if neighbor_count < min_neighbor_count:
                    continue
                print(f"generate an Watts-Strongatz graph with {vertex_count} vertexes "
                      f", {edge_probability} for edges "
                      f"and {neighbor_count} connected neighbors")
                graph = networkx.generators.watts_strogatz_graph(n=vertex_count, k=neighbor_count, p=edge_probability)
                networkx.write_graphml(graph, f'watts_strongatz_n={vertex_count}_p={edge_probability:.4f}_k={neighbor_count}.graphml')
                uploader.from_networkx(graph, 'graph')
                print("measuring the generated graph")
                reports[(vertex_count, edge_probability, neighbor_count)] = inspector.generate_report()
    xmax = max([max(report.degrees.keys()) for report in reports.values()])
    ymax = max([max(report.degrees.values()) for report in reports.values()])
    for (vertex_count, edge_probability, neighbor_count), report in sorted(reports.items(), key=lambda e: e[0]):
        title = f'Watts-Strongatz graph with n={vertex_count}, p={edge_probability:.4f}, and k={neighbor_count}'
        print(f"saving visual report #{(vertex_count, edge_probability, neighbor_count)}")
        collage = report.visualize(xmax, ymax, title=title)
        collage.save(f'watts_strongatz_vertex_{vertex_count}_edgeprobability_{edge_probability:.4f}_neighbors_{neighbor_count}.png')

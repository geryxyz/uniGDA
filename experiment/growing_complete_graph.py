from graph_input import GremlinUploader
import networkx
import sys

from graph_inspect import GraphInspector

if __name__ == '__main__':
    uploader = GremlinUploader('ws://localhost:8182/gremlin', 'g')
    inspector = GraphInspector(uploader.output_graph)
    size = 10
    reports = {}
    for index in range(1, size):
        print(f"generate a complete graph with {index} vertexes")
        graph = networkx.generators.complete_graph(index)
        uploader.from_networkx(graph, 'complete_graph')
        print("measuring the generated graph")
        reports[index] = inspector.generate_report()
    xmax = max([max(report.degrees.keys()) for report in reports.values()])
    ymax = max([max(report.degrees.values()) for report in reports.values()])
    for index, report in sorted(reports.items(), key=lambda e: e[0]):
        title = f'Complete graph with {index} vertices'
        print(f"saving visual report #{index}")
        collage = report.visualize(xmax, ymax, title=title)
        collage.save(f'complete_graph_{index}.png')

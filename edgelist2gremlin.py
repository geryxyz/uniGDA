import argparse
import graph_input
import logging


def Bela_WGFL_parser(line: str):
    parts = line.split('\t')
    return graph_input.GremlinUploader.ParsedEdge(
        graph_input.GremlinUploader.ParsedNode(original_id=parts[0], label=parts[0]),
        graph_input.GremlinUploader.ParsedNode(original_id=parts[1], label=parts[0]),
        original_id=f'{parts[0]}->{parts[1]}', label=f'{parts[0]}->{parts[1]}', props={'weight': parts[2]}
    )


if __name__ == '__main__':
    clap = argparse.ArgumentParser(
        description='This script load edge list formats to Apache TinkerPop Gremlin server.')
    clap.add_argument(
        '-i', '--input',
        dest='input_file',
        action='store',
        help='path to input file',
        required=True)
    clap.add_argument(
        '-os', '--output-server',
        dest='output_server',
        action='store',
        help='URL of the output Gremlin server',
        required=True)
    clap.add_argument(
        '-ots', '--output-source',
        dest='output_source',
        action='store',
        help='name of the output Gremlin traversal source',
        required=True)
    clap.add_argument(
        '-k', '--keep',
        dest='delete',
        action='store_false',
        help='do not delete existing graph')

    args = clap.parse_args()

    logging.root.setLevel(logging.INFO)

    uploader = graph_input.GremlinUploader(args.output_server, args.output_source)
    with open(args.input_file, 'r') as text_file:
        uploader.edges_from_text(text_file, args.input_file, Bela_WGFL_parser, drop_graph=args.delete)

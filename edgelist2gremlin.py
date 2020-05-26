import argparse

import graph_input

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

    clargs = clap.parse_args()

    uploader = graph_input.GremlinUploader(clargs.output_server, clargs.output_source)
    with open(clargs.input_file, 'r') as text_file:
        uploader.edge_from_text(text_file, clargs.input_file, drop_graph=clargs.delete)

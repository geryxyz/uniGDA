# python3 gremlin2gremlin.py -i "samples\totinfo.dynamic.json" -os "ws://localhost:8182/gremlin" -ots "g"

import input
import argparse

if __name__ == '__main__':
    clap = argparse.ArgumentParser(
        description='This script load JSON (d3JS) graph formats to Apache TinkerPop Gremlin server.')
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
        '-q', '--quiet',
        dest='verbose',
        action='store_false',
        help='do not print messages except fatal errors')
    clap.add_argument(
        '-k', '--keep',
        dest='delete',
        action='store_false',
        help='do not delete existing graph')

    clargs = clap.parse_args()

    uploader = input.GremlinUploader(clargs.output_server, clargs.output_source)
    with open(clargs.input_file, 'r') as jsonfile:
        uploader.from_d3js(jsonfile, clargs.input_file, verbose=clargs.verbose, drop_graph=clargs.delete)

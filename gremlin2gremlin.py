# python gremlin2gremlin.py -is "ws://localhost:8183/gremlin" -its "g" -os "ws://localhost:8182/gremlin" -ots "g"
import pdb

import input
import argparse
import logging

if __name__ == '__main__':
    clap = argparse.ArgumentParser(
        description='This script load Apache TinkerPop Gremlin graph formats to Apache TinkerPop Gremlin server.')
    clap.add_argument(
        '-is', '--input-server',
        dest='input_server',
        action='store',
        help='URL of the input Gremlin server',
        required=True)
    clap.add_argument(
        '-its', '--input-source',
        dest='input_source',
        action='store',
        help='name of the input Gremlin traversal source',
        required=True)
    clap.add_argument(
        '-il', '--input-label',
        dest='input_label',
        action='store',
        help='unique label of the input',
        required=False)
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
        "-l", "--log",
        default='INFO',
        dest="log_level",
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        help="Set the logging level",
        required=False)
    clap.add_argument(
        '-k', '--keep',
        default=True,
        dest='delete',
        action='store_false',
        help='do not delete existing graph',
        required=False)

    clargs = clap.parse_args()

    logging.basicConfig(level=logging.getLevelName(clargs.log_level))

    uploader = input.GremlinUploader(clargs.output_server, clargs.output_source)
    uploader.from_gremlin(clargs.input_server, clargs.input_source, drop_graph=clargs.delete, label=clargs.input_label)

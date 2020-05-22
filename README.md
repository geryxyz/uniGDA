# uniGDA

## Upload Graphs into a Common Database

### Loading Data from Gremlin Server

You can use `gremlin2gremlin.py` script to upload (merge) existing graphs into a common Gremlin Server.
This script load Apache TinkerPop Gremlin graph formats to Apache TinkerPop
Gremlin server.

#### Usage
```
gremlin2gremlin.py [-h] -is INPUT_SERVER -its INPUT_SOURCE
                          [-il INPUT_LABEL] -os OUTPUT_SERVER -ots
                          OUTPUT_SOURCE
                          [-l {DEBUG,INFO,WARNING,ERROR,CRITICAL}] [-k]

optional arguments:
  -h, --help            show this help message and exit
  -is INPUT_SERVER, --input-server INPUT_SERVER
                        URL of the input Gremlin server
  -its INPUT_SOURCE, --input-source INPUT_SOURCE
                        name of the input Gremlin traversal source
  -il INPUT_LABEL, --input-label INPUT_LABEL
                        unique label of the input
  -os OUTPUT_SERVER, --output-server OUTPUT_SERVER
                        URL of the output Gremlin server
  -ots OUTPUT_SOURCE, --output-source OUTPUT_SOURCE
                        name of the output Gremlin traversal source
  -l {DEBUG,INFO,WARNING,ERROR,CRITICAL}, --log {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        Set the logging level
  -k, --keep            do not delete existing graph
```

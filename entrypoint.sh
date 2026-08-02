#!/bin/bash
set -e

# Start JupyterLab
exec /opt/conda/bin/jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --NotebookApp.token=''

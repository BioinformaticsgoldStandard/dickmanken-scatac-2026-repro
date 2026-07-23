#!/bin/bash
set -e


# --storage-driver=overlay2 
dockerd --host=unix:///var/run/docker.sock --host=tcp://0.0.0.0:2375 --storage-driver=overlay2 &
DOCKER_PID=$!


echo "Attendo che il demone Docker interno sia pronto..."
for i in {1..30}; do
    if docker info > /dev/null 2>&1; then
        echo "Docker pronto!"
        break
    fi
    sleep 1
done


if ! docker info > /dev/null 2>&1; then
    echo "ERRORE: Docker non si è avviato in tempo."
    exit 1
fi

# Start JupyterLab 
exec jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --allow-root --NotebookApp.token=''

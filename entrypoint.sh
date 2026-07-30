#!/bin/bash
set -e

# Remove any stale pid/socket files from a previous unclean shutdown
rm -f /var/run/docker.pid
rm -f /var/run/docker/containerd/containerd.pid
rm -f /var/run/docker.sock

# Start the Docker daemon in background (running as root)
dockerd --host=unix:///var/run/docker.sock --host=tcp://0.0.0.0:2375 --storage-driver=overlay2 &
DOCKER_PID=$!

# Wait for Docker to be ready
echo "Waiting for internal Docker daemon to be ready..."
for i in {1..30}; do
    if docker info > /dev/null 2>&1; then
        echo "Docker ready!"
        break
    fi
    sleep 1
done

if ! docker info > /dev/null 2>&1; then
    echo "ERROR: Docker did not start in time."
    exit 1
fi

# Start JupyterLab as jovyan user (non-root)
# NB_USER, NB_UID, NB_GID are passed from docker-compose.yml
exec su -c "/opt/conda/bin/jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --allow-root --NotebookApp.token=''" ${NB_USER}

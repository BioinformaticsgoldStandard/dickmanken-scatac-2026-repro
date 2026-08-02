# -----------------------------------------------------------
# 1. Base image: Jupyter + Python 3.11
# -----------------------------------------------------------
FROM jupyter/datascience-notebook:python-3.11

# -----------------------------------------------------------
# 2. ROOT section: system tools + Apptainer installation
# -----------------------------------------------------------
USER root

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    openjdk-17-jre-headless \
    wget curl git unzip build-essential \
    samtools bedtools bwa picard \
    ca-certificates \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# ---- Apptainer installation ----
# Installed from the official .deb release asset (pinned version) rather
# than via PPA, to avoid depending on an external repository at build time.
ARG APPTAINER_VERSION=1.4.5
RUN wget -q https://github.com/apptainer/apptainer/releases/download/v${APPTAINER_VERSION}/apptainer_${APPTAINER_VERSION}_amd64.deb -O /tmp/apptainer.deb \
    && apt-get update && apt-get install -y /tmp/apptainer.deb \
    && rm /tmp/apptainer.deb \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# ---- MACS2 installation (via pip) ----
RUN pip install --no-cache-dir macs2==2.2.9.1

# ---- Nextflow installation ----
# Pinned to 21.04.3: PUMATAC's own nextflow.config enforces this exact
# version (nextflowVersion = '!21.04.3'), so any other version would be
# rejected by the pipeline at runtime.
RUN wget -q https://github.com/nextflow-io/nextflow/releases/download/v21.04.3/nextflow-21.04.3-all -O /usr/local/bin/nextflow \
    && chmod +x /usr/local/bin/nextflow

# -----------------------------------------------------------
# 3. USER section (jovyan): Python packages and specific tools
# -----------------------------------------------------------
USER jovyan

# pycisTopic v2.0a0 - specific commit 53fe3f7
RUN git clone https://github.com/aertslab/pycisTopic.git /home/jovyan/pycisTopic \
    && cd /home/jovyan/pycisTopic \
    && git checkout 53fe3f7 \
    && sed -i 's/\.group_by(by="CB", maintain_order=True)/\.group_by("CB", maintain_order=True)/' src/pycisTopic/fragments.py \
    && pip install -e /home/jovyan/pycisTopic

# PUMATAC v0.0.1
RUN git clone --branch v0.0.1 https://github.com/aertslab/PUMATAC.git /home/jovyan/PUMATAC

# Other Python packages with specific versions
RUN pip install --no-cache-dir \
    pyBigWig==0.3.25 \
    deeptools==3.5.3 \
    ipywidgets==8.1.0 \
    pandas==2.0.3 \
    numpy==1.24.3 \
    scikit-learn==1.3.0 \
    matplotlib==3.7.2 \
    seaborn==0.12.2 \
    pillow

# -----------------------------------------------------------
# 4. Entrypoint: starts JupyterLab
# -----------------------------------------------------------
WORKDIR /home/jovyan/work

# Copy the entrypoint script
COPY --chown=jovyan:users entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

EXPOSE 8888

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

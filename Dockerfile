# -----------------------------------------------------------
# 1. Base image: Jupyter + Python 3.11
# -----------------------------------------------------------
FROM jupyter/datascience-notebook:python-3.11

# -----------------------------------------------------------
# 2. ROOT section: system tools + Apptainer installation
# -----------------------------------------------------------
USER root

# Install system dependencies
# Java 11, not a newer release: Nextflow 21.04.3 hardcodes a version check
# that only accepts Java up to 15, and rejects anything above it outright.
RUN apt-get update && apt-get install -y --no-install-recommends \
    openjdk-11-jre-headless \
    wget curl git unzip tree build-essential \
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

# setuptools is pinned below 81: pycisTopic imports pkg_resources, which
# newer releases no longer provide.
RUN pip install --no-cache-dir "setuptools<81"

# pycisTopic v2.0a0 - specific commit 53fe3f7
RUN git clone https://github.com/aertslab/pycisTopic.git /home/jovyan/pycisTopic \
    && cd /home/jovyan/pycisTopic \
    && git checkout 53fe3f7 \
    && sed -i 's/\.group_by(by="CB", maintain_order=True)/\.group_by("CB", maintain_order=True)/' src/pycisTopic/fragments.py \
    && pip install -e /home/jovyan/pycisTopic

# PUMATAC v0.0.1
# Cloned to /home/jovyan/ATACflow, not /home/jovyan/PUMATAC: a bug in
# PUMATAC's own src/utils/processes/config.nf checks the cloned directory's
# name against the string "ATACflow" (PUMATAC's previous name, before a
# rebrand that never updated this check) to decide how to resolve internal
# config include paths. Naming the directory "PUMATAC" - the name the
# tutorial itself instructs you to use - makes that check silently take
# the wrong branch, breaking config resolution (e.g. "conf/generic.config"
# resolves to the nonexistent /home/conf/generic.config instead of the
# correct path).
RUN git clone --branch v0.0.1 https://github.com/aertslab/PUMATAC.git /home/jovyan/ATACflow

# PUMATAC's source additionally hardcodes ${VSC_SCRATCH}, an environment
# variable specific to the authors' cluster, as the temporary directory for
# GATK. The pipeline cannot run elsewhere without rewriting it. See
# scripts/patch_pumatac_source.py for the full list of patches and the
# reasoning behind each one.
COPY --chown=jovyan:users scripts/patch_pumatac_source.py /home/jovyan/patch_pumatac_source.py
RUN python3 /home/jovyan/patch_pumatac_source.py

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
    palettable==3.3.3 \
    jupyter-black==0.4.0 \
    pillow \
    "matplotlib_inline<0.2" \
    bash_kernel

# Two of the tutorial notebooks run shell commands and declare a Bash
# kernel, which is not part of the base image.
RUN python3 -m bash_kernel.install --user

# -----------------------------------------------------------
# 4. Entrypoint: starts JupyterLab
# -----------------------------------------------------------
WORKDIR /home/jovyan/work

# Copy the entrypoint script
COPY --chown=jovyan:users entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

EXPOSE 8888

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

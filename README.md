# dickmanken-scatac-2026-repro
Reproducibility of Dickmänken et al. (2026) - Nature Communications "Evaluating single-cell ATAC-seq atlasing technologies using sequence-to-function modeling" DOI: 10.1038/s41467-026-68742-4  Dockerized pipeline with JupyterLab: from 10x scATAC-seq FASTQ to microglia-specific FIRE enhancer visualization.

## Overview

This repository provides a fully containerized pipeline to reproduce the analysis of the FIRE enhancer (a microglia-specific regulatory element) from the 10x Genomics scATAC-seq dataset (mouse motor cortex).

The pipeline processes raw FASTQ files from the 8k mouse cortex ATAC v2 sample, runs the PUMATAC preprocessing workflow, performs cisTopic topic modeling (LDA), generates pseudobulk BigWig tracks, and visualizes the FIRE enhancer in IGV.

All software dependencies are fixed to exact versions inside a Docker container, ensuring full reproducibility.

---

## Requirements

- Docker (>= 20.10)
- Docker Compose (>= 2.0, the "docker compose" plugin - not the legacy "docker-compose" v1 binary)
- Disk space: ~40 GB (38 GB compressed tar + FASTQ files after extraction)
- RAM: >= 32 GB recommended (LDA step is memory-intensive)
- Internet connection: Required for data download (~38 GB)

---

## Quick start

### 1. Clone the repository

    git clone https://github.com/BioinformaticsgoldStandard/dickmanken-scatac-2026-repro.git
    cd dickmanken-scatac-2026-repro

### 2. Build and start the container

    docker compose build
    docker compose up -d

The first build may take several minutes as it downloads the base image and installs all dependencies.

### 3. Access JupyterLab

Open your browser and navigate to http://localhost:8888 . The working directory is /home/jovyan/work and already contains the repository files.

### 4. Download data and notebooks

Inside JupyterLab, open and run notebooks/notebooks_and_data.ipynb . This notebook:

- Downloads the 8k mouse cortex ATAC v2 FASTQ files (~38 GB) from 10x Genomics
- Fetches the PUMATAC analysis notebooks
- Performs MD5 integrity check on downloaded data

Temporary extraction requires ~40 GB free disk space. After download completes, the raw data resides in data/ and the notebooks are ready to use.

### 5. Execute the analysis

Run the following notebooks in numerical order. Each notebook is self-contained and can be executed cell-by-cell.

| Notebook                                    | Purpose                                                    |
|---------------------------------------------|------------------------------------------------------------|
| notebooks/01_PUMATAC.ipynb                  | PUMATAC preprocessing (Nextflow, alignment, peak calling)  |
| notebooks/02_Downstream_analysis.ipynb      | cisTopic LDA topic modelling, pseudobulk BigWig generation |
| notebooks/03_Downstream_clustering.ipynb    | Dimensionality reduction and clustering                    |
| notebooks/04_Visualization.ipynb            | FIRE enhancer visualisation in IGV and matplotlib          |

All results are written to the results/ directory.

---

## Repository structure

    dickmanken-scatac-2026-repro/
    +-- Dockerfile                         Container definition (system + Python dependencies)
    +-- docker-compose.yml                 Docker Compose service configuration
    +-- entrypoint.sh                      Startup script (JupyterLab)
    +-- README.md                          This file
    +-- LICENSE                            MIT License
    +-- .gitignore                         Excludes data/, downloaded notebooks, etc.
    +-- notebooks/                         Jupyter notebooks for data download and analysis
    |   +-- notebooks_and_data.ipynb       Orchestration: downloads PUMATAC tutorial + FASTQ data
    |   +-- notebooks_PUMATAC/             PUMATAC tutorial notebooks (downloaded, not versioned;
    |   |                                  only .gitkeep is tracked - see scripts/download_notebooks.py)
    |   +-- 01_PUMATAC.ipynb               PUMATAC preprocessing (Nextflow, alignment, peak calling)
    |   +-- 02_Downstream_analysis.ipynb   cisTopic LDA topic modelling, pseudobulk BigWig generation
    |   +-- 03_Downstream_clustering.ipynb Dimensionality reduction and clustering
    |   +-- 04_Visualization.ipynb         FIRE enhancer visualisation in IGV and matplotlib
    +-- scripts/                           Helper scripts
    |   +-- download_data.py               Downloads FASTQ data, with MD5 check
    |   +-- download_notebooks.py          Downloads PUMATAC tutorial notebooks (pinned commit)
    |   +-- patch_notebooks.py             Applies documented patches to the downloaded notebooks
    +-- data/                              Raw and intermediate data (created at runtime, not versioned)
    +-- results/                           Output directory (created at runtime)

---

## Container architecture

The container is built on the official jupyter/datascience-notebook:python-3.11 image and includes:

- System tools: Java, samtools, bedtools, bwa, picard, Apptainer, Nextflow (all pinned to fixed versions, see table below - except samtools/bedtools/bwa/picard, see note).
- Apptainer (not Docker-in-Docker): Nextflow pipeline processes run via Apptainer, not via a nested Docker daemon. This avoids running the container with privileged: true, which would be problematic on a shared, multi-user host.
- Minimal added privileges: running Apptainer unprivileged inside Docker requires two narrow security_opt relaxations (seccomp:unconfined, systempaths:unconfined) instead of full privileged: true - see Apptainer's own documentation (https://apptainer.org/docs/admin/main/installation.html) for details. The container otherwise runs as the non-root jovyan user throughout.
- Volume mount: The entire repository is mounted at /home/jovyan/work, making all files accessible inside JupyterLab.
- Port: 8888 is exposed for the JupyterLab web interface.

### A note on where the pipeline actually runs

This Docker+Apptainer container is the reference environment for reproducibility: anyone can clone this repository and run the full analysis on their own machine with Docker installed, exactly as described in this README.

For this specific reproduction, the heavy computation (PUMATAC preprocessing) was run on a shared university JupyterHub server instead, where Docker access is not available to individual users (JupyterHub itself runs each user's session inside its own container, via DockerSpawner, without access to the host's Docker daemon). Apptainer was installed natively there (via conda, pinned to the same version used in this Docker image) to run the pipeline directly, without going through this container. This is functionally equivalent - the same PUMATAC pipeline, the same Apptainer version, the same singularity Nextflow profile - just without an extra layer of Docker around it on that specific machine.

---

## Fixed package versions

All software versions are explicitly pinned in the Dockerfile, with one exception noted below. Key components:

| Package / Software       | Version (or commit)          |
|--------------------------|------------------------------|
| Python                   | 3.11                         |
| Apptainer                | 1.4.5                        |
| Nextflow                 | 21.04.3 (pinned to match PUMATAC's own nextflowVersion requirement) |
| pycisTopic               | commit 53fe3f7 (bug-fix)     |
| PUMATAC                  | v0.0.1                       |
| deepTools                | 3.5.3                        |
| pyBigWig                 | 0.3.25                       |
| pandas                   | 2.0.3                        |
| numpy                    | 1.24.3                       |
| matplotlib               | 3.7.2                        |
| seaborn                  | 0.12.2                       |
| scikit-learn             | 1.3.0                        |
| MACS2                    | 2.2.9.1                      |
| palettable               | 3.3.3                        |
| jupyter-black            | 0.4.0                        |
| samtools                 | not pinned - see note        |
| bedtools                 | not pinned - see note        |
| bwa                      | not pinned - see note        |
| picard                   | not pinned - see note        |

Note on samtools/bedtools/bwa/picard: these are currently installed via apt-get install without an explicit version pin, so the exact version depends on the Ubuntu package repository state at build time. This is a known deviation from the "pin everything" principle followed elsewhere in this project, to be addressed in a future revision.

Note on palettable and jupyter-black: these are dependencies of pypumatac.py (a helper module used by the downloaded PUMATAC tutorial notebooks), not of the core reproduction pipeline itself.

### A note on notebook kernels

The downloaded PUMATAC tutorial notebooks assume Jupyter kernels that do not exist in this project: a "bash" kernel for 1_write_metadata.ipynb (should be Python, since it imports pandas/pypumatac), and a kernel built from a Singularity image specific to the original authors' VSC cluster for 5_qc_diagnosis.ipynb. scripts/patch_notebooks.py automatically repoints both notebooks to the standard "python3" kernel, into which pycisTopic and its dependencies are installed directly (no dedicated kernel or sys.path workaround needed). 2_running_nextflow_pipeline.ipynb is correctly left on the "bash" kernel, since it runs shell/Nextflow commands rather than Python.

A full frozen list of Python packages is available inside the container (requirements.txt).

---

## Useful commands

| Action                                     | Command                                                                 |
|--------------------------------------------|-------------------------------------------------------------------------|
| Check if container is running              | docker ps                                                               |
| View container logs                        | docker logs scatac-repro                                               |
| Open a shell inside the container          | docker exec -it scatac-repro /bin/bash                                 |
| Stop the container                         | docker compose down                                                    |
| Restart the container                      | docker compose up -d                                                   |
| Rebuild the image after Dockerfile changes | docker compose build --no-cache && docker compose up -d                |

---

## Expected result

Successful execution produces:

- Pseudobulk BigWig tracks for each identified cell cluster.
- UMAP and clustering plots that clearly separate microglia from other cell types.
- FIRE enhancer visualisation: The region chr18:61,108,475-61,108,975 (mm10) shows a strong, microglia-specific ATAC-seq peak, while other clusters exhibit no signal. This replicates the finding of Dickmänken et al. (2026) that the FIRE enhancer is a robust microglia-specific regulatory element.

Figures and IGV snapshots are saved under results/.

---

## Important notes

- Chromosome naming: PUMATAC uses Ensembl-style names (1, 2, ..., MT); IGV expects chr-prefixed names (chr1, chr2, ..., chrM). The visualisation notebook handles this conversion automatically.
- Genome annotation: The TSS annotation corresponds to mm10 (GRCm38); do not substitute mm39.
- Memory: The LDA step in cisTopic requires at least 32 GB RAM. Reduce the number of topics or increase Docker's memory allocation if the kernel crashes.
- Nextflow executor: For this reproduction, the pipeline was run on a shared university server. Resources are limited to those allocated on that machine (see "Container architecture" above for details on where the pipeline actually runs).

---

## Reproducibility status

| Component                   | Status                                                |
|------------------------------|-------------------------------------------------------|
| Data download                | Reproducible (fixed 10x Genomics URL)                  |
| Data integrity (MD5)         | Verified (checksum 6dc98e7d...)                        |
| PUMATAC preprocessing        | Reproducible (version v0.0.1)                          |
| cisTopic LDA                 | Reproducible (pycisTopic commit 53fe3f7)                |
| Clustering & visualisation   | Reproducible (fixed random seed, pinned dependencies)   |
| BigWig generation            | Reproducible (deepTools 3.5.3)                          |
| FIRE enhancer visualisation  | Reproducible                                            |

---

## References

- Dickmänken, S. et al. (2026). "Evaluating single-cell ATAC-seq atlasing technologies using sequence-to-function modeling", Nature Communications. DOI: 10.1038/s41467-026-68742-4 (https://doi.org/10.1038/s41467-026-68742-4)
- 10x Genomics dataset: 8k adult mouse cortex ATAC v2 (https://www.10xgenomics.com/datasets/8k-adult-mouse-cortex-atac-v2-1-standard-2-0-0)
- PUMATAC: https://github.com/aertslab/PUMATAC
- pycisTopic: https://github.com/aertslab/pycisTopic (commit 53fe3f7)

---

## License

This project is licensed under the MIT License. See LICENSE for the full text.

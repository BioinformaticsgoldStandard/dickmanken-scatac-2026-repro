# dickmanken-scatac-2026-repro
Reproducibility of Dickmänken et al. (2026) - Nature Communications "Evaluating single-cell ATAC-seq atlasing technologies using sequence-to-function modeling" DOI: 10.1038/s41467-026-68742-4  Dockerized pipeline with JupyterLab: from 10x scATAC-seq FASTQ to microglia-specific FIRE enhancer visualization.

## Overview

This repository provides a fully containerized pipeline to reproduce the analysis of the **FIRE enhancer** (a microglia-specific regulatory element) from the 10x Genomics scATAC-seq dataset (mouse motor cortex).

The pipeline processes raw FASTQ files from the **8k mouse cortex ATAC v2** sample, runs the **PUMATAC** preprocessing workflow, performs **cisTopic** topic modeling (LDA), generates **pseudobulk BigWig** tracks, and visualizes the **FIRE enhancer** in IGV.

All software dependencies are fixed to exact versions inside a **Docker container**, ensuring full reproducibility.

---

## Requirements

- **Docker** (≥ 20.10)
- **Docker Compose** (≥ 1.29)
- **Disk space:** ~2.1 GB for compressed data (temporary extraction requires ~40 GB)
- **RAM:** ≥ 32 GB recommended (LDA step is memory-intensive)
- **Internet connection:** Required for data download (~2.1 GB)

---

## Quick start

### 1. Clone the repository

```bash
git clone https://github.com/bioinformaticsgoldstandard/dickmanken-scatac-2026-repro.git
cd dickmanken-scatac-2026-repro
```

### 2. Build and start the container

```bash
docker-compose build
docker-compose up -d
```

The first build may take several minutes as it downloads the base image and installs all dependencies.

### 3. Access JupyterLab

Open your browser and navigate to [http://localhost:8888](http://localhost:8888). The working directory is `/home/jovyan/work` and already contains the repository files.

Retrieve the JupyterLab token (if required) with:

```bash
docker logs $(docker ps -q -f "name=dickmanken") 2>&1 | grep "token="
```

### 4. Download data and notebooks

Inside JupyterLab, open and run **`notebooks/notebooks_and_data.ipynb`**. This notebook:

- Downloads the **8k mouse cortex ATAC v2** FASTQ files (~2.1 GB) from 10x Genomics
- Fetches the PUMATAC analysis notebooks
- Performs MD5 integrity check on downloaded data

Temporary extraction requires **~40 GB** free disk space. After download completes, the raw data resides in `data/` and the notebooks are ready to use.

### 5. Execute the analysis

Run the following notebooks in numerical order. Each notebook is self-contained and can be executed cell‑by‑cell.

| Notebook                                    | Purpose                                                    |
|---------------------------------------------|------------------------------------------------------------|
| `notebooks/01_PUMATAC.ipynb`                | PUMATAC preprocessing (Nextflow, alignment, peak calling)  |
| `notebooks/02_Downstream_analysis.ipynb`    | cisTopic LDA topic modelling, pseudobulk BigWig generation |
| `notebooks/03_Downstream_clustering.ipynb`  | Dimensionality reduction and clustering                    |
| `notebooks/04_Visualization.ipynb`          | FIRE enhancer visualisation in IGV and matplotlib          |

All results are written to the `results/` directory.

---

## Repository structure

```
dickmanken-scatac-2026-repro/
├── Dockerfile                   # Container definition (system + Python dependencies)
├── docker-compose.yml           # Docker Compose service configuration
├── entrypoint.sh                # Startup script (Docker daemon + JupyterLab)
├── README.md                    # This file
├── LICENSE                      # MIT License
├── notebooks/                   # Jupyter notebooks for data download and analysis
│   ├── notebooks_and_data.ipynb # Data download + MD5 verification
│   ├── 01_PUMATAC.ipynb
│   ├── 02_Downstream_analysis.ipynb
│   ├── 03_Downstream_clustering.ipynb
│   └── 04_Visualization.ipynb
├── scripts/                     # Helper scripts
│   ├── download_data.py         # Download script with MD5 check
│   └── download_notebooks.py
├── data/                        # Raw and intermediate data (created at runtime)
└── results/                     # Output directory (created at runtime)
```

---

## Container architecture

The container is built on the official **`jupyter/datascience-notebook:python-3.11`** image and includes:

- **System tools:** Java, samtools, bedtools, bwa, picard (all with fixed versions)
- **Docker‑in‑Docker (DinD):** Docker Engine is installed inside the container. The `entrypoint.sh` script starts `dockerd` as root, enabling Nextflow pipelines to spawn Docker containers internally.
- **Privileged mode:** `docker-compose.yml` uses `privileged: true` and `user: root` to allow Docker daemon operation. After daemon initialisation, JupyterLab runs as the non‑root `jovyan` user.
- **Volume mount:** The entire repository is mounted at `/home/jovyan/work`, making all files accessible inside JupyterLab.
- **Port:** 8888 is exposed for the JupyterLab web interface.

This design completely isolates the analysis environment from the host, guaranteeing full reproducibility.

---

## Fixed package versions

All software versions are explicitly pinned in the Dockerfile. Key components:

| Package / Software       | Version (or commit)          |
|--------------------------|------------------------------|
| Python                   | 3.11                         |
| pycisTopic               | commit `53fe3f7` (bug‑fix)   |
| PUMATAC                  | v0.0.1                       |
| Nextflow                 | 23.04.4                      |
| deepTools                | 3.5.1                        |
| pyBigWig                 | 0.3.22                       |
| pandas                   | 2.1.4                        |
| numpy                    | 1.26.4                       |
| matplotlib               | 3.8.2                        |
| seaborn                  | 0.13.0                       |
| scikit-learn             | 1.3.2                        |
| MACS2                    | 2.2.7.1                      |
| samtools                 | 1.15                         |
| bedtools                 | 2.30.0                       |
| bwa                      | 0.7.17                       |
| picard                   | 2.26.10                      |

A full frozen list of Python packages is available inside the container (`requirements.txt`).

---

## Useful commands

| Action                                     | Command                                                                 |
|--------------------------------------------|-------------------------------------------------------------------------|
| Check if container is running              | `docker ps`                                                             |
| View container logs                        | `docker logs <container_id>`                                            |
| Show JupyterLab token                      | `docker logs <container_id> 2>&1 \| grep "token="`                     |
| Open a shell inside the container          | `docker exec -it <container_id> /bin/bash`                             |
| Stop the container                         | `docker-compose down`                                                   |
| Restart the container                      | `docker-compose up -d`                                                  |
| Rebuild the image after Dockerfile changes | `docker-compose build --no-cache && docker-compose up -d`               |

Replace `<container_id>` with the actual ID from `docker ps`.

---

## Expected result

Successful execution produces:

- **Pseudobulk BigWig tracks** for each identified cell cluster.
- **UMAP and clustering plots** that clearly separate microglia from other cell types.
- **FIRE enhancer visualisation:** The region **chr18:61,108,475–61,108,975** (mm10) shows a strong, microglia‑specific ATAC‑seq peak, while other clusters exhibit no signal. This replicates the finding of Dickmänken et al. (2026) that the FIRE enhancer is a robust microglia‑specific regulatory element.

Figures and IGV snapshots are saved under `results/`.

---

## Important notes

- **Chromosome naming:** PUMATAC uses Ensembl‑style names (`1`, `2`, …, `MT`); IGV expects `chr`‑prefixed names (`chr1`, `chr2`, …, `chrM`). The visualisation notebook handles this conversion automatically.
- **Genome annotation:** The TSS annotation corresponds to **mm10 (GRCm38)**; do not substitute mm39.
- **Memory:** The LDA step in cisTopic requires at least 32 GB RAM. Reduce the number of topics or increase Docker's memory allocation if the kernel crashes.
- **Nextflow executor:** The pipeline runs locally inside the container (no HPC scheduler required). Resources are limited to those available in the DinD environment.

---

## Reproducibility status

| Component                  | Status                                      |
|----------------------------|---------------------------------------------|
| Data download              | ✅ Reproducible (fixed 10x Genomics URL)     |
| Data integrity (MD5)       | ✅ Verified (checksum 6dc98e7d…)             |
| PUMATAC preprocessing      | ✅ Reproducible (version v0.0.1)             |
| cisTopic LDA               | ✅ Reproducible (pycisTopic commit 53fe3f7)  |
| Clustering & visualisation | ✅ Reproducible (fixed random seed, pinned dependencies) |
| BigWig generation          | ✅ Reproducible (deepTools 3.5.1)            |
| FIRE enhancer visualisation | ✅ Reproducible                              |

---

## References

- Dickmänken, S. et al. (2026). ‘Evaluating single-cell ATAC-seq atlasing technologies using sequence-to-function modeling’, *Nature Communications*. DOI: [10.1038/s41467-026-68742-4](https://doi.org/10.1038/s41467-026-68742-4)
- 10x Genomics dataset: [8k adult mouse cortex ATAC v2](https://www.10xgenomics.com/datasets/8k-adult-mouse-cortex-atac-v2-1-standard-2-0-0)
- PUMATAC: [https://github.com/aertslab/PUMATAC](https://github.com/aertslab/PUMATAC)
- pycisTopic: [https://github.com/aertslab/pycisTopic](https://github.com/aertslab/pycisTopic) (commit `53fe3f7`)

---

## License

This project is licensed under the **MIT License**. See `LICENSE` for the full text.

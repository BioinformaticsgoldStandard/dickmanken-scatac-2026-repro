# dickmanken-scatac-2026-repro

Reproduction of the FIRE enhancer analysis from Dickmänken et al. (2026), Nature Communications, "Evaluating single-cell ATAC-seq atlasing technologies using sequence-to-function modeling", DOI: 10.1038/s41467-026-68742-4.

Containerised pipeline, from raw 10x scATAC-seq FASTQ files to the microglia-specific accessibility of the FIRE enhancer.

## Overview

FIRE (Fms intronic regulatory element) is an enhancer in the first intron of Csf1r, specifically accessible in microglia. Figure 3b of the paper shows its cell-type-specific accessibility across scATAC-seq platforms. This repository reproduces that result independently, starting from the public 10x Genomics sample used by the authors.

The pipeline runs PUMATAC preprocessing (barcode correction, trimming, alignment, fragment generation), builds a cisTopic object, performs topic modelling with LDA, clusters and annotates cell types, generates per-cell-type pseudobulk tracks and peaks, and compares the result against the tracks and regions published by the authors.

Sample: 8k adult mouse cortex, ATAC v2, Chromium Controller (10x Genomics, public).

## Results

The microglia-specific accessibility of the FIRE enhancer is reproduced. Mean accessibility within chr18:61,108,475-61,108,975:

| Cell type          | Mean accessibility |
|--------------------|--------------------|
| Microglia          | 8.13               |
| Astrocytes         | 0.39               |
| Endothelial        | 0.34               |
| Excitatory neurons | 0.24               |
| Inhibitory neurons | 0.19               |
| Oligodendrocytes   | 0.04               |
| OPC                | 0.00               |

Quantitative agreement with the tracks published by the authors for the same platform (Spearman, candidate regulatory regions): astrocytes 0.98, microglia 0.94, oligodendrocytes 0.93, OPC 0.93, endothelial 0.84. Each cell type correlates with its published counterpart far more than with any other type, and hierarchical clustering pairs them without using the labels.

89% of the microglia peaks called here fall within the microglia-derived consensus regions published by the authors.

## Requirements

- Docker (>= 20.10) and the `docker compose` plugin (>= 2.0, not the legacy `docker-compose` v1 binary)
- Disk space: **~150 GB**. Roughly 38 GB for the FASTQ archive, a similar amount once extracted, ~21 GB for the PUMATAC reference dependencies, and the rest for fragments, pseudobulk tracks and intermediate Nextflow files
- RAM: 32 GB minimum, 64 GB or more recommended. The LDA step is the most memory-intensive
- Time: the full pipeline takes on the order of 15 hours of compute, dominated by PUMATAC preprocessing (~5 h) and LDA (~6 h). See "Execution order" for a breakdown
- Internet connection for the initial downloads

## Quick start

Clone the repository:

    git clone https://github.com/BioinformaticsgoldStandard/dickmanken-scatac-2026-repro.git
    cd dickmanken-scatac-2026-repro

Build and start the container:

    docker compose build
    docker compose up -d

Open JupyterLab at http://localhost:8888 . The repository is mounted at `/home/jovyan/work`.

Then follow the execution order below.

## Execution order

Notebooks from the PUMATAC tutorial keep the numbering given by their authors (0 to 5) and live in `notebooks/notebooks_PUMATAC/`. They are downloaded at setup and patched automatically, and are not versioned here. Notebooks written for this project start at 10 and live in `notebooks/`.

### Setup

**`notebooks/notebooks_and_data.ipynb`** — downloads the PUMATAC tutorial notebooks, applies the patches described below, then downloads and verifies the FASTQ archive (~38 GB, MD5-checked). Around 1 hour, mostly download.

### Preprocessing

**`notebooks/notebooks_PUMATAC/0_resources.ipynb`** (Bash kernel) — verifies that PUMATAC is installed at the pinned version and downloads the reference dependencies (genome index, blacklists, whitelists, ~21 GB) into `/home/jovyan/work/PUMATAC_dependencies`, outside the repository. Only the first two cells and the download cell are relevant; the rest documents how the authors built resources for other species and can be skipped.

**`notebooks/notebooks_PUMATAC/1_write_metadata.ipynb`** (Python kernel) — generates `metadata.tsv`, listing the FASTQ files and the barcode chemistry. Seconds.

**`notebooks/notebooks_PUMATAC/2_running_nextflow_pipeline.ipynb`** (Bash kernel) — generates the Nextflow config and runs the pipeline. **Skip section 2, "Edit the .config file"**: those cells contain Nextflow config syntax inside Bash cells and are documentation, not executable code. Their content is applied automatically through `config/nextflow_override.config`. Around 5 hours.

Notebooks 3 and 4 of the tutorial are marked optional by their authors and do not apply here: notebook 3 is for Bio-Rad ddSEQ samples, notebook 4 for BAM-level analyses such as freemuxlet. Notebook 5 targets an earlier pycisTopic API and is replaced by `10_qc.ipynb`.

### Analysis

**`notebooks/10_qc.ipynb`** — quality control on the fragments: TSS enrichment, FRIP, duplication rate, insert size distribution, and Otsu thresholding to select real cells. Around 1 hour.

**`notebooks/11_cistopic_lda.ipynb`** — builds the cisTopic object and trains LDA models with 10 to 50 topics. Around 7 hours.

**Restart the kernel before continuing.** Ray, used internally by the LDA step, and numba, used by UMAP's nearest-neighbour routines, cannot both be initialised in the same kernel session: running UMAP after the LDA raises a numba `TypingError` during compilation.

**`notebooks/12_clustering.ipynb`** — Leiden clustering, UMAP and t-SNE, and cell type annotation from canonical cortical markers. Around 30 minutes, dominated by accessibility imputation.

**`notebooks/13_pseudobulk_peaks.ipynb`** — per-cell-type pseudobulk BED and BigWig files, and MACS2 peak calling. Around 30 minutes.

**`notebooks/14_comparison.ipynb`** — genome-wide Spearman correlation against the tracks published by the authors. Around 30 minutes.

**`notebooks/15_fire_visualization.ipynb`** — accessibility tracks at the Csf1r locus and at the FIRE enhancer. Minutes.

**`notebooks/16_quantitative_validation.ipynb`** — bin-by-bin scatter of the microglia tracks, accessibility profile at the FIRE locus, correlation restricted to candidate regulatory regions, overlap with the published consensus regions, and comparison against the De Rop et al. 2023 scATAC-seq benchmark. Around 30 minutes.

Outputs are written to `results/`, which is not versioned.

## Repository structure

    dickmanken-scatac-2026-repro/
    +-- Dockerfile                          Container definition
    +-- docker-compose.yml                  Service configuration
    +-- entrypoint.sh                       Starts JupyterLab
    +-- config/
    |   +-- nextflow_override.config        Project-specific Nextflow settings
    +-- notebooks/
    |   +-- notebooks_and_data.ipynb        Setup: downloads notebooks and data
    |   +-- 10_qc.ipynb                     Quality control and cell selection
    |   +-- 11_cistopic_lda.ipynb           cisTopic object and topic modelling
    |   +-- 12_clustering.ipynb             Clustering and cell type annotation
    |   +-- 13_pseudobulk_peaks.ipynb       Pseudobulk tracks and peak calling
    |   +-- 14_comparison.ipynb             Correlation with published tracks
    |   +-- 15_fire_visualization.ipynb     FIRE enhancer accessibility tracks
    |   +-- 16_quantitative_validation.ipynb  Further quantitative comparisons
    |   +-- notebooks_PUMATAC/              Tutorial notebooks (downloaded, not versioned)
    +-- resources/
    |   +-- mm10_annotation.tsv             Verified TSS annotation
    |   +-- README.md                       Provenance and verification
    +-- scripts/
    |   +-- download_data.py                FASTQ download with MD5 check
    |   +-- download_notebooks.py           Tutorial notebooks, pinned commit
    |   +-- patch_notebooks.py              Patches applied to those notebooks
    |   +-- patch_pumatac_source.py         Patches applied to the PUMATAC source
    +-- data/                               Raw data (runtime, not versioned)
    +-- results/                            Outputs (runtime, not versioned)

`PUMATAC_dependencies/` holds around 21 GB of reference data and is downloaded at runtime to `/home/jovyan/work/PUMATAC_dependencies`. Inside the container that path is the repository root, since the repository is mounted there; it is excluded from version control.

## Container architecture

Built on `jupyter/datascience-notebook:python-3.11`.

Nextflow pipeline processes run through **Apptainer**, not through a nested Docker daemon. This avoids `privileged: true`, which would be a problem on a shared host. Running Apptainer unprivileged inside Docker requires two narrow `security_opt` relaxations, `seccomp:unconfined` and `systempaths=unconfined`, documented by Apptainer itself at https://apptainer.org/docs/admin/main/installation.html . The container otherwise runs as the non-root `jovyan` user.

The repository is mounted at `/home/jovyan/work` and port 8888 is exposed for JupyterLab.

### Where this reproduction was actually run

The container is the reference environment: anyone can clone this repository and run the analysis on a machine with Docker.

The reproduction itself was run on a shared university JupyterHub server, where individual users have no access to the host's Docker daemon, since JupyterHub spawns each session inside its own container. Apptainer was installed natively there, at the same version pinned in this image, and the pipeline was run directly. This is functionally equivalent: same PUMATAC version, same Apptainer version, same Nextflow `singularity` profile, without an extra layer of Docker.

## Patches applied to upstream code

PUMATAC v0.0.1 and its tutorial contain assumptions about the authors' own compute environment that prevent them from running elsewhere. Two scripts apply the necessary changes automatically, and both are safe to run more than once.

**`scripts/patch_notebooks.py`** rewrites cells in the downloaded tutorial notebooks: placeholder data paths, the VSC-specific Nextflow profile and scheduler, a separately downloaded Nextflow binary, a `git pull` that would move PUMATAC past its pinned tag, and the TSS annotation download. It also repoints two notebooks to the standard `python3` kernel: `1_write_metadata.ipynb` declares a Bash kernel although it imports pandas, and `5_qc_diagnosis.ipynb` declares a kernel built from a Singularity image on the authors' cluster. `2_running_nextflow_pipeline.ipynb` correctly keeps the Bash kernel.

**`scripts/patch_pumatac_source.py`** rewrites `${VSC_SCRATCH}` in PUMATAC's GATK process, an environment variable that only exists on the authors' cluster. It cannot be fixed from a config file: within a Nextflow script block the variable is resolved as a Groovy local, not as a parameter.

PUMATAC is also cloned into a directory named `ATACflow` rather than `PUMATAC`. Its own `src/utils/processes/config.nf` resolves internal config include paths by comparing the directory name against the string `"ATACflow"`, the project's former name. Using the name the tutorial itself instructs you to use makes that check take the wrong branch, and config resolution fails.

`config/nextflow_override.config` carries the settings that the tutorial presents as snippets to be copy-pasted by hand into the generated config file: genome index, barcode whitelist, local executor instead of PBS, bind mounts and cache directory.

## Fixed versions

| Component      | Version                                                     |
|----------------|-------------------------------------------------------------|
| Python         | 3.11                                                        |
| Apptainer      | 1.4.5                                                       |
| Nextflow       | 21.04.3, required by PUMATAC's own `nextflowVersion` setting |
| Java           | 11. Nextflow 21.04.3 rejects anything above 15               |
| PUMATAC        | v0.0.1                                                      |
| pycisTopic     | commit 53fe3f7                                              |
| MACS2          | 2.2.9.1                                                     |
| deepTools      | 3.5.3                                                       |
| pyBigWig       | 0.3.25                                                      |
| pandas         | 2.0.3                                                       |
| numpy          | 1.24.3                                                      |
| matplotlib     | 3.7.2                                                       |
| seaborn        | 0.12.2                                                      |
| scikit-learn   | 1.3.0                                                       |
| palettable     | 3.3.3                                                       |
| jupyter-black  | 0.4.0                                                       |

`samtools`, `bedtools`, `bwa` and `picard` are installed through `apt-get` without an explicit version pin, so their versions depend on the Ubuntu package repository at build time. This is a known deviation from the approach taken elsewhere in this project.

`palettable` and `jupyter-black` are dependencies of `pypumatac.py`, the helper module used by the tutorial notebooks, not of the analysis itself.

## Notes

**Chromosome naming.** Whether fragments carry a `chr` prefix depends on the reference genome used for alignment. In this run the main chromosomes are UCSC-style (`chr1`, `chrX`, `chrM`) while scaffolds keep GenBank names. A mismatch between fragments, annotation and regions does not raise an error: it silently produces empty results, which surface much later as an opaque failure. `10_qc.ipynb` therefore checks explicitly that the three inputs share chromosome names.

**Genome annotation.** The TSS annotation is mm10 (GRCm38). Querying Ensembl BioMart for mm10 can silently return GRCm39 coordinates, which produces a flat and meaningless TSS enrichment profile; a verified copy is versioned in `resources/`.

**Ray and shared memory.** Ray, used by pycisTopic for parallelism, stores objects in `/dev/shm`. Docker allocates 64 MB by default, which forces Ray to spill to disk and slows the LDA step considerably; `docker-compose.yml` therefore requests 16 GB. On a machine with less RAM, lower `shm_size` accordingly.

## References

- Dickmänken, H. et al. (2026). Evaluating single-cell ATAC-seq atlasing technologies using sequence-to-function modeling. *Nature Communications*. https://doi.org/10.1038/s41467-026-68742-4
- De Rop, F.V. et al. (2023). Systematic benchmarking of single-cell ATAC-sequencing protocols. *Nature Biotechnology*.
- 10x Genomics dataset: https://www.10xgenomics.com/datasets/8k-adult-mouse-cortex-cells-atac-v2-chromium-controller-2-standard
- PUMATAC: https://github.com/aertslab/PUMATAC
- pycisTopic: https://github.com/aertslab/pycisTopic
- Published tracks and consensus regions: https://ucsctracks.aertslab.org/papers/hydrop_v2_paper/ and https://zenodo.org/records/16569439

## License

MIT. See LICENSE.
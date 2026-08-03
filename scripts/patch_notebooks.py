#!/usr/bin/env python3
"""
Apply known, documented patches to the PUMATAC_tutorial notebooks after
they are (re-)downloaded by download_notebooks.py.

Why this exists: the notebooks in notebooks_PUMATAC/ are downloaded fresh
from https://github.com/aertslab/PUMATAC_tutorial on every run of the
setup notebook, so any manual edit made directly on those files would be
silently overwritten the next time someone (re)runs the setup. Patches
therefore live here instead, as code, so they are applied automatically,
consistently, and are visible in version control - each one documented
with what it changes and why, following the same "patch vs rewrite"
principle already used elsewhere in this project.

Each patch is idempotent: running it twice (e.g. because the setup
notebook is re-run) produces the same result and does not error out if
the target cell was already patched or is missing.
"""
import os
import sys

import nbformat

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
NOTEBOOKS_DIR = os.path.join(REPO_ROOT, "notebooks", "notebooks_PUMATAC")

# Marker used to recognize the original, unpatched cell we want to replace.
# Kept narrow and specific on purpose, to avoid accidentally matching an
# unrelated cell.
PUMATAC_CLONE_MARKER = "git clone https://github.com/aertslab/PUMATAC"

PUMATAC_CLONE_REPLACEMENT = '''# --- PATCHED by scripts/patch_notebooks.py ---
# Original cell cloned/pulled the PUMATAC repo directly into the notebook's
# working directory, with no pinned tag. This is redundant with, and can
# silently diverge from, the copy already pinned in the Docker image
# (Dockerfile: git clone --branch v0.0.1 .../PUMATAC.git /home/jovyan/PUMATAC).
# We verify the pre-installed copy instead of re-cloning.
PUMATAC_DIR="/home/jovyan/PUMATAC"

if [ ! -d "$PUMATAC_DIR" ]; then
    echo "ERROR: $PUMATAC_DIR not found. Expected PUMATAC to be pre-installed in the Docker image (see Dockerfile)."
    exit 1
fi

cd "$PUMATAC_DIR"
CURRENT_TAG=$(git describe --tags --exact-match 2>/dev/null || echo "unknown/detached")
echo "PUMATAC found at $PUMATAC_DIR, version: $CURRENT_TAG"

if [ "$CURRENT_TAG" != "v0.0.1" ]; then
    echo "WARNING: expected tag v0.0.1, found '$CURRENT_TAG'. Check the Dockerfile / image build."
fi

cd - > /dev/null
'''

# Marker used to recognize the placeholder fastq_dir in notebook 1
# (Case #1: standard bcl2fastq format filenames). Kept narrow to avoid
# accidentally matching the Case #2 cell later in the same notebook.
FASTQ_DIR_MARKER = 'fastq_dir = "10x_fastq/"'

FASTQ_DIR_REPLACEMENT = '''# --- PATCHED by scripts/patch_notebooks.py ---
# Original cell pointed to a placeholder directory ("10x_fastq/") that
# does not exist in this project. Point it to the real FASTQ location
# downloaded by scripts/download_data.py for the sample analyzed in this
# reproduction (8k mouse cortex ATAC v2). A relative path (anchored to the
# notebook's own location) is used instead of an absolute one, so this
# works both inside the Docker container (repo mounted at /home/jovyan/work)
# and when running natively on a server without that mount (repo cloned
# under an arbitrary path, e.g. ~/work/repo on the university JupyterHub).
fastq_dir = "../../data/10x_v2/8k_mouse_cortex_ATACv2_nextgem_Chromium_Controller_fastqs"
'''

# --- Notebook 2 (running_nextflow_pipeline) patches ---
# The original tutorial targets the VSC HPC cluster (PBS scheduler,
# lustre1/staging paths, a separately downloaded Nextflow binary). We
# replace these with: the system-wide pinned Nextflow (21.04.3, matching
# PUMATAC's own nextflowVersion constraint), the generic "singularity"
# profile instead of "vsc", and bind mounts/paths relevant to this project.

CELL7_MARKER = "chmod 755 PUMATAC_dependencies/nextflow/nextflow-22.10.7-all"
CELL7_REPLACEMENT = '''# --- PATCHED by scripts/patch_notebooks.py ---
# No longer needed: we use the system-wide Nextflow 21.04.3 (pinned in the
# Dockerfile / installed via conda), instead of downloading a separate
# binary here. This also resolves an inconsistency in the original
# tutorial, which used nextflow-22.10.7-all to generate the config but
# nextflow-21.04.3-all to actually run the pipeline.
echo "Skipped: using system-wide pinned Nextflow instead."
'''

CELL8_MARKER = "module load Java/17.0.2"
CELL8_REPLACEMENT = '''# --- PATCHED by scripts/patch_notebooks.py ---
# - Removed "module load": no environment module system here (not an HPC
#   cluster with Lmod); Java is already available system-wide.
# - Replaced the pinned nextflow-22.10.7-all binary with the system-wide
#   nextflow (21.04.3, matching the version PUMATAC's own nextflow.config
#   requires - see Dockerfile comment for details).
# - Replaced the "vsc" profile (VSC-cluster-specific: PBS scheduler, etc.)
#   with "singularity", PUMATAC's generic profile for running with
#   Apptainer/Singularity as the container engine, confirmed present in
#   PUMATAC/conf/singularity.config (pinned v0.0.1).
NXF_WORK=./work
[ ! -d $NXF_WORK ] && mkdir $NXF_WORK
nextflow config ./PUMATAC/main_atac.nf \\
    -profile atac_preprocess_rapid,singularity \\
    > atac_preprocess_rapid.config
'''

CELL21_MARKER = "runOptions = \'--cleanenv -H $PWD -B /lustre1"
CELL21_REPLACEMENT = '''# --- PATCHED by scripts/patch_notebooks.py ---
# Original bind mounts (/lustre1, /staging, ${VSC_SCRATCH}, ...) are
# specific to the VSC cluster filesystem layout and do not exist in this
# environment. Everything relevant here (repo files, FASTQ data,
# PUMATAC_dependencies) lives under /home/jovyan/work.
runOptions = \'--cleanenv -H $PWD -B /home/jovyan/work,${HOME}/.nextflow/assets/\'
'''

CELL23_MARKER = "cacheDir = \'PUMATAC_dependencies/cache\'"
CELL23_REPLACEMENT = '''# --- PATCHED by scripts/patch_notebooks.py ---
# Same relative path as the original - kept as-is since PUMATAC_dependencies
# already lives at this location relative to the working directory. No
# change needed beyond this comment documenting that it was checked.
cacheDir = \'PUMATAC_dependencies/cache\'
'''

CELL27_MARKER = "PUMATAC_dependencies/nextflow/nextflow-21.04.3-all -C"
CELL27_REPLACEMENT = '''# --- PATCHED by scripts/patch_notebooks.py ---
# Use the system-wide pinned Nextflow instead of a separately downloaded
# binary (see patch on the config-generation cell above for details).
nextflow -C atac_preprocess_rapid.config run PUMATAC/main_atac.nf -entry atac_preprocess_rapid
'''

NOTEBOOK0_KERNEL_MARKER = 'KERNEL_PATH=("/data2/florian'
NOTEBOOK0_KERNEL_REPLACEMENT = '''# --- PATCHED by scripts/patch_notebooks.py ---
# This section (and the following cells, up to "4. Example FASTQ") documents
# how the original authors built a dedicated Jupyter kernel from a
# Singularity image with pycisTopic pre-installed, using paths specific to
# their VSC cluster. This is not needed in this project: pycisTopic is
# installed directly into the same Python environment used by the standard
# "python3" Jupyter kernel (see Dockerfile, and scripts/patch_notebooks.py
# KERNEL_PATCHES), so no dedicated kernel is required. Notebooks that
# originally assumed the "cistopic_20230504" kernel (5_qc_diagnosis.ipynb)
# have been repointed to "python3" accordingly.
print("Skipped: no dedicated kernel needed, see comment above.")
'''

PUMATAC_UPDATE_MARKER = "cd PUMATAC && git pull && cd .."
PUMATAC_UPDATE_REPLACEMENT = '''# --- PATCHED by scripts/patch_notebooks.py ---
# Original cell ran "git pull" to update a PUMATAC copy located relative
# to the notebook's own directory. In this project, PUMATAC lives at a
# fixed absolute path (/home/jovyan/PUMATAC) and is pinned to tag v0.0.1
# (see Dockerfile) - running "git pull" there would silently move it past
# the pinned tag, breaking reproducibility. The version check already
# happens in 0_resources.ipynb (patched cell verifying the v0.0.1 tag).
echo "Skipped: PUMATAC version is pinned to v0.0.1, not updated here (see 0_resources.ipynb for the version check)."
'''

# List of (notebook filename, marker to find, replacement source) patches.
# Add new entries here as new incompatibilities are found, each with a
# comment explaining the reason - this list doubles as a changelog of
# deviations from the upstream PUMATAC_tutorial notebooks.
PATCHES = [
    (
        "0_resources.ipynb",
        PUMATAC_CLONE_MARKER,
        PUMATAC_CLONE_REPLACEMENT,
    ),
    (
        "1_write_metadata.ipynb",
        FASTQ_DIR_MARKER,
        FASTQ_DIR_REPLACEMENT,
    ),
    (
        "2_running_nextflow_pipeline.ipynb",
        CELL7_MARKER,
        CELL7_REPLACEMENT,
    ),
    (
        "2_running_nextflow_pipeline.ipynb",
        CELL8_MARKER,
        CELL8_REPLACEMENT,
    ),
    (
        "2_running_nextflow_pipeline.ipynb",
        CELL21_MARKER,
        CELL21_REPLACEMENT,
    ),
    (
        "2_running_nextflow_pipeline.ipynb",
        CELL23_MARKER,
        CELL23_REPLACEMENT,
    ),
    (
        "2_running_nextflow_pipeline.ipynb",
        CELL27_MARKER,
        CELL27_REPLACEMENT,
    ),
    (
        "0_resources.ipynb",
        NOTEBOOK0_KERNEL_MARKER,
        NOTEBOOK0_KERNEL_REPLACEMENT,
    ),
    (
        "2_running_nextflow_pipeline.ipynb",
        PUMATAC_UPDATE_MARKER,
        PUMATAC_UPDATE_REPLACEMENT,
    ),
]


def apply_patches():
    applied = 0
    skipped = 0

    for filename, marker, replacement in PATCHES:
        nb_path = os.path.join(NOTEBOOKS_DIR, filename)

        if not os.path.exists(nb_path):
            print(f"WARNING: {filename} not found in {NOTEBOOKS_DIR}, skipping this patch.")
            continue

        nb = nbformat.read(nb_path, as_version=4)
        patched_this_notebook = False

        for cell in nb.cells:
            if cell.cell_type != "code":
                continue
            # The marker is only present in the ORIGINAL, unpatched cell -
            # once patched, the cell contains the replacement instead, so we
            # separately recognize the "already patched" case by comparing
            # against the replacement text itself. Without this, re-running
            # this script on already-patched notebooks would find no marker
            # and, misleadingly, report zero patches applied AND zero
            # skipped, instead of correctly reporting them as up to date.
            # Check "already patched" FIRST, before checking for the marker.
            # Some replacements intentionally keep the original value
            # unchanged (only adding an explanatory comment above it), in
            # which case the marker text is still present inside the
            # replacement itself. Checking the marker first would then
            # always match and re-apply the patch on every run, instead of
            # correctly recognizing it as already up to date.
            if cell.source.strip() == replacement.strip():
                print(f"{filename}: cell already patched, nothing to do.")
                skipped += 1
            elif marker in cell.source:
                cell.source = replacement
                patched_this_notebook = True
                applied += 1
                print(f"{filename}: patched cell containing '{marker}'.")

        if patched_this_notebook:
            nbformat.write(nb, nb_path)

    print(f"\nPatches applied: {applied}, already up to date: {skipped}.")
    if applied == 0 and skipped == 0:
        print("WARNING: no patch targets were found. Check whether the upstream notebooks changed.")


# --- Kernel patches ---
# Separate from the cell-content patches above: these change a notebook's
# kernelspec metadata (which kernel it opens with), not a cell's source.
# The original tutorial notebooks assume kernels that do not exist in this
# project: "bash" for 1_write_metadata.ipynb (should be Python, since it
# imports pypumatac/pandas), and a VSC-cluster-specific Singularity kernel
# ("cistopic_20230504", built from a .sif image with a path only valid on
# the original authors' cluster) for 5_qc_diagnosis.ipynb. In this project,
# pycisTopic is installed directly into the same Python environment used by
# the standard "python3" Jupyter kernel (verified: the python3 kernel and
# the terminal's `python3` resolve to the same interpreter), so no dedicated
# kernel or sys.path workaround is needed - just pointing these notebooks at
# "python3" is sufficient. 2_running_nextflow_pipeline.ipynb is correctly
# left on "bash" (it runs shell/Nextflow commands, not Python).
KERNEL_PATCHES = [
    ("1_write_metadata.ipynb", "python3"),
    ("5_qc_diagnosis.ipynb", "python3"),
]

PYTHON3_KERNELSPEC = {
    "display_name": "Python 3 (ipykernel)",
    "language": "python",
    "name": "python3",
}


def apply_kernel_patches():
    applied = 0
    skipped = 0

    for filename, kernel_name in KERNEL_PATCHES:
        nb_path = os.path.join(NOTEBOOKS_DIR, filename)

        if not os.path.exists(nb_path):
            print(f"WARNING: {filename} not found in {NOTEBOOKS_DIR}, skipping kernel patch.")
            continue

        nb = nbformat.read(nb_path, as_version=4)
        current = nb.metadata.get("kernelspec", {}).get("name")

        if current == kernel_name:
            print(f"{filename}: kernel already set to '{kernel_name}', nothing to do.")
            skipped += 1
        else:
            nb.metadata["kernelspec"] = dict(PYTHON3_KERNELSPEC)
            nbformat.write(nb, nb_path)
            print(f"{filename}: kernel changed from '{current}' to '{kernel_name}'.")
            applied += 1

    print(f"\nKernel patches applied: {applied}, already up to date: {skipped}.")


if __name__ == "__main__":
    apply_patches()
    apply_kernel_patches()
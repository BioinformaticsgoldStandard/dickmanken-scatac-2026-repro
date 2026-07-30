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
            if cell.cell_type == "code" and marker in cell.source:
                if cell.source.strip() == replacement.strip():
                    print(f"{filename}: cell already patched, nothing to do.")
                    skipped += 1
                else:
                    cell.source = replacement
                    patched_this_notebook = True
                    applied += 1
                    print(f"{filename}: patched cell containing '{marker}'.")

        if patched_this_notebook:
            nbformat.write(nb, nb_path)

    print(f"\nPatches applied: {applied}, already up to date: {skipped}.")
    if applied == 0 and skipped == 0:
        print("WARNING: no patch targets were found. Check whether the upstream notebooks changed.")


if __name__ == "__main__":
    apply_patches()
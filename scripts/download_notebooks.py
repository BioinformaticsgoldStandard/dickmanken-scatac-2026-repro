#!/usr/bin/env python3
"""
Download notebooks from the PUMATAC tutorial fork.

The fork carries the changes needed to run the notebooks outside the
original authors' cluster. See its README_REPRO.md for what differs from
upstream and why.
This script clones that fork and copies all .ipynb
files, plus pypumatac.py (a helper module imported by several of the
tutorial notebooks), into notebooks/notebooks_PUMATAC/.
"""
import os
import shutil
import subprocess
import sys

# Fork of aertslab/PUMATAC_tutorial, adapted for this reproduction.
REPO_URL = "https://github.com/BioinformaticsgoldStandard/PUMATAC_tutorial.git"
# Pinned to a tag rather than a branch, so the notebooks stay fixed even if
# the fork is updated later. Based on upstream commit ace7c3c.
REPO_COMMIT = "v1-repro"
TEMP_DIR = "/tmp/pumatac_tutorial"


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
TARGET_DIR = os.path.join(REPO_ROOT, "notebooks", "notebooks_PUMATAC")


def download_notebooks():
    """Clone the PUMATAC tutorial repo and copy all notebook files."""

    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)

    os.makedirs(TARGET_DIR, exist_ok=True)

    print("=" * 60)
    print("Downloading notebooks from PUMATAC tutorial repository")
    print("=" * 60)
    print(f"Source: {REPO_URL}")
    print(f"Target: {TARGET_DIR}/")
    print("-" * 60)

    print("Cloning repository...")
    cmd = ["git", "clone", REPO_URL, TEMP_DIR]
    result = subprocess.run(cmd)

    if result.returncode != 0:
        print("ERROR: Failed to clone repository.")
        sys.exit(1)

    print(f"Checking out {REPO_COMMIT}...")
    cmd = ["git", "-C", TEMP_DIR, "checkout", REPO_COMMIT]
    result = subprocess.run(cmd)

    if result.returncode != 0:
        print(f"ERROR: Failed to checkout {REPO_COMMIT}.")
        sys.exit(1)

    # Files required to run the tutorial notebooks: the notebooks themselves,
    # plus pypumatac.py, a helper module that several notebooks import
    # directly (e.g. "import pypumatac as pum").
    FILES_TO_COPY = (".ipynb", "pypumatac.py")

    copied = 0
    for root, dirs, files in os.walk(TEMP_DIR):
        for file in files:
            if file.endswith(FILES_TO_COPY):
                src_path = os.path.join(root, file)
                dst_path = os.path.join(TARGET_DIR, file)
                shutil.copy2(src_path, dst_path)
                print(f"  Copied: {file}")
                copied += 1

    shutil.rmtree(TEMP_DIR)

    print("-" * 60)
    if copied == 0:
        print("WARNING: No notebooks found in the repository.")
        sys.exit(1)
    else:
        print(f"Successfully downloaded {copied} files.")
    print("=" * 60)


if __name__ == "__main__":
    download_notebooks()
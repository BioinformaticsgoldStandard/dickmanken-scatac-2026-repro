#!/usr/bin/env python3
"""
Download notebooks from the PUMATAC tutorial repository.
This script clones the PUMATAC_tutorial repository and copies all .ipynb
files, plus pypumatac.py (a helper module imported by several of the
tutorial notebooks), into notebooks/notebooks_PUMATAC/.
"""
import os
import shutil
import subprocess
import sys

# PUMATAC tutorial repository (the one you actually used)
REPO_URL = "https://github.com/aertslab/PUMATAC_tutorial.git"
# Pinned commit: the repo has no tagged releases, so we pin to a specific
# commit hash instead, to keep the downloaded notebooks' content stable
# over time (verified 2026-07-30).
REPO_COMMIT = "ace7c3c8264f6f51a43cc758ebfe0e1138325e0a"
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

    print(f"Checking out pinned commit {REPO_COMMIT}...")
    cmd = ["git", "-C", TEMP_DIR, "checkout", REPO_COMMIT]
    result = subprocess.run(cmd)

    if result.returncode != 0:
        print("ERROR: Failed to checkout pinned commit.")
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
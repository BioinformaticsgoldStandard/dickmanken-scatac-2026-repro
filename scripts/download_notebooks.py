#!/usr/bin/env python3
"""
Download notebooks from the PUMATAC tutorial repository.
This script clones the PUMATAC_tutorial repository and copies all .ipynb
files into notebooks/notebooks_PUMATAC/.
"""
import os
import shutil
import subprocess
import sys

# PUMATAC tutorial repository (the one you actually used)
REPO_URL = "https://github.com/aertslab/PUMATAC_tutorial.git"
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
    cmd = ["git", "clone", "--depth", "1", REPO_URL, TEMP_DIR]
    result = subprocess.run(cmd)

    if result.returncode != 0:
        print("ERROR: Failed to clone repository.")
        sys.exit(1)

    copied = 0
    for root, dirs, files in os.walk(TEMP_DIR):
        for file in files:
            if file.endswith(".ipynb"):
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
        print(f"Successfully downloaded {copied} notebooks.")
    print("=" * 60)


if __name__ == "__main__":
    download_notebooks()
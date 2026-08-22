#!/usr/bin/env python3
"""
Apply required patches to the PUMATAC source tree.

PUMATAC v0.0.1 contains references to the authors' own compute environment
that prevent it from running elsewhere. This script rewrites them in place.

Run after cloning PUMATAC and before running the pipeline. Running it twice
is safe: patches already applied are detected and skipped.
"""
import os
import sys

# PUMATAC must be cloned into a directory named "ATACflow": its own
# src/utils/processes/config.nf resolves internal config include paths by
# checking the directory name against that string, which is the project's
# former name.
PUMATAC_DIR = os.environ.get("PUMATAC_DIR", "/home/jovyan/ATACflow")

# Temporary directory passed to GATK. The original value is ${VSC_SCRATCH},
# an environment variable that only exists on the authors' cluster.
TMP_DIR = os.environ.get("PUMATAC_TMP_DIR", "/tmp")


# List of (relative file path, original text, replacement) patches.
# Add new entries here as further incompatibilities are found.
PATCHES = [
    (
        "src/gatk/processes/merge_sam_files.nf",
        "--TMP_DIR ${VSC_SCRATCH}/tmp",
        f"--TMP_DIR {TMP_DIR}",
    ),
]


def apply_patches():
    if not os.path.isdir(PUMATAC_DIR):
        print(f"ERROR: {PUMATAC_DIR} not found.")
        print("Set PUMATAC_DIR if PUMATAC is installed elsewhere.")
        sys.exit(1)

    applied = 0
    skipped = 0

    for rel_path, original, replacement in PATCHES:
        path = os.path.join(PUMATAC_DIR, rel_path)

        if not os.path.exists(path):
            print(f"WARNING: {rel_path} not found, skipping.")
            continue

        with open(path) as f:
            content = f.read()

        if original in content:
            count = content.count(original)
            content = content.replace(original, replacement)
            with open(path, "w") as f:
                f.write(content)
            print(f"{rel_path}: patched {count} occurrence(s).")
            applied += count
        elif replacement in content:
            print(f"{rel_path}: already patched, nothing to do.")
            skipped += 1
        else:
            print(f"WARNING: {rel_path}: neither original nor patched text found.")
            print("         The upstream source may have changed.")

    print(f"\nPatches applied: {applied}, already up to date: {skipped}.")


if __name__ == "__main__":
    apply_patches()

# scripts/download_data.py
"""
Download the 10x Genomics scATAC-seq dataset
(8k mouse cortex, ATAC v2, Chromium Controller, Cell Ranger ATAC 2.1.0),
verify integrity with MD5, and extract FASTQ files.

Dataset page (to manually verify official URL and MD5):
https://www.10xgenomics.com/datasets/8k-adult-mouse-cortex-cells-atac-v2-chromium-controller-2-standard
"""
import hashlib
import os
import sys
import tarfile
import urllib.request
import urllib.error

# Official URL, verified against the 10x Genomics dataset page (Cell Ranger ATAC 2.1.0)
DOWNLOAD_URL = (
    "https://cf.10xgenomics.com/samples/cell-atac/2.1.0/"
    "8k_mouse_cortex_ATACv2_nextgem_Chromium_Controller/"
    "8k_mouse_cortex_ATACv2_nextgem_Chromium_Controller_fastqs.tar"
)
FILENAME = "8k_mouse_cortex_ATACv2_nextgem_Chromium_Controller_fastqs.tar"

# Path anchored to the script's own location, not to the current working directory.
# This avoids the script behaving differently depending on where it is launched from.
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "..", "data", "10x_v2")

# MD5 checksum, manually verified against the 10x Genomics
# dataset page ("Input files" section) on 2026-07-24.
EXPECTED_MD5 = "6dc98e7dbb7f6369dd506b340feec9b6"


def md5(file_path):
    """Compute the MD5 hash of a file, reading it in chunks so the whole
    file (potentially several GB) is never loaded into memory at once."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def _print_progress(downloaded, total_size):
    """Print a download progress percentage on the same line."""
    if total_size <= 0:
        sys.stdout.write(f"\r  Downloaded: {downloaded / (1024**2):.1f} MB")
    else:
        percent = min(downloaded / total_size * 100, 100)
        sys.stdout.write(f"\r  Downloaded: {percent:5.1f}%")
    sys.stdout.flush()


def _download(file_path):
    print(f"Downloading {FILENAME} from 10x Genomics...")
    # 10x Genomics returns HTTP 403 Forbidden for requests without a
    # browser-like User-Agent header. urllib.request.urlretrieve() does not
    # allow setting custom headers, so we build the request manually with
    # Request + urlopen instead, and stream it to disk in chunks.
    req = urllib.request.Request(
        DOWNLOAD_URL,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            )
        },
    )
    try:
        with urllib.request.urlopen(req) as response:
            total_size = int(response.headers.get("Content-Length", 0))
            downloaded = 0
            chunk_size = 1024 * 1024  # 1 MB per chunk
            with open(file_path, "wb") as out_file:
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    out_file.write(chunk)
                    downloaded += len(chunk)
                    _print_progress(downloaded, total_size)
        print("\nDownload completed.")
    except (urllib.error.HTTPError, urllib.error.URLError) as e:
        # Remove any partial file, otherwise a re-run of the script would
        # wrongly assume the download had already completed.
        if os.path.exists(file_path):
            os.remove(file_path)
        print(f"\nDownload failed: {e}")
        print("Please download the file manually from:")
        print("https://www.10xgenomics.com/datasets/8k-adult-mouse-cortex-cells-atac-v2-chromium-controller-2-standard")
        print(f"and place it as '{file_path}' before re-running this script.")
        raise SystemExit(1)


def download_and_verify():
    os.makedirs(DATA_DIR, exist_ok=True)
    file_path = os.path.join(DATA_DIR, FILENAME)

    if os.path.exists(file_path):
        print(f"{FILENAME} already present, checking integrity before skipping download...")
        if md5(file_path) == EXPECTED_MD5:
            print("Existing file is valid, skipping download.")
        else:
            print("Existing file is corrupted or incomplete, re-downloading.")
            os.remove(file_path)
            _download(file_path)
    else:
        _download(file_path)

    # Final MD5 check (redundant if the existing file was already valid,
    # but necessary right after a fresh download)
    print("Verifying integrity with MD5...")
    actual_md5 = md5(file_path)
    if actual_md5 != EXPECTED_MD5:
        raise ValueError(
            f"MD5 mismatch!\nExpected: {EXPECTED_MD5}\nComputed:  {actual_md5}\n"
            "The downloaded file does not match the expected checksum: do NOT "
            "proceed with the analysis until this discrepancy is resolved."
        )
    print("MD5 verification passed.")

    # Extraction: use filter="data" to follow the newer Python security
    # guidelines (PEP 706) when available.
    print("Extracting FASTQ files...")
    with tarfile.open(file_path) as tar:
        try:
            tar.extractall(path=DATA_DIR, filter="data")
        except TypeError:
            # Python versions older than ~3.11.4 do not support the "filter" argument
            tar.extractall(path=DATA_DIR)
        member_names = tar.getnames()

    print("Extraction complete.")

    # Instead of assuming a fixed folder structure, infer the real path
    # from the names of the members that were just extracted.
    top_level_dirs = {name.split("/")[0] for name in member_names if "/" in name}
    if len(top_level_dirs) == 1:
        extracted_dir = os.path.join(DATA_DIR, top_level_dirs.pop())
        print(f"FASTQ files extracted to: {extracted_dir}")
        return extracted_dir
    else:
        print(
            "Warning: could not identify a single top-level folder in the "
            f"archive (found: {top_level_dirs}). "
            f"Please check the contents of {DATA_DIR} manually."
        )
        return DATA_DIR


if __name__ == "__main__":
    download_and_verify()
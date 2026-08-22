# Resources

Small, verified reference files versioned directly in this repository,
rather than downloaded at runtime.

## mm10_annotation.tsv

TSS annotation for mm10 (GRCm38), used by `notebooks/10_qc.ipynb` to
compute TSS enrichment.

MD5: 623be14601d7e22f170e712ac0608e06

### Why it is versioned here instead of downloaded

The upstream notebook fetches this annotation at runtime by querying
Ensembl BioMart (pypumatac.download_genome_annotation). That approach is
not reliable enough for this step, for two independent reasons:

1. Querying the jul2023 Ensembl archive for mm10 returns GRCm39/mm39
   coordinates instead, without raising any error. The mismatch is
   silent: the code runs and produces a TSS enrichment profile that is
   flat and biologically meaningless.
2. The BioMart server may return malformed XML, in which case pybiomart
   fails with "not well-formed (invalid token)".

Since correct TSS coordinates are essential for the TSS enrichment
metric, and this file is small (2.4 MB), it is versioned here as a
verified fixed input. This removes a fragile external dependency and
makes the QC step reproducible regardless of BioMart availability or
behaviour.

### Verification

Coordinates checked against a known reference: Actb at chr5:142,906,754
(mm10).

Chromosome names are chr-prefixed. Whether this matches the fragments
depends on the reference genome used for alignment, so `10_qc.ipynb`
converts the annotation to the naming convention found in the fragments
and checks explicitly that the two share chromosome names: a mismatch
does not raise an error but silently produces an empty TSS matrix.
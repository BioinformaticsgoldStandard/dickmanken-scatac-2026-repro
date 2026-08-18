# Resources

Small, verified reference files versioned directly in this repository,
rather than downloaded at runtime.

## mm10_annotation.tsv

TSS annotation for mm10 (GRCm38), used by the QC diagnosis notebook
(5_qc_diagnosis.ipynb) to compute TSS enrichment.

MD5: 623be14601d7e22f170e712ac0608e06

### Why it is versioned here instead of downloaded

The upstream notebook fetches this annotation at runtime by querying
Ensembl BioMart (pypumatac.download_genome_annotation). That approach
proved unreliable twice in this project:

1. Querying the jul2023 Ensembl archive for mm10 silently returned
   GRCm39/mm39 coordinates instead - a wrong result that does not raise
   any error, and is easy to miss.
2. On a later run the BioMart server returned malformed XML, making
   pybiomart fail with "not well-formed (invalid token)".

Since correct TSS coordinates are essential for the TSS enrichment
metric, and this file is small (2.4 MB), it is versioned here as a
verified fixed input. This removes a fragile external dependency and
makes the QC step reproducible regardless of BioMart availability or
behaviour.

### Verification

Coordinates checked against a known reference: Actb at chr5:142,906,754
(mm10). Note the chr-prefixed chromosome naming, which is what
pycisTopic expects for this annotation - unlike the fragments files
produced by PUMATAC, which use Ensembl-style names without the prefix.

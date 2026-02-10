# CLAUDE.md - CLAXBOI Project Guide

## Project Overview
**CLAXBOI** (Classification of X-ray sources using Naive Bayes Optimized Inference) is a probabilistic classification system for X-ray sources, developed as part of the XMM-Newton Source Catalog (5XMM) project. It implements the methodology from Tranin et al. (2022, A&A 657, 138).

**Repository:** https://github.com/mcoriat/classificationXray

## Architecture & Pipeline

The processing pipeline is sequential and modular:

```
INPUT CATALOG (FITS/CSV)
  → [1] auto_nway.py       — Multiwavelength cross-matching (Gaia, PanSTARRS, 2MASS, AllWISE)
  → [2] auto_xlinks.py     — X-ray variability across XMM/Chandra/Swift
  → [3] auto_gaiaglade.py  — Distance, proper motion, luminosity enrichment
  → [4] auto_classes.py    — Training sample identification via Vizier/Simbad
  → [5] classify_new.py    — Naive Bayes classification into 7 classes
```

**7 Classification Classes:** QSO/AGN, Star, Galactic XRB, CV, Nearby AGN, Extragalactic XRB, Extended

**Analysis Tools:** `plotdistrib.py`, `Pbatrack.py` (probability tracking), `randomforest.py` (experimental alternative)

## Directory Structure

```
classificationXray/
├── CLAUDE.md                  # This file
├── README.md                  # User documentation
├── claxboi/                   # Source code (9 Python modules, ~2300 LOC)
│   ├── configfile.ini         # Configuration (YAML-like format)
│   ├── auto_nway.py           # Step 1: multiwavelength cross-matching
│   ├── auto_xlinks.py         # Step 2: X-ray variability
│   ├── auto_gaiaglade.py      # Step 3: distance/luminosity enrichment
│   ├── auto_classes.py        # Step 4: training sample building
│   ├── classify_new.py        # Step 5: Naive Bayes classifier (main engine)
│   ├── makedistrib.py         # KDE probability distributions
│   ├── plotdistrib.py         # Distribution visualization
│   ├── Pbatrack.py            # Interactive probability tracking
│   └── randomforest.py        # Random Forest classifier (experimental)
└── data/                      # Sample FITS catalogs (~144 MB)
    ├── 2SXPSout.fits
    └── XMM10out.fits
```

## Dependencies

**Python:** >= 3.6
**Core packages:** astropy, numpy, scipy, pandas, scikit-learn, imbalanced-learn, matplotlib, pyyaml, tqdm
**External tools:** NWAY (Bayesian cross-matcher), STILTS (astronomical catalog tool)
**Platform:** Originally developed on Linux (Ubuntu); external tool calls use `subprocess.run()` with argument lists

## Configuration

Edit `claxboi/configfile.ini` before running. Key parameters:
- `filename` / `fileout`: input/output catalog paths
- `categories`: feature categories (location, spectrum, multiwavelength, variability)
- `global_coeffs`: weighting coefficients (first = missing value weight, rest = per-category)
- `classnames` / `trueprop`: class names and prior proportions (must sum to 1.0)

## Running the Pipeline

```bash
cd claxboi/
python3 auto_nway.py [input_catalog.fits]
python3 auto_xlinks.py
python3 auto_gaiaglade.py [catalog_with_counterparts.fits]
python3 auto_classes.py [catalog_with_counterparts_x.fits]
python3 classify_new.py [catalog_with_counterparts_x_loc_typ.fits]
```

## Key Code Patterns & Caveats

- **Config format** uses `.ini` extension but is parsed as YAML (not standard INI)
- **Classification loop** in classify_new.py is per-source Python loop (slow for large catalogs — vectorization would give ~100x speedup but requires careful validation)
- **All modules have `if __name__ == "__main__":` guards** — safe to import without triggering execution
- **External tools** (STILTS, NWAY) called via `subprocess.run()` with argument lists (no shell injection risk)

## Common Development Tasks

- **Adding a new class:** Update `classnames`, `trueprop` in configfile.ini; add Vizier catalogs in auto_classes.py `vizcat` dict; update class indices throughout
- **Adding a multiwavelength catalog:** Update `cds_tables`, `cds_cov`, `cds_ntot`, `cds_names` in auto_nway.py
- **Changing matching radius:** Modify the `radius` variable in auto_nway.py (units: arcseconds)

## Testing

No automated tests exist. Manual validation is done by:
1. Checking classification results against known sources
2. Using `Pbatrack.py` to inspect individual source probability tracks
3. Comparing with `randomforest.py` as an alternative classifier

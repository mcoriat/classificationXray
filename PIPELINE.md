# CLAXBOI Pipeline — 5XMM-DR15 Classification

Probabilistic X-ray source classification using Naive Bayes (Tranin et al. 2022).
Classifies sources into 7 classes: AGN, Star, galactic XRB, CV, background AGN,
extragalactic XRB, and extended sources.

## Prerequisites

| Tool | Purpose | Install |
|------|---------|---------|
| Python 3.9+ | Pipeline scripts | System or venv |
| Java 8+ | STILTS | `java -version` |
| [STILTS](http://www.star.bris.ac.uk/~mbt/stilts/) | Catalog cross-matching | On `$PATH` |
| [NWAY](https://github.com/JohannesBuchner/nway) | Bayesian positional matching | `pip install nway` |
| Python packages | See `requirements.txt` | `pip install -r requirements.txt` |

## Directory layout

```
classificationXray/
  data/                         Input reference data
    5XMM_DR15_stacked.fits        Full 5XMM-DR15 stacked catalogue (1.4 GB)
    GLADE2016_corrected_0123.fits GLADE galaxy catalogue (104 MB)
    XMM10out.fits                 XMM training data
    2SXPSout.fits                 Swift/2SXPS training data
  claxboi/                      Code and configuration
    configfile.ini                Pipeline configuration
    auto_nway.py                  Step 1 — multiwavelength cross-matching
    auto_xlinks.py                Step 2 — X-ray cross-linking (optional)
    auto_gaiaglade.py             Step 3 — GLADE + Gaia enrichment
    auto_classes.py               Step 4 — training sample identification
    classify_new_fast.py          Step 5 — Bayesian classification (vectorized)
    classify_new.py               Original classifier (kept for reference)
    add_descriptions_and_convert.py Step 6 — FITS conversion + metadata
    makedistrib.py                KDE distribution computation (called by step 5)
    plotdistrib.py                Distribution plotting
    Pbatrack.py                   Probability tracking utilities
    randomforest.py               Random Forest alternative classifier
    prepare_5xmm.py              Catalogue preparation helper
    intermediates/                Pipeline intermediate products
    nway_results/                 NWAY cross-match outputs (81 files)
    output/                       Final classification products
    classif/distrib_KDE_5XMM/     KDE probability distributions
```

---

## Step 0 — Prepare the input catalogue

**Goal:** Extract the stacked (unique source) rows from the raw 5XMM-DR15 catalogue.
The raw catalogue contains both stacked rows (one per unique source, with valid `N_OBS`)
and individual observation rows (with masked `N_OBS`). We keep only the stacked rows.

**Prerequisite:** The raw catalogue file, e.g. `xmmcat5xmmdr15_20260203.fits`.

### Commands

```bash
# Extract stacked rows (N_OBS is not null)
stilts tpipe \
  in=xmmcat5xmmdr15_20260203.fits \
  cmd='select "!NULL_N_OBS"' \
  out=data/5XMM_DR15_stacked.fits

# Reorder columns so SRCID comes first (required by NWAY)
stilts tpipe \
  in=data/5XMM_DR15_stacked.fits \
  cmd='addcol -before IAUNAME SRCID_FIRST SRCID' \
  cmd='delcols SRCID' \
  cmd='colmeta -name SRCID SRCID_FIRST' \
  out=data/5XMM_DR15_stacked.fits

# Replace NaN position errors with median value (NWAY crashes on NaN)
stilts tpipe \
  in=data/5XMM_DR15_stacked.fits \
  cmd='replaceval null 1.37 RADEC_ERR' \
  out=data/5XMM_DR15_stacked.fits
```

### Output
- `data/5XMM_DR15_stacked.fits` — 818,816 unique stacked sources, 352 columns, ~1.4 GB

### Runtime
~1 minute (STILTS, local)

---

## Step 1 — Multiwavelength cross-matching (NWAY)

**Goal:** Cross-match X-ray sources against 7 optical and infrared catalogues from CDS
using NWAY probabilistic Bayesian matching.

**Script:** `auto_nway.py`

**What it does:**
1. For each of 7 CDS catalogues (Gaia EDR3, PanSTARRS DR1, USNO-B1, DES DR1,
   2MASS, AllWISE, UnWISE):
   - Queries CDS Vizier via `stilts cdsskymatch` within 8 arcsec of each X-ray source
   - Calibrates photometric magnitudes to a common system (empirical linear fits)
   - Runs NWAY Bayesian matching with position error and magnitude bias
   - Computes false-positive cutoff using randomised (fake) positions
2. Combines best optical and best infrared counterpart per source
3. Resolves duplicates (keeps highest-probability match)

### Command

```bash
cd claxboi
python3 auto_nway.py
```

### Input
- `data/5XMM_DR15_stacked.fits`

### Output
- `intermediates/5XMM_with_counterparts.fits` — 818,815 rows, ~125 MB
  - Added columns: `RA_Opt`, `DEC_Opt`, `Bmag`, `Rmag`, `angdist_Opt`,
    `p_single_Opt`, `p_any_Opt`, `Ref_Opt`, `RA_IR`, `DEC_IR`, `W1mag`,
    `W2mag`, `angdist_IR`, `p_single_IR`, `p_any_IR`, `Ref_IR`
- `nway_results/` — All intermediate NWAY files (cross-match results,
  cutoff quality plots, magnitude fit parameters)

### External services
CDS Vizier (via STILTS `cdsskymatch`) — requires internet

### Runtime
**~2-6 hours** depending on network speed and CDS server load.
This is the slowest step. Run on a server if possible.

---

## Step 2 — X-ray cross-linking (SKIPPED for 5XMM)

**Script:** `auto_xlinks.py`

**Goal:** Cross-match with other X-ray catalogues (Swift/LSXPS, Chandra CSC2) to
identify common sources and compute flux variability ratios.

**Status:** Skipped for the 5XMM-DR15 run. The script is partially implemented
and requires external catalogue files not available for this run.

---

## Step 3 — GLADE galaxy association + Gaia enrichment

**Goal:** Associate X-ray sources with nearby galaxies (GLADE 2016), retrieve Gaia
proper motions and distances, and compute derived properties (luminosities,
multiwavelength flux ratios).

**Script:** `auto_gaiaglade.py`

**What it does:**
1. **GLADE galaxy matching** — `stilts tmatch2` sky-ellipse matcher (60 arcsec radius)
   matches X-ray sources to GLADE galaxies using their actual angular extent (R1, R2, PA)
2. **Galactic coordinates** — computes l, b from RA, DEC
3. **Gaia proper motions** — extracted from NWAY Gaia cross-match results
4. **Gaia distances** — queries CDS `I/352/gedr3dis` (Bailer-Jones+2021) via STILTS
5. **X-ray luminosities** — Lx_1 (from GLADE distance), Lx_2 (from Gaia distance)
6. **Flux ratios** — log(Fx/Fopt) and log(Fx/FIR) for each optical/IR band

### Command

```bash
cd claxboi
python3 auto_gaiaglade.py
```

### Input
- `intermediates/5XMM_with_counterparts.fits`
- `data/GLADE2016_corrected_0123.fits` (columns: RA, DEC, R1, R2, PA, Dist, ...)

### Output
- `intermediates/5XMM_with_counterparts_loc.fits` — ~234 MB
  - Added columns: `l`, `b`, `RA_GLADE`, `DEC_GLADE`, `R1`, `R2`, `PA`, `Dist`,
    `Separation_GLADE`, `SepToRadius`, `Lx_1`, `Lx_2`, `logFxFb`, `logFxFr`,
    `logFxFw1`, `logFxFw2`, `GAIA_pm`, `GAIA_Dist`

### External services
CDS Vizier (Gaia distances) — requires internet

### Runtime
~20-30 minutes

---

## Step 4 — Training sample identification

**Goal:** Identify known source types from Vizier catalogues and Simbad to build
the labelled training sample for classification.

**Script:** `auto_classes.py`

**What it does:**
1. Queries 14 Vizier catalogues and Simbad for known AGN, stars, XRBs, and CVs
   within 3 arcsec of each X-ray source
2. Assigns class labels based on matches:
   - 0 = AGN, 1 = Star, 2 = XRB, 3 = CV
   - 4 = background AGN (AGN inside a GLADE galaxy)
   - 5 = extragalactic XRB (XRB inside a GLADE galaxy)
   - 6 = extended source (EXTENT > 0)
   - NaN = unclassified (no match or ambiguous)
3. Sources matched to multiple conflicting types are set to NaN (ambiguous)

### Vizier catalogues queried

| Class | Catalogues |
|-------|-----------|
| AGN | Secrest+2015 (J/ApJS/221/12), Veron-Cetty+2010 (VII/258) |
| Star | ASCC-2.5 (I/280B) |
| XRB | Liu+2006/2007 LMXB/HMXB, Tetarenko+2016, Sazonov+2020, Walter+2015, ... |
| CV | Ritter+Downes (V/123A), Downes (B/cb) |
| All types | Simbad (main object type) |

### Command

```bash
cd claxboi
python3 auto_classes.py
```

### Input
- `intermediates/5XMM_with_counterparts_loc.fits`

### Output
- `intermediates/5XMM_with_counterparts_loc_typ.fits` — ~266 MB
  - Added columns: `isAGN`, `isStar`, `isXRB`, `isCV` (bit flags),
    `class` (integer label 0-6 or NaN)

### Training sample size (5XMM-DR15 run)
| Class | Label | Count |
|-------|-------|-------|
| AGN | 0 | 20,515 |
| Star | 1 | 7,948 |
| XRB | 2 | 109 |
| CV | 3 | 235 |
| bk_AGN | 4 | 647 |
| ext_xrb | 5 | 677 |
| Extended | 6 | 0 |
| Unclassified | NaN | 788,684 |

### External services
CDS Vizier + Simbad (via STILTS `cdsskymatch`) — requires internet

### Runtime
~30-45 minutes

---

## Step 5 — Bayesian classification

**Goal:** Classify all 818,815 sources using Naive Bayes with KDE-estimated
probability distributions, per-category weighting, and missing value handling.

**Script:** `classify_new_fast.py` (vectorized drop-in replacement for `classify_new.py`)

**What it does:**
1. **Direct FITS I/O** — reads the input FITS directly into numpy (no CSV roundtrip),
   merges hardness ratios and extent columns from the stacked catalogue in memory
2. **Property configuration** — reads the `.in` file defining which columns to use,
   their weights, categories, and scales
3. **KDE estimation** — computes probability density distributions for each
   property x class combination on the training sample (via `makedistrib.py`)
4. **Vectorized classification** — computes posterior probabilities
   P(class | properties) for all sources simultaneously using log-space matrix
   operations (replaces the per-source Python loop):
   - Per-property likelihoods interpolated from KDE curves
   - Auto-weights from measurement errors (1/sigma)
   - Category-level weighting (global_coeffs in configfile.ini)
   - Missing value probabilities (P(property exists | class))
   - Class priors (trueprop in configfile.ini)
5. **Output** — writes classified catalogue as FITS, CSV, and ECSV directly

### Properties used (5XMM-DR15 run)

| Property | Category | Scale | Description |
|----------|----------|-------|-------------|
| `b` | location | logit | Galactic latitude |
| `Lx_1` | location | log | X-ray luminosity (GLADE) |
| `Lx_2` | location | log | X-ray luminosity (Gaia) |
| `GAIA_pm` | location | log | Gaia proper motion |
| `EP_HR1-4` | spectrum | logit | EPIC hardness ratios |
| `logFxFb` | multiwavelength | linear | X-ray to B-band flux ratio |
| `logFxFr` | multiwavelength | linear | X-ray to R-band flux ratio |
| `logFxFw1` | multiwavelength | linear | X-ray to WISE W1 flux ratio |
| `logFxFw2` | multiwavelength | linear | X-ray to WISE W2 flux ratio |

### Configuration (configfile.ini)

```yaml
categories: ['location', 'spectrum', 'multiwavelength', 'variability']
global_coeffs: [0.0, 6.89, 0.59, 3.37, 0.03]
classnames: ['AGN','star','gal_xrb','CV','bk_AGN','ext_xrb','extended']
trueprop: [0.55, 0.20, 0.03, 0.02, 0.05, 0.05, 0.10]
```

### Command

```bash
cd claxboi
python3 classify_new_fast.py
```

### Input
- `intermediates/5XMM_with_counterparts_loc_typ.fits`
- `../data/5XMM_DR15_stacked.fits` (for hardness ratios + extent, merged automatically)
- `intermediates/5XMM_with_counterparts_loc_typ.in` (property config)

### Output
- `output/classification_5XMM_DR15.fits` — full table with input + classification columns
- `output/classification_5XMM_DR15.csv` — classification-only columns
- `output/classification_5XMM_DR15_with_input.csv` — full table in ECSV format
- `output/classification_5XMM_DR15.metrics` — performance metrics on training sample
- `classif/distrib_KDE_5XMM/*.dat` — KDE probability distributions (one per property)
- `classif/distrib_KDE_5XMM/*.png` — distribution plots

### Classification output columns

| Column | Description |
|--------|-------------|
| `prediction` | Predicted class index (0-6) |
| `prediction_name` | Predicted class name |
| `alt` | Alternative class if one property category is ignored |
| `ClMargin` | Classification margin: P(prediction) - P(not prediction) |
| `outlier` | Outlier measure (high = source lies in tails of all distributions) |
| `N_missing` | Number of properties with missing values |
| `PbaC0`-`PbaC6` | Posterior probability for each class (sum to 1) |
| `PbaC0_location`-`PbaC6_variability` | Per-category likelihoods per class |

### Runtime
**~1 minute** with precomputed distributions (`compute_distrib: 0`),
**~5-10 minutes** with KDE re-estimation (`compute_distrib: 1`).
Classification itself takes ~2 seconds for 818K sources.

---

## Step 6 — FITS conversion with metadata

**Goal:** Add column descriptions and units to the classification output,
convert to a proper FITS file readable by TOPCAT and other tools.

**Script:** `add_descriptions_and_convert.py`

**What it does:**
1. Reads the ECSV output from step 5
2. Adds units (deg, arcsec, erg/s, Mpc, ...) and descriptions to all 122 columns
3. Writes FITS with `TCOMMn` header keywords (readable by TOPCAT)

### Command

```bash
cd claxboi
python3 add_descriptions_and_convert.py
```

### Input
- `output/classification_5XMM_DR15_with_input.csv`

### Output
- `output/classification_5XMM_DR15_with_input.fits` — 122 columns, ~771 MB
  - All columns have descriptions (visible in TOPCAT column info)
  - Physical units on all applicable columns

### Runtime
~5 minutes

---

## Quick-start: full pipeline from scratch

```bash
# 0. Setup
cd classificationXray/claxboi

# 1. Prepare the stacked catalogue (see Step 0 for STILTS commands)

# 2. Cross-match with optical/IR catalogues (slow — run on server)
python3 auto_nway.py                    # ~2-6 hours

# 3. GLADE galaxy + Gaia enrichment
python3 auto_gaiaglade.py               # ~20-30 min

# 4. Training sample identification
python3 auto_classes.py                  # ~30-45 min

# 5. Bayesian classification (vectorized)
python3 classify_new_fast.py             # ~1-10 min

# 6. Add metadata and convert to FITS
python3 add_descriptions_and_convert.py  # ~5 min
```

**Total runtime: ~3-7 hours** (dominated by NWAY cross-matching)

### Final product
`output/classification_5XMM_DR15_with_input.fits`
— 818,815 sources, 122 columns, posterior probabilities for 7 classes.

---

## References

- Tranin et al. 2022, A&A, 657, A138 — CLAXBOI methodology
- Buchner et al. 2015, NWAY — Bayesian cross-matching
- Taylor 2006, STILTS — Starlink Tables Infrastructure
- Dalya et al. 2018, GLADE — Galaxy catalog for gravitational-wave research

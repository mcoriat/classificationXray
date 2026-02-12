#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extract stacked (unique source) rows from the 5XMM DR15 catalog.

The raw catalog contains one stacked row per source (with valid N_OBS,
empty OBS_ID) plus individual observation rows. This script extracts
only the stacked rows for use in the CLAXBOI classification pipeline.

Usage:
    python3 prepare_5xmm.py [input_catalog.fits]

Output:
    5XMM_DR15_stacked.fits in the current directory
"""

import sys
import numpy as np
from astropy.table import Table

# Input file
if len(sys.argv) > 1:
    input_fname = sys.argv[1]
else:
    input_fname = "/Users/mcoriat/Desktop/XMM-SSC/5XMM/ProtoCat/xmmcat5xmmdr15_20260203.fits"

output_fname = "5XMM_DR15_stacked.fits"

print(f"Reading {input_fname}...")
t = Table.read(input_fname)
print(f"  Total rows: {len(t)}")
print(f"  Total columns: {len(t.colnames)}")

# Stacked rows have valid (unmasked) N_OBS; observation rows have masked N_OBS
if hasattr(t['N_OBS'], 'mask'):
    stacked_mask = ~t['N_OBS'].mask
else:
    # Fallback: use the FITS integer null sentinel value
    stacked_mask = t['N_OBS'] != -2147483648
t_stacked = t[stacked_mask]

print(f"  Stacked rows (valid N_OBS): {len(t_stacked)}")
print(f"  Unique SRCIDs: {len(np.unique(t_stacked['SRCID']))}")

# Verify key columns exist
required_cols = ['IAUNAME', 'SRCID', 'RA', 'DEC', 'RADEC_ERR',
                 'EP_FLUX', 'EP_HR1', 'EP_HR2', 'EP_HR3', 'EP_HR4',
                 'LII', 'BII', 'EXTENT', 'VAR_PROB']
missing = [c for c in required_cols if c not in t_stacked.colnames]
if missing:
    print(f"  WARNING: Missing expected columns: {missing}")
else:
    print(f"  All required columns present.")

# Check RADEC_ERR validity
valid_err = ~np.isnan(t_stacked['RADEC_ERR']) & (t_stacked['RADEC_ERR'] > 0)
print(f"  Valid RADEC_ERR: {valid_err.sum()} / {len(t_stacked)}")

# Save
print(f"Writing {output_fname}...")
t_stacked.write(output_fname, overwrite=True)
print(f"Done. {len(t_stacked)} sources written to {output_fname}")

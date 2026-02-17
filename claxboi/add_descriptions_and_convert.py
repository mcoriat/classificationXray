#!/usr/bin/env python3
"""
Add column descriptions and units to classification_5XMM_DR15_with_input.csv
and convert to FITS format.

Descriptions for columns 1-5 sourced from 5XMM_DR15_stacked.fits,
descriptions for columns 6-81 sourced from classification_DR12_with_input.fits,
classification output columns (82+) already have descriptions in the ECSV.
"""

import os
from astropy.table import Table
from astropy.io import fits
import astropy.units as u

BASEDIR = os.path.dirname(os.path.abspath(__file__))

# --- Column metadata: (unit_string_or_None, description) ---
# Units use FITS-compatible strings

COLUMN_META = {
    # === Columns 1-5: from 5XMM_DR15_stacked.fits ===
    'SRCID':        (None,          'Unique source identifier in 5XMM-DR15'),
    'RA':           ('deg',         'Right ascension (J2000) of the stacked source'),
    'DEC':          ('deg',         'Declination (J2000) of the stacked source'),
    'RADEC_ERR':    ('arcsec',      'Combined statistical and systematic error on RA and DEC'),
    'EP_FLUX':      ('erg cm-2 s-1', 'All-EPIC mean integrated 0.2-12 keV flux'),

    # === Columns 6-13: Optical counterpart (from NWAY cross-match) ===
    'RA_Opt':       ('deg',         'Right ascension of optical counterpart'),
    'DEC_Opt':      ('deg',         'Declination of optical counterpart'),
    'angdist_Opt':  ('arcsec',      'Angular distance between X-ray source and optical counterpart'),
    'Bmag':         (None,          'B-band magnitude of optical counterpart'),
    'Rmag':         (None,          'R-band magnitude of optical counterpart'),
    'p_single_Opt': (None,          'NWAY probability of single optical match'),
    'p_any_Opt':    (None,          'NWAY probability of any optical match'),
    'Ref_Opt':      (None,          'Reference catalogue for optical counterpart'),

    # === Columns 14-21: IR counterpart (from NWAY cross-match) ===
    'RA_IR':        ('deg',         'Right ascension of infrared counterpart'),
    'DEC_IR':       ('deg',         'Declination of infrared counterpart'),
    'angdist_IR':   ('arcsec',      'Angular distance between X-ray source and IR counterpart'),
    'W1mag':        (None,          'WISE W1 (3.4 um) magnitude of IR counterpart'),
    'W2mag':        (None,          'WISE W2 (4.6 um) magnitude of IR counterpart'),
    'p_single_IR':  (None,          'NWAY probability of single IR match'),
    'p_any_IR':     (None,          'NWAY probability of any IR match'),
    'Ref_IR':       (None,          'Reference catalogue for IR counterpart'),

    # === Columns 22-23: Galactic coordinates ===
    'l':            ('deg',         'Galactic longitude'),
    'b':            ('deg',         'Galactic latitude'),

    # === Columns 24-31: GLADE galaxy association ===
    'RA_GLADE':         ('deg',     'Right ascension of associated GLADE galaxy'),
    'DEC_GLADE':        ('deg',     'Declination of associated GLADE galaxy'),
    'R1':               ('arcsec',  'Semi-major axis of associated GLADE galaxy'),
    'R2':               ('arcsec',  'Semi-minor axis of associated GLADE galaxy'),
    'PA':               ('deg',     'Position angle of associated GLADE galaxy'),
    'Dist':             ('Mpc',     'Distance to associated GLADE galaxy'),
    'Separation_GLADE': ('arcsec',  'Angular separation to associated GLADE galaxy'),
    'SepToRadius':      (None,      'Ratio of separation to galaxy optical radius'),

    # === Columns 32-36: Derived multiwavelength properties ===
    'Lx_1':     ('erg/s',  'X-ray luminosity from GLADE galaxy distance'),
    'logFxFb':  (None,     'Log10 of X-ray to B-band optical flux ratio'),
    'logFxFr':  (None,     'Log10 of X-ray to R-band optical flux ratio'),
    'logFxFw1': (None,     'Log10 of X-ray to WISE W1 flux ratio'),
    'logFxFw2': (None,     'Log10 of X-ray to WISE W2 flux ratio'),

    # === Columns 37-39: Gaia properties ===
    'GAIA_pm':   ('mas/yr', 'Gaia total proper motion'),
    'GAIA_Dist': ('pc',     'Distance estimate from Gaia parallax'),
    'Lx_2':      ('erg/s',  'X-ray luminosity from Gaia distance'),

    # === Columns 40-44: Training sample flags ===
    'isAGN':  (None, 'Flag: identified as AGN in training sample'),
    'isStar': (None, 'Flag: identified as star in training sample'),
    'isXRB':  (None, 'Flag: identified as X-ray binary in training sample'),
    'isCV':   (None, 'Flag: identified as cataclysmic variable in training sample'),
    'class':  (None, 'Training class label (0=AGN,1=star,2=XRB,3=CV,4=bk_AGN,5=ext_xrb,6=extended)'),

    # === Columns 45-49: Extent (from 5XMM_DR15_stacked.fits init) ===
    'EXTENT':        ('arcsec', 'Source extent radius'),
    'EXTENT_ERR':    ('arcsec', 'Statistical error on source extent'),
    'EXTENT_ERR_LO': ('arcsec', 'Lower confidence bound on source extent'),
    'EXTENT_ERR_UP': ('arcsec', 'Upper confidence bound on source extent'),
    'EXTENT_ML':     (None,     'Maximum likelihood of source extent'),

    # === Columns 50-57: EPIC combined hardness ratios ===
    'EP_HR1':     (None, 'EPIC hardness ratio between bands 1 and 2'),
    'EP_HR1_ERR': (None, 'Error on EPIC hardness ratio HR1'),
    'EP_HR2':     (None, 'EPIC hardness ratio between bands 2 and 3'),
    'EP_HR2_ERR': (None, 'Error on EPIC hardness ratio HR2'),
    'EP_HR3':     (None, 'EPIC hardness ratio between bands 3 and 4'),
    'EP_HR3_ERR': (None, 'Error on EPIC hardness ratio HR3'),
    'EP_HR4':     (None, 'EPIC hardness ratio between bands 4 and 5'),
    'EP_HR4_ERR': (None, 'Error on EPIC hardness ratio HR4'),

    # === Columns 58-65: PN hardness ratios ===
    'PN_HR1':     (None, 'PN hardness ratio between bands 1 and 2'),
    'PN_HR1_ERR': (None, 'Error on PN hardness ratio HR1'),
    'PN_HR2':     (None, 'PN hardness ratio between bands 2 and 3'),
    'PN_HR2_ERR': (None, 'Error on PN hardness ratio HR2'),
    'PN_HR3':     (None, 'PN hardness ratio between bands 3 and 4'),
    'PN_HR3_ERR': (None, 'Error on PN hardness ratio HR3'),
    'PN_HR4':     (None, 'PN hardness ratio between bands 4 and 5'),
    'PN_HR4_ERR': (None, 'Error on PN hardness ratio HR4'),

    # === Columns 66-73: MOS1 hardness ratios ===
    'M1_HR1':     (None, 'MOS1 hardness ratio between bands 1 and 2'),
    'M1_HR1_ERR': (None, 'Error on MOS1 hardness ratio HR1'),
    'M1_HR2':     (None, 'MOS1 hardness ratio between bands 2 and 3'),
    'M1_HR2_ERR': (None, 'Error on MOS1 hardness ratio HR2'),
    'M1_HR3':     (None, 'MOS1 hardness ratio between bands 3 and 4'),
    'M1_HR3_ERR': (None, 'Error on MOS1 hardness ratio HR3'),
    'M1_HR4':     (None, 'MOS1 hardness ratio between bands 4 and 5'),
    'M1_HR4_ERR': (None, 'Error on MOS1 hardness ratio HR4'),

    # === Columns 74-81: MOS2 hardness ratios ===
    'M2_HR1':     (None, 'MOS2 hardness ratio between bands 1 and 2'),
    'M2_HR1_ERR': (None, 'Error on MOS2 hardness ratio HR1'),
    'M2_HR2':     (None, 'MOS2 hardness ratio between bands 2 and 3'),
    'M2_HR2_ERR': (None, 'Error on MOS2 hardness ratio HR2'),
    'M2_HR3':     (None, 'MOS2 hardness ratio between bands 3 and 4'),
    'M2_HR3_ERR': (None, 'Error on MOS2 hardness ratio HR3'),
    'M2_HR4':     (None, 'MOS2 hardness ratio between bands 4 and 5'),
    'M2_HR4_ERR': (None, 'Error on MOS2 hardness ratio HR4'),

    # === Classification output columns (already have descriptions in ECSV,
    #     but we add them here too for completeness / in case they are missing) ===
    'prediction_name': (None, 'Name of the predicted class'),
    'prediction':      (None, 'Output class, given by the classification'),
    'alt':             (None, 'Alternative classifications if a property category is ignored'),
    'ClMargin':        (None, 'Classification margin, i.e. P(prediction)-P(not(prediction))'),
    'outlier':         (None, 'Outlier measure'),
    'N_missing':       (None, 'Number of fields having a missing value'),
}

# Add PbaC0-6 descriptions
CLASS_NAMES = ['AGN', 'star', 'gal_xrb', 'CV', 'bk_AGN', 'ext_xrb', 'extended']
for i, cn in enumerate(CLASS_NAMES):
    COLUMN_META[f'PbaC{i}'] = (None, f'Posterior probability that the source is {cn}')

# Add per-category likelihoods
CATEGORIES = ['location', 'spectrum', 'multiwavelength', 'variability']
for cat in CATEGORIES:
    for i, cn in enumerate(CLASS_NAMES):
        COLUMN_META[f'PbaC{i}_{cat}'] = (None, f'Combined likelihood of {cat} properties for the class {cn}')


def main():
    csv_path = os.path.join(BASEDIR, 'output', 'classification_5XMM_DR15_with_input.csv')
    fits_path = os.path.join(BASEDIR, 'output', 'classification_5XMM_DR15_with_input.fits')

    print(f'Reading {csv_path} ...')
    t = Table.read(csv_path, format='ascii.ecsv')
    print(f'  -> {len(t)} rows, {len(t.colnames)} columns')

    # Apply units and descriptions
    n_desc = 0
    n_unit = 0
    missing = []
    for col in t.colnames:
        if col in COLUMN_META:
            unit_str, desc = COLUMN_META[col]
            # Set description
            if desc:
                t[col].description = desc
                n_desc += 1
            # Set unit
            if unit_str:
                t[col].unit = unit_str
                n_unit += 1
        else:
            missing.append(col)

    print(f'  -> Set {n_desc} descriptions, {n_unit} units')
    if missing:
        print(f'  -> WARNING: no metadata for columns: {missing}')

    print(f'Writing {fits_path} ...')
    t.write(fits_path, format='fits', overwrite=True)

    # Post-process: inject descriptions as TCOMMn keywords (read by TOPCAT)
    # and as TTYPE comments in the FITS header
    print('Adding descriptions to FITS header (TCOMMn + TTYPE comments) ...')
    with fits.open(fits_path, mode='update') as hdu:
        header = hdu[1].header
        ncols = header.get('TFIELDS', 0)
        for i in range(1, ncols + 1):
            colname = header.get(f'TTYPE{i}', '')
            if colname in COLUMN_META:
                _, desc = COLUMN_META[colname]
                if desc:
                    header[f'TCOMM{i}'] = desc
                    header.comments[f'TTYPE{i}'] = desc
        hdu.flush()
    print('Done.')

    # Quick verification
    with fits.open(fits_path) as hdu:
        header = hdu[1].header
        nrows = header.get('NAXIS2', 0)
        ncols = header.get('TFIELDS', 0)
        print(f'\nVerification: {nrows} rows, {ncols} columns')
        print('\nFirst 10 columns:')
        for i in range(1, min(11, ncols+1)):
            ttype = header.get(f'TTYPE{i}', '')
            tunit = header.get(f'TUNIT{i}', '')
            tcomm = header.get(f'TCOMM{i}', '')
            print(f'  {i:3d}: {ttype:25s} unit={tunit:15s} TCOMM="{tcomm}"')
        print('\nClassification columns (sample):')
        for i in range(82, min(95, ncols+1)):
            ttype = header.get(f'TTYPE{i}', '')
            tunit = header.get(f'TUNIT{i}', '')
            tcomm = header.get(f'TCOMM{i}', '')
            print(f'  {i:3d}: {ttype:25s} unit={tunit:15s} TCOMM="{tcomm}"')


if __name__ == '__main__':
    main()

# EODP-TS-ISM
# Runs the Instrument Module on the test scene, cross-validates with the
# reference outputs and generates the figures and tables of the report.

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'common'))
from harness_utils import *

from ism.src.ism import ism

TEST = 'EODP-TS-ISM'
INDIR = os.path.join(DATA, TEST, 'input', 'gradient_alt100_act150')
REFDIR = os.path.join(DATA, TEST, 'output')

# TOA outputs and MTFs to cross-validate
TOA_PREFIXES = ['ism_toa_isrf_', 'ism_toa_optical_', 'ism_toa_e_', 'ism_toa_prnu_',
                'ism_toa_ds_', 'ism_toa_detection_', 'ism_toa_']
MTF_PREFIXES = ['Hdiff_', 'Hdefoc_', 'Hwfe_', 'Hdet_', 'Hsmear_', 'Hmotion_', 'Hsys_']


def runIsm(dirs, logger):
    logger.info('Running the ISM. Input ' + INDIR)
    myIsm = ism(AUX, INDIR, dirs['output'])
    myIsm.processModule()
    moduleDone(logger, dirs, dirs['output'], 'ISM')
    return myIsm.ismConfig


def crossValidation(dirs, logger):
    rows_toa = crossValidate(REFDIR, dirs['output'], TOA_PREFIXES, logger)
    rows_mtf = crossValidate(REFDIR, dirs['output'], MTF_PREFIXES, logger)
    writeTables(rows_toa, 'ism_crossval_toa', 'ISM cross-validation of the TOA outputs. Maximum relative difference [\\%] per band.')
    writeTables(rows_mtf, 'ism_crossval_mtf', 'ISM cross-validation of the MTFs. Maximum relative difference [\\%] per band.')
    ok = all(r[3] for r in rows_toa + rows_mtf)
    logger.info('ISM cross-validation ' + ('PASSED' if ok else 'FAILED'))
    return ok


if __name__ == '__main__':
    dirs = testDirs(TEST)
    logger = harnessLogger(dirs, TEST)
    conf = runIsm(dirs, logger)
    crossValidation(dirs, logger)
    logger.info('End of ' + TEST)

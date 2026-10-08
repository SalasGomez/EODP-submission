# EODP-TS-L1B
# Runs the L1B with and without equalization, cross-validates with the
# reference outputs and generates the calibration plot.

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'common'))
from harness_utils import *

from l1b.src.l1b import l1b

TEST = 'EODP-TS-L1B'
INDIR = os.path.join(DATA, TEST, 'input')
REFDIR = os.path.join(DATA, TEST, 'output')


def runL1b(dirs, logger, equalization):
    '''
    Runs the L1B. Outputs in output/eq or output/noeq
    '''
    outdir = os.path.join(dirs['output'], 'eq' if equalization else 'noeq')
    logger.info('Running the L1B with do_equalization=' + str(equalization))
    myL1b = l1b(AUX, INDIR, outdir)
    myL1b.l1bConfig.do_equalization = equalization
    myL1b.processModule()
    moduleDone(logger, dirs, outdir, 'L1B')
    if not equalization:
        os.replace(os.path.join(dirs['log'], 'L1B.log'), os.path.join(dirs['log'], 'L1B_noeq.log'))
    return outdir


def crossValidation(dirs, eqdir, logger):
    rows = crossValidate(REFDIR, eqdir, ['l1b_toa_eq_', 'l1b_toa_'], logger)
    writeTables(rows, 'l1b_crossval', 'L1B cross-validation with equalization. Maximum relative difference [\\%] per band.')
    ok = all(r[3] for r in rows)
    logger.info('L1B cross-validation ' + ('PASSED' if ok else 'FAILED'))
    return ok


def calibrationPlot(dirs, eqdir, noeqdir, logger):
    '''
    Central line: ISRF TOA (truth) vs L1B without and with equalization.
    Also the relative error with respect to the truth and the saturation.
    '''
    rows = []
    fig, axs = plt.subplots(2, 2, figsize=(14, 10))
    for ax, band in zip(axs.flatten(), BANDS):
        truth = readVar(os.path.join(INDIR, 'ism_toa_isrf_' + band + '.nc'))
        noeq = readVar(os.path.join(noeqdir, 'l1b_toa_' + band + '.nc'))
        eq = readVar(os.path.join(eqdir, 'l1b_toa_' + band + '.nc'))
        dn = readVar(os.path.join(INDIR, 'ism_toa_' + band + '.nc'))
        ialt = int(truth.shape[0] / 2)

        ax.plot(truth[ialt, :], '-k', linewidth=2, label='TOA after ISRF (truth)')
        ax.plot(noeq[ialt, :], '-r', label='L1B without equalization')
        ax.plot(eq[ialt, :], '-b', label='L1B with equalization')
        ax.set_title('Central ALT line ' + str(ialt) + ', ' + band)
        ax.set_xlabel('ACT pixel [-]')
        ax.set_ylabel(r'TOA [mW/m$^2$/sr]')
        ax.grid(True)

        # Errors on the non saturated pixels, without the MTF edge columns
        ok = dn < 4095
        ok[:, :2] = False
        ok[:, -2:] = False
        err_noeq = np.mean(np.abs(noeq[ok] - truth[ok]) / truth[ok]) * 100
        err_eq = np.mean(np.abs(eq[ok] - truth[ok]) / truth[ok]) * 100
        sat = np.mean(dn >= 4095) * 100
        rows.append((band, err_noeq, err_eq, sat))
        logger.info('%s mean rel error vs truth: no eq %.3f %%, eq %.3f %%. Saturated pixels %.1f %%' %
                    (band, err_noeq, err_eq, sat))
    axs[0, 0].legend(loc='upper left', fontsize=11)
    saveFig(fig, dirs, 'l1b_calibration')

    with open(os.path.join(REPORT, 'tables', 'l1b_errors.tex'), 'w') as fid:
        fid.write('\\begin{tabular}{lccc}\n\\toprule\n')
        fid.write('Band & Error without eq. [\\%] & Error with eq. [\\%] & Saturated pixels [\\%] \\\\\n\\midrule\n')
        for r in rows:
            fid.write('%s & %.3f & %.3f & %.1f \\\\\n' % r)
        fid.write('\\bottomrule\n\\end{tabular}\n')


if __name__ == '__main__':
    dirs = testDirs(TEST)
    logger = harnessLogger(dirs, TEST)
    noeqdir = runL1b(dirs, logger, False)
    eqdir = runL1b(dirs, logger, True)
    crossValidation(dirs, eqdir, logger)
    calibrationPlot(dirs, eqdir, noeqdir, logger)
    logger.info('End of ' + TEST)

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


MTF_LABELS = ['Diffraction', 'Defocus', 'WFE aberrations', 'Detector', 'Smearing', 'Motion blur', 'System']
MTF_STYLES = [('b', '-'), ('g', '--'), ('c', '-'), ('m', '-'), ('orange', '-.'), ('k', ':'), ('r', '-')]


def mtfCuts(H):
    '''
    Frequencies and central cuts ACT/ALT from 0 to Nyquist
    '''
    nlines, ncols = H[0].shape
    fnAct = np.arange(-ncols / 2, ncols / 2) / ncols
    fnAlt = np.arange(-nlines / 2, nlines / 2) / nlines
    ialt, iact = int(nlines / 2), int(ncols / 2)
    act = (fnAct[iact:], [h[ialt, iact:] for h in H])
    alt = (fnAlt[ialt:], [h[ialt:, iact] for h in H])
    return act, alt


def plotMtfs(dirs, conf, logger):
    '''
    ACT and ALT cuts of all the MTF contributors and the system MTF
    '''
    nyq = []
    for band in BANDS:
        H = [readVar(os.path.join(dirs['output'], p + band + '.nc')) for p in MTF_PREFIXES]
        act, alt = mtfCuts(H)

        fig, axs = plt.subplots(1, 2, figsize=(14, 6))
        for ax, (fn, Hs), cut in zip(axs, [act, alt], ['ACT', 'ALT']):
            for h, lab, (col, ls) in zip(Hs, MTF_LABELS, MTF_STYLES):
                ax.plot(fn, h, color=col, linestyle=ls, linewidth=2.5 if lab == 'System' else 1.5, label=lab)
            ax.axvline(0.5, color='k', linestyle='--', linewidth=1)
            ax.text(0.49, 0.03, 'Nyquist', rotation=90, ha='right')
            ax.set_xlim(0, 0.52)
            ax.set_ylim(0, 1.05)
            ax.set_title('MTF cut ' + cut + ', ' + band)
            ax.set_xlabel(r'Normalised frequency $f/(1/w)$ [-]')
            ax.set_ylabel('MTF [-]')
            ax.grid(True)
        axs[0].legend(loc='lower left', fontsize=11)
        saveFig(fig, dirs, 'ism_mtf_' + band)

        # MTF values at the last sample before Nyquist, ACT and ALT
        nyq.append(([h[-1] for h in act[1]], [h[-1] for h in alt[1]]))
    logger.info('MTF figures saved')
    return nyq


def mtfNyquistTable(nyq, logger):
    '''
    MTF of each contributor at the last sample before Nyquist (ACT and ALT)
    '''
    with open(os.path.join(REPORT, 'tables', 'ism_mtf_nyquist.tex'), 'w') as fid:
        fid.write('\\begin{tabular}{l' + 'cc' * len(BANDS) + '}\n\\toprule\n')
        fid.write(' & ' + ' & '.join('\\multicolumn{2}{c}{' + b + '}' for b in BANDS) + ' \\\\\n')
        fid.write('MTF' + ' & ACT & ALT' * len(BANDS) + ' \\\\\n\\midrule\n')
        for i, lab in enumerate(MTF_LABELS):
            vals = []
            for b in range(len(BANDS)):
                vals += ['%.3f' % nyq[b][0][i], '%.3f' % nyq[b][1][i]]
            fid.write(lab + ' & ' + ' & '.join(vals) + ' \\\\\n')
        fid.write('\\bottomrule\n\\end{tabular}\n')
    for b, band in enumerate(BANDS):
        for c, cut in enumerate(['ACT', 'ALT']):
            vals = nyq[b][c]
            imin = int(np.argmin(vals[:-1]))
            logger.info('%s %s: lowest contributor at Nyquist is %s (%.4f). System %.4f' %
                        (band, cut, MTF_LABELS[imin], vals[imin], vals[-1]))


if __name__ == '__main__':
    dirs = testDirs(TEST)
    logger = harnessLogger(dirs, TEST)
    conf = runIsm(dirs, logger)
    crossValidation(dirs, logger)
    nyq = plotMtfs(dirs, conf, logger)
    mtfNyquistTable(nyq, logger)
    logger.info('End of ' + TEST)

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


STEPS = [r'Radiance $\rightarrow$ irradiance', r'Irradiance $\rightarrow$ photons', r'Photons $\rightarrow$ electrons',
         r'Electrons $\rightarrow$ volts', r'Volts $\rightarrow$ DN']
STEP_UNITS = [r'[sr]', r'[ph m$^2$/mW]', r'[e$^-$/ph]', r'[V/e$^-$]', r'[DN/V]']


def conversionFactors(conf, band):
    '''
    Scalar factor of each unit conversion step for a band
    '''
    h = 6.62607004e-34 # [J s] same as auxiliary/constants.py
    c = 299792458      # [m/s]
    wv = conf.wv[int(band[-1])]
    f_irr = conf.Tr * np.pi / 4 * (conf.D / conf.f) ** 2
    f_ph = 1e-3 * conf.pix_size ** 2 * conf.t_int * wv / (h * c)
    f_e = conf.QE
    f_v = conf.OCF * conf.ADC_gain
    f_dn = (2 ** conf.bit_depth - 1) / (conf.max_voltage - conf.min_voltage)
    return [f_irr, f_ph, f_e, f_v, f_dn]


def unitConversion(dirs, conf, logger):
    '''
    Analytic unit conversion at the central pixel of ism_toa_isrf,
    compared with the saved electrons (ism_toa_e) and DN (ism_toa)
    '''
    rows = []
    for band in BANDS:
        isrf = readVar(os.path.join(dirs['output'], 'ism_toa_isrf_' + band + '.nc'))
        ialt, iact = int(isrf.shape[0] / 2), int(isrf.shape[1] / 2)
        L = float(isrf[ialt, iact])
        f = conversionFactors(conf, band)

        # Analytic chain from the radiance
        e_an = L * f[0] * f[1] * f[2]
        dn_an = np.round(e_an * f[3] * f[4])

        # Saved outputs at the same pixel
        e_sv = float(readVar(os.path.join(dirs['output'], 'ism_toa_e_' + band + '.nc'))[ialt, iact])
        dn_sv = float(readVar(os.path.join(dirs['output'], 'ism_toa_' + band + '.nc'))[ialt, iact])

        # Same chain starting after the MTF and after the detection effects
        opt = float(readVar(os.path.join(dirs['output'], 'ism_toa_optical_' + band + '.nc'))[ialt, iact])
        det = float(readVar(os.path.join(dirs['output'], 'ism_toa_detection_' + band + '.nc'))[ialt, iact])
        e_opt = opt * f[1] * f[2]
        dn_det = min(np.round(det * f[3] * f[4]), 2 ** conf.bit_depth - 1)

        rows.append(dict(band=band, L=L, f=f, e_an=e_an, e_sv=e_sv, e_opt=e_opt,
                         dn_an=dn_an, dn_sv=dn_sv, dn_det=dn_det, opt=opt, det=det))
        logger.info('%s pixel [%d,%d] L=%.4f e: analytic %.2f saved %.2f (from optical %.2f). '
                    'DN: analytic %.0f saved %.0f (from detection %.0f)' %
                    (band, ialt, iact, L, e_an, e_sv, e_opt, dn_an, dn_sv, dn_det))
    writeUnitTables(rows)
    return rows


def writeUnitTables(rows):
    '''
    LaTeX tables of the factors and the comparison with the outputs
    '''
    # Factors, the two largest per band in bold
    with open(os.path.join(REPORT, 'tables', 'ism_units_factors.tex'), 'w') as fid:
        fid.write('\\begin{tabular}{ll' + 'c' * len(BANDS) + '}\n\\toprule\n')
        fid.write('Step & Units & ' + ' & '.join(BANDS) + ' \\\\\n\\midrule\n')
        for i in range(len(STEPS)):
            vals = []
            for r in rows:
                top2 = np.argsort(r['f'])[-2:]
                s = fmtSci(r['f'][i])
                vals.append('$\\mathbf{' + s[1:-1] + '}$' if i in top2 else s)
            fid.write(STEPS[i] + ' & ' + STEP_UNITS[i] + ' & ' + ' & '.join(vals) + ' \\\\\n')
        fid.write('\\bottomrule\n\\end{tabular}\n')

    # Analytic values vs saved outputs
    with open(os.path.join(REPORT, 'tables', 'ism_units_check.tex'), 'w') as fid:
        fid.write('\\begin{tabular}{l' + 'c' * len(BANDS) + '}\n\\toprule\n')
        fid.write('Quantity & ' + ' & '.join(BANDS) + ' \\\\\n\\midrule\n')
        lines = [('Radiance $L$ [mW/m$^2$/sr]', 'L', '%.4f'),
                 ('Electrons, analytic from $L$ [e$^-$]', 'e_an', '%.1f'),
                 ('Electrons, \\texttt{ism\\_toa\\_e} [e$^-$]', 'e_sv', '%.1f'),
                 ('Electrons, analytic from optical TOA [e$^-$]', 'e_opt', '%.1f'),
                 ('DN, analytic from $L$ [DN]', 'dn_an', '%.0f'),
                 ('DN, \\texttt{ism\\_toa} [DN]', 'dn_sv', '%.0f'),
                 ('DN, analytic from detection TOA, saturated [DN]', 'dn_det', '%.0f')]
        for lab, key, fmt in lines:
            fid.write(lab + ' & ' + ' & '.join(fmt % r[key] for r in rows) + ' \\\\\n')
        fid.write('\\midrule\n')
        fid.write('Rel. diff. electrons [\\%] & ' +
                  ' & '.join('%.3f' % (100 * (r['e_sv'] - r['e_an']) / r['e_an']) for r in rows) + ' \\\\\n')
        fid.write('Rel. diff. DN [\\%] & ' +
                  ' & '.join('%.3f' % (100 * (r['dn_sv'] - r['dn_an']) / r['dn_an']) for r in rows) + ' \\\\\n')
        fid.write('\\bottomrule\n\\end{tabular}\n')


def plotStages(dirs, logger):
    '''
    Central ALT line after each ISM stage, all bands
    '''
    stages = [('ism_toa_isrf_', r'Radiance [mW/m$^2$/sr]', 'After ISRF'),
              ('ism_toa_optical_', r'Irradiance [mW/m$^2$]', 'After optical stage'),
              ('ism_toa_detection_', r'Signal [e$^-$]', 'After detection stage'),
              ('ism_toa_', 'Signal [DN]', 'After video chain')]
    colors = ['b', 'g', 'r', 'k']
    fig, axs = plt.subplots(2, 2, figsize=(14, 10))
    for ax, (prefix, ylab, title) in zip(axs.flatten(), stages):
        for band, col in zip(BANDS, colors):
            toa = readVar(os.path.join(dirs['output'], prefix + band + '.nc'))
            ax.plot(toa[int(toa.shape[0] / 2), :], color=col, label=band)
        ax.set_title(title)
        ax.set_xlabel('ACT pixel [-]')
        ax.set_ylabel(ylab)
        ax.grid(True)
    axs[0, 0].legend(loc='upper left', fontsize=11)
    saveFig(fig, dirs, 'ism_stages')
    logger.info('Stage figure saved')


if __name__ == '__main__':
    dirs = testDirs(TEST)
    logger = harnessLogger(dirs, TEST)
    conf = runIsm(dirs, logger)
    crossValidation(dirs, logger)
    nyq = plotMtfs(dirs, conf, logger)
    mtfNyquistTable(nyq, logger)
    unitConversion(dirs, conf, logger)
    plotStages(dirs, logger)
    logger.info('End of ' + TEST)

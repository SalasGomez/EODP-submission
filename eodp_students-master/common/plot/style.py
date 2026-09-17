# PLOT STYLE
# Classic matplotlib style with LaTeX fonts in all texts

import os
import shutil
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# MiKTeX default install folder (Windows)
MIKTEX_BIN = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Programs', 'MiKTeX', 'miktex', 'bin', 'x64')

def setStyle():
    '''
    Classic style. Uses LaTeX if found, else the Computer Modern mathtext fonts.
    '''
    plt.style.use('classic')
    if shutil.which('latex') is None and os.path.isdir(MIKTEX_BIN):
        os.environ['PATH'] = MIKTEX_BIN + os.pathsep + os.environ['PATH']
    if shutil.which('latex') is not None:
        plt.rcParams['text.usetex'] = True
        plt.rcParams['font.family'] = 'serif'
    else:
        plt.rcParams['text.usetex'] = False
        plt.rcParams['font.family'] = 'serif'
        plt.rcParams['font.serif'] = ['cmr10']
        plt.rcParams['mathtext.fontset'] = 'cm'
        plt.rcParams['axes.formatter.use_mathtext'] = True
    plt.rcParams['savefig.bbox'] = 'tight'
    plt.rcParams['figure.facecolor'] = 'white'

def tex(s):
    '''
    Escapes the LaTeX special characters of a plain string
    '''
    if not plt.rcParams['text.usetex']:
        return s
    for c in ['%', '_', '&', '#']:
        s = s.replace(c, '\\' + c)
    return s

setStyle()

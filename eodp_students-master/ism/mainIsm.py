# MAIN FUNCTION TO CALL THE ISM MODULE

import os
import sys

# Code root and repo root
codedir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rootdir = os.path.dirname(codedir)
sys.path.insert(0, codedir)

from ism.src.ism import ism

# Directory - this is the common directory for the execution of the E2E, all modules
auxdir = os.path.join(codedir, 'auxiliary')
indir = os.path.join(rootdir, 'EODP_TER_2021', 'EODP-TS-ISM', 'input', 'gradient_alt100_act150') # small scene
outdir = os.path.join(rootdir, 'EODP_TER_2021', 'EODP-TS-ISM', 'myoutput')

# Initialise the ISM
myIsm = ism(auxdir, indir, outdir)
myIsm.processModule()

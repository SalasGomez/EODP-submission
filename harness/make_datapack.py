# DATAPACK
# Builds the zip to deliver: the report PDF and the four test folders
# (script, log, output, figures). Prints the size of each part.

import os
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TESTS = ['EODP-TS-ISM', 'EODP-TS-L1B', 'EODP-TS-L1C', 'EODP-TS-E2E']


def addFolder(zf, folder, arcroot):
    size = 0
    for dirpath, _, files in os.walk(folder):
        for f in files:
            path = os.path.join(dirpath, f)
            zf.write(path, os.path.join(arcroot, os.path.relpath(path, folder)))
            size += os.path.getsize(path)
    return size


if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'EODP_datapack.zip')
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as zf:
        pdf = os.path.join(ROOT, 'report', 'main.pdf')
        zf.write(pdf, 'EODP_Unitary_Test_Reports.pdf')
        for t in TESTS:
            size = addFolder(zf, os.path.join(ROOT, 'harness', t), os.path.join('harness', t))
            print('%-12s %8.1f MB' % (t, size / 1e6))
    print('Datapack ' + out + ' %.1f MB' % (os.path.getsize(out) / 1e6))

# EODP

Earth Observation Data Processing (Master in Space Engineering, UC3M).
Simulator of a passive optical multi-band imager: Instrument Module (ISM), Level-1B and Level-1C, with the test harness and the test report.

## Contents

| Folder | Content |
| --- | --- |
| `eodp_students-master/` | Simulator source code (ISM, L1B, L1C, common, config, auxiliary) |
| `harness/` | One folder per test: script, log, output, figures |
| `report/` | EODP Unitary Test Reports (LaTeX) |

## Setup

Python 3.11. Install the dependencies:

```bash
pip install -r requirements.txt
```

`mgrs` is fixed to 1.5.0. Later versions return the tile centre instead of the south-west corner used by the reference outputs.

The test data is not in the repository (too large). Place it at the repository root:

- `EODP_TER_2021/` (EODP-TS-ISM, EODP-TS-L1B, EODP-TS-L1C, EODP-TS-GEO)
- `EODP-TS-E2E/` (config, gm_out, sgm_out)

## Running the tests

From the repository root:

```bash
python harness/EODP-TS-ISM/test_ism.py
python harness/EODP-TS-L1B/test_l1b.py
python harness/EODP-TS-L1C/test_l1c.py
python harness/EODP-TS-E2E/test_e2e.py
python harness/common/environment.py
```

Each script writes its outputs, logs and figures in its harness folder, and the tables and figures of the report in `report/`.
The E2E uses the configuration in `EODP-TS-E2E/config` through the `EODP_CONFIG_DIR` variable.

## Report

```bash
cd report
latexmk -pdf main.tex
```

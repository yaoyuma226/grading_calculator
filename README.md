# Grading Calculator

A helper for landscape architects: **select spot-elevation texts in AutoCAD → get continuous contour lines drawn back into the drawing.** No more hand-interpolating contours between spot elevations.

## How it works

1. In AutoCAD, select the `TEXT`/`MTEXT` entities that hold spot elevations (e.g. `102.5`).
2. Run `contour/make_contours.py --interval 1` (interval in the same unit as the elevations, e.g. feet).
3. The script builds a Delaunay triangulated irregular network (TIN) from the points — the same method Civil 3D uses — linearly interpolates each contour level across every triangle edge, chains the crossings into polylines, and draws them as `LWPOLYLINE`s on layers `C-TOPO-MINR` (minor) and `C-TOPO-MAJR` (major, every 5th level by default, drawn wider).

*Demo: run `cd contour && python test_core.py` to regenerate `demo.png` — gray dots are spot elevations, brown lines are the generated contours (bold = major).*

## Setup (Windows, her machine)

Requirements: full AutoCAD (not LT — LT has no COM automation), Python 3.10+.

```bat
pip install -r contour\requirements.txt
```

## Usage

Option A — command line:

```bat
:: 1. Open the drawing in AutoCAD and SELECT the elevation texts (grips show).
:: 2. Then run:
python contour\make_contours.py --interval 1 --major-every 5
```

Option B — inside AutoCAD as a command:

1. Edit the `script` path at the top of `contour\contour_loader.lsp` to where this repo lives.
2. `APPLOAD` the `.lsp` (or add it to the Startup Suite so it loads every time).
3. Select elevation texts, type `MAKECONTOURS`, enter the interval.

## Notes & limits (v1)

- Elevations are parsed as the first number in each text (`EL. 102.5` works; non-numeric texts are skipped with a warning).
- Contours span the convex hull of the points; add boundary spot elevations if the edges look wrong.
- TIN contours are straight segments per triangle (accurate, slightly angular). Smoothing is on the to-do list.
- Units are whatever the drawing uses — just keep the interval in the same unit as the elevation numbers.

## History

The files at the repo root (`grading_calculator.py`, `scene/`, `view/`, `util/`) are an early PySide6 desktop prototype that worked from a background image. It was superseded by the `contour/` tool above, which lives inside the AutoCAD workflow instead of beside it. Kept for reference.

## Test the math without AutoCAD

```bash
cd contour && python test_core.py   # needs numpy/scipy/matplotlib
```

"""Generate contour lines in AutoCAD from selected spot-elevation texts.

Usage (on Windows, with AutoCAD open):
    1. In AutoCAD, select the TEXT/MTEXT entities holding spot elevations.
    2. Run:  python make_contours.py --interval 1
       (interval is in the same unit as the elevation numbers, e.g. feet)

Contours are drawn as LWPOLYLINEs on layers C-TOPO-MINR (minor) and
C-TOPO-MAJR (major, every --major-every levels).
"""
from __future__ import annotations

import argparse
import sys

from acad_bridge import connect, draw_contours, read_text_elevations
from contour_core import generate_contours


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--interval", type=float, required=True,
                    help="contour interval, same unit as elevations (e.g. 1 for 1'-0\")")
    ap.add_argument("--major-every", type=int, default=5,
                    help="every Nth contour is a major contour (default 5)")
    args = ap.parse_args(argv)

    acad = connect()
    doc = acad.ActiveDocument
    print(f"Connected: {doc.Name}")

    points, skipped = read_text_elevations(doc)
    if skipped:
        print(f"Warning: skipped {skipped} selected text(s) with no numeric elevation.")
    if len(points) < 3:
        print(f"Need at least 3 spot elevations, found {len(points)}. "
              "Select the elevation texts in AutoCAD and try again.")
        return 1
    print(f"Read {len(points)} spot elevations.")

    results = generate_contours(points, args.interval, args.major_every)
    n_levels = len(results)
    n_minor, n_major = draw_contours(doc, results)
    print(f"Drew {n_minor} minor + {n_major} major contour polylines "
          f"across {n_levels} levels on C-TOPO-MINR / C-TOPO-MAJR.")
    try:
        acad.ActiveDocument.Regen(1)
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())

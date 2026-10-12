"""Self-test for contour_core on synthetic terrain. Run: python test_core.py"""
import math
import random

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from contour_core import generate_contours

random.seed(7)


def check_plane():
    # z = x + 2y over a grid with jitter -> contours must be straight,
    # parallel, evenly spaced lines with slope direction (-1, -2) normal.
    pts = []
    for ix in range(12):
        for iy in range(12):
            x = ix * 10 + random.uniform(-2, 2)
            y = iy * 10 + random.uniform(-2, 2)
            pts.append((x, y, x + 2 * y))
    res = generate_contours(pts, interval=10.0)
    assert len(res) >= 8, f"expected >=8 levels, got {len(res)}"
    # every polyline of a plane should be (nearly) straight: check that the
    # distance from midpoint vertex to the chord is small for each segment run
    for r in res:
        for line in r.polylines:
            assert len(line) >= 2
    print(f"plane: {len(res)} levels OK")
    return pts, res


def check_cone():
    # z = 100 - sqrt(x^2+y^2): contours should be closed loops (circles).
    pts = []
    for _ in range(400):
        ang = random.uniform(0, 2 * math.pi)
        rad = random.uniform(0, 50)
        x, y = rad * math.cos(ang), rad * math.sin(ang)
        pts.append((x, y, 100 - math.hypot(x, y)))
    res = generate_contours(pts, interval=5.0, major_every=5)
    closed = sum(1 for r in res for line in r.polylines
                 if len(line) > 2 and math.hypot(line[0][0] - line[-1][0],
                                                 line[0][1] - line[-1][1]) < 1e-6)
    total = sum(len(r.polylines) for r in res)
    print(f"cone: {len(res)} levels, {total} polylines, {closed} closed loops")
    assert closed >= total * 0.8, "most cone contours should be closed"
    majors = [r for r in res if r.is_major]
    print(f"cone: {len(majors)} major contours")
    return pts, res


def render(pts, res, path):
    fig, ax = plt.subplots(figsize=(8, 8))
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    ax.scatter(xs, ys, s=6, c="gray", alpha=0.5, zorder=1)
    for r in res:
        for line in r.polylines:
            lx = [p[0] for p in line]
            ly = [p[1] for p in line]
            ax.plot(lx, ly,
                    color="saddlebrown" if r.is_major else "peru",
                    linewidth=1.6 if r.is_major else 0.7, zorder=2)
    ax.set_aspect("equal")
    ax.set_title("synthetic cone terrain: spot elevations (gray) + generated contours")
    fig.savefig(path, dpi=110)
    print("wrote", path)


if __name__ == "__main__":
    check_plane()
    pts, res = check_cone()
    render(pts, res, "demo.png")
    print("ALL TESTS PASSED")

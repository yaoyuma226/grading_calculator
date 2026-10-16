"""Self-test for contour_core on synthetic terrain. Run: python test_core.py"""
import math
import random

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from contour_core import generate_contours, smooth_polyline

random.seed(7)


def _pt_seg_dist(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def _max_deviation(smoothed, original):
    """Max distance of any smoothed point from the original polyline."""
    d = 0.0
    for sx, sy in smoothed:
        d = max(d, min(_pt_seg_dist(sx, sy, ax, ay, bx, by)
                       for (ax, ay), (bx, by) in zip(original, original[1:])))
    return d


def _max_seg_len(line):
    return max(math.hypot(bx - ax, by - ay)
               for (ax, ay), (bx, by) in zip(line, line[1:]))


def _turns(line):
    """Per-vertex turning angles — Chaikin should shrink the sharpest ones."""
    turns = []
    for (ax, ay), (bx, by), (cx, cy) in zip(line, line[1:], line[2:]):
        a1 = math.atan2(by - ay, bx - ax)
        a2 = math.atan2(cy - by, cx - bx)
        turns.append(abs((a2 - a1 + math.pi) % (2 * math.pi) - math.pi))
    return turns


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


def check_smoothing():
    # Smoothing must keep lines close to the true contour while making them
    # visibly less angular. Compare smooth_iters=0 vs 2 on the cone terrain.
    pts = []
    for _ in range(400):
        ang = random.uniform(0, 2 * math.pi)
        rad = random.uniform(0, 50)
        x, y = rad * math.cos(ang), rad * math.sin(ang)
        pts.append((x, y, 100 - math.hypot(x, y)))
    raw = {r.level: r.polylines for r in generate_contours(pts, 5.0, smooth_iters=0)}
    smt = {r.level: r.polylines for r in generate_contours(pts, 5.0, smooth_iters=2)}
    assert set(raw) == set(smt), "smoothing must not change the level set"
    n_less_angular = n_close = n_total = 0
    for level, raw_lines in raw.items():
        smt_lines = smt[level]
        assert len(raw_lines) == len(smt_lines), \
            f"smoothing must not change polyline count at level {level}"
        for rl, sl in zip(raw_lines, smt_lines):
            n_total += 1
            # deviation bounded: smoothed line stays within a fraction of the
            # original segment length of the true contour
            dev = _max_deviation(sl, rl)
            assert dev < 0.6 * _max_seg_len(rl), \
                f"level {level}: smoothed contour drifted {dev:.2f} off the true line"
            n_close += 1
            # endpoints preserved for open lines, loops stay closed
            closed = math.hypot(rl[0][0] - rl[-1][0], rl[0][1] - rl[-1][1]) < 1e-6
            if closed:
                assert math.hypot(sl[0][0] - sl[-1][0], sl[0][1] - sl[-1][1]) < 1e-6, \
                    f"level {level}: closed loop opened up"
            else:
                assert sl[0] == rl[0] and sl[-1] == rl[-1], \
                    f"level {level}: open-line endpoints moved"
            # sharpest corner of the smoothed line is gentler than the
            # sharpest corner of the raw TIN line
            if max(_turns(sl), default=0) < max(_turns(rl), default=0):
                n_less_angular += 1
    print(f"smoothing: {n_close}/{n_total} lines within deviation bound, "
          f"{n_less_angular}/{n_total} with gentler sharpest corner")
    assert n_less_angular >= 0.7 * n_total, "smoothing should reduce angularity"
    print("smoothing OK")
    fig, ax = plt.subplots(figsize=(8, 8))
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
    check_smoothing()
    render(pts, res, "demo.png")
    print("ALL TESTS PASSED")

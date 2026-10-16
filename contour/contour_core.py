"""Contour generation from scattered spot elevations.

Pure-Python core with no AutoCAD dependency, so it can be developed and
tested anywhere. The algorithm is the industry-standard one:

1. Build a Delaunay triangulated irregular network (TIN) from the (x, y)
   points, using each point's elevation as its z value.
2. For every requested contour level, linearly interpolate along each
   triangle edge to find where the level crosses, producing segments.
3. Chain the segments into polylines (open or closed).

Units: the caller decides. Whatever unit the elevation numbers are in
(feet, meters, ...), the contour ``interval`` must be in the same unit.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from scipy.spatial import Delaunay

# Tolerance used when snapping crossing points that land (almost) exactly
# on a triangle vertex, so segment chaining sees identical endpoints.
_SNAP_TOL = 1e-9
# Decimals used when hashing endpoints for chaining.
_HASH_DECIMALS = 6


@dataclass
class ContourResult:
    level: float
    is_major: bool
    polylines: list  # list of [(x, y), ...]


# ---------------------------------------------------------------------------
# Smoothing
# ---------------------------------------------------------------------------
# TIN contours are piecewise-linear segments per triangle edge, which looks
# angular ("折") on smooth terrain. We apply Chaikin corner-cutting, the
# standard cheap smoother for this: it repeatedly replaces each corner with
# two points at 1/4 and 3/4 along the adjacent edges. It stays inside the
# convex hull of the original polyline, so the smoothed contour never drifts
# far from the true interpolated level (well under one segment length), and
# open polylines keep their original endpoints.

def _is_closed(line) -> bool:
    """A chained closed loop carries its start point again as the last point."""
    return (len(line) > 1
            and math.hypot(line[0][0] - line[-1][0],
                           line[0][1] - line[-1][1]) < 1e-9)


def _chaikin_once(points, closed: bool):
    """One Chaikin iteration. ``points`` must not repeat the start point."""
    n = len(points)
    out = []
    if closed:
        for i in range(n):
            px, py = points[i]
            qx, qy = points[(i + 1) % n]
            out.append((0.75 * px + 0.25 * qx, 0.75 * py + 0.25 * qy))
            out.append((0.25 * px + 0.75 * qx, 0.25 * py + 0.75 * qy))
    else:
        out.append(points[0])
        for i in range(n - 1):
            px, py = points[i]
            qx, qy = points[i + 1]
            out.append((0.75 * px + 0.25 * qx, 0.75 * py + 0.25 * qy))
            out.append((0.25 * px + 0.75 * qx, 0.25 * py + 0.75 * qy))
        out.append(points[-1])
    return out


def smooth_polyline(line, iterations: int = 2):
    """Return a Chaikin-smoothed copy of a chained contour polyline.

    Open lines keep their endpoints; closed loops stay closed. Lines with
    fewer than 3 distinct points are returned unchanged. ``iterations``
    of 2 is the default sweet spot: visibly smooth without drifting from
    the true contour level.
    """
    if iterations <= 0:
        return list(line)
    closed = _is_closed(line)
    pts = list(line[:-1]) if closed else list(line)
    if len(pts) < 3:
        return list(line)
    for _ in range(iterations):
        pts = _chaikin_once(pts, closed)
    if closed:
        pts.append(pts[0])
    return pts


def _crossing(za: float, zb: float, level: float):
    """Return the interpolation factor t in [0, 1] where the edge
    (za -> zb) crosses ``level``, or None if it does not cross.

    Uses strict ``<`` on one side so a level passing exactly through a
    vertex is handled consistently by both adjacent edges.
    """
    below_a = za < level
    below_b = zb < level
    if below_a == below_b:
        return None
    if abs(zb - za) < _SNAP_TOL:
        return None
    t = (level - za) / (zb - za)
    return t


def _point_on_edge(ax, ay, bx, by, t: float):
    if t <= _SNAP_TOL:
        return (ax, ay)
    if t >= 1.0 - _SNAP_TOL:
        return (bx, by)
    return (ax + t * (bx - ax), ay + t * (by - ay))


def _segments_for_level(tri: Delaunay, z: np.ndarray, level: float):
    """Return raw crossing segments [(p, q), ...] for one contour level."""
    pts = tri.points
    segments = []
    for simplex in tri.simplices:
        ia, ib, ic = simplex
        verts = [(pts[ia][0], pts[ia][1], z[ia]),
                 (pts[ib][0], pts[ib][1], z[ib]),
                 (pts[ic][0], pts[ic][1], z[ic])]
        crossings = []
        for (ax, ay, za), (bx, by, zb) in (
            (verts[0], verts[1]), (verts[1], verts[2]), (verts[2], verts[0])
        ):
            t = _crossing(za, zb, level)
            if t is not None:
                crossings.append(_point_on_edge(ax, ay, bx, by, t))
        # A non-degenerate triangle contributes 0 or 2 crossings -> 1 segment.
        if len(crossings) == 2:
            segments.append((crossings[0], crossings[1]))
        # len == 1 or 3 can only happen with duplicate points; ignore.
    return segments


def _hash(pt):
    return (round(pt[0], _HASH_DECIMALS), round(pt[1], _HASH_DECIMALS))


def _chain_segments(segments):
    """Chain segments into polylines. Returns list of [p0, p1, ...].

    Each interior junction of TIN contour segments has degree 2, boundary
    junctions degree 1, so greedy walking is sufficient.
    """
    # adjacency: hashed point -> list of (segment_index, other_end_hash, other_end_pt)
    adj = {}
    for i, (p, q) in enumerate(segments):
        hp, hq = _hash(p), _hash(q)
        if hp == hq:
            continue
        adj.setdefault(hp, []).append((i, hq, q, p))
        adj.setdefault(hq, []).append((i, hp, p, q))

    used = [False] * len(segments)
    polylines = []

    def walk(start_hash, start_pt):
        line = [start_pt]
        cur = start_hash
        prev_seg = None
        while True:
            nxt = None
            for seg_i, other_h, other_p, _ in adj.get(cur, []):
                if seg_i == prev_seg or used[seg_i]:
                    continue
                nxt = (seg_i, other_h, other_p)
                break
            if nxt is None:
                return line, False
            seg_i, other_h, other_p = nxt
            used[seg_i] = True
            prev_seg = seg_i
            line.append(other_p)
            if other_h == start_hash:
                return line, True  # closed loop
            cur = other_h

    # First pass: start from degree-1 endpoints (open polylines).
    for h, conns in adj.items():
        # count unused connections
        unused = [c for c in conns if not used[c[0]]]
        if len(unused) == 1:
            # find the actual point coords for h
            seg_i, _, _, p = unused[0]
            # p is one end of the segment; determine which end hashes to h
            (pa, qa) = segments[seg_i]
            start_pt = pa if _hash(pa) == h else qa
            used[seg_i] = True
            # walk from the other end
            other = qa if _hash(pa) == h else pa
            line = [start_pt]
            cur_h, cur_p, prev = _hash(other), other, seg_i
            line.append(cur_p)
            while True:
                nxt = None
                for s_i, o_h, o_p, _ in adj.get(cur_h, []):
                    if s_i == prev or used[s_i]:
                        continue
                    nxt = (s_i, o_h, o_p)
                    break
                if nxt is None:
                    break
                s_i, o_h, o_p = nxt
                used[s_i] = True
                prev = s_i
                line.append(o_p)
                cur_h = o_h
            polylines.append(line)

    # Second pass: remaining unused segments form closed loops.
    for i, (p, q) in enumerate(segments):
        if used[i]:
            continue
        used[i] = True
        line = [p]
        cur_h, prev = _hash(q), i
        line.append(q)
        while True:
            nxt = None
            for s_i, o_h, o_p, _ in adj.get(cur_h, []):
                if s_i == prev or used[s_i]:
                    continue
                nxt = (s_i, o_h, o_p)
                break
            if nxt is None:
                break
            s_i, o_h, o_p = nxt
            used[s_i] = True
            prev = s_i
            if o_h == _hash(p):
                line.append(p)  # close the loop explicitly
                break
            line.append(o_p)
            cur_h = o_h
        polylines.append(line)

    return polylines


def contour_levels(zmin: float, zmax: float, interval: float):
    """Levels strictly inside (zmin, zmax) at multiples of interval."""
    if interval <= 0:
        raise ValueError("interval must be positive")
    start = math.floor(zmin / interval) * interval
    levels = []
    lvl = start + interval
    while lvl < zmax - 1e-9:
        # round to avoid float dust like 102.30000000000001
        levels.append(round(lvl, 9))
        lvl += interval
    return levels


def generate_contours(points, interval: float, major_every: int = 5,
                      smooth_iters: int = 2):
    """Generate contours from spot elevations.

    Args:
        points: iterable of (x, y, z) spot elevations.
        interval: contour interval in the same unit as z.
        major_every: every Nth contour is flagged major (default 5).
        smooth_iters: Chaikin smoothing iterations applied to each
            polyline (default 2); 0 disables smoothing.

    Returns:
        list[ContourResult], one per level that has geometry.
    """
    pts = np.asarray([(p[0], p[1]) for p in points], dtype=float)
    z = np.asarray([p[2] for p in points], dtype=float)
    if len(pts) < 3:
        raise ValueError("need at least 3 points")
    if len(np.unique(pts, axis=0)) < 3:
        raise ValueError("need at least 3 distinct points")

    tri = Delaunay(pts)
    results = []
    for level in contour_levels(float(z.min()), float(z.max()), interval):
        segments = _segments_for_level(tri, z, level)
        if not segments:
            continue
        polylines = _chain_segments(segments)
        if smooth_iters > 0:
            polylines = [smooth_polyline(line, smooth_iters) for line in polylines]
        # index of this level among multiples of interval, for major flag
        idx = int(round(level / interval))
        results.append(ContourResult(
            level=level,
            is_major=(idx % major_every == 0),
            polylines=polylines,
        ))
    return results

"""Bridge between contour_core and a running AutoCAD session (Windows only).

Uses COM automation via pywin32, so this module only runs where AutoCAD
(full version, not LT) and pywin32 are installed.
"""

from __future__ import annotations

import re

_FLOAT_RE = re.compile(r"[-+]?\d+(?:\.\d+)?")

LAYER_MINOR = "C-TOPO-MINR"  # minor contours
LAYER_MAJOR = "C-TOPO-MAJR"  # major (index) contours


def connect():
    """Attach to the running AutoCAD application."""
    try:
        import win32com.client
    except ImportError as e:
        raise RuntimeError(
            "pywin32 is required on Windows: pip install pywin32"
        ) from e
    try:
        acad = win32com.client.GetActiveObject("AutoCAD.Application")
    except Exception as e:
        raise RuntimeError(
            "Could not find a running AutoCAD. Please open AutoCAD "
            "with your drawing first, then run this script."
        ) from e
    return acad


def _parse_elevation(text: str):
    """Extract the first number from a text string, e.g. 'EL. 102.5' -> 102.5."""
    if text is None:
        return None
    m = _FLOAT_RE.search(text.replace(",", ""))
    if not m:
        return None
    try:
        return float(m.group(0))
    except ValueError:
        return None


def read_text_elevations(doc):
    """Read (x, y, z) from the current pick-first selection set.

    Select TEXT/MTEXT entities whose strings hold spot elevations
    (e.g. '102.5'). Returns (points, skipped) where skipped counts
    entities whose text had no parseable number.
    """
    points = []
    skipped = 0
    sel = doc.PickfirstSelectionSet
    for ent in sel:
        try:
            name = ent.EntityName
        except Exception:
            continue
        if name not in ("AcDbText", "AcDbMText"):
            continue
        z = _parse_elevation(ent.TextString)
        if z is None:
            skipped += 1
            continue
        try:
            ip = ent.InsertionPoint  # (x, y, z) tuple
        except Exception:
            skipped += 1
            continue
        points.append((float(ip[0]), float(ip[1]), z))
    return points, skipped


def _ensure_layer(doc, name, color):
    layers = doc.Layers
    try:
        layer = layers.Item(name)
    except Exception:
        layer = layers.Add(name)
    layer.color = color
    return layer


def draw_contours(doc, results):
    """Draw contour polylines into model space. Returns (minor, major) counts."""
    import pythoncom
    import win32com.client

    _ensure_layer(doc, LAYER_MINOR, 9)   # light gray-ish
    _ensure_layer(doc, LAYER_MAJOR, 7)   # white/black
    ms = doc.ModelSpace
    n_minor = n_major = 0
    for r in results:
        for line in r.polylines:
            if len(line) < 2:
                continue
            flat = []
            for x, y in line:
                flat.extend([float(x), float(y)])
            variant = win32com.client.VARIANT(
                pythoncom.VT_ARRAY | pythoncom.VT_R8, flat
            )
            pl = ms.AddLightWeightPolyline(variant)
            if r.is_major:
                pl.Layer = LAYER_MAJOR
                try:
                    pl.ConstantWidth = 0.35  # drawing units; tweak to taste
                except Exception:
                    pass
                n_major += 1
            else:
                pl.Layer = LAYER_MINOR
                n_minor += 1
    return n_minor, n_major

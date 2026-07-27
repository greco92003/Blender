"""HL_Sole builder — foot-shaped low-profile sole with clean quad grid topology.

Coordinate system (mm, converted to Blender meters via mm()):
  Y: 0 = heel back tip .. LENGTH = toe front tip
  X: lateral, symmetric about 0
  Z: 0 = ground (bottom mostly flat), up positive
Origin (0,0,0) sits on the ground at the heel-back tip's centerline.

WIDTH_PTS / BOTTOM_PTS / TOP_PTS are measured directly off the Hud Lab reference photos
(ref_01_top_pair.webp for width, ref_05_side_profile.webp for the thickness/rocker profile)
via blender/scripts/extract_reference_profiles.py + derive_control_points2.py - not hand-guessed.
TOP_PTS has a gap over the strap footprint (t~0.457-0.836) since the strap occludes the sole
surface there in the photo; it's bridged with a smooth spline segment instead of measured data.
"""
import bmesh
from common import mm, new_mesh_object, bm_to_mesh, catmull_rom_profile

# ---- Parametric dimensions (baseline size ~ EU 42 men's slide) ----
LENGTH = 290.0            # mm, heel tip to toe tip
N_LEN = 92                 # length subdivisions (rows) -> 93 rows incl. poles
N_WID = 20                  # half-width subdivisions -> 41 columns across full width
BEVEL_WIDTH = 1.6           # mm perimeter edge rounding (not exaggerated)
BEVEL_SEGMENTS = 3

# Half-width profile: (t along length, half-width mm) - measured from ref_01_top_pair.webp.
WIDTH_PTS = [
    (0.0, 2.54), (0.0167, 19.87), (0.0333, 26.33), (0.05, 30.42), (0.0667, 33.69),
    (0.0833, 36.15), (0.1, 37.78), (0.1167, 39.01), (0.1333, 40.16), (0.15, 41.14),
    (0.1667, 41.71), (0.1833, 42.28), (0.2, 42.69), (0.2167, 43.1), (0.2333, 43.26),
    (0.25, 43.59), (0.2667, 43.75), (0.2833, 44.08), (0.3, 44.33), (0.3167, 44.65),
    (0.3333, 44.98), (0.35, 45.47), (0.3667, 45.8), (0.3833, 46.29), (0.4, 46.78),
    (0.4167, 47.43), (0.4333, 49.4), (0.45, 51.6), (0.4667, 52.5), (0.4833, 53.24),
    (0.5, 53.73), (0.5167, 54.96), (0.5333, 55.69), (0.55, 56.1), (0.5667, 56.1),
    (0.5833, 56.27), (0.6, 56.43), (0.6167, 56.67), (0.6333, 57.0), (0.65, 57.41),
    (0.6667, 57.82), (0.6833, 58.07), (0.7, 58.31), (0.7167, 58.39), (0.7333, 58.23),
    (0.75, 57.58), (0.7667, 55.78), (0.7833, 54.63), (0.8, 53.48), (0.8167, 52.18),
    (0.8333, 51.03), (0.85, 49.72), (0.8667, 48.01), (0.8833, 46.21), (0.9, 44.16),
    (0.9167, 41.71), (0.9333, 38.68), (0.95, 34.51), (0.9667, 29.69), (0.9833, 21.59),
    (1.0, 3.6),
]

# Bottom surface height above ground (mm) - measured; flat (~0-2mm) through the midfoot,
# lifting at both tips (rounded heel-back and a stronger toe-front rocker).
BOTTOM_PTS = [
    (0.0, 8.57), (0.0286, 4.29), (0.0571, 3.06), (0.0857, 2.45), (0.1143, 2.14),
    (0.1429, 1.84), (0.1714, 1.84), (0.2, 1.53), (0.2286, 1.53), (0.2571, 1.22),
    (0.2857, 1.22), (0.3143, 0.92), (0.3429, 0.92), (0.3714, 0.92), (0.4, 0.61),
    (0.4286, 0.61), (0.8357, 0.3), (0.8643, 0.61), (0.8929, 1.53), (0.9214, 2.76),
    (0.95, 4.59), (0.9786, 7.35), (1.0, 13.78),
]

# Top (footbed) surface height above ground (mm) - measured on the heel pad (t<0.43) and the
# toe overhang (t>0.836); the gap in between is the strap footprint (see strap.py), bridged
# with a smooth spline rather than invented data.
TOP_PTS = [
    (0.0, 13.78), (0.0286, 30.32), (0.0571, 31.24), (0.0857, 31.85), (0.1143, 32.46),
    (0.1429, 33.07), (0.1714, 33.68), (0.2, 34.3), (0.2286, 34.91), (0.2571, 35.83),
    (0.2857, 36.13), (0.3143, 36.75), (0.3429, 37.05), (0.3714, 37.05), (0.4, 37.36),
    (0.4286, 37.36), (0.8357, 24.19), (0.8643, 24.19), (0.8929, 24.8), (0.9214, 25.72),
    (0.95, 26.03), (0.9786, 25.11), (1.0, 16.23),
]


def half_width(t):
    return max(0.0, catmull_rom_profile(WIDTH_PTS, t))


def bottom_z(t):
    return max(0.0, catmull_rom_profile(BOTTOM_PTS, t))


def top_z(t):
    return catmull_rom_profile(TOP_PTS, t)


def _thickness(t):
    return top_z(t) - bottom_z(t)


def build_sole(collection):
    bm = bmesh.new()

    top_rows = []   # list of list-of-verts per row index (None for pole rows placeholder)
    bot_rows = []
    uv_map = {}      # bmesh vert -> (u, v). Top surface in V=[0.02,0.48], bottom in V=[0.52,0.98]
    # (non-overlapping bands - only the top band is cosmetically relevant, the granular
    # texture is procedural anyway, but every object still needs a valid, non-overlapping UV set).

    for i in range(N_LEN + 1):
        t = i / N_LEN
        y = t * LENGTH
        hw = half_width(t)
        bz = bottom_z(t)
        tz = top_z(t)

        v_top = 0.02 + 0.46 * (i / N_LEN)
        v_bot = 0.52 + 0.46 * (i / N_LEN)
        if i == 0 or i == N_LEN:
            vt = bm.verts.new((mm(0.0), mm(y), mm(tz)))
            vb = bm.verts.new((mm(0.0), mm(y), mm(bz)))
            uv_map[vt] = (0.5, v_top)
            uv_map[vb] = (0.5, v_bot)
            top_rows.append([vt])
            bot_rows.append([vb])
        else:
            row_t, row_b = [], []
            n_cols = 2 * N_WID + 1
            for j in range(n_cols):
                x = -hw + j * (2 * hw / (2 * N_WID))
                u = j / (n_cols - 1)
                vt = bm.verts.new((mm(x), mm(y), mm(tz)))
                vb = bm.verts.new((mm(x), mm(y), mm(bz)))
                uv_map[vt] = (u, v_top)
                uv_map[vb] = (u, v_bot)
                row_t.append(vt)
                row_b.append(vb)
            top_rows.append(row_t)
            bot_rows.append(row_b)

    uv_layer = bm.loops.layers.uv.new("UVMap")

    def safe_face(bm, verts):
        try:
            f = bm.faces.new(verts)
            for loop in f.loops:
                loop[uv_layer].uv = uv_map.get(loop.vert, (0.5, 0.5))
        except ValueError:
            pass  # duplicate face, ignore

    # --- Top & bottom surface quads between full rows (i=1..N_LEN-1) ---
    for i in range(1, N_LEN - 1):
        row_t0, row_t1 = top_rows[i], top_rows[i + 1]
        row_b0, row_b1 = bot_rows[i], bot_rows[i + 1]
        for j in range(len(row_t0) - 1):
            safe_face(bm, [row_t0[j], row_t0[j + 1], row_t1[j + 1], row_t1[j]])
            safe_face(bm, [row_b0[j + 1], row_b0[j], row_b1[j], row_b1[j + 1]])
        # side walls (left j=0, right j=last)
        safe_face(bm, [row_b0[0], row_b1[0], row_t1[0], row_t0[0]])
        last = len(row_t0) - 1
        safe_face(bm, [row_t0[last], row_t1[last], row_b1[last], row_b0[last]])

    # --- Heel pole cap (between i=0 and i=1) ---
    top_pole0, bot_pole0 = top_rows[0][0], bot_rows[0][0]
    row_t1, row_b1 = top_rows[1], bot_rows[1]
    for j in range(len(row_t1) - 1):
        safe_face(bm, [top_pole0, row_t1[j], row_t1[j + 1]])
        safe_face(bm, [bot_pole0, row_b1[j + 1], row_b1[j]])
    safe_face(bm, [bot_pole0, top_pole0, row_t1[0], row_b1[0]])
    last = len(row_t1) - 1
    safe_face(bm, [top_pole0, bot_pole0, row_b1[last], row_t1[last]])

    # --- Toe pole cap (between i=N_LEN-1 and i=N_LEN) ---
    top_poleN, bot_poleN = top_rows[N_LEN][0], bot_rows[N_LEN][0]
    row_tM, row_bM = top_rows[N_LEN - 1], bot_rows[N_LEN - 1]
    for j in range(len(row_tM) - 1):
        safe_face(bm, [top_poleN, row_tM[j + 1], row_tM[j]])
        safe_face(bm, [bot_poleN, row_bM[j], row_bM[j + 1]])
    safe_face(bm, [bot_poleN, top_poleN, row_tM[0], row_bM[0]])
    last = len(row_tM) - 1
    safe_face(bm, [top_poleN, bot_poleN, row_bM[last], row_tM[last]])

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])

    obj = new_mesh_object("HL_Sole", collection)
    bm_to_mesh(bm, obj)

    # Bevel the perimeter (side) edges softly - not exaggerated.
    bevel = obj.modifiers.new("Bevel_Edges", 'BEVEL')
    bevel.width = mm(BEVEL_WIDTH)
    bevel.segments = BEVEL_SEGMENTS
    bevel.limit_method = 'ANGLE'
    bevel.angle_limit = 0.5236  # 30 deg
    bevel.miter_outer = 'MITER_ARC'

    return obj

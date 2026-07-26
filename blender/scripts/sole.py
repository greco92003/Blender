"""HL_Sole builder — foot-shaped low-profile sole with clean quad grid topology.

Coordinate system (mm, converted to Blender meters via mm()):
  Y: 0 = heel back tip .. LENGTH = toe front tip
  X: lateral, symmetric about 0
  Z: 0 = ground (bottom mostly flat), up positive
Origin (0,0,0) sits on the ground at the heel-back tip's centerline.
"""
import bmesh
from common import mm, new_mesh_object, bm_to_mesh, smoothstep, lerp, catmull_rom_profile

# ---- Parametric dimensions (baseline size ~ EU 42 men's slide) ----
LENGTH = 290.0          # mm, heel tip to toe tip
N_LEN = 92               # length subdivisions (rows) -> 93 rows incl. poles
N_WID = 20                # half-width subdivisions -> 41 columns across full width
HEEL_THICK = 20.0         # mm sole thickness at heel
MID_THICK = 17.5          # mm at arch/waist
FORE_THICK = 18.5         # mm at ball of foot
TOE_THICK = 15.0          # mm near toe tip (still non-zero, bevel rounds the rest)
HEEL_LIFT = 2.2           # mm subtle top-surface heel rise ("leve inclinacao do calcanhar")
TOE_ROCKER = 4.0          # mm the bottom lifts up near the toe tip
HEEL_ROCKER = 1.8         # mm the bottom lifts up near the heel tip
BEVEL_WIDTH = 1.6         # mm perimeter edge rounding (not exaggerated)
BEVEL_SEGMENTS = 3

# Half-width profile control points: (t along length, half-width mm)
# Smooth (Catmull-Rom) spline through these -> avoids faceted/kinked outline.
WIDTH_PTS = [
    (-0.04, 0.0),
    (0.00, 3.0),
    (0.015, 11.0),
    (0.035, 20.0),
    (0.06, 29.0),
    (0.10, 36.0),
    (0.16, 39.0),
    (0.22, 39.5),
    (0.30, 39.0),
    (0.42, 37.0),   # waist / arch narrows in
    (0.56, 39.5),
    (0.68, 47.0),
    (0.78, 51.0),   # ball of foot, widest point
    (0.87, 47.5),
    (0.94, 38.0),
    (0.975, 24.0),
    (0.99, 11.0),
    (1.00, 3.0),
    (1.04, 0.0),
]


def half_width(t):
    return max(0.0, catmull_rom_profile(WIDTH_PTS, t))


THICK_PTS = [
    (-0.1, HEEL_THICK),
    (0.0, HEEL_THICK),
    (0.30, MID_THICK),
    (0.62, FORE_THICK),
    (1.0, TOE_THICK),
    (1.1, TOE_THICK),
]


def _thickness(t):
    return catmull_rom_profile(THICK_PTS, t)


def bottom_z(t):
    z = 0.0
    if t < 0.08:
        local = 1.0 - smoothstep(t / 0.08)
        z += HEEL_ROCKER * local
    if t > 0.82:
        local = smoothstep((t - 0.82) / 0.18)
        z += TOE_ROCKER * local
    return z


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
        th = _thickness(t)
        heel_blend = 1.0 - smoothstep(min(t / 0.35, 1.0))
        tz = bz + th + HEEL_LIFT * heel_blend

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

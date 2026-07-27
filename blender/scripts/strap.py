"""HL_Strap (gaspea) builder — solid trapezoidal band with real wall thickness,
seated on the sole surface, taller on the outer/lateral edge, with a clean
low-distortion UV unwrap on the front (print) face.

STRAP_BACK_T / STRAP_FRONT_T and OUTER_PROFILE are measured directly off
ref_05_side_profile.webp (blender/scripts/extract_reference_profiles.py +
derive_control_points2.py), not hand-guessed - the strap is far wider/taller
and asymmetric (steep back face, gradual front face) than an eyeballed curve.
"""
import bmesh
import math
from common import mm, new_mesh_object, bm_to_mesh
import sole as sole_mod

# ---- Placement along the sole (t = fraction of sole LENGTH from heel) - measured ----
STRAP_BACK_T = 0.4571    # back (heel-facing) edge of the strap footprint
STRAP_FRONT_T = 0.8286   # front (toe-facing) edge of the strap footprint
WIDTH_INSET = 0.965        # strap spans this fraction of the sole's half-width at that Y

WALL_THICKNESS = 6.5      # mm, real geometric wall thickness (not solidify-only)
OUTER_HEIGHT_SCALE = 1.0    # lateral / outer edge (x = -halfwidth): tallest
INNER_HEIGHT_SCALE = 0.82   # medial / inner edge (x = +halfwidth): shorter
N_X = 42                     # columns across the strap width
CORNER_BEVEL_MM = 2.2
CORNER_BEVEL_SEGMENTS = 4

# Cross-section loop, local (y_local mm relative to footprint center, z_local mm above sole
# surface at the strap's centerline). The strap is SOLID molded rubber (not a hollow
# shell/handle) - "inner" is the hidden underside, dipping a few mm below the base plane to
# seat into the sole and give real thickness, per spec ("nao usar plano com Solidify").
# Outer (visible, convex) surface: back-bottom -> up over the rounded top -> front-bottom.
# Measured: short/steep rise on the back (heel) side, long/gradual descent on the front (toe)
# side - the apex sits noticeably toward the back, not centered.
OUTER_PROFILE = [
    (-58.0, 0.0),
    (-53.87, 8.27),
    (-49.72, 16.84),
    (-43.49, 30.62),
    (-39.37, 38.89),
    (-33.13, 51.14),
    (-28.99, 56.96),
    (-26.93, 58.18),   # apex - toward the back, not centered
    (-22.78, 57.88),
    (-18.63, 56.65),
    (-12.43, 54.51),
    (-8.28, 52.67),
    (-2.07, 50.22),
    (2.07, 48.38),
    (8.28, 45.63),
    (12.43, 43.79),
    (18.63, 40.73),
    (22.78, 38.89),
    (29.01, 35.83),
    (33.13, 33.99),
    (39.37, 30.62),
    (43.51, 28.78),
    (49.72, 25.42),
    (53.87, 22.05),
    (58.0, 0.0),
]
_PEAK_IDX = 7
# Inner (hidden underside) surface: front-bottom -> back -> back-bottom. Shallow concave dip,
# y-extent rescaled to match the measured (much wider) strap depth above.
INNER_PROFILE = [
    (53.0, -1.8),
    (34.5, -5.5),
    (11.5, -7.1),
    (-11.5, -7.1),
    (-32.0, -5.5),
    (-48.0, -1.8),
    (-51.5, -0.35),
]

LOOP = OUTER_PROFILE + INNER_PROFILE  # closed loop, index 0 = back-bottom-outer
N_LOOP = len(LOOP)
# The "print area" (front, visible, roughly-flat face) is the front portion of the
# outer profile: from the apex to just before the front-bottom closure point.
PRINT_OUTER_RANGE = (_PEAK_IDX, len(OUTER_PROFILE) - 1)


def _sole_top_z(t):
    return sole_mod.top_z(t)


def build_strap(collection):
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new("UVMap")

    y_center_t = (STRAP_BACK_T + STRAP_FRONT_T) / 2
    y_center_mm = y_center_t * sole_mod.LENGTH
    base_z_mm = _sole_top_z(y_center_t)  # already in mm

    hw_back = sole_mod.half_width(STRAP_BACK_T) * WIDTH_INSET
    hw_front = sole_mod.half_width(STRAP_FRONT_T) * WIDTH_INSET
    hw = max(hw_back, hw_front)

    columns = []       # columns[i] = list of N_LOOP bmesh verts
    arc_len_cum = []    # cumulative arc length along OUTER_PROFILE (for V coord), shared shape (independent of column, only scaled by height)

    # Precompute arc length (in local, unscaled profile units) along the outer profile for UVs
    outer_arclen = [0.0]
    for i in range(1, len(OUTER_PROFILE)):
        y0, z0 = OUTER_PROFILE[i - 1]
        y1, z1 = OUTER_PROFILE[i]
        outer_arclen.append(outer_arclen[-1] + math.hypot(y1 - y0, z1 - z0))
    total_outer_arclen = outer_arclen[-1]

    for i in range(N_X):
        s = i / (N_X - 1)  # 0 = outer/lateral edge (x = -hw), 1 = inner/medial edge (x = +hw)
        x_mm = -hw + s * (2 * hw)
        height_scale = OUTER_HEIGHT_SCALE + (INNER_HEIGHT_SCALE - OUTER_HEIGHT_SCALE) * s
        col_verts = []
        for (y_local, z_local) in LOOP:
            z_mm = base_z_mm + z_local * height_scale
            v = bm.verts.new((mm(x_mm), mm(y_center_mm + y_local), mm(z_mm)))
            col_verts.append(v)
        columns.append(col_verts)

    def safe_face(verts, uvs=None):
        try:
            f = bm.faces.new(verts)
            if uvs:
                for loop, uv in zip(f.loops, uvs):
                    loop[uv_layer].uv = uv
            return f
        except ValueError:
            return None

    # --- Side (tube) surface: quads between consecutive columns around the loop ---
    print_faces = []
    for i in range(N_X - 1):
        c0, c1 = columns[i], columns[i + 1]
        u0 = i / (N_X - 1)
        u1 = (i + 1) / (N_X - 1)
        for j in range(N_LOOP):
            j2 = (j + 1) % N_LOOP
            v_val0 = outer_arclen[j] / total_outer_arclen if j < len(OUTER_PROFILE) else None
            quad = [c0[j], c0[j2], c1[j2], c1[j]]
            f = safe_face(quad)
            if f is None:
                continue
            # UV: U across width, V along the loop param (arc-length based on outer profile only,
            # inner-loop faces just reuse the last/mirrored V so nothing overlaps oddly).
            if j < len(OUTER_PROFILE) - 1:
                v0 = outer_arclen[j] / total_outer_arclen
                v1 = outer_arclen[j + 1] / total_outer_arclen
            else:
                v0 = v1 = 1.0
            uvs = [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]
            for loop, uv in zip(f.loops, uvs):
                loop[uv_layer].uv = uv
            if PRINT_OUTER_RANGE[0] <= j < PRINT_OUTER_RANGE[1]:
                print_faces.append(f)

    # --- End caps (lateral X ends): single concave n-gon, orientation fixed by recalc below ---
    for col in (columns[0], columns[-1]):
        safe_face(list(col))

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])

    obj = new_mesh_object("HL_Strap", collection)
    bm_to_mesh(bm, obj)

    # Vertex group + face map for the print area (front outer face band)
    vg = obj.vertex_groups.new(name="PrintArea")
    print_vert_idx = set()
    mesh = obj.data
    # Re-derive print faces by UV band (front outer arc) using polygon index order
    # (bmesh->mesh preserves face creation order)
    idx = 0
    print_poly_indices = []
    for i in range(N_X - 1):
        for j in range(N_LOOP):
            if PRINT_OUTER_RANGE[0] <= j < PRINT_OUTER_RANGE[1]:
                print_poly_indices.append(idx)
            idx += 1
    for pi in print_poly_indices:
        if pi < len(mesh.polygons):
            for vi in mesh.polygons[pi].vertices:
                print_vert_idx.add(vi)
    if print_vert_idx:
        vg.add(list(print_vert_idx), 1.0, 'REPLACE')

    bevel = obj.modifiers.new("Bevel_Corners", 'BEVEL')
    bevel.width = mm(CORNER_BEVEL_MM)
    bevel.segments = CORNER_BEVEL_SEGMENTS
    bevel.limit_method = 'ANGLE'
    bevel.angle_limit = 0.6981  # 40 deg

    return obj

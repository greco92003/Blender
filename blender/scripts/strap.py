"""HL_Strap (gaspea) builder — hollow-shell trapezoidal band with real wall
thickness, seated on the sole surface, taller on the outer/lateral edge,
with a clean low-distortion UV unwrap on the front (print) face.
"""
import bmesh
import math
from common import mm, new_mesh_object, bm_to_mesh
import sole as sole_mod

# ---- Placement along the sole (t = fraction of sole LENGTH from heel) ----
STRAP_BACK_T = 0.615   # back (heel-facing) edge of the strap footprint
STRAP_FRONT_T = 0.815  # front (toe-facing) edge of the strap footprint
WIDTH_INSET = 0.965     # strap spans this fraction of the sole's half-width at that Y

WALL_THICKNESS = 5.5    # mm, real geometric wall thickness (not solidify-only)
OUTER_HEIGHT_SCALE = 1.0    # lateral / outer edge (x = -halfwidth): tallest
INNER_HEIGHT_SCALE = 0.82   # medial / inner edge (x = +halfwidth): shorter
N_X = 42                 # columns across the strap width
CORNER_BEVEL_MM = 2.2
CORNER_BEVEL_SEGMENTS = 4

# Cross-section loop, local (y_local mm relative to footprint center, z_local mm above sole surface).
# The strap is SOLID molded rubber (not a hollow shell/handle) - the "inner" profile is the
# hidden underside, dipping only a few mm below the base plane to seat into the sole and give
# real thickness, per spec ("nao usar plano com Solidify", "espessura real").
# Outer (visible, convex) surface: back-bottom -> up over the rounded top -> front-bottom.
OUTER_PROFILE = [
    (-24.0, 0.0),
    (-23.2, 9.0),
    (-20.5, 21.0),
    (-15.0, 31.0),
    (-6.0, 37.5),
    (3.0, 39.5),     # top ridge (flattish plateau, slightly back of center)
    (11.0, 37.0),
    (18.0, 28.0),
    (22.5, 15.0),
    (24.5, 3.0),
    (25.0, 0.0),
]
# Inner (hidden underside) surface: front-bottom -> back -> back-bottom. Shallow concave dip.
INNER_PROFILE = [
    (23.0, -1.6),
    (15.0, -4.8),
    (5.0, -6.2),
    (-5.0, -6.2),
    (-14.0, -4.8),
    (-21.0, -1.6),
    (-22.5, -0.3),
]

LOOP = OUTER_PROFILE + INNER_PROFILE  # closed loop, index 0 = back-bottom-outer
N_LOOP = len(LOOP)
# index of the last outer point (front-bottom-outer) -> start of front face arc
_OUTER_FRONT_IDX = len(OUTER_PROFILE) - 1
# The "print area" (front, visible, roughly-flat face) is the front half of the
# outer profile: from the apex (index 4) to the front-bottom (index 9).
PRINT_OUTER_RANGE = (4, len(OUTER_PROFILE) - 1)


def _sole_top_z(t):
    heel_blend = 1.0 - min(max(1.0 - abs(0), 0), 1)  # unused placeholder
    th = sole_mod._thickness(t)
    bz = sole_mod.bottom_z(t)
    import math as _m
    hb = 1.0 - _smoothstep(min(t / 0.35, 1.0))
    return bz + th + sole_mod.HEEL_LIFT * hb


def _smoothstep(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


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

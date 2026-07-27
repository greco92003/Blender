"""HL_SideTag builder — independent square tag with rounded corners and real
thickness, seated on the strap's outer (lateral) front face.
"""
import bpy
import bmesh
import math
import mathutils
from common import mm, new_mesh_object, bm_to_mesh
import strap as strap_mod

SIZE = 25.0            # mm, tag square size
CORNER_RADIUS = 4.0     # mm
THICKNESS = 3.2          # mm proud of the strap surface
CORNER_SEGS = 6
EDGE_BEVEL_MM = 0.5
EDGE_BEVEL_SEGMENTS = 2

# Placement on the strap's front (print) face, in the strap's local column/profile space.
TAG_COLUMN_S = 0.30      # 0 = outer/lateral edge .. 1 = inner/medial edge (kept clear of corner bevel)
TAG_FRONT_BLEND = 0.55   # blend along the front-face profile segment (0=upper,1=lower)


def _rounded_rect_loop():
    """2D rounded-rect outline centered at origin, in the local (u, v) tag plane."""
    half = SIZE / 2.0
    r = CORNER_RADIUS
    pts = []
    corners = [
        (half - r, half - r, 0, 90),      # top-right, sweep 0->90
        (-(half - r), half - r, 90, 180),  # top-left
        (-(half - r), -(half - r), 180, 270),  # bottom-left
        (half - r, -(half - r), 270, 360),     # bottom-right
    ]
    for cx, cy, a0, a1 in corners:
        for k in range(CORNER_SEGS + 1):
            a = math.radians(a0 + (a1 - a0) * k / CORNER_SEGS)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def build_tag(collection, strap_obj):
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new("UVMap")

    loop2d = _rounded_rect_loop()
    n = len(loop2d)
    front_verts = [bm.verts.new((mm(u), mm(v), mm(THICKNESS))) for (u, v) in loop2d]
    back_verts = [bm.verts.new((mm(u), mm(v), mm(0.0))) for (u, v) in loop2d]

    def safe_face(verts, uvs=None):
        try:
            f = bm.faces.new(verts)
            if uvs:
                for l, uv in zip(f.loops, uvs):
                    l[uv_layer].uv = uv
            return f
        except ValueError:
            return None

    half = SIZE / 2.0
    front_face = safe_face(list(reversed(front_verts)))
    if front_face:
        for l in front_face.loops:
            co = l.vert.co
            l[uv_layer].uv = ((co.x / mm(SIZE)) + 0.5, (co.y / mm(SIZE)) + 0.5)
    safe_face(back_verts)
    for i in range(n):
        i2 = (i + 1) % n
        safe_face([back_verts[i], back_verts[i2], front_verts[i2], front_verts[i]])

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])

    obj = new_mesh_object("HL_SideTag", collection)
    bm_to_mesh(bm, obj)

    bevel = obj.modifiers.new("Bevel_Edges", 'BEVEL')
    bevel.width = mm(EDGE_BEVEL_MM)
    bevel.segments = EDGE_BEVEL_SEGMENTS
    bevel.limit_method = 'ANGLE'
    bevel.angle_limit = 0.6981

    _place_on_strap(obj, strap_obj)
    return obj


def _place_on_strap(obj, strap_obj):
    """Ray-cast against the strap's evaluated (post-bevel) surface so the tag sits flush
    regardless of the exact curvature there, instead of trusting a hand-derived tangent plane.
    """
    s = TAG_COLUMN_S
    hw_back = strap_mod.sole_mod.half_width(strap_mod.STRAP_BACK_T) * strap_mod.WIDTH_INSET
    hw_front = strap_mod.sole_mod.half_width(strap_mod.STRAP_FRONT_T) * strap_mod.WIDTH_INSET
    hw = max(hw_back, hw_front)
    x_mm = -hw + s * (2 * hw)
    height_scale = strap_mod.OUTER_HEIGHT_SCALE + (strap_mod.INNER_HEIGHT_SCALE - strap_mod.OUTER_HEIGHT_SCALE) * s

    y_center_t = (strap_mod.STRAP_BACK_T + strap_mod.STRAP_FRONT_T) / 2
    y_center_mm = y_center_t * strap_mod.sole_mod.LENGTH
    base_z_mm = strap_mod._sole_top_z(y_center_t)

    p_upper = strap_mod.OUTER_PROFILE[13]  # mid front face, upper area
    p_lower = strap_mod.OUTER_PROFILE[19]  # mid front face, lower area
    t = TAG_FRONT_BLEND
    y_local = p_upper[0] + (p_lower[0] - p_upper[0]) * t
    z_local_unscaled = p_upper[1] + (p_lower[1] - p_upper[1]) * t

    approx = mathutils.Vector((mm(x_mm), mm(y_center_mm + y_local), mm(base_z_mm + z_local_unscaled * height_scale)))
    normal_guess = mathutils.Vector((0.0, 0.85, 0.45)).normalized()

    depsgraph = bpy.context.evaluated_depsgraph_get()
    strap_eval = strap_obj.evaluated_get(depsgraph)
    origin = approx + normal_guess * mm(100.0)
    direction = -normal_guess
    ok, hit_loc, hit_normal, _ = strap_eval.ray_cast(origin, direction, distance=mm(200.0))

    if not ok:
        # Fallback: keep the analytic estimate if the ray missed.
        hit_loc, hit_normal = approx, normal_guess

    n = hit_normal.normalized()
    if n.z < 0:
        n = -n  # keep it pointing outward/up, not into the sole
    world_x_axis = mathutils.Vector((1.0, 0.0, 0.0))
    tag_x = (world_x_axis - n * world_x_axis.dot(n))
    if tag_x.length < 1e-6:
        tag_x = mathutils.Vector((1.0, 0.0, 0.0))
    tag_x.normalize()
    tag_y = n.cross(tag_x).normalized()

    rot_mat = mathutils.Matrix((tag_x, tag_y, n)).transposed()

    embed = mm(0.6)  # sink the tag slightly into the strap surface for a seated look
    obj.location = hit_loc - n * embed
    obj.rotation_euler = rot_mat.to_euler()

"""Shared helpers for the HudLab Slide parametric build."""
import bpy
import bmesh
import math

MM = 0.001  # 1 Blender unit = 1 meter; we author in mm and scale down.


def mm(v):
    return v * MM


def new_collection(name, parent):
    if name in bpy.data.collections:
        col = bpy.data.collections[name]
    else:
        col = bpy.data.collections.new(name)
    if col.name not in [c.name for c in parent.children]:
        parent.children.link(col)
    return col


def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def new_mesh_object(name, collection):
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    return obj


def bm_to_mesh(bm, mesh_obj):
    bm.normal_update()
    bm.to_mesh(mesh_obj.data)
    bm.free()
    mesh_obj.data.update()


def apply_transform(obj, location=False, rotation=True, scale=True):
    bpy.context.view_layer.objects.active = obj
    for o in bpy.context.selected_objects:
        o.select_set(False)
    obj.select_set(True)
    bpy.ops.object.transform_apply(location=location, rotation=rotation, scale=scale)


def shade_auto_smooth(obj, angle_deg=35):
    obj.data.use_auto_smooth = True if hasattr(obj.data, "use_auto_smooth") else None
    try:
        obj.data.use_auto_smooth = True
        obj.data.auto_smooth_angle = math.radians(angle_deg)
    except Exception:
        pass
    for p in obj.data.polygons:
        p.use_smooth = True


def smoothstep(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def lerp(a, b, t):
    return a + (b - a) * t


def repair_zero_area_uvs(obj, area_eps=1e-8):
    """Bevel modifiers (applied) generate new faces along the beveled edges that inherit no
    UV data (zero-area, all loops collapsed at the origin). Find just those faces and give
    them a real (if minor - they're thin edge strips, not the visible print area) UV via
    Smart UV Project, leaving the carefully-authored UVs on the rest of the mesh untouched.
    """
    import bmesh as _bmesh
    bpy.context.view_layer.objects.active = obj
    for o in bpy.context.selected_objects:
        o.select_set(False)
    obj.select_set(True)

    bpy.ops.object.mode_set(mode='EDIT')
    bm = _bmesh.from_edit_mesh(obj.data)
    uv_layer = bm.loops.layers.uv.active
    for f in bm.faces:
        f.select = False
    bad = 0
    if uv_layer:
        for f in bm.faces:
            uvs = [l[uv_layer].uv for l in f.loops]
            area = 0.0
            for i in range(len(uvs)):
                x1, y1 = uvs[i]
                x2, y2 = uvs[(i + 1) % len(uvs)]
                area += x1 * y2 - x2 * y1
            if abs(area) < area_eps:
                f.select = True
                bad += 1
    _bmesh.update_edit_mesh(obj.data)
    if bad:
        bpy.ops.uv.smart_project(angle_limit=1.1519, island_margin=0.02)
    bpy.ops.object.mode_set(mode='OBJECT')
    return bad


def surface_ray_cast(obj, approx_world_point, normal_guess, max_dist_mm=120.0):
    """Ray-cast toward an evaluated (post-modifier) object's surface from just outside it,
    so placement follows the true surface rather than a hand-derived tangent-plane guess.
    Returns (hit_location, hit_normal, success). Falls back to the approx point/normal on miss.
    """
    depsgraph = bpy.context.evaluated_depsgraph_get()
    obj_eval = obj.evaluated_get(depsgraph)
    origin = approx_world_point + normal_guess * mm(60.0)
    direction = -normal_guess
    ok, hit_loc, hit_normal, _ = obj_eval.ray_cast(origin, direction, distance=mm(max_dist_mm))
    if not ok:
        return approx_world_point, normal_guess, False
    return hit_loc, hit_normal.normalized(), True


def catmull_rom_profile(pts, t):
    """Smooth (C1) interpolation through control points [(t_i, v_i), ...], t_i ascending.
    Clamps at the ends by duplicating the boundary points (no overshoot tangent there).
    """
    t = max(pts[0][0], min(pts[-1][0], t))
    n = len(pts)
    seg = 0
    for i in range(n - 1):
        if pts[i][0] <= t <= pts[i + 1][0]:
            seg = i
            break
    p1 = pts[seg]
    p2 = pts[seg + 1]
    p0 = pts[seg - 1] if seg - 1 >= 0 else p1
    p3 = pts[seg + 2] if seg + 2 < n else p2
    t1, t2 = p1[0], p2[0]
    local = 0.0 if t2 == t1 else (t - t1) / (t2 - t1)
    l2 = local * local
    l3 = l2 * local
    v0, v1, v2, v3 = p0[1], p1[1], p2[1], p3[1]
    return 0.5 * (
        (2 * v1)
        + (-v0 + v2) * local
        + (2 * v0 - 5 * v1 + 4 * v2 - v3) * l2
        + (-v0 + 3 * v1 - 3 * v2 + v3) * l3
    )

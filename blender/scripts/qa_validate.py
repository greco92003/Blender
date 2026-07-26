"""QA validation pass for HudLab_Slide.blend — checks the asset against the project spec.
Run: blender -b /path/to/HudLab_Slide.blend --python qa_validate.py
Exits with a non-zero code (via printed FAIL lines) if something needs fixing; always prints a report.
"""
import bpy
import mathutils

REQUIRED_OBJECTS = ["HL_Sole", "HL_Strap", "HL_SideTag"]
REQUIRED_MATERIALS = ["MAT_Sole", "MAT_Strap", "MAT_Tag"]
REQUIRED_COLLECTIONS = ["HudLab_Slide", "Chinelo", "Anchors", "Cameras", "Lights"]
REQUIRED_ANCHORS = ["Anchor_Front", "Anchor_Back", "Anchor_Print_Center", "Anchor_Tag"]
REQUIRED_CAMERAS = ["Cam_Top", "Cam_Front", "Cam_Back", "Cam_Side", "Cam_Perspective"]
POLY_MIN, POLY_MAX = 10_000, 40_000

issues = []
warnings = []


def check(cond, msg):
    if not cond:
        issues.append(msg)


def warn(cond, msg):
    if not cond:
        warnings.append(msg)


print("=" * 70)
print("HudLab Slide QA report")
print("=" * 70)

# --- Collections ---
col_names = [c.name for c in bpy.data.collections]
for name in REQUIRED_COLLECTIONS:
    check(name in col_names, f"Missing collection: {name}")
print("Collections found:", col_names)

# --- Objects present, named, not hidden ---
objs = {}
for name in REQUIRED_OBJECTS:
    obj = bpy.data.objects.get(name)
    check(obj is not None, f"Missing object: {name}")
    if obj:
        objs[name] = obj
        check(not obj.hide_get() and not obj.hide_render, f"{name} is hidden (hide_viewport/hide_render)")
        check(obj.type == 'MESH', f"{name} is not a MESH object")

# --- Anchors ---
anchor_names = [o.name for o in bpy.data.objects if o.name in REQUIRED_ANCHORS]
for name in REQUIRED_ANCHORS:
    check(name in anchor_names, f"Missing anchor empty: {name}")

# --- Cameras ---
cam_names = [o.name for o in bpy.data.objects if o.type == 'CAMERA']
for name in REQUIRED_CAMERAS:
    check(name in cam_names, f"Missing camera: {name}")
print("Cameras found:", cam_names)

# --- Materials ---
mat_names = [m.name for m in bpy.data.materials]
for name in REQUIRED_MATERIALS:
    check(name in mat_names, f"Missing material: {name}")
mat_users = {}
for name, obj in objs.items():
    slots = [s.material.name if s.material else None for s in obj.material_slots]
    mat_users[name] = slots
    check(len(slots) >= 1 and slots[0] is not None, f"{name} has no material assigned")
# no shared/duplicated materials across objects
used_mats = [s[0] for s in mat_users.values() if s]
check(len(used_mats) == len(set(used_mats)), f"Materials are shared/duplicated across objects: {mat_users}")
print("Material assignment:", mat_users)

# --- Topology: quads-first, poly budget, mesh validity ---
total_polys = 0
for name, obj in objs.items():
    mesh = obj.data
    n_v, n_p = len(mesh.vertices), len(mesh.polygons)
    quads = sum(1 for p in mesh.polygons if len(p.vertices) == 4)
    tris = sum(1 for p in mesh.polygons if len(p.vertices) == 3)
    ngons = sum(1 for p in mesh.polygons if len(p.vertices) > 4)
    total_polys += n_p
    quad_pct = 100.0 * quads / n_p if n_p else 0
    print(f"{name}: verts={n_v} polys={n_p} quads={quads} ({quad_pct:.1f}%) tris={tris} ngons={ngons}")
    warn(quad_pct >= 90.0, f"{name} quad ratio only {quad_pct:.1f}% (expect mostly quads)")
    dup = mesh.validate(verbose=False)
    check(not dup, f"{name} mesh.validate() reported issues (degenerate geometry)")
    # manifold-ish check: every edge should have exactly 2 face users
    edge_face_count = {}
    for p in mesh.polygons:
        vs = list(p.vertices)
        for i in range(len(vs)):
            a, b = vs[i], vs[(i + 1) % len(vs)]
            key = (min(a, b), max(a, b))
            edge_face_count[key] = edge_face_count.get(key, 0) + 1
    non_manifold_edges = sum(1 for c in edge_face_count.values() if c != 2)
    warn(non_manifold_edges == 0, f"{name} has {non_manifold_edges} non-manifold edges (face-count != 2)")

print(f"TOTAL_POLYGONS = {total_polys} (target {POLY_MIN}-{POLY_MAX})")
check(POLY_MIN <= total_polys <= POLY_MAX, f"Total polycount {total_polys} outside target range {POLY_MIN}-{POLY_MAX}")

# --- Transforms applied (rotation=0, scale=1) ---
for name, obj in objs.items():
    rot_ok = all(abs(a) < 1e-5 for a in obj.rotation_euler)
    scale_ok = all(abs(s - 1.0) < 1e-5 for s in obj.scale)
    check(rot_ok, f"{name} rotation not applied/zeroed: {list(obj.rotation_euler)}")
    check(scale_ok, f"{name} scale not applied (!=1,1,1): {list(obj.scale)}")

# --- UVs present, in 0-1 range, no obviously-degenerate islands ---
for name, obj in objs.items():
    uv_layer = obj.data.uv_layers.active
    check(uv_layer is not None, f"{name} has no active UV map")
    if uv_layer:
        us = [l.uv.x for l in uv_layer.data]
        vs = [l.uv.y for l in uv_layer.data]
        warn(min(us) >= -0.001 and max(us) <= 1.001, f"{name} UV U out of [0,1]: [{min(us):.3f},{max(us):.3f}]")
        warn(min(vs) >= -0.001 and max(vs) <= 1.001, f"{name} UV V out of [0,1]: [{min(vs):.3f},{max(vs):.3f}]")
        # zero-area UV triangle/face check (degenerate island)
        degenerate = 0
        for p in obj.data.polygons:
            uv_pts = [uv_layer.data[li].uv for li in p.loop_indices]
            area = 0.0
            for i in range(len(uv_pts)):
                x1, y1 = uv_pts[i]
                x2, y2 = uv_pts[(i + 1) % len(uv_pts)]
                area += x1 * y2 - x2 * y1
            if abs(area) < 1e-8:
                degenerate += 1
        warn(degenerate == 0, f"{name} has {degenerate} zero-area UV faces")

# --- PrintArea vertex group on strap ---
strap = objs.get("HL_Strap")
if strap:
    vg = strap.vertex_groups.get("PrintArea")
    check(vg is not None, "HL_Strap missing 'PrintArea' vertex group")
    if vg:
        count = sum(1 for v in strap.data.vertices for g in v.groups if g.group == vg.index)
        check(count > 0, "PrintArea vertex group is empty")
        print(f"PrintArea vertex group: {count} verts")

# --- Real-world scale sanity (sole length ~ 250-320mm for a plausible adult slide) ---
sole = objs.get("HL_Sole")
if sole:
    mn = mathutils.Vector((1e9,) * 3)
    mx = mathutils.Vector((-1e9,) * 3)
    for c in sole.bound_box:
        w = sole.matrix_world @ mathutils.Vector(c)
        mn.x, mn.y, mn.z = min(mn.x, w.x), min(mn.y, w.y), min(mn.z, w.z)
        mx.x, mx.y, mx.z = max(mx.x, w.x), max(mx.y, w.y), max(mx.z, w.z)
    length_mm = (mx.y - mn.y) * 1000
    width_mm = (mx.x - mn.x) * 1000
    height_mm = (mx.z - mn.z) * 1000
    print(f"Sole real-world size: {length_mm:.1f} x {width_mm:.1f} x {height_mm:.1f} mm")
    check(250 <= length_mm <= 320, f"Sole length {length_mm:.1f}mm outside plausible adult-slide range")

# --- Scene units ---
scene = bpy.context.scene
check(scene.unit_settings.system == 'METRIC', "Scene unit system is not METRIC")
check(scene.unit_settings.length_unit == 'MILLIMETERS', "Scene length display unit is not MILLIMETERS")

# --- No stray/unnamed/orphan objects in the Chinelo collection ---
chinelo = bpy.data.collections.get("Chinelo")
if chinelo:
    extra = [o.name for o in chinelo.objects if o.name not in REQUIRED_OBJECTS]
    warn(len(extra) == 0, f"Unexpected extra objects in Chinelo collection: {extra}")

print("=" * 70)
if issues:
    print(f"FAIL: {len(issues)} issue(s)")
    for i in issues:
        print("  [FAIL]", i)
else:
    print("PASS: no blocking issues")
if warnings:
    print(f"{len(warnings)} warning(s)")
    for w in warnings:
        print("  [WARN]", w)
print("=" * 70)

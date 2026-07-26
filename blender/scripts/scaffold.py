"""Scene scaffold: units, collection hierarchy, anchors, origin/transform finalization."""
import bpy
import mathutils
from common import mm, new_collection, apply_transform


def setup_units(scene):
    scene.unit_settings.system = 'METRIC'
    scene.unit_settings.length_unit = 'MILLIMETERS'
    scene.unit_settings.scale_length = 1.0


def build_collections(scene):
    root = new_collection("HudLab_Slide", scene.collection)
    chinelo = new_collection("Chinelo", root)
    anchors = new_collection("Anchors", root)
    cameras = new_collection("Cameras", root)
    lights = new_collection("Lights", root)
    return {"root": root, "chinelo": chinelo, "anchors": anchors, "cameras": cameras, "lights": lights}


def _new_empty(name, collection, location, rotation_euler=(0, 0, 0), size=0.015, empty_type='PLAIN_AXES'):
    obj = bpy.data.objects.new(name, None)
    obj.empty_display_type = empty_type
    obj.empty_display_size = size
    obj.location = location
    obj.rotation_euler = rotation_euler
    collection.objects.link(obj)
    return obj


def create_anchors(anchors_col, sole_mod, strap_mod, strap_obj):
    # Anchor_Front / Anchor_Back: toe and heel tips at ground level.
    anchor_back = _new_empty("Anchor_Back", anchors_col, (0.0, 0.0, 0.0))
    anchor_front = _new_empty("Anchor_Front", anchors_col, (0.0, mm(sole_mod.LENGTH), 0.0))

    # Anchor_Print_Center: mid-width, mid-height point on the strap's front (print) face,
    # found by ray-casting against the real (post-bevel) surface.
    s = 0.5
    hw_back = sole_mod.half_width(strap_mod.STRAP_BACK_T) * strap_mod.WIDTH_INSET
    hw_front = sole_mod.half_width(strap_mod.STRAP_FRONT_T) * strap_mod.WIDTH_INSET
    hw = max(hw_back, hw_front)
    x_mm = -hw + s * (2 * hw)
    height_scale = strap_mod.OUTER_HEIGHT_SCALE + (strap_mod.INNER_HEIGHT_SCALE - strap_mod.OUTER_HEIGHT_SCALE) * s
    y_center_t = (strap_mod.STRAP_BACK_T + strap_mod.STRAP_FRONT_T) / 2
    y_center_mm = y_center_t * sole_mod.LENGTH
    base_z_mm = strap_mod._sole_top_z(y_center_t)
    p_upper = strap_mod.OUTER_PROFILE[6]
    p_lower = strap_mod.OUTER_PROFILE[7]
    t_blend = 0.5
    y_local = p_upper[0] + (p_lower[0] - p_upper[0]) * t_blend
    z_local = p_upper[1] + (p_lower[1] - p_upper[1]) * t_blend
    approx = mathutils.Vector((mm(x_mm), mm(y_center_mm + y_local), mm(base_z_mm + z_local * height_scale)))
    from common import surface_ray_cast
    normal_guess = mathutils.Vector((0.0, 0.85, 0.45)).normalized()
    hit_loc, hit_normal, ok = surface_ray_cast(strap_obj, approx, normal_guess)
    n = hit_normal if hit_normal.z >= 0 else -hit_normal
    anchor_print = _new_empty("Anchor_Print_Center", anchors_col, hit_loc, size=0.012, empty_type='PLAIN_AXES')
    world_x_axis = mathutils.Vector((1.0, 0.0, 0.0))
    tag_x = (world_x_axis - n * world_x_axis.dot(n))
    tag_x.normalize()
    tag_y = n.cross(tag_x).normalized()
    rot_mat = mathutils.Matrix((tag_x, tag_y, n)).transposed()
    anchor_print.rotation_euler = rot_mat.to_euler()

    return {
        "Anchor_Back": anchor_back,
        "Anchor_Front": anchor_front,
        "Anchor_Print_Center": anchor_print,
    }


def set_origin_world(obj, world_point):
    scene = bpy.context.scene
    prev_cursor = scene.cursor.location.copy()
    scene.cursor.location = world_point
    bpy.context.view_layer.objects.active = obj
    for o in bpy.context.selected_objects:
        o.select_set(False)
    obj.select_set(True)
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    obj.select_set(False)
    scene.cursor.location = prev_cursor


def set_origin_geometry_bounds(obj):
    bpy.context.view_layer.objects.active = obj
    for o in bpy.context.selected_objects:
        o.select_set(False)
    obj.select_set(True)
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
    obj.select_set(False)


def finalize_mesh_object(obj, shade_smooth_angle=35):
    import math
    obj.data.use_auto_smooth = True
    obj.data.auto_smooth_angle = math.radians(shade_smooth_angle)
    for p in obj.data.polygons:
        p.use_smooth = True
    apply_transform(obj, location=False, rotation=True, scale=True)

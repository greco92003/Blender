"""Master build script for the HudLab Slide parametric asset.
Run: blender -b --python build_all.py
Produces: /home/user/Blender/blender/output/HudLab_Slide.blend
"""
import bpy
import sys
import os
import math

sys.path.insert(0, os.path.dirname(__file__))
import importlib
import common, sole, strap, tag, scaffold
importlib.reload(common)
importlib.reload(sole)
importlib.reload(strap)
importlib.reload(tag)
importlib.reload(scaffold)

try:
    import materials
    importlib.reload(materials)
    HAVE_MATERIALS = True
except ImportError:
    HAVE_MATERIALS = False

try:
    import cameras_lighting
    importlib.reload(cameras_lighting)
    HAVE_CAMERAS_LIGHTING = True
except ImportError:
    HAVE_CAMERAS_LIGHTING = False


def apply_all_modifiers(obj):
    bpy.context.view_layer.objects.active = obj
    for o in bpy.context.selected_objects:
        o.select_set(False)
    obj.select_set(True)
    for mod in list(obj.modifiers):
        bpy.ops.object.modifier_apply(modifier=mod.name)
    obj.select_set(False)


def bounds_world(obj):
    import mathutils
    mn = mathutils.Vector((1e9, 1e9, 1e9))
    mx = mathutils.Vector((-1e9, -1e9, -1e9))
    for c in obj.bound_box:
        w = obj.matrix_world @ mathutils.Vector(c)
        mn.x, mn.y, mn.z = min(mn.x, w.x), min(mn.y, w.y), min(mn.z, w.z)
        mx.x, mx.y, mx.z = max(mx.x, w.x), max(mx.y, w.y), max(mx.z, w.z)
    return mn, mx


def main():
    common.reset_scene()
    scene = bpy.context.scene
    scaffold.setup_units(scene)
    cols = scaffold.build_collections(scene)

    sole_obj = sole.build_sole(cols["chinelo"])
    strap_obj = strap.build_strap(cols["chinelo"])
    bpy.context.view_layer.update()
    tag_obj = tag.build_tag(cols["chinelo"], strap_obj)
    bpy.context.view_layer.update()

    anchors = scaffold.create_anchors(cols["anchors"], sole, strap, strap_obj)
    anchor_tag = scaffold._new_empty(
        "Anchor_Tag", cols["anchors"], tag_obj.location, tag_obj.rotation_euler, size=0.01
    )
    tag_obj.parent = anchor_tag
    tag_obj.matrix_parent_inverse = anchor_tag.matrix_world.inverted()

    # Apply modifiers now (while pre-modifier data is no longer needed) so the delivered
    # asset is clean static geometry, not modifier-dependent.
    for obj in (sole_obj, strap_obj, tag_obj):
        apply_all_modifiers(obj)
        n_fixed = common.repair_zero_area_uvs(obj)
        if n_fixed:
            print(f"Repaired {n_fixed} zero-area UV faces on {obj.name} (bevel-introduced)")

    # Origins: Sole pivots at ground level, centered under the product (turntable-friendly).
    sole_mn, sole_mx = bounds_world(sole_obj)
    sole_center_world = ((sole_mn.x + sole_mx.x) / 2, (sole_mn.y + sole_mx.y) / 2, 0.0)
    scaffold.set_origin_world(sole_obj, sole_center_world)

    # Strap pivots at its own geometry center (natural rotate/scale pivot for automation).
    scaffold.set_origin_geometry_bounds(strap_obj)

    # Tag: origin stays at its build-time local (0,0,0), which IS the strap-attachment point -
    # do not recenter, that's the whole point of it being swap-friendly.

    for obj in (sole_obj, strap_obj, tag_obj):
        scaffold.finalize_mesh_object(obj)

    if HAVE_MATERIALS:
        mats = materials.build_materials()
        materials.assign_materials(sole_obj, strap_obj, tag_obj, mats)
    else:
        print("WARNING: materials module not available yet, skipping material assignment")

    if HAVE_CAMERAS_LIGHTING:
        try:
            cameras_lighting.build_cameras(cols["cameras"])
            cameras_lighting.build_lighting(cols["lights"])
        except Exception as e:
            print("WARNING: cameras_lighting errored (agent still iterating?):", e)
    else:
        print("WARNING: cameras_lighting module not available yet, skipping cameras/lights")

    out_path = "/home/user/Blender/blender/output/HudLab_Slide.blend"
    bpy.ops.wm.save_as_mainfile(filepath=out_path)
    print("Saved:", out_path)

    # Summary report
    for obj in (sole_obj, strap_obj, tag_obj):
        quads = sum(1 for p in obj.data.polygons if len(p.vertices) == 4)
        tris = sum(1 for p in obj.data.polygons if len(p.vertices) == 3)
        ngons = sum(1 for p in obj.data.polygons if len(p.vertices) > 4)
        print(f"{obj.name}: verts={len(obj.data.vertices)} polys={len(obj.data.polygons)} "
              f"quads={quads} tris={tris} ngons={ngons} loc={list(obj.location)} "
              f"rot={list(obj.rotation_euler)} scale={list(obj.scale)}")
    total_polys = sum(len(o.data.polygons) for o in (sole_obj, strap_obj, tag_obj))
    print("TOTAL_POLYGONS", total_polys)


if __name__ == "__main__":
    main()

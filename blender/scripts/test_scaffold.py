import bpy, sys, os
sys.path.insert(0, os.path.dirname(__file__))
import importlib
import common, sole, strap, tag, scaffold
importlib.reload(common)
importlib.reload(sole)
importlib.reload(strap)
importlib.reload(tag)
importlib.reload(scaffold)

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

# Anchor_Tag: empty at the tag's current world transform, then parent the tag to it.
anchor_tag = scaffold._new_empty("Anchor_Tag", cols["anchors"], tag_obj.location, tag_obj.rotation_euler, size=0.01)
tag_obj.parent = anchor_tag
tag_obj.matrix_parent_inverse = anchor_tag.matrix_world.inverted()

print("Collections:", [c.name for c in bpy.data.collections])
print("Anchors:", [o.name for o in cols["anchors"].objects])
print("Chinelo objs:", [o.name for o in cols["chinelo"].objects])
print("Tag parent:", tag_obj.parent.name if tag_obj.parent else None)
print("Unit system:", scene.unit_settings.system, scene.unit_settings.length_unit)

bpy.ops.wm.save_as_mainfile(filepath="/home/user/Blender/blender/output/test_scaffold.blend")

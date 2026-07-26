import bpy, sys, os
sys.path.insert(0, os.path.dirname(__file__))
import importlib
import common, sole, strap, tag
importlib.reload(common)
importlib.reload(sole)
importlib.reload(strap)
importlib.reload(tag)

common.reset_scene()
col = bpy.context.scene.collection
sole_obj = sole.build_sole(col)
strap_obj = strap.build_strap(col)
bpy.context.view_layer.update()
tag_obj = tag.build_tag(col, strap_obj)
bpy.context.view_layer.update()

for obj in (sole_obj, strap_obj, tag_obj):
    print(obj.name, "VERTS", len(obj.data.vertices), "POLYS", len(obj.data.polygons), "LOC", list(obj.location))

bpy.ops.wm.save_as_mainfile(filepath="/home/user/Blender/blender/output/test_full.blend")

import bpy, sys, os
sys.path.insert(0, os.path.dirname(__file__))
import importlib
import common, sole, strap
importlib.reload(common)
importlib.reload(sole)
importlib.reload(strap)

common.reset_scene()
col = bpy.context.scene.collection
sole_obj = sole.build_sole(col)
strap_obj = strap.build_strap(col)
bpy.context.view_layer.update()

for obj in (sole_obj, strap_obj):
    print(obj.name, "VERTS", len(obj.data.vertices), "POLYS", len(obj.data.polygons))
    quads = sum(1 for p in obj.data.polygons if len(p.vertices) == 4)
    tris = sum(1 for p in obj.data.polygons if len(p.vertices) == 3)
    ngons = sum(1 for p in obj.data.polygons if len(p.vertices) > 4)
    print("  QUADS", quads, "TRIS", tris, "NGONS", ngons, "VALID_ISSUES", obj.data.validate(verbose=True))
    print("  DIMENSIONS_MM", [d*1000 for d in obj.dimensions])

bpy.ops.wm.save_as_mainfile(filepath="/home/user/Blender/blender/output/test_strap.blend")

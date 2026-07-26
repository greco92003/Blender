import bpy, sys, os
sys.path.insert(0, os.path.dirname(__file__))
import importlib
import common, sole
importlib.reload(common)
importlib.reload(sole)

common.reset_scene()
scene = bpy.context.scene
col = scene.collection
obj = sole.build_sole(col)
bpy.context.view_layer.update()

print("VERTS", len(obj.data.vertices), "POLYS", len(obj.data.polygons))
quads = sum(1 for p in obj.data.polygons if len(p.vertices) == 4)
tris = sum(1 for p in obj.data.polygons if len(p.vertices) == 3)
ngons = sum(1 for p in obj.data.polygons if len(p.vertices) > 4)
print("QUADS", quads, "TRIS", tris, "NGONS", ngons)

mesh_check = obj.data.validate(verbose=True)
print("MESH_VALID_ISSUES", mesh_check)

dims = obj.dimensions
print("DIMENSIONS_MM", dims.x*1000, dims.y*1000, dims.z*1000)

bpy.ops.wm.save_as_mainfile(filepath="/home/user/Blender/blender/output/test_sole.blend")

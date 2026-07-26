"""Debug script to check what's in the scene."""
import bpy
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
import importlib
import common
importlib.reload(common)

# Open the test blend file
test_blend = "/home/user/Blender/blender/output/test_full.blend"
bpy.ops.wm.open_mainfile(filepath=test_blend)

print("Objects in scene:")
for obj in bpy.context.scene.objects:
    if obj.type == 'MESH':
        print(f"  {obj.name}: {len(obj.data.vertices)} verts, {len(obj.data.polygons)} polys")
        print(f"    Location: {obj.location}")
        print(f"    Bounds: min={obj.bound_box[0]}, max={obj.bound_box[6]}")
    elif obj.type == 'CAMERA':
        print(f"  {obj.name}: CAMERA at {obj.location}")
    elif obj.type == 'LIGHT':
        print(f"  {obj.name}: LIGHT at {obj.location}")

print("\nCollections:")
for col in bpy.data.collections:
    print(f"  {col.name}: {len(col.objects)} objects")
    for obj in col.objects:
        print(f"    - {obj.name} ({obj.type})")

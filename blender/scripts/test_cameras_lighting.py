"""Test harness for cameras_lighting.py module.

Opens test_full.blend, creates cameras and lighting, and renders test images.
"""
import bpy
import sys
import os

# Setup paths
sys.path.insert(0, os.path.dirname(__file__))
import importlib
import common, cameras_lighting
importlib.reload(common)
importlib.reload(cameras_lighting)

# Open the test blend file
test_blend = "/home/user/Blender/blender/output/test_full.blend"
bpy.ops.wm.open_mainfile(filepath=test_blend)

print(f"Opened {test_blend}")

# Create or get collections for cameras and lights
scene = bpy.context.scene
cameras_col = common.new_collection("Cameras", scene.collection)
lights_col = common.new_collection("Lights", scene.collection)

print("Created/got collections")

# Build cameras and lighting
cameras = cameras_lighting.build_cameras(cameras_col)
lights = cameras_lighting.build_lighting(lights_col)

print(f"Built {len(cameras)} cameras and {len(lights)} lights")
for name, obj in cameras.items():
    print(f"  {name}: at {obj.location}")

# Set output directory
output_dir = "/home/user/Blender/blender/output"
os.makedirs(output_dir, exist_ok=True)

# Configure render settings for Cycles tests
scene.render.engine = 'CYCLES'
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.render.image_settings.file_format = 'PNG'

# Cycles settings: 64 samples, no denoising
scene.cycles.samples = 64
scene.cycles.use_denoising = False

# Disable denoising on all view layers
for view_layer in scene.view_layers:
    view_layer.cycles.use_denoising = False

print("\nRendering 5 cameras with Cycles (64 samples, no denoising)")
print("="*60)

# Test render from each camera with Cycles
camera_names = ["Cam_Top", "Cam_Front", "Cam_Back", "Cam_Side", "Cam_Perspective"]
for cam_name in camera_names:
    if cam_name in cameras:
        cam_obj = cameras[cam_name]
        scene.camera = cam_obj
        bpy.context.view_layer.update()

        output_path = os.path.join(output_dir, f"cam_{cam_name}.png")
        scene.render.filepath = output_path

        print(f"\nRendering {cam_name} to {output_path}")
        bpy.ops.render.render(write_still=True)
        print(f"  Done: {output_path}")

# Now do one final high-quality Cycles render from Cam_Perspective
print("\n" + "="*60)
print("Final render: Cam_Perspective with Cycles (128 samples for detail)")
print("="*60)

scene.cycles.samples = 128

cam_obj = cameras["Cam_Perspective"]
scene.camera = cam_obj
bpy.context.view_layer.update()

output_path = os.path.join(output_dir, "cam_Perspective_cycles.png")
scene.render.filepath = output_path

print(f"Rendering to {output_path}")
bpy.ops.render.render(write_still=True)
print(f"Done: {output_path}")

print("\n" + "="*60)
print("All renders complete!")
print("="*60)

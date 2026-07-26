"""Camera and lighting setup for HudLab Slide product photography.

Creates 5 product cameras and a 3-point studio light rig with white background.
Coordinate system: X [-52, 52]mm width, Y [0, 290]mm length (heel to toe), Z [0, 58]mm height.
"""
import bpy
from mathutils import Vector, Euler
import math
from common import mm


def build_cameras(cameras_collection):
    """Create 5 orthographic-friendly product cameras framing the whole slide.

    Returns:
        dict: {"Cam_Top": obj, "Cam_Front": obj, "Cam_Back": obj, "Cam_Side": obj, "Cam_Perspective": obj}
    """
    cameras = {}

    # Product center (Y-axis midpoint is 145mm = heel(0) + (290/2))
    product_center_y = mm(145.0)
    product_center_z = mm(29.0)  # Roughly middle of product height

    # --- Cam_Top: straight down orthographic view ---
    cam_data = bpy.data.cameras.new("Cam_Top")
    cam_data.type = 'ORTHO'
    cam_data.ortho_scale = mm(350.0)  # Frame ~300mm with ~25mm margin on sides
    cam_data.clip_start = mm(1.0)
    cam_data.clip_end = mm(10000.0)

    cam_obj = bpy.data.objects.new("Cam_Top", cam_data)
    cam_obj.location = (mm(0.0), product_center_y, mm(250.0))
    # Rotation (0,0,0) looks down -Z by default; no rotation needed for top view
    cam_obj.rotation_euler = Euler((0.0, 0.0, 0.0), 'XYZ')
    cameras_collection.objects.link(cam_obj)
    cameras["Cam_Top"] = cam_obj

    # --- Cam_Front: perspective view of toe end ---
    cam_data = bpy.data.cameras.new("Cam_Front")
    cam_data.type = 'PERSP'
    cam_data.lens = 50.0  # 50mm lens
    cam_data.clip_start = mm(1.0)
    cam_data.clip_end = mm(10000.0)

    cam_obj = bpy.data.objects.new("Cam_Front", cam_data)
    # Position in front of toe (Y > 290mm), at product height
    cam_obj.location = (mm(0.0), mm(310.0), mm(35.0))
    # Looking back along -Y toward product
    cam_obj.rotation_euler = Euler((math.radians(0.0), 0.0, math.radians(0.0)), 'XYZ')
    cameras_collection.objects.link(cam_obj)
    cameras["Cam_Front"] = cam_obj

    # --- Cam_Back: perspective view of heel end ---
    cam_data = bpy.data.cameras.new("Cam_Back")
    cam_data.type = 'PERSP'
    cam_data.lens = 50.0  # 50mm lens
    cam_data.clip_start = mm(1.0)
    cam_data.clip_end = mm(10000.0)

    cam_obj = bpy.data.objects.new("Cam_Back", cam_data)
    # Position behind heel (Y < 0), at product height, looking forward
    cam_obj.location = (mm(0.0), mm(-30.0), mm(35.0))
    # Looking forward along +Y toward product (180 degree yaw)
    cam_obj.rotation_euler = Euler((math.radians(0.0), 0.0, math.radians(180.0)), 'XYZ')
    cameras_collection.objects.link(cam_obj)
    cameras["Cam_Back"] = cam_obj

    # --- Cam_Side: full side profile orthographic ---
    cam_data = bpy.data.cameras.new("Cam_Side")
    cam_data.type = 'ORTHO'
    # Frame both length (290mm) and height (58mm) plus margins
    cam_data.ortho_scale = mm(350.0)  # Tall enough for both dimensions
    cam_data.clip_start = mm(1.0)
    cam_data.clip_end = mm(10000.0)

    cam_obj = bpy.data.objects.new("Cam_Side", cam_data)
    # Position far to the side (+X), looking along -X axis
    cam_obj.location = (mm(200.0), product_center_y, mm(50.0))
    # Rotate 90 degrees around Z so we're looking along X axis
    cam_obj.rotation_euler = Euler((math.radians(0.0), math.radians(90.0), 0.0), 'XYZ')
    cameras_collection.objects.link(cam_obj)
    cameras["Cam_Side"] = cam_obj

    # --- Cam_Perspective: 3/4 hero shot ---
    cam_data = bpy.data.cameras.new("Cam_Perspective")
    cam_data.type = 'PERSP'
    cam_data.lens = 55.0  # Slightly wider than 50mm for nice framing
    cam_data.clip_start = mm(1.0)
    cam_data.clip_end = mm(10000.0)

    cam_obj = bpy.data.objects.new("Cam_Perspective", cam_data)
    # Elevated, offset to front-left corner (front-side = high Y, -X)
    # Looking down at ~35 degree angle
    cam_obj.location = (mm(-120.0), mm(220.0), mm(180.0))
    # Rotation: looking down-ish and slightly back
    cam_obj.rotation_euler = Euler((math.radians(-35.0), 0.0, math.radians(-25.0)), 'XYZ')
    cameras_collection.objects.link(cam_obj)
    cameras["Cam_Perspective"] = cam_obj

    return cameras


def build_lighting(lights_collection):
    """Create a 3-point studio lighting rig with white background.

    Sets up:
    - Key light (main): overhead front
    - Fill light: side fill
    - Rim light: subtle back rim
    - White world background
    - White infinity backdrop plane

    Returns:
        dict: {"Light_Key": obj, "Light_Fill": obj, "Light_Rim": obj, "Light_Backdrop": obj}
    """
    lights = {}

    # Product center for light positioning
    product_center_y = mm(145.0)
    product_center_z = mm(29.0)

    # --- Key light: main overhead-front light ---
    # Using physically realistic power: 2W for close-in product key light at ~250mm distance
    light_data = bpy.data.lights.new("Light_Key", 'AREA')
    light_data.energy = 2.0  # Watts: physically realistic for close-in product lighting
    light_data.size = mm(300.0)  # Large soft area light for diffuse illumination

    light_obj = bpy.data.objects.new("Light_Key", light_data)
    # Positioned above-front of product
    light_obj.location = (mm(100.0), mm(180.0), mm(250.0))
    # Angled down toward product center
    light_obj.rotation_euler = Euler((math.radians(-45.0), math.radians(-30.0), 0.0), 'XYZ')
    lights_collection.objects.link(light_obj)
    lights["Light_Key"] = light_obj

    # --- Fill light: opposite side, softer ---
    light_data = bpy.data.lights.new("Light_Fill", 'AREA')
    light_data.energy = 1.0  # 1W fill light for balance, half the key light intensity
    light_data.size = mm(400.0)  # Larger area for soft fill

    light_obj = bpy.data.objects.new("Light_Fill", light_data)
    # Positioned to the opposite side (+X) and slightly back
    light_obj.location = (mm(250.0), mm(100.0), mm(150.0))
    light_obj.rotation_euler = Euler((math.radians(-30.0), math.radians(60.0), 0.0), 'XYZ')
    lights_collection.objects.link(light_obj)
    lights["Light_Fill"] = light_obj

    # --- Rim light: subtle back highlight ---
    light_data = bpy.data.lights.new("Light_Rim", 'AREA')
    light_data.energy = 0.8  # 0.8W subtle rim light for back edge definition
    light_data.size = mm(200.0)

    light_obj = bpy.data.objects.new("Light_Rim", light_data)
    # Positioned behind-high
    light_obj.location = (mm(-150.0), mm(-50.0), mm(200.0))
    light_obj.rotation_euler = Euler((math.radians(-60.0), math.radians(150.0), 0.0), 'XYZ')
    lights_collection.objects.link(light_obj)
    lights["Light_Rim"] = light_obj

    # --- Set world background to white ---
    # Get or create world
    if "World" not in bpy.data.worlds:
        world = bpy.data.worlds.new("World")
    else:
        world = bpy.data.worlds["World"]

    # Set as the current scene's world if needed
    if bpy.context.scene.world is None:
        bpy.context.scene.world = world
    else:
        world = bpy.context.scene.world

    world.use_nodes = True
    nodes = world.node_tree.nodes
    nodes.clear()

    # Create simple white emission background
    bg_node = nodes.new('ShaderNodeBackground')
    bg_node.inputs['Color'].default_value = (1.0, 1.0, 1.0, 1.0)  # White
    bg_node.inputs['Strength'].default_value = 1.0

    output_node = nodes.new('ShaderNodeOutputWorld')
    world.node_tree.links.new(bg_node.outputs['Background'], output_node.inputs['Surface'])

    return lights

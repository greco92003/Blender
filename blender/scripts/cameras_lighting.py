"""Camera and lighting setup for HudLab Slide product photography.

Creates 5 product cameras and a 3-point studio light rig with white background.
Coordinate system: X [-52, 52]mm width, Y [0, 290]mm length (heel to toe), Z [0, 58]mm height.
"""
import bpy
from mathutils import Vector, Euler
import math
from common import mm


def _look_at(cam_obj, target):
    """Point a camera object's -Z axis at `target` (world space), +Y up - robust replacement
    for hand-picked Euler guesses, which were leaving Front/Back/Perspective mis-framed."""
    direction = target - cam_obj.location
    cam_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()


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

    target = Vector((mm(0.0), product_center_y, mm(22.0)))

    # --- Cam_Front: straight-on view from the toe end, looking back along -Y ---
    cam_data = bpy.data.cameras.new("Cam_Front")
    cam_data.type = 'PERSP'
    cam_data.lens = 45.0
    cam_data.clip_start = mm(0.5)
    cam_data.clip_end = mm(10000.0)

    cam_obj = bpy.data.objects.new("Cam_Front", cam_data)
    cam_obj.location = Vector((mm(0.0), mm(430.0), mm(95.0)))
    _look_at(cam_obj, target)
    cameras_collection.objects.link(cam_obj)
    cameras["Cam_Front"] = cam_obj

    # --- Cam_Back: straight-on view from the heel end, looking forward along +Y ---
    cam_data = bpy.data.cameras.new("Cam_Back")
    cam_data.type = 'PERSP'
    cam_data.lens = 45.0
    cam_data.clip_start = mm(0.5)
    cam_data.clip_end = mm(10000.0)

    cam_obj = bpy.data.objects.new("Cam_Back", cam_data)
    cam_obj.location = Vector((mm(0.0), mm(-285.0), mm(95.0)))
    _look_at(cam_obj, target)
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

    # --- Cam_Perspective: 3/4 hero shot elevated ---
    cam_data = bpy.data.cameras.new("Cam_Perspective")
    cam_data.type = 'PERSP'
    cam_data.lens = 50.0  # Moderate focal length for 3/4 hero view
    cam_data.clip_start = mm(0.5)
    cam_data.clip_end = mm(10000.0)

    cam_obj = bpy.data.objects.new("Cam_Perspective", cam_data)
    # Elevated 3/4 hero angle, offset toward the toe/lateral corner.
    cam_obj.location = Vector((mm(220.0), mm(340.0), mm(180.0)))
    _look_at(cam_obj, Vector((mm(0.0), product_center_y, mm(20.0))))
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

    target = Vector((mm(0.0), product_center_y, product_center_z))

    # --- Key light: main overhead-front light ---
    light_data = bpy.data.lights.new("Light_Key", 'AREA')
    light_data.energy = 0.6
    light_data.size = mm(300.0)  # Large soft area light for diffuse illumination

    light_obj = bpy.data.objects.new("Light_Key", light_data)
    light_obj.location = Vector((mm(100.0), mm(180.0), mm(250.0)))
    _look_at(light_obj, target)
    lights_collection.objects.link(light_obj)
    lights["Light_Key"] = light_obj

    # --- Fill light: opposite side, softer ---
    light_data = bpy.data.lights.new("Light_Fill", 'AREA')
    light_data.energy = 0.3
    light_data.size = mm(400.0)  # Larger area for soft fill

    light_obj = bpy.data.objects.new("Light_Fill", light_data)
    light_obj.location = Vector((mm(250.0), mm(100.0), mm(150.0)))
    _look_at(light_obj, target)
    lights_collection.objects.link(light_obj)
    lights["Light_Fill"] = light_obj

    # --- Rim light: subtle back highlight ---
    light_data = bpy.data.lights.new("Light_Rim", 'AREA')
    light_data.energy = 0.2
    light_data.size = mm(200.0)

    light_obj = bpy.data.objects.new("Light_Rim", light_data)
    light_obj.location = Vector((mm(-150.0), mm(-50.0), mm(200.0)))
    _look_at(light_obj, target)
    lights_collection.objects.link(light_obj)
    lights["Light_Rim"] = light_obj

    # --- White infinity-cove backdrop (floor + curved wall) so the product sits in a clean
    # catalog sweep instead of floating on the raw world color. ---
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=(0.0, product_center_y, 0.0))
    backdrop = bpy.context.active_object
    backdrop.name = "Backdrop_Plane"
    backdrop.scale = (mm(1200.0), mm(1200.0), 1.0)
    mat = bpy.data.materials.get("MAT_Backdrop") or bpy.data.materials.new("MAT_Backdrop")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.92, 0.92, 0.92, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.85
    backdrop.data.materials.append(mat)
    for c in list(backdrop.users_collection):
        c.objects.unlink(backdrop)
    lights_collection.objects.link(backdrop)
    lights["Backdrop_Plane"] = backdrop

    # --- Predictable sRGB-like exposure so a true-black product and a white backdrop both
    # read correctly - AgX (Blender 4.0 default) lifts near-black albedos toward mid-gray. ---
    bpy.context.scene.view_settings.view_transform = 'Standard'

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

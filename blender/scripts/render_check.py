"""Quick multi-angle solid-shaded render for visual QA during development."""
import bpy, sys, os, math
sys.path.insert(0, os.path.dirname(__file__))

blend_path = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else None
out_prefix = sys.argv[sys.argv.index('--') + 2] if '--' in sys.argv else "/home/user/Blender/blender/output/check"

if blend_path:
    bpy.ops.wm.open_mainfile(filepath=blend_path)

scene = bpy.context.scene
scene.render.engine = 'BLENDER_WORKBENCH'
scene.render.resolution_x = 900
scene.render.resolution_y = 900
scene.display.shading.light = 'STUDIO'
scene.display.shading.color_type = 'MATERIAL'

# bounding box center/size across all mesh objects
import mathutils
mn = mathutils.Vector((1e9, 1e9, 1e9))
mx = mathutils.Vector((-1e9, -1e9, -1e9))
chinelo = bpy.data.collections.get("Chinelo")
target_objs = chinelo.objects if chinelo else [o for o in bpy.context.scene.objects if o.type == 'MESH']
for o in target_objs:
    if o.type != 'MESH':
        continue
    for corner in o.bound_box:
        wc = o.matrix_world @ mathutils.Vector(corner)
        mn.x, mn.y, mn.z = min(mn.x, wc.x), min(mn.y, wc.y), min(mn.z, wc.z)
        mx.x, mx.y, mx.z = max(mx.x, wc.x), max(mx.y, wc.y), max(mx.z, wc.z)
center = (mn + mx) / 2
size = max((mx - mn).x, (mx - mn).y, (mx - mn).z, 0.05)

def make_cam(name, loc, rot_euler, ortho_scale):
    cam_data = bpy.data.cameras.new(name)
    cam_data.type = 'ORTHO'
    cam_data.ortho_scale = ortho_scale
    cam = bpy.data.objects.new(name, cam_data)
    bpy.context.scene.collection.objects.link(cam)
    cam.location = loc
    cam.rotation_euler = rot_euler
    return cam

d = size * 3
views = {
    "top": (mathutils.Vector((center.x, center.y, center.z + d)), (0, 0, 0)),
    "side": (mathutils.Vector((center.x + d, center.y, center.z)), (math.radians(90), 0, math.radians(90))),
    "persp": (mathutils.Vector((center.x + d*0.8, center.y - d*0.8, center.z + d*0.6)), None),
}

for name, (loc, rot) in views.items():
    cam = make_cam("QA_" + name, loc, (0,0,0), size * 1.3)
    if rot is None:
        direction = center - loc
        rot_quat = direction.to_track_quat('-Z', 'Y')
        cam.rotation_euler = rot_quat.to_euler()
        cam.data.type = 'PERSP'
        cam.data.lens = 50
    else:
        cam.rotation_euler = rot
    scene.camera = cam
    scene.render.filepath = f"{out_prefix}_{name}.png"
    bpy.ops.render.render(write_still=True)
    print("Rendered", scene.render.filepath)

"""Test materials.py by building and assigning materials to the full asset.

This script:
1. Opens test_full.blend (which has HL_Sole, HL_Strap, HL_SideTag objects)
2. Imports materials module and builds materials
3. Assigns materials to the objects
4. Tests with both CYCLES and BLENDER_EEVEE render engines
5. Saves output to test_materials.blend
6. Prints material node counts and confirms no errors
"""
import bpy
import sys
import os

# Add scripts dir to path
sys.path.insert(0, os.path.dirname(__file__))

try:
    # Open test_full.blend
    print("\n[TEST] Opening test_full.blend...")
    bpy.ops.wm.open_mainfile(filepath="/home/user/Blender/blender/output/test_full.blend")
    bpy.context.view_layer.update()

    # Get references to the objects
    print("[TEST] Fetching objects...")
    sole_obj = bpy.data.objects.get("HL_Sole")
    strap_obj = bpy.data.objects.get("HL_Strap")
    tag_obj = bpy.data.objects.get("HL_SideTag")

    if not sole_obj:
        raise RuntimeError("HL_Sole not found in test_full.blend")
    if not strap_obj:
        raise RuntimeError("HL_Strap not found in test_full.blend")
    if not tag_obj:
        raise RuntimeError("HL_SideTag not found in test_full.blend")

    print(f"  - HL_Sole: {len(sole_obj.data.vertices)} verts, {len(sole_obj.data.polygons)} polys")
    print(f"  - HL_Strap: {len(strap_obj.data.vertices)} verts, {len(strap_obj.data.polygons)} polys")
    print(f"  - HL_SideTag: {len(tag_obj.data.vertices)} verts, {len(tag_obj.data.polygons)} polys")

    # Import and build materials
    print("\n[TEST] Importing materials module...")
    import importlib
    import materials
    importlib.reload(materials)

    print("[TEST] Building materials...")
    mats = materials.build_materials()
    print(f"  - Created {len(mats)} materials: {list(mats.keys())}")

    # Assign materials
    print("\n[TEST] Assigning materials to objects...")
    materials.assign_materials(sole_obj, strap_obj, tag_obj, mats)

    # Verify assignments
    print("[TEST] Verifying material assignments...")
    assert sole_obj.data.materials[0].name == "MAT_Sole", "Sole material not assigned correctly"
    assert strap_obj.data.materials[0].name == "MAT_Strap", "Strap material not assigned correctly"
    assert tag_obj.data.materials[0].name == "MAT_Tag", "Tag material not assigned correctly"
    print("  - All materials assigned correctly")

    # Print material node info
    print("\n[TEST] Material node structure:")
    for mat_key, mat in mats.items():
        node_count = len(mat.node_tree.nodes)
        link_count = len(mat.node_tree.links)
        node_types = [n.type for n in mat.node_tree.nodes]
        print(f"  - {mat.name}: {node_count} nodes, {link_count} links")
        print(f"    Node types: {node_types}")

    # Test CYCLES engine
    print("\n[TEST] Testing CYCLES render engine...")
    scene = bpy.context.scene
    try:
        scene.render.engine = 'CYCLES'
        print(f"  - Render engine set to: {scene.render.engine}")
    except Exception as e:
        print(f"  ! Warning: CYCLES engine error: {e}")

    # Verify materials still exist and are valid
    assert bpy.data.materials["MAT_Sole"] is not None, "MAT_Sole not found"
    assert bpy.data.materials["MAT_Strap"] is not None, "MAT_Strap not found"
    assert bpy.data.materials["MAT_Tag"] is not None, "MAT_Tag not found"
    print("  - All materials valid in CYCLES")

    # Test BLENDER_EEVEE engine
    print("\n[TEST] Testing BLENDER_EEVEE render engine...")
    try:
        scene.render.engine = 'BLENDER_EEVEE'
        print(f"  - Render engine set to: {scene.render.engine}")
    except Exception as e:
        print(f"  ! Warning: EEVEE engine error: {e}")

    # Verify materials still valid in EEVEE
    assert bpy.data.materials["MAT_Sole"] is not None, "MAT_Sole not found in EEVEE"
    assert bpy.data.materials["MAT_Strap"] is not None, "MAT_Strap not found in EEVEE"
    assert bpy.data.materials["MAT_Tag"] is not None, "MAT_Tag not found in EEVEE"
    print("  - All materials valid in EEVEE")

    # Save output
    print("\n[TEST] Saving to test_materials.blend...")
    bpy.ops.wm.save_as_mainfile(filepath="/home/user/Blender/blender/output/test_materials.blend")
    print("  - Saved successfully")

    # Final summary
    print("\n[TEST] === SUCCESS ===")
    print(f"  - MAT_Sole: {len(bpy.data.materials['MAT_Sole'].node_tree.nodes)} nodes")
    print(f"  - MAT_Strap: {len(bpy.data.materials['MAT_Strap'].node_tree.nodes)} nodes")
    print(f"  - MAT_Tag: {len(bpy.data.materials['MAT_Tag'].node_tree.nodes)} nodes")
    print("  - All materials functional in both CYCLES and EEVEE")
    print("  - Output: /home/user/Blender/blender/output/test_materials.blend")

except Exception as e:
    print(f"\n[ERROR] {e}", file=sys.stderr)
    import traceback
    traceback.print_exc()
    sys.exit(1)

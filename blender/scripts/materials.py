"""Material builders for HudLab Slide parametric asset.

Creates three node-based Principled BSDF materials:
- MAT_Sole: matte black, high roughness, procedural granular/suede texture (Noise + Bump, no displacement)
- MAT_Strap: matte rubbery, smooth micro-relief, subtle bump
- MAT_Tag: matte black, simple/clean (logo-swappable placeholder)

All materials work in both Cycles and Eevee render engines.
"""
import bpy


def build_materials():
    """Create and return {'sole': mat_sole, 'strap': mat_strap, 'tag': mat_tag} bpy.data.materials.

    Each material uses node-based Principled BSDF with procedural textures (Noise, Bump).
    """
    mats = {}

    # ---- MAT_Sole: high-roughness matte black with granular/suede procedural texture ----
    mat_sole = bpy.data.materials.new("MAT_Sole")
    mat_sole.use_nodes = True
    mat_sole.shadow_method = 'HASHED'  # works in both Cycles and Eevee
    bsdf_sole = mat_sole.node_tree.nodes["Principled BSDF"]
    mat_sole.node_tree.nodes.clear()

    # Nodes for sole material
    bsdf_sole = mat_sole.node_tree.nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf_sole.name = "Principled BSDF"
    bsdf_sole.inputs['Base Color'].default_value = (0.02, 0.02, 0.02, 1.0)  # near-black
    bsdf_sole.inputs['Roughness'].default_value = 0.78  # base roughness (high, matte)

    # Noise texture for granular/suede bump (larger scale, more detail for speckled look)
    noise_granular = mat_sole.node_tree.nodes.new(type='ShaderNodeTexNoise')
    noise_granular.name = "Noise Granular"
    noise_granular.inputs['Scale'].default_value = 12.0  # larger bumps for visible speckle
    noise_granular.inputs['Detail'].default_value = 6.0   # more detail for organic look

    # Bump node from granular noise -> Principled Normal
    bump_granular = mat_sole.node_tree.nodes.new(type='ShaderNodeBump')
    bump_granular.name = "Bump Granular"
    bump_granular.inputs['Strength'].default_value = 0.035  # moderate bump depth

    # Second noise for roughness variation (different frequency, smaller scale)
    noise_rough = mat_sole.node_tree.nodes.new(type='ShaderNodeTexNoise')
    noise_rough.name = "Noise Roughness"
    noise_rough.inputs['Scale'].default_value = 8.5   # smaller, finer detail
    noise_rough.inputs['Detail'].default_value = 5.0

    # Mix the roughness variation (create ColorRamp to map noise output to roughness range)
    colorramp_rough = mat_sole.node_tree.nodes.new(type='ShaderNodeValToRGB')
    colorramp_rough.name = "ColorRamp Roughness"
    # Map noise value to roughness range [0.70, 0.88]
    colorramp_rough.color_ramp.elements[0].position = 0.0
    colorramp_rough.color_ramp.elements[0].color = (0.70, 0.70, 0.70, 1.0)
    colorramp_rough.color_ramp.elements[1].position = 1.0
    colorramp_rough.color_ramp.elements[1].color = (0.88, 0.88, 0.88, 1.0)

    # Output material node
    out_mat = mat_sole.node_tree.nodes.new(type='ShaderNodeOutputMaterial')
    out_mat.name = "Material Output"

    # Link nodes: Noise Granular -> Bump -> BSDF Normal
    mat_sole.node_tree.links.new(noise_granular.outputs['Fac'], bump_granular.inputs['Height'])
    mat_sole.node_tree.links.new(bump_granular.outputs['Normal'], bsdf_sole.inputs['Normal'])

    # Link nodes: Noise Roughness -> ColorRamp -> BSDF Roughness
    mat_sole.node_tree.links.new(noise_rough.outputs['Fac'], colorramp_rough.inputs['Fac'])
    mat_sole.node_tree.links.new(colorramp_rough.outputs['Color'], bsdf_sole.inputs['Roughness'])

    # Link BSDF to Material Output
    mat_sole.node_tree.links.new(bsdf_sole.outputs['BSDF'], out_mat.inputs['Surface'])

    mats['sole'] = mat_sole

    # ---- MAT_Strap: smooth matte rubbery (lower roughness, subtle micro-relief) ----
    mat_strap = bpy.data.materials.new("MAT_Strap")
    mat_strap.use_nodes = True
    mat_strap.shadow_method = 'HASHED'
    mat_strap.node_tree.nodes.clear()

    # Nodes for strap material
    bsdf_strap = mat_strap.node_tree.nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf_strap.name = "Principled BSDF"
    bsdf_strap.inputs['Base Color'].default_value = (0.02, 0.02, 0.02, 1.0)  # near-black
    bsdf_strap.inputs['Roughness'].default_value = 0.62  # smoother than sole, matte rubber

    # Subtle noise for micro-relief (small scale, minimal detail)
    noise_micro = mat_strap.node_tree.nodes.new(type='ShaderNodeTexNoise')
    noise_micro.name = "Noise Micro Relief"
    noise_micro.inputs['Scale'].default_value = 28.0  # very fine detail
    noise_micro.inputs['Detail'].default_value = 3.0   # minimal detail for subtle look

    # Bump for micro-relief (low strength, barely visible)
    bump_micro = mat_strap.node_tree.nodes.new(type='ShaderNodeBump')
    bump_micro.name = "Bump Micro"
    bump_micro.inputs['Strength'].default_value = 0.035  # subtle, not pronounced

    # Output material node
    out_strap = mat_strap.node_tree.nodes.new(type='ShaderNodeOutputMaterial')
    out_strap.name = "Material Output"

    # Link nodes: Noise Micro -> Bump -> BSDF Normal
    mat_strap.node_tree.links.new(noise_micro.outputs['Fac'], bump_micro.inputs['Height'])
    mat_strap.node_tree.links.new(bump_micro.outputs['Normal'], bsdf_strap.inputs['Normal'])

    # Link BSDF to Material Output
    mat_strap.node_tree.links.new(bsdf_strap.outputs['BSDF'], out_strap.inputs['Surface'])

    mats['strap'] = mat_strap

    # ---- MAT_Tag: simple, clean, swappable placeholder for logo ----
    mat_tag = bpy.data.materials.new("MAT_Tag")
    mat_tag.use_nodes = True
    mat_tag.shadow_method = 'HASHED'
    mat_tag.node_tree.nodes.clear()

    # Nodes for tag material
    bsdf_tag = mat_tag.node_tree.nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf_tag.name = "Principled BSDF"
    bsdf_tag.inputs['Base Color'].default_value = (0.02, 0.02, 0.02, 1.0)  # near-black matte
    bsdf_tag.inputs['Roughness'].default_value = 0.55  # medium matte
    # NOTE: For future logo texture injection, insert a ShaderNodeTexImage node here,
    #       connect its Color output to Principled BSDF Base Color input (replaces this constant).
    #       Example (to be done by automation pipeline):
    #         img_tex = node_tree.nodes.new(type='ShaderNodeTexImage')
    #         node_tree.links.new(img_tex.outputs['Color'], bsdf_tag.inputs['Base Color'])

    # Minimal bump texture (very subtle, barely perceptible)
    noise_tag_bump = mat_tag.node_tree.nodes.new(type='ShaderNodeTexNoise')
    noise_tag_bump.name = "Noise Subtle"
    noise_tag_bump.inputs['Scale'].default_value = 30.0  # very fine
    noise_tag_bump.inputs['Detail'].default_value = 2.0   # minimal detail

    # Very low-strength bump (nearly flat, clean look)
    bump_tag = mat_tag.node_tree.nodes.new(type='ShaderNodeBump')
    bump_tag.name = "Bump Minimal"
    bump_tag.inputs['Strength'].default_value = 0.012  # barely visible, keeps tag clean

    # Output material node
    out_tag = mat_tag.node_tree.nodes.new(type='ShaderNodeOutputMaterial')
    out_tag.name = "Material Output"

    # Link nodes: Noise -> Bump -> BSDF Normal
    mat_tag.node_tree.links.new(noise_tag_bump.outputs['Fac'], bump_tag.inputs['Height'])
    mat_tag.node_tree.links.new(bump_tag.outputs['Normal'], bsdf_tag.inputs['Normal'])

    # Link BSDF to Material Output
    mat_tag.node_tree.links.new(bsdf_tag.outputs['BSDF'], out_tag.inputs['Surface'])

    mats['tag'] = mat_tag

    return mats


def assign_materials(sole_obj, strap_obj, tag_obj, mats):
    """Assign materials to objects using material_slots.

    Args:
        sole_obj: HL_Sole mesh object
        strap_obj: HL_Strap mesh object
        tag_obj: HL_SideTag mesh object
        mats: dict from build_materials() with keys 'sole', 'strap', 'tag'
    """
    # Assign MAT_Sole to sole_obj
    if sole_obj.data.materials:
        sole_obj.data.materials.clear()
    sole_obj.data.materials.append(mats['sole'])

    # Assign MAT_Strap to strap_obj
    if strap_obj.data.materials:
        strap_obj.data.materials.clear()
    strap_obj.data.materials.append(mats['strap'])

    # Assign MAT_Tag to tag_obj
    if tag_obj.data.materials:
        tag_obj.data.materials.clear()
    tag_obj.data.materials.append(mats['tag'])

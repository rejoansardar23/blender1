"""Inspect supplied assets without claiming to auto-rig or retarget them.

Run in Blender with --disable-autoexec and --python-exit-code 1:
  blender -b --disable-autoexec --python blender/character_tools/inspect_asset.py -- \
    --asset incoming/character.glb --report artifacts/character-report.json

Use trusted files. glTF/FBX/OBJ import is supported; .blend appends objects.
The report identifies obvious data issues, not motion quality or collision safety.
"""

import argparse
import json
import sys
from pathlib import Path

import bpy


def inspect_asset(asset, report):
    asset = Path(asset).resolve()
    if not asset.is_file():
        raise FileNotFoundError(asset)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    suffix = asset.suffix.lower()
    if suffix in (".glb", ".gltf"):
        bpy.ops.import_scene.gltf(filepath=str(asset))
    elif suffix == ".fbx":
        bpy.ops.import_scene.fbx(filepath=str(asset))
    elif suffix == ".obj":
        bpy.ops.wm.obj_import(filepath=str(asset))
    elif suffix == ".blend":
        with bpy.data.libraries.load(str(asset), link=False) as (source, target):
            target.objects = source.objects
        for obj in target.objects:
            if obj:
                bpy.context.collection.objects.link(obj)
    else:
        raise ValueError("Supported assets: .glb, .gltf, .fbx, .obj, .blend")
    meshes = []
    for obj in bpy.context.scene.objects:
        if obj.type != "MESH":
            continue
        meshes.append({
            "name": obj.name,
            "vertices": len(obj.data.vertices),
            "polygons": len(obj.data.polygons),
            "zero_area_polygons": sum(p.area < 1e-10 for p in obj.data.polygons),
            "dimensions_m": list(obj.dimensions),
            "scale": list(obj.scale),
            "negative_scale": any(value < 0 for value in obj.scale),
            "materials": [slot.material.name if slot.material else None for slot in obj.material_slots],
            "vertex_groups": len(obj.vertex_groups),
            "armature": obj.find_armature().name if obj.find_armature() else None,
            "shape_keys": list(obj.data.shape_keys.key_blocks.keys()) if obj.data.shape_keys else []
        })
    rigs = [{"name": obj.name, "bones": len(obj.data.bones),
             "root_bones": [b.name for b in obj.data.bones if not b.parent]}
            for obj in bpy.context.scene.objects if obj.type == "ARMATURE"]
    missing_images = [image.filepath for image in bpy.data.images
                      if image.source == "FILE" and not image.packed_file
                      and not Path(bpy.path.abspath(image.filepath)).is_file()]
    result = {"asset": str(asset), "blender": bpy.app.version_string,
              "meshes": meshes, "rigs": rigs, "missing_images": missing_images,
              "actions": [a.name for a in bpy.data.actions],
              "requires_assisted_rigging": bool(meshes) and not bool(rigs),
              "limitations": ["No automatic human rigging, weight repair, motion retargeting or professional animation-quality claim.",
                              "Dimensions reflect the imported unit conventions; confirm scale against your reference."]}
    destination = Path(report).resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"report": str(destination), "meshes": len(meshes), "rigs": len(rigs),
                      "missing_images": len(missing_images)}))
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--asset", required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    inspect_asset(args.asset, args.report)

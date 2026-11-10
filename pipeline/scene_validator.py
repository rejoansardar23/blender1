"""Basic structural Blender QC, not an automatic animation-quality judgement.

blender -b scene.blend --disable-autoexec --python-exit-code 1 --python
pipeline/scene_validator.py -- --out artifacts/scene-validation.json
"""
import argparse
import json
import math
from pathlib import Path
import sys


def report(scene):
    import bpy
    errors, warnings = [], []
    if scene.camera is None or scene.camera.type != 'CAMERA':
        errors.append('No active scene camera')
    if scene.frame_end < scene.frame_start:
        errors.append('Frame range ends before it starts')
    if min(scene.render.resolution_x, scene.render.resolution_y, scene.render.fps) <= 0:
        errors.append('Render resolution and FPS must be positive')
    missing = []
    for image in bpy.data.images:
        if image.source != 'FILE' or image.packed_file or not image.filepath:
            continue
        if not Path(bpy.path.abspath(image.filepath)).exists():
            missing.append(image.name)
    if missing:
        errors.append('Missing external image files: ' + ', '.join(missing))
    meshes, rigs, animated = [], [], []
    for obj in scene.objects:
        if any(not math.isfinite(value) for row in obj.matrix_world for value in row):
            errors.append(f'Non-finite transform: {obj.name}')
        if obj.animation_data and (obj.animation_data.action or len(obj.animation_data.nla_tracks)):
            animated.append(obj.name)
        if obj.type == 'MESH':
            meshes.append(obj)
            if not obj.data.vertices:
                warnings.append(f'Empty mesh: {obj.name}')
            armature_modifiers = [mod for mod in obj.modifiers if mod.type == 'ARMATURE']
            for modifier in armature_modifiers:
                if modifier.object is None or modifier.object.type != 'ARMATURE':
                    errors.append(f'Missing armature modifier target: {obj.name}')
                elif modifier.use_vertex_groups:
                    deform_groups = {group.index for group in obj.vertex_groups
                                     if group.name in modifier.object.data.bones and
                                     modifier.object.data.bones[group.name].use_deform}
                    unweighted = sum(not any(group.group in deform_groups and group.weight > 0
                                             for group in vertex.groups)
                                     for vertex in obj.data.vertices)
                    if unweighted:
                        warnings.append(f'{obj.name}: {unweighted} vertices have no deform-bone weights')
        elif obj.type == 'ARMATURE':
            rigs.append({'name': obj.name, 'bones': len(obj.data.bones),
                         'deform_bones': sum(bone.use_deform for bone in obj.data.bones)})
            if not obj.data.bones:
                errors.append(f'Armature has no bones: {obj.name}')
    if not animated:
        warnings.append('No object actions or NLA tracks found')
    if not rigs:
        warnings.append('No armature found; scene may use rigid object animation only')
    return {'status': 'failed' if errors else 'passed_basic_checks',
            'blender': bpy.app.version_string, 'scene': scene.name,
            'frames': [scene.frame_start, scene.frame_end], 'fps': scene.render.fps,
            'camera': scene.camera.name if scene.camera else None,
            'objects': len(scene.objects), 'meshes': len(meshes), 'armatures': rigs,
            'animated_objects': animated, 'errors': errors, 'warnings': warnings,
            'not_checked': ['Foot sliding, collisions and cloth simulation',
                            'Natural motion, facial quality and lip synchronization',
                            'Camera obstruction and shot continuity',
                            'Asset licensing and professional production quality']}


def main():
    import bpy
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    result = report(bpy.context.scene)
    path = Path(args.out)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
    if result['errors']:
        raise RuntimeError('Scene failed basic structural checks')


if __name__ == '__main__':
    main()

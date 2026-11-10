"""Local, content-addressed assets and Blender import without embedded-script execution.

Cache: python -m pipeline.asset_manager cache character.glb --cache artifacts/assets
Import: blender -b --disable-autoexec --python-exit-code 1 --python
pipeline/asset_manager.py -- import character.glb --out artifacts/imported.blend

Original asset licences must be reviewed separately. No remote downloads occur.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shlex
import shutil
import sys

SUPPORTED = {'.blend', '.glb', '.gltf', '.fbx', '.obj'}


def digest(path):
    result = hashlib.sha256()
    with open(path, 'rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(block)
    return result.hexdigest()


def safe_dependency(parent, name):
    if '://' in name or name.startswith('data:'):
        raise ValueError('Only local sidecar dependencies can be cached')
    path = (parent / name).resolve()
    if not path.is_relative_to(parent.resolve()) or not path.is_file():
        raise ValueError(f'Missing or unsafe asset dependency: {name}')
    return path


def dependencies(source):
    """Discover portable glTF and common OBJ/MTL sidecars, rejecting path escapes."""
    found = [source]
    if source.suffix.lower() == '.gltf':
        document = json.loads(source.read_text())
        for entry in document.get('buffers', []) + document.get('images', []):
            uri = entry.get('uri', '')
            if uri and not uri.startswith('data:'):
                found.append(safe_dependency(source.parent, uri))
    elif source.suffix.lower() == '.obj':
        for line in source.read_text(errors='replace').splitlines():
            tokens = shlex.split(line, comments=True)
            if tokens and tokens[0] == 'mtllib':
                for name in tokens[1:]:
                    material = safe_dependency(source.parent, name)
                    found.append(material)
                    for material_line in material.read_text(errors='replace').splitlines():
                        parts = shlex.split(material_line, comments=True)
                        if parts and (parts[0].startswith('map_') or parts[0] in ('bump', 'disp', 'decal')):
                            # Common MTL syntax places the filename after map options.
                            texture = safe_dependency(material.parent, parts[-1])
                            if not texture.is_relative_to(source.parent):
                                raise ValueError('MTL texture escapes the source asset directory')
                            found.append(texture)
    return sorted(set(found))


def cache_asset(source, cache):
    source = Path(source).resolve(strict=True)
    if not source.is_file() or source.suffix.lower() not in SUPPORTED:
        raise ValueError('Supported assets: .blend, .glb, .gltf, .fbx, .obj')
    inputs = dependencies(source)
    records = {p.relative_to(source.parent).as_posix(): digest(p) for p in inputs}
    identifier = hashlib.sha256(json.dumps(records, sort_keys=True).encode()).hexdigest()
    destination = Path(cache).resolve() / identifier
    destination.mkdir(parents=True, exist_ok=True)
    for path in inputs:
        relative = path.relative_to(source.parent)
        target = destination / relative
        if target.is_symlink():
            raise ValueError('Cache contains an unexpected symlink')
        if target.exists():
            if digest(target) != records[relative.as_posix()]:
                raise ValueError('Cached asset failed checksum verification')
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.resolve().is_relative_to(destination):
                raise ValueError('Cache dependency path escapes cache root')
            shutil.copyfile(path, target)
    manifest = {'asset_id': identifier, 'entry': source.name,
                'format': source.suffix.lower(), 'files': records}
    (destination / 'asset.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return destination / source.name, manifest


def import_asset(source):
    """Call in Blender; never execute text datablocks/drivers from imported assets."""
    import bpy
    path = Path(source).resolve(strict=True)
    if path.suffix.lower() not in SUPPORTED:
        raise ValueError('Unsupported asset format')
    bpy.context.preferences.filepaths.use_scripts_auto_execute = False
    before = set(bpy.data.objects)
    if path.suffix.lower() == '.blend':
        with bpy.data.libraries.load(str(path), link=False) as (data_from, data_to):
            data_to.objects = data_from.objects
        for obj in data_to.objects:
            if obj is not None:
                bpy.context.collection.objects.link(obj)
    elif path.suffix.lower() in ('.gltf', '.glb'):
        bpy.ops.import_scene.gltf(filepath=str(path))
    elif path.suffix.lower() == '.fbx':
        bpy.ops.import_scene.fbx(filepath=str(path))
    else:
        bpy.ops.wm.obj_import(filepath=str(path))
    imported = sorted(set(bpy.data.objects) - before, key=lambda obj: obj.name)
    for obj in imported:
        # Preserve animation data, but imported Python expression drivers stay disabled
        # unless the operator explicitly trusts the asset in a separate workflow.
        if obj.animation_data:
            for driver in obj.animation_data.drivers:
                driver.mute = True
    return {'source': path.name, 'sha256': digest(path), 'objects': len(imported),
            'meshes': sum(obj.type == 'MESH' for obj in imported),
            'armatures': [{'name': obj.name, 'bones': len(obj.data.bones)}
                          for obj in imported if obj.type == 'ARMATURE'],
            'embedded_script_execution': False,
            'limitations': ['Imported expression drivers are muted.',
                           'Import does not automatically rig, retarget or repair a character.']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    cache = commands.add_parser('cache')
    cache.add_argument('source')
    cache.add_argument('--cache', required=True)
    importer = commands.add_parser('import')
    importer.add_argument('source')
    importer.add_argument('--out', required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else None)
    if args.command == 'cache':
        path, manifest = cache_asset(args.source, args.cache)
        print(json.dumps({'path': str(path), **manifest}, indent=2))
    else:
        import bpy
        result = import_asset(args.source)
        output = Path(args.out).resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        bpy.ops.file.pack_all()
        bpy.ops.wm.save_as_mainfile(filepath=str(output))
        output.with_suffix('.assets.json').write_text(json.dumps(result, indent=2) + '\n')
        print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()

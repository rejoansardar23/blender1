"""Cycles GPU selection. A detected GPU is not evidence of successful rendering."""
import json
import bpy


def configure_gpu(scene, backend="AUTO"):
    preferences = bpy.context.preferences.addons['cycles'].preferences
    attempts = []
    for candidate in (["OPTIX", "CUDA"] if backend == "AUTO" else [backend]):
        try:
            preferences.compute_device_type = candidate
            preferences.refresh_devices()
            devices = list(preferences.devices)
            selected = [d for d in devices if d.type == candidate]
            for device in devices:
                device.use = device in selected
            attempts.append({"backend": candidate, "devices": [
                {"name": d.name, "type": d.type, "enabled": d.use} for d in devices]})
            if selected:
                scene.render.engine = 'CYCLES'
                scene.cycles.device = 'GPU'
                evidence = {"backend": candidate, "devices": [d.name for d in selected],
                            "attempts": attempts, "render_verified": False}
                print('GPU_DETECTION ' + json.dumps(evidence), flush=True)
                return evidence
        except (TypeError, RuntimeError) as error:
            attempts.append({"backend": candidate, "error": str(error)})
    raise RuntimeError('No supported Cycles GPU; CPU fallback is disabled. ' + json.dumps(attempts))

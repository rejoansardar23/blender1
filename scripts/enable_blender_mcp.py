"""Enable the installed addon inside GUI Blender. No source .blend file is saved."""
import bpy
import addon_utils

addon_utils.enable('blender_mcp', default_set=True, persistent=True)
entry = bpy.context.preferences.addons.get('blender_mcp')
if entry is None:
    raise RuntimeError('Blender MCP addon did not enable; check BLENDER_USER_SCRIPTS')
entry.preferences.telemetry_consent = False
entry.preferences.bind_address = '127.0.0.1'
if hasattr(entry.preferences, 'allow_remote_connections'):
    entry.preferences.allow_remote_connections = False
bpy.context.scene.blendermcp_auto_start_server = True
bpy.context.scene.blendermcp_port = 9876
bpy.ops.wm.save_userpref()
if not bpy.context.scene.blendermcp_server_running:
    bpy.ops.blendermcp.start_server()
print('CLOUD_MCP_ADDON_ENABLED', bpy.app.version_string, flush=True)

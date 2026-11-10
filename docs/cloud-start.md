# Cloud startup instructions

Use the existing checkout at `/workspace/blender1`. Each cloud task is already isolated;
do not create a Git worktree unless explicitly requested. Do not overwrite existing assets
or user changes. Retained files and installed packages may survive snapshots; live servers,
MCP processes and authentication must be started/rechecked in each task.

1. Run `blender --version`, `ffmpeg -version`; use `scripts/blender-headless --version` for the updated Blender 5.2.3 LTS
   runtime and pass `--blender ./scripts/blender-headless` to the pipeline explicitly. Check the version written into each blend/job before rendering.
2. Run the Python unit suites in README. If dependencies need refreshing, use
   `bash scripts/cloud_install.sh`. Credentials must stay in secure environment settings.
3. In `viewer/`, run `npm run dev -- --port 4173`; locally validate the HTTP response and
   browser loading of the actual sample. A running local server is not a public deployment.
4. For fresh scenes, run the independent build, render, encode and package commands in
   README. Expensive production rendering requires a verified GPU. Use the tiny probe first.
5. For Kaggle, check credentials by presence only, then use the documented official
   submission/status/output operations. Read actual account quotas and session settings;
   metadata requesting GPU does not establish access. Never assume an old job remains live.
6. MCP: run `python3 scripts/start_blender_mcp.py` and verify it with
   `/workspace/tools/blender-mcp-venv/bin/python scripts/probe_blender_mcp.py`.
   It uses the GUI Blender executable; the newer headless runtime cannot host this addon.
7. Public sharing uses the manual Pages workflow and verified completed deployment.

These instructions are repository files. Environment draft persistence and publication
must be confirmed separately; neither occurred solely by writing this document.

# Browser scene review

A static Three.js viewer for GLB scenes, exported animation, Blender stills, and MP4/WebM video. Drag to orbit, scroll to zoom, select an exported scene camera, pause, or scrub the timeline. Assets opened with the file picker stay in your browser; there is no upload endpoint. Use GLB for models with external textures: a loose GLTF file can only load if its buffers/textures are embedded.

```sh
cd /workspace/blender1/viewer
npm ci --cache /tmp/animation-npm-cache
npm run dev
```

For a static build run `npm run build`. The generated `dist/` folder can be served from HTTPS static hosting. `base: './'` supports a GitHub Pages project path. Put the generated sample assets at `public/demo/scene.glb`, `public/demo/poster.png`, and `public/demo/preview.mp4` before building. Missing assets produce a helpful state and you can open your own files. WebGL uses an environment map, review lights, and up to four intensity-normalized imported lights to stay responsive; Blender rendered images and video determine final lighting/material quality.

To publish without installing software on your computer: in the repository’s **Settings → Pages**, select **GitHub Actions**; then run the **Publish browser viewer** workflow under **Actions**. The workflow returns the actual HTTPS deployment URL. Publication is not automatic on push and has not been claimed until a successful deployment is observed. Large private assets should use authorized object storage, rather than a public Pages deployment.

Run the browser smoke check against the running development server with `npm run test:browser`. It exercises the generated GLB, animation timeline, exported camera, and mobile layout. Set `VIEWER_URL` to change the server URL and `CHROMIUM_PATH` if Chromium is installed elsewhere. This cloud machine uses `/usr/bin/chromium`; nothing is installed on your personal computer.

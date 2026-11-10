import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import './style.css';

const $ = (id) => document.getElementById(id);
const canvas = $('scene-canvas');
const viewport = $('viewport');
const status = $('asset-status');
const image = $('render-image');
const video = $('render-video');
const timeline = $('timeline');
const play = $('play');
let renderer, controls, sceneCamera, model, mixer;
let cameras = [], actions = [], duration = 0, time = 0, playing = true, mode = 'scene';
let loadSequence = 0;
let ownedMediaUrls = [];
const sources = { image: `${import.meta.env.BASE_URL}demo/poster.png`, video: `${import.meta.env.BASE_URL}demo/preview.mp4` };
const scene = new THREE.Scene();
scene.background = new THREE.Color('#172126');
const orbitCamera = new THREE.PerspectiveCamera(45, 1, .05, 1000);
orbitCamera.position.set(12, 8, 14);
const ambient = new THREE.HemisphereLight(0xcce3ff, 0x715740, 1.8);
scene.add(ambient);
const key = new THREE.DirectionalLight(0xffdfb7, 2.3);
key.position.set(7, 12, 6);
scene.add(key);
const fill = new THREE.DirectionalLight(0x9db9ff, 1);
fill.position.set(-8, 5, -3);
scene.add(fill);
const clock = new THREE.Clock();
const loader = new GLTFLoader();
function message(text) { status.textContent = text; status.hidden = !text; }
function formatTime(value) { return `${String(Math.floor(value / 60)).padStart(2, '0')}:${(value % 60).toFixed(2).padStart(5, '0')}`; }
function updateTransport() {
  const isVideo = mode === 'video';
  const activeDuration = isVideo ? (Number.isFinite(video.duration) ? video.duration : 0) : duration;
  const activeTime = isVideo ? video.currentTime : time;
  $('current-time').textContent = formatTime(activeTime);
  $('duration').textContent = formatTime(activeDuration);
  timeline.max = String(activeDuration || 1);
  timeline.value = String(activeTime);
  timeline.disabled = mode === 'image' || !activeDuration;
  play.disabled = mode === 'image' || !activeDuration;
  $('restart').disabled = mode === 'image' || !activeDuration;
  play.textContent = (isVideo ? !video.paused : playing) ? 'Ⅱ' : '▶';
  play.setAttribute('aria-label', (isVideo ? !video.paused : playing) ? 'Pause animation' : 'Play animation');
}
function disposeObject(object) {
  object.traverse((node) => {
    node.geometry?.dispose();
    const materials = Array.isArray(node.material) ? node.material : [node.material];
    for (const material of materials) {
      if (!material) continue;
      for (const value of Object.values(material)) if (value?.isTexture) value.dispose();
      material.dispose();
    }
  });
}
function frameModel() {
  if (!model || !controls) return;
  scene.updateMatrixWorld(true);
  const bounds = new THREE.Box3().setFromObject(model);
  if (bounds.isEmpty()) return;
  const center = bounds.getCenter(new THREE.Vector3());
  const size = Math.max(...bounds.getSize(new THREE.Vector3()).toArray(), 1);
  orbitCamera.position.copy(center).add(new THREE.Vector3(size * .8, size * .55, size * .9));
  orbitCamera.near = Math.max(.01, size / 2000);
  orbitCamera.far = size * 100;
  orbitCamera.updateProjectionMatrix();
  controls.target.copy(center);
  controls.maxDistance = size * 8;
  controls.minDistance = size * .03;
  controls.update();
}
function resize() {
  if (!renderer) return;
  const { width, height } = viewport.getBoundingClientRect();
  renderer.setSize(width, height, false);
  orbitCamera.aspect = width / height;
  orbitCamera.updateProjectionMatrix();
  // Keep authored scene cameras' framing; renderer uses letterboxing for them.
}
function render() {
  requestAnimationFrame(render);
  const delta = Math.min(clock.getDelta(), .1);
  if (mixer && playing && mode === 'scene' && duration) {
    time = (time + delta) % duration;
    mixer.setTime(time);
  }
  if (controls) { controls.enabled = mode === 'scene' && !sceneCamera; controls.update(); }
  if (renderer && mode === 'scene') {
    const width = viewport.clientWidth, height = viewport.clientHeight;
    const camera = sceneCamera || orbitCamera;
    renderer.setViewport(0, 0, width, height);
    renderer.setScissorTest(false);
    renderer.clear();
    if (sceneCamera?.isPerspectiveCamera) {
      const aspect = sceneCamera.aspect || 16 / 9;
      let w = width, h = width / aspect;
      if (h > height) { h = height; w = h * aspect; }
      renderer.setViewport((width - w) / 2, (height - h) / 2, w, h);
      renderer.setScissor((width - w) / 2, (height - h) / 2, w, h);
      renderer.setScissorTest(true);
    }
    renderer.render(scene, camera);
  }
  updateTransport();
}
async function loadScene(url, title) {
  const sequence = ++loadSequence;
  message('Opening the scene…');
  try {
    const gltf = await loader.loadAsync(url);
    if (sequence !== loadSequence) { disposeObject(gltf.scene); return; }
    if (model) { mixer?.stopAllAction(); mixer?.uncacheRoot(model); scene.remove(model); disposeObject(model); }
    model = gltf.scene;
    scene.add(model);
    cameras = gltf.cameras || [];
    mixer = new THREE.AnimationMixer(model);
    actions = gltf.animations.map((clip) => mixer.clipAction(clip).play());
    duration = Math.max(0, ...gltf.animations.map((clip) => clip.duration));
    time = 0;
    playing = true;
    const cameraSelect = $('camera');
    cameraSelect.replaceChildren(new Option('Free orbit', 'orbit'));
    cameras.forEach((camera, i) => cameraSelect.add(new Option(camera.name || `Scene camera ${i + 1}`, String(i))));
    sceneCamera = cameras[0] || null;
    if (sceneCamera) cameraSelect.value = '0';
    $('scene-title').textContent = title;
    $('animation-info').textContent = duration ? `${duration.toFixed(1)}s · ${gltf.animations.length} action${gltf.animations.length === 1 ? '' : 's'}` : 'Static scene';
    // Review lighting is intentionally normalized; final Blender lighting is reviewed as rendered media.
    const importedLights = [];
    model.traverse((node) => { if (node.isLight) importedLights.push(node); });
    importedLights.sort((a, b) => b.intensity - a.intensity);
    importedLights.forEach((light, i) => {
      light.visible = i < 4; // Keep the interactive preview responsive on smaller devices.
      light.intensity = Math.min(light.intensity, 35);
    });
    frameModel();
    if (mode === 'scene') message('');
  } catch (error) {
    if (sequence !== loadSequence) return;
    console.error('Scene load failed:', error);
    message('No preview scene is available yet. Open a GLB asset, or generate the example scene with the pipeline.');
    $('animation-info').textContent = 'No scene loaded';
  }
}
function switchMode(nextMode) {
  mode = nextMode;
  document.querySelectorAll('[data-mode]').forEach((button) => button.classList.toggle('active', button.dataset.mode === mode));
  canvas.hidden = mode !== 'scene'; image.hidden = mode !== 'image'; video.hidden = mode !== 'video';
  $('orbit-help').hidden = mode !== 'scene';
  $('camera').disabled = mode !== 'scene';
  $('mode-badge').textContent = mode === 'scene' ? 'WEBGL PREVIEW' : mode === 'image' ? 'RENDERED STILL' : 'RENDERED VIDEO';
  $('quality-note').textContent = mode === 'scene' ? 'Interactive scene · final lighting may differ' : 'Blender output · render quality follows the selected preset';
  video.pause();
  message('');
  if (mode === 'image') {
    image.onerror = () => { if (mode === 'image') message('No rendered still yet. Open an image, or render a preview with the pipeline.'); };
    if (image.src !== new URL(sources.image, location.href).href) image.src = sources.image;
    else if (!image.complete || !image.naturalWidth) message('No rendered still yet. Open an image, or render a preview with the pipeline.');
  }
  if (mode === 'video') {
    video.onerror = () => { if (mode === 'video') message('No rendered video yet. Open an MP4, or encode the rendered frames with the pipeline.'); };
    if (video.src !== new URL(sources.video, location.href).href) video.src = sources.video;
    else if (video.error) message('No rendered video yet. Open an MP4, or encode the rendered frames with the pipeline.');
  }
  if (mode === 'scene' && !model) message('No preview scene is available yet. Open a GLB asset, or generate the example scene with the pipeline.');
  resize(); updateTransport();
}
try {
  renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: false });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.0;
  const environment = new RoomEnvironment();
  const pmrem = new THREE.PMREMGenerator(renderer);
  scene.environment = pmrem.fromScene(environment, .04).texture;
  environment.dispose();
  pmrem.dispose();
  controls = new OrbitControls(orbitCamera, canvas);
  controls.enableDamping = true;
  controls.dampingFactor = .08;
  new ResizeObserver(resize).observe(viewport);
  resize();
  loadScene(`${import.meta.env.BASE_URL}demo/scene.glb`, 'Night market · scene study');
} catch (error) {
  message('WebGL is unavailable in this browser. You can still review rendered stills and videos.');
  console.error(error);
}
render();
document.querySelectorAll('[data-mode]').forEach((button) => button.addEventListener('click', () => switchMode(button.dataset.mode)));
$('camera').addEventListener('change', (event) => {
  sceneCamera = event.target.value === 'orbit' ? null : cameras[Number(event.target.value)];
  $('orbit-help').hidden = Boolean(sceneCamera);
});
$('reset-camera').addEventListener('click', () => { $('camera').value = 'orbit'; sceneCamera = null; frameModel(); });
play.addEventListener('click', () => {
  if (mode === 'video') { if (video.paused) video.play().catch((error) => message(`Playback could not start: ${error.message}`)); else video.pause(); }
  else playing = !playing;
  updateTransport();
});
$('restart').addEventListener('click', () => { if (mode === 'video') video.currentTime = 0; else { time = 0; mixer?.setTime(0); } updateTransport(); });
timeline.addEventListener('input', () => {
  if (mode === 'video') video.currentTime = Number(timeline.value);
  else { time = Number(timeline.value); mixer?.setTime(time); }
  updateTransport();
});
video.addEventListener('loadedmetadata', updateTransport);
$('asset-input').addEventListener('change', async (event) => {
  const file = event.target.files?.[0];
  if (!file) return;
  const extension = file.name.split('.').pop().toLowerCase();
  const url = URL.createObjectURL(file);
  if (extension === 'glb' || extension === 'gltf') {
    switchMode('scene');
    await loadScene(url, file.name);
    URL.revokeObjectURL(url);
  } else if (['mp4', 'webm'].includes(extension)) { sources.video = url; ownedMediaUrls.push(url); switchMode('video'); }
  else if (['png', 'jpg', 'jpeg'].includes(extension)) { sources.image = url; ownedMediaUrls.push(url); switchMode('image'); }
  else { URL.revokeObjectURL(url); message('Choose a GLB, self-contained GLTF, MP4, WebM, PNG, or JPEG.'); }
  event.target.value = '';
});
window.addEventListener('beforeunload', () => ownedMediaUrls.forEach((url) => URL.revokeObjectURL(url)));

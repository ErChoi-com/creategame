import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

// The scene is built entirely from a world JSON object (see world.json).
// It loads world.json on start, then, if served by the MCP server, listens on /ws for live updates.

const FALLBACK_WORLD = {
  grid: { width: 10, depth: 10, tileSize: 10, gap: 1, tileHeight: 10, color: '#ffffff', tiles: {} },
  entities: [{ id: 'player', type: 'box', x: 0, z: 0, color: '#4287f5', size: 4 }],
  camera: 'orbit',
};

class GameView {
  constructor() {
    this.renderer = new THREE.WebGLRenderer({ antialias: true });
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    this.renderer.setPixelRatio(window.devicePixelRatio);
    this.renderer.setSize(window.innerWidth, window.innerHeight);
    document.body.appendChild(this.renderer.domElement);

    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0x1b1d22);

    this.camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 1, 2000);
    this.controls = new OrbitControls(this.camera, this.renderer.domElement);

    this.sun = new THREE.DirectionalLight(0xffffff, 1);
    this.sun.castShadow = true;
    this.sun.shadow.bias = -0.001;
    this.sun.shadow.mapSize.set(2048, 2048);
    this.scene.add(this.sun, this.sun.target, new THREE.AmbientLight(0x404040, 0.8));

    this.worldGroup = new THREE.Group();
    this.scene.add(this.worldGroup);

    window.addEventListener('resize', () => this.onResize());
    document.addEventListener('keydown', (e) => {
      const preset = { 1: 'orbit', 2: 'isometric', 3: 'top' }[e.key];
      if (preset) this.setCamera(preset);
    });

    this.renderer.setAnimationLoop(() => this.render());
  }

  // Rebuild every mesh from the world description. Cheap enough for grids up to 64x64.
  setWorld(world) {
    const firstLoad = !this.world;
    const cameraChanged = !firstLoad && this.world.camera !== world.camera;
    this.world = world;

    this.worldGroup.traverse((o) => { o.geometry?.dispose(); o.material?.dispose(); });
    this.worldGroup.clear();

    const { width, depth, tileSize, gap, tileHeight, color, tiles } = world.grid;
    const pitch = tileSize + gap;
    // Center the grid on the origin so the camera and controls orbit its middle.
    this.toWorld = (x, z) => [(x - (width - 1) / 2) * pitch, (z - (depth - 1) / 2) * pitch];

    const tileGeo = new THREE.BoxGeometry(tileSize, 1, tileSize);
    const materials = new Map();
    const mat = (c) => {
      if (!materials.has(c)) materials.set(c, new THREE.MeshStandardMaterial({ color: c }));
      return materials.get(c);
    };

    this.tileTops = new Map();
    for (let x = 0; x < width; x++) {
      for (let z = 0; z < depth; z++) {
        const o = tiles[`${x},${z}`] || {};
        const h = o.height ?? tileHeight;
        if (o.hidden || h <= 0) {
          this.tileTops.set(`${x},${z}`, 0);
          continue;
        }
        const tile = new THREE.Mesh(tileGeo, mat(o.color || color));
        const [wx, wz] = this.toWorld(x, z);
        tile.scale.y = h;
        tile.position.set(wx, h / 2, wz); // tiles stand on y = 0
        tile.castShadow = tile.receiveShadow = true;
        this.worldGroup.add(tile);
        this.tileTops.set(`${x},${z}`, h);
      }
    }

    for (const e of world.entities) {
      const s = e.size ?? 4;
      const geo = {
        sphere: () => new THREE.SphereGeometry(s / 2, 24, 16),
        cone: () => new THREE.ConeGeometry(s / 2, s, 24),
      }[e.type]?.() ?? new THREE.BoxGeometry(s, s, s);
      const mesh = new THREE.Mesh(geo, new THREE.MeshStandardMaterial({ color: e.color, roughness: 0.6 }));
      const [wx, wz] = this.toWorld(e.x, e.z);
      mesh.position.set(wx, (this.tileTops.get(`${e.x},${e.z}`) ?? 0) + s / 2, wz);
      mesh.castShadow = mesh.receiveShadow = true;
      mesh.name = e.id;
      this.worldGroup.add(mesh);
    }

    // Fit the light's shadow camera to the grid.
    const span = Math.max(width, depth) * pitch;
    this.span = span;
    this.sun.position.set(span, span * 1.2, span * 0.6);
    Object.assign(this.sun.shadow.camera, { left: -span, right: span, top: span, bottom: -span, far: span * 4 });
    this.sun.shadow.camera.updateProjectionMatrix();

    if (firstLoad || cameraChanged) this.setCamera(world.camera);
  }

  setCamera(preset) {
    const d = this.span ?? 110;
    const pos = {
      orbit: [d * 0.9, d * 0.5, d * 0.9],
      isometric: [d * 0.85, d * 0.85, d * 0.85],
      top: [0, d * 1.3, 0.01],
    }[preset] ?? [d, d * 0.5, d];
    this.camera.position.set(...pos);
    this.controls.target.set(0, 0, 0);
    this.controls.update();
  }

  render() {
    this.renderer.render(this.scene, this.camera);
  }

  screenshot() {
    this.render(); // draw now so the buffer is filled
    return this.renderer.domElement.toDataURL('image/png');
  }

  onResize() {
    this.camera.aspect = window.innerWidth / window.innerHeight;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(window.innerWidth, window.innerHeight);
  }
}

const view = new GameView();

fetch('world.json', { cache: 'no-store' })
  .then((r) => (r.ok ? r.json() : FALLBACK_WORLD))
  .catch(() => FALLBACK_WORLD)
  .then((w) => { if (!view.world) view.setWorld(w); });

// Live link to the MCP server. Silently does nothing under a plain static server.
function connect() {
  const ws = new WebSocket(`${location.protocol === 'https:' ? 'wss' : 'ws'}://${location.host}/ws`);
  ws.onmessage = (ev) => {
    const msg = JSON.parse(ev.data);
    if (msg.type === 'world') view.setWorld(msg.world);
    if (msg.type === 'screenshot') {
      try {
        ws.send(JSON.stringify({ type: 'screenshot', id: msg.id, data: view.screenshot() }));
      } catch (err) {
        ws.send(JSON.stringify({ type: 'screenshot', id: msg.id, error: String(err) }));
      }
    }
  };
  let opened = false;
  ws.onopen = () => { opened = true; };
  ws.onclose = () => { if (opened) setTimeout(connect, 2000); }; // retry only if we were ever connected
}
connect();

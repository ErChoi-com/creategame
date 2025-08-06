import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

class baseWorld {
    constructor() {
        this._Initialize();
    }

    panelAnimate() {
        /*
        const plane = new THREE.Mesh(
            new THREE.PlaneGeometry(100, 100, 1, 1),
            new THREE.MeshStandardMaterial({ color: 0x808080, side: THREE.DoubleSide })
        );
        plane.castShadow = true;
        plane.receiveShadow = true;
        plane.rotation.x = -Math.PI / 2;
        this._scene.add(plane);
        */
        // above code was used to generate a single plane, below is for a grid of tiles. 
        const tileCount = 10;
        const tileXYZ = [10, 10, 10];
        // parameters for the tile generation

        const tileMaterial = new THREE.MeshStandardMaterial({
            color: 0xFFFFFF,})
        const geometry = new THREE.BoxGeometry(tileXYZ[0], tileXYZ[1], tileXYZ[2]);
        //geometry + material = mesh

        for (let x = 0; x < tileCount; x++) {
            for (let y = 0; y < tileCount; y++) {
                const tile = new THREE.Mesh(geometry, tileMaterial);
                tile.position.set(x * (tileXYZ[0] + 1), 0, y * (tileXYZ[2] + 1)); // Added +1 for spacing
                tile.castShadow = true;
                tile.receiveShadow = true;
                this._scene.add(tile);
            }
        }
    }

    snapToIsometricPerspective() {
        this._camera.position.set(40, 40, 40);
        this._camera.lookAt(0, 0, 0);
    }

    _Initialize() {
        this._threejs = new THREE.WebGLRenderer();
        this._threejs.shadowMap.enabled = true;
        this._threejs.shadowMap.type = THREE.PCFSoftShadowMap;
        this._threejs.setPixelRatio(window.devicePixelRatio);
        this._threejs.setSize(window.innerWidth, window.innerHeight);

        document.addEventListener('keydown', (e) => {
        if (e.key === ('a')) {
            this.snapToIsometricPerspective();
        }
    })

        document.body.appendChild(this._threejs.domElement);

        window.addEventListener('resize', () => {
            this._OnWindowResize();
        }, false);

        const fov = 60;
        const aspect = window.innerWidth / window.innerHeight;
        const near =  1;
        const far = 1000;
        this._camera = new THREE.PerspectiveCamera(fov, aspect, near, far);
        this._camera.position.set(75, 20, 0);

        this._scene = new THREE.Scene();

        let light = new THREE.DirectionalLight(0xFFFFFF, 1);
        light.position.set(100, 100, 100);
        light.target.position.set(0, 0, 0);
        light.castShadow = true;
        light.shadow.bias = -0.01;
        light.shadow.mapSize.width = 2048;
        light.shadow.mapSize.height = 2048;
        this._scene.add(light);

        // Add a helper to visualize the first directional light
        const helper = new THREE.DirectionalLightHelper(light, 10);
        this._scene.add(helper);

        light = new THREE.AmbientLight(0x404040, 0.5); // Reduced ambient light intensity
        this._scene.add(light);

        const controls = new OrbitControls(this._camera, this._threejs.domElement);
        controls.target.set(0, 0, 0);
        controls.update();

        // Create a box mesh with geometry and material
        const box = new THREE.Mesh(
        new THREE.BoxGeometry(2, 2, 2), // Width, Height, Depth
        new THREE.MeshStandardMaterial({
            color: 0x4287f5, // Blue color
            roughness: 0.5,
            metalness: 0.5
        })
        );

        //Animate the panels
        this.panelAnimate();

        // Set position of the box
        box.position.set(0, 1, 0); // x, y, z

        // Enable shadows
        box.castShadow = true;
        box.receiveShadow = true;

        // Add box to the scene
        this._scene.add(box);

        this._RAF();
    }

    _OnWindowResize() {
        this._camera.aspect = window.innerWidth / window.innerHeight;
        this._camera.updateProjectionMatrix();
        this._threejs.setSize(window.innerWidth, window.innerHeight);
    }

    _RAF() {
        requestAnimationFrame(() => {
            this._threejs.render(this._scene, this._camera);
            this._RAF();  // Keep the animation loop going
        });
    }
}

// Create an instance of the baseWorld class
let app = new baseWorld();
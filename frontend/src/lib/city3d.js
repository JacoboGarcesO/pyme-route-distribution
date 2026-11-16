// Escena 3D de WareTrack compartida por el mapa del panel (T13) y la página de
// seguimiento. Solo dibuja datos del backend: posiciones x, y de GET /network y
// la ruta ya calculada por GET /shortest-path (con parada `via`, CAMBIO-REQUISITO-F4).
// Lo demás (manzanas, aceras, semáforos, peatones) es decorado: no altera la red.
import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'

export const SCALE = 28
const BLUE = 0x2563eb
const ORANGE = 0xf97316
const ASPHALT = 0xb9c1cf
const SIDEWALK = 0xe3e7ef
const WHITE = 0xffffff
const TRUNK = 0x8b6b4a
const WALK = 2.2 // ancho de la acera
const CROSS = 6 // ancho que ocupa el cruce de una calle
const LOT = 7 // fondo de un lote
// Zona nítida alrededor del punto de vista: 3 x 3 manzanas.
export const FOCUS_HALF = SCALE * 1.5
// Recorrido del camión: unidades por segundo y pausas en A, en la parada y en B.
const SPEED = 10
const LOAD = 3.2
const STOP = 6
const END = 6.5
const ACCEL = 6 // aceleración y frenado del camión (unidades/s²)
const DECEL = 9
const STOP_LINE = 6.4 // distancia del centro del cruce a la línea de pare
const TRUCK_NOSE = 2.2 // del centro del camión a su parachoques

// Semáforos: las calles del mismo eje comparten fase y los dos ejes nunca
// están en verde a la vez. Ciclo de 14 s: verde 6, amarillo 1.5, rojo 6.5.
const SIGNAL_CYCLE = 14
export function signalColor(phase, time) {
  const t = (time + phase * (SIGNAL_CYCLE / 2)) % SIGNAL_CYCLE
  return t < 6 ? 'g' : t < 7.5 ? 'y' : 'r'
}
const axisPhase = (out) => (Math.abs(out.x) >= Math.abs(out.z) ? 0 : 1)

const WALLS = [0xffffff, 0xfdf6e3, 0xfde2cf, 0xe0ecff, 0xe5e7eb, 0xf5e1c8, 0xe8f5e9, 0xfce7f3]
const ROOFS = [0xb45309, 0x64748b, 0xd9603b, 0x8b5a3c, 0x9ca3af] // sin azul: el techo azul es del cliente
const DOORS = [0x7c4a2d, 0x14532d, 0x7f1d1d, 0x1e3a5f, 0x374151]
const GREENS = [0x6cc58a, 0x5bb37a, 0x7fd49a, 0x4f9f6a]
const SHIRTS = [0xef4444, 0x2563eb, 0xf59e0b, 0x10b981, 0x8b5cf6, 0xec4899, 0x0ea5e9, 0xffffff]
const pick = (rand, list) => list[Math.floor(rand() * list.length)]

// ---------- Escenario: cámara, luces y desenfoque fuera de foco ----------

const blurShader = {
  vertexShader: 'varying vec2 vUv; void main() { vUv = uv; gl_Position = vec4(position.xy, 0.0, 1.0); }',
  fragmentShader: `
    uniform sampler2D tColor;
    uniform sampler2D tDepth;
    uniform mat4 projInv;
    uniform mat4 viewInv;
    uniform vec2 focus;
    uniform float half_;
    uniform vec2 texel;
    varying vec2 vUv;
    void main() {
      vec4 base = texture2D(tColor, vUv);
      float depth = texture2D(tDepth, vUv).x;
      float amount = 1.0;
      if (depth < 1.0) {
        vec4 view = projInv * vec4(vUv * 2.0 - 1.0, depth * 2.0 - 1.0, 1.0);
        vec3 world = (viewInv * vec4(view.xyz / view.w, 1.0)).xyz;
        vec2 d = abs(world.xz - focus);
        amount = smoothstep(half_, half_ + 14.0, max(d.x, d.y));
      }
      vec4 color = base;
      if (amount > 0.0) {
        vec4 sum = vec4(0.0);
        for (int i = 0; i < 24; i++) {
          float a = float(i) * 2.39996;
          float r = sqrt((float(i) + 0.5) / 24.0) * 9.0 * amount;
          sum += texture2D(tColor, vUv + vec2(cos(a), sin(a)) * r * texel);
        }
        vec4 blurred = sum / 24.0;
        float gray = dot(blurred.rgb, vec3(0.299, 0.587, 0.114));
        blurred.rgb = mix(blurred.rgb, vec3(gray), 0.3 * amount);
        color = mix(base, blurred, amount);
      }
      gl_FragColor = color;
      #include <colorspace_fragment>
    }`,
}

// Luz según la hora local: [hora, cielo, luz ambiente, sol o luna, color del sol, noche 0..1].
const DAY_KEYS = [
  [0, 0x0b1026, 0.45, 0.35, 0x8fa6ff, 1],
  [5.2, 0x151b3d, 0.5, 0.35, 0x8fa6ff, 1],
  [6.2, 0xf4b98f, 1, 0.75, 0xffb070, 0.45],
  [7.5, 0xdfe8f5, 1.55, 1.25, 0xfff1d6, 0],
  [12, 0xeef2f8, 1.8, 1.5, 0xffffff, 0],
  [16.5, 0xe8ebf3, 1.7, 1.4, 0xfff4e0, 0],
  [17.7, 0xf2a477, 1.05, 0.85, 0xff9a5c, 0.3],
  [18.6, 0x3a3566, 0.6, 0.4, 0x9a8cff, 0.85],
  [19.4, 0x0b1026, 0.45, 0.35, 0x8fa6ff, 1],
  [24, 0x0b1026, 0.45, 0.35, 0x8fa6ff, 1],
]

// Hora actual en horas decimales. `?hora=21` en la URL la simula (para demos).
export function currentHour() {
  const forced = Number(new URLSearchParams(window.location.search).get('hora'))
  if (window.location.search.includes('hora=') && forced >= 0 && forced < 24) return forced
  const now = new Date()
  return now.getHours() + now.getMinutes() / 60
}

export const lightsOnAt = (hour) => hour >= 18 || hour < 6

export function dayPart(hour) {
  return hour < 5.5 || hour >= 19 ? 'Noche' : hour < 7.5 ? 'Amanecer' : hour < 11.5 ? 'Mañana' : hour < 13 ? 'Mediodía' : hour < 17.3 ? 'Tarde' : 'Atardecer'
}

function daylight(hour) {
  const i = DAY_KEYS.findIndex(([h], k) => hour >= h && hour < DAY_KEYS[k + 1][0])
  const [h0, sky0, amb0, sun0, col0, night0] = DAY_KEYS[i]
  const [h1, sky1, amb1, sun1, col1, night1] = DAY_KEYS[i + 1]
  const t = (hour - h0) / (h1 - h0)
  const mix = (a, b) => new THREE.Color(a).lerp(new THREE.Color(b), t)
  return {
    sky: mix(sky0, sky1),
    ambient: amb0 + (amb1 - amb0) * t,
    sun: sun0 + (sun1 - sun0) * t,
    sunColor: mix(col0, col1),
    night: night0 + (night1 - night0) * t,
    // De día el sol va de oriente (+x) a occidente; de noche la luna queda alta.
    angle: hour >= 6 && hour <= 18 ? (Math.PI * (hour - 6)) / 12 : null,
  }
}

export function createStage(container, { focusBlur = false } = {}) {
  const scene = new THREE.Scene()
  scene.background = new THREE.Color(0xeef2f8)
  scene.fog = new THREE.Fog(0xeef2f8, 260, 560)
  const camera = new THREE.PerspectiveCamera(40, 1, 0.5, 1200)
  camera.position.set(90, 130, 170)
  const renderer = new THREE.WebGLRenderer({ antialias: true })
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
  renderer.shadowMap.enabled = true
  renderer.shadowMap.type = THREE.PCFSoftShadowMap
  container.appendChild(renderer.domElement)

  const controls = new OrbitControls(camera, renderer.domElement)
  controls.enableDamping = true
  controls.maxPolarAngle = Math.PI / 2.3
  controls.minDistance = 8
  controls.maxDistance = 360

  const ambient = new THREE.HemisphereLight(0xffffff, 0xb8c4dc, 1.8)
  scene.add(ambient)
  const sun = new THREE.DirectionalLight(0xffffff, 1.5)
  sun.castShadow = true
  Object.assign(sun.shadow.camera, { left: -130, right: 130, top: 130, bottom: -130, far: 400 })
  sun.shadow.mapSize.set(4096, 4096)
  sun.shadow.bias = -0.0005
  scene.add(sun, sun.target)

  const ground = new THREE.Mesh(new THREE.PlaneGeometry(1400, 1400), new THREE.MeshStandardMaterial({ color: 0xeef1f6 }))
  ground.rotation.x = -Math.PI / 2
  ground.receiveShadow = true
  scene.add(ground)

  // Con focusBlur se pinta primero en una textura y un pase final desenfoca
  // todo lo que queda fuera de las 3 x 3 manzanas alrededor de la mira.
  let target = null
  let post = null
  if (focusBlur) {
    target = new THREE.WebGLRenderTarget(1, 1, { samples: 4, type: THREE.HalfFloatType, depthTexture: new THREE.DepthTexture(1, 1) })
    const material = new THREE.ShaderMaterial({
      ...blurShader,
      uniforms: {
        tColor: { value: target.texture },
        tDepth: { value: target.depthTexture },
        projInv: { value: camera.projectionMatrixInverse },
        viewInv: { value: camera.matrixWorld },
        focus: { value: new THREE.Vector2() },
        half_: { value: FOCUS_HALF },
        texel: { value: new THREE.Vector2() },
      },
      depthTest: false,
      depthWrite: false,
    })
    post = { scene: new THREE.Scene(), camera: new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1), material }
    post.scene.add(new THREE.Mesh(new THREE.PlaneGeometry(2, 2), material))
  }

  const resize = () => {
    const { clientWidth: w, clientHeight: h } = container
    if (!w || !h) return
    renderer.setSize(w, h)
    camera.aspect = w / h
    camera.updateProjectionMatrix()
    if (target) {
      const ratio = renderer.getPixelRatio()
      target.setSize(w * ratio, h * ratio)
      post.material.uniforms.texel.value.set(1 / (w * ratio), 1 / (h * ratio))
    }
  }
  const observer = new ResizeObserver(resize)
  observer.observe(container)
  resize()

  let frame = 0
  return {
    scene,
    camera,
    controls,
    start(tick) {
      const clock = new THREE.Clock()
      let light = null
      let lightAt = 0
      const loop = () => {
        frame = requestAnimationFrame(loop)
        const dt = Math.min(clock.getDelta(), 0.1)
        tick(clock.elapsedTime, dt)
        controls.update()
        // La sombra sigue a la mira para que la zona visible siempre la tenga.
        const focus = controls.target
        sun.target.position.set(focus.x, 0, focus.z)
        if (!light || clock.elapsedTime - lightAt > 1) {
          const hour = currentHour()
          light = daylight(hour)
          scene.userData.lightsOn = lightsOnAt(hour)
          lightAt = clock.elapsedTime
          scene.background.copy(light.sky)
          scene.fog.color.copy(light.sky)
          ambient.intensity = light.ambient
          // La luz ambiente toma el tono del cielo (naranja al atardecer) y se azula de noche.
          ambient.color.set(0xffffff).lerp(light.sky, 0.45).lerp(new THREE.Color(0x8fa6ff), light.night * 0.6)
          sun.intensity = light.sun
          sun.color.copy(light.sunColor)
          scene.userData.night = light.night
        }
        if (light.angle === null) sun.position.set(focus.x - 45, 95, focus.z - 35)
        else sun.position.set(focus.x + Math.cos(light.angle) * 95, Math.sin(light.angle) * 105 + 10, focus.z + 40)
        if (post) {
          post.material.uniforms.focus.value.set(focus.x, focus.z)
          renderer.setRenderTarget(target)
          renderer.render(scene, camera)
          renderer.setRenderTarget(null)
          renderer.render(post.scene, post.camera)
        } else {
          renderer.render(scene, camera)
        }
      }
      loop()
    },
    dispose() {
      cancelAnimationFrame(frame)
      observer.disconnect()
      controls.dispose()
      disposeObject(scene)
      target?.dispose()
      post?.material.dispose()
      renderer.dispose()
      renderer.domElement.remove()
    },
  }
}

export function disposeObject(object) {
  object.traverse((o) => {
    o.geometry?.dispose()
    o.material?.map?.dispose()
    o.material?.dispose()
    if (o.isInstancedMesh) o.dispose()
  })
}

// ---------- Utilidades ----------

// Aleatorio determinista: la misma red siempre da la misma ciudad.
function seeded(seed) {
  return () => {
    seed = (seed + 0x6d2b79f5) | 0
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

function segmentDistance(p, a, b) {
  const ab = new THREE.Vector3().subVectors(b, a)
  const t = THREE.MathUtils.clamp(new THREE.Vector3().subVectors(p, a).dot(ab) / ab.lengthSq(), 0, 1)
  return p.distanceTo(a.clone().addScaledVector(ab, t))
}

// Lado derecho de quien avanza en la dirección d (vista desde arriba, y hacia arriba).
const rightOf = (d) => new THREE.Vector3(-d.z, 0, d.x)
// Giro que lleva el eje +x local a la dirección d (placas y textos).
const yawX = (d) => Math.atan2(-d.z, d.x)

// Las piezas repetidas (cajas, conos, esferas...) se dibujan en pocas InstancedMesh.
function makeBatcher() {
  const items = new Map()
  const geometries = {
    box: () => new THREE.BoxGeometry(1, 1, 1),
    roof: () => new THREE.ConeGeometry(Math.SQRT1_2, 1, 4).rotateY(Math.PI / 4),
    sphere: () => new THREE.IcosahedronGeometry(0.5, 2),
    cyl: () => new THREE.CylinderGeometry(0.5, 0.5, 1, 12),
    cone: () => new THREE.ConeGeometry(0.5, 1, 10),
    tri: () => new THREE.CylinderGeometry(0.5, 0.5, 1, 3),
    glass: () => new THREE.BoxGeometry(1, 1, 1),
    bulb: () => new THREE.BoxGeometry(1, 1, 1),
  }
  // Brillo nocturno de cada tipo: ventanas cálidas y bombillas más intensas.
  const glow = { glass: [0xffcf7a, 0.85], bulb: [0xfff1b8, 2.2] }
  const add = (kind, color, x, y, z, sx, sy, sz, ry = 0, shadow = true, rx = 0, rz = 0) => {
    const key = `${kind}:${shadow}`
    if (!items.has(key)) items.set(key, [])
    items.get(key).push([color, x, y, z, sx, sy, sz, rx, ry, rz])
  }
  // Marco local: +z mira hacia `front`, +x a lo ancho. `yaw` gira la pieza dentro del marco.
  const frame = (origin, front) => {
    const r = new THREE.Vector3(front.z, 0, -front.x)
    const base = Math.atan2(front.x, front.z)
    return (kind, color, lx, y, lz, sx, sy, sz, shadow = true, { yaw = 0, tilt = 0 } = {}) =>
      add(kind, color, origin.x + r.x * lx + front.x * lz, y, origin.z + r.z * lx + front.z * lz, sx, sy, sz, base + yaw, shadow, tilt)
  }
  const build = (group) => {
    const m = new THREE.Matrix4()
    const q = new THREE.Quaternion()
    const e = new THREE.Euler(0, 0, 0, 'YXZ')
    const p = new THREE.Vector3()
    const s = new THREE.Vector3()
    const c = new THREE.Color()
    for (const [key, list] of items) {
      const [kind, shadow] = key.split(':')
      const material = new THREE.MeshStandardMaterial({ roughness: glow[kind] ? 0.3 : 0.8 })
      if (glow[kind]) {
        material.emissive.set(glow[kind][0])
        material.emissiveIntensity = 0
        group.userData.nightMats.push([material, glow[kind][1], kind])
      }
      const mesh = new THREE.InstancedMesh(geometries[kind](), material, list.length)
      list.forEach(([color, x, y, z, sx, sy, sz, rx, ry, rz], i) => {
        mesh.setMatrixAt(i, m.compose(p.set(x, y, z), q.setFromEuler(e.set(rx, ry, rz)), s.set(sx, sy, sz)))
        mesh.setColorAt(i, c.set(color))
      })
      mesh.castShadow = shadow === 'true'
      mesh.receiveShadow = true
      group.add(mesh)
    }
  }
  return { add, frame, build }
}

// Posición en el plano: x, y del backend; sin posición, un círculo como respaldo.
function positions(points) {
  const map = new Map()
  const placed = points.filter((p) => p.x != null && p.y != null)
  const cx = placed.length ? placed.reduce((s, p) => s + p.x, 0) / placed.length : 0
  const cy = placed.length ? placed.reduce((s, p) => s + p.y, 0) / placed.length : 0
  const loose = points.filter((p) => p.x == null || p.y == null)
  placed.forEach((p) => map.set(p.id, new THREE.Vector3((p.x - cx) * SCALE, 0, (p.y - cy) * SCALE)))
  loose.forEach((p, i) => {
    const a = (i / loose.length) * Math.PI * 2
    map.set(p.id, new THREE.Vector3(Math.cos(a) * SCALE * 2.5, 0, Math.sin(a) * SCALE * 2.5))
  })
  return map
}

// "Calle 11 con Carrera 6" y "Calle 11 con Carrera 7" comparten la "Calle 11".
const parts = (name) => name.split(/\s+con\s+/i)
function sharedStreet(nameA, nameB) {
  const b = parts(nameB)
  return parts(nameA).find((part) => b.includes(part)) ?? null
}

function crossNumber(cornerName, street) {
  return parts(cornerName).find((part) => part !== street)?.match(/\d+/)?.[0] ?? null
}

function canvasTexture(width, height, draw) {
  const canvas = document.createElement('canvas')
  canvas.width = width
  canvas.height = height
  draw(canvas.getContext('2d'))
  const texture = new THREE.CanvasTexture(canvas)
  texture.colorSpace = THREE.SRGBColorSpace
  texture.anisotropy = 4
  return texture
}

function glowTexture(width, height, cx, cy, radius) {
  return canvasTexture(width, height, (ctx) => {
    const g = ctx.createRadialGradient(cx, cy, 0, cx, cy, radius)
    g.addColorStop(0, 'rgba(255,255,255,1)')
    g.addColorStop(0.45, 'rgba(255,255,255,0.45)')
    g.addColorStop(1, 'rgba(255,255,255,0)')
    ctx.fillStyle = g
    ctx.fillRect(0, 0, width, height)
  })
}

function textWidth(text, font) {
  const ctx = document.createElement('canvas').getContext('2d')
  ctx.font = font
  return ctx.measureText(text).width
}

// Placa de dos caras (cada cara se lee de frente). +x local = a lo largo de la placa.
function plate(texture, width, height) {
  const g = new THREE.Group()
  const mat = new THREE.MeshStandardMaterial({ map: texture, roughness: 0.5 })
  for (const turn of [0, Math.PI]) {
    const face = new THREE.Mesh(new THREE.PlaneGeometry(width, height), mat)
    face.rotation.y = turn
    face.position.z = turn ? -0.015 : 0.015
    g.add(face)
  }
  const edge = new THREE.Mesh(new THREE.BoxGeometry(width + 0.06, height + 0.06, 0.02), new THREE.MeshStandardMaterial({ color: 0xcbd5e1 }))
  g.add(edge)
  return g
}

// Placa de nomenclatura verde (como las de las esquinas de la ciudad).
function streetSignTexture(name) {
  const font = '800 44px Plus Jakarta Sans, system-ui, sans-serif'
  const width = Math.ceil(textWidth(name, font)) + 60
  return [
    canvasTexture(width, 72, (ctx) => {
      ctx.fillStyle = '#ffffff'
      ctx.fillRect(0, 0, width, 72)
      ctx.fillStyle = '#0b6b3a'
      ctx.fillRect(4, 4, width - 8, 64)
      ctx.fillStyle = '#ffffff'
      ctx.font = font
      ctx.textBaseline = 'middle'
      ctx.fillText(name, 30, 38)
    }),
    width / 72,
  ]
}

// Señal reglamentaria de sentido único: rectángulo negro, flecha y "UNA VÍA" en blanco.
function oneWayTexture(pointsRight) {
  return canvasTexture(256, 96, (ctx) => {
    ctx.fillStyle = '#ffffff'
    ctx.fillRect(0, 0, 256, 96)
    ctx.fillStyle = '#111111'
    ctx.fillRect(5, 5, 246, 86)
    ctx.save()
    if (!pointsRight) {
      ctx.translate(256, 0)
      ctx.scale(-1, 1)
    }
    ctx.fillStyle = '#ffffff'
    ctx.beginPath()
    ctx.moveTo(22, 38)
    ctx.lineTo(176, 38)
    ctx.lineTo(176, 18)
    ctx.lineTo(234, 48)
    ctx.lineTo(176, 78)
    ctx.lineTo(176, 58)
    ctx.lineTo(22, 58)
    ctx.closePath()
    ctx.fill()
    ctx.restore()
    ctx.fillStyle = '#111111'
    ctx.font = '800 17px system-ui, sans-serif'
    ctx.textAlign = 'center'
    ctx.textBaseline = 'middle'
    ctx.fillText('UNA VÍA', pointsRight ? 104 : 152, 49)
  })
}

// Letrero de un cliente o de la bodega: nombre arriba y dato pequeño abajo.
function boardTexture(title, subtitle, bg) {
  const titleFont = '800 40px Plus Jakarta Sans, system-ui, sans-serif'
  const subFont = '600 26px Plus Jakarta Sans, system-ui, sans-serif'
  const width = Math.ceil(Math.max(textWidth(title, titleFont), subtitle ? textWidth(subtitle, subFont) : 0)) + 48
  const height = subtitle ? 108 : 70
  return [
    canvasTexture(width, height, (ctx) => {
      ctx.fillStyle = bg
      ctx.beginPath()
      ctx.roundRect(0, 0, width, height, 14)
      ctx.fill()
      ctx.fillStyle = '#ffffff'
      ctx.textBaseline = 'middle'
      ctx.font = titleFont
      ctx.fillText(title, 24, 38)
      if (subtitle) {
        ctx.font = subFont
        ctx.globalAlpha = 0.85
        ctx.fillText(subtitle, 24, 80)
      }
    }),
    width / height,
  ]
}

// Texto pintado sobre el asfalto (costo de la conexión).
function paintTexture(text) {
  return canvasTexture(256, 96, (ctx) => {
    ctx.fillStyle = 'rgba(255,255,255,0.92)'
    ctx.font = '800 64px Plus Jakarta Sans, system-ui, sans-serif'
    ctx.textAlign = 'center'
    ctx.textBaseline = 'middle'
    ctx.fillText(text, 128, 52)
  })
}

function pinLabel(text, color) {
  const [texture, ratio] = boardTexture(text, null, `#${color.toString(16).padStart(6, '0')}`)
  const sprite = new THREE.Sprite(new THREE.SpriteMaterial({ map: texture }))
  sprite.scale.set(1.4 * ratio, 1.4, 1)
  return sprite
}

// ---------- Árboles: frondoso, pino, guayacán, palma y arbusto ----------

function tree(L, lx, lz, rand, s = 1) {
  const kind = rand()
  if (kind < 0.32) {
    const g = pick(rand, GREENS)
    L('cyl', TRUNK, lx, 1.1 * s, lz, 0.42 * s, 2.2 * s, 0.42 * s)
    L('sphere', g, lx, 3 * s, lz, 2.7 * s, 2.4 * s, 2.7 * s)
    L('sphere', pick(rand, GREENS), lx + 0.8 * s, 2.6 * s, lz + 0.3 * s, 1.9 * s, 1.7 * s, 1.9 * s)
    L('sphere', pick(rand, GREENS), lx - 0.7 * s, 2.7 * s, lz - 0.5 * s, 2 * s, 1.8 * s, 2 * s)
    L('sphere', g, lx + 0.1 * s, 3.9 * s, lz - 0.1 * s, 1.7 * s, 1.5 * s, 1.7 * s)
  } else if (kind < 0.52) {
    L('cyl', 0x6b4f37, lx, 0.7 * s, lz, 0.32 * s, 1.4 * s, 0.32 * s)
    L('cone', 0x2f7d4f, lx, 2.1 * s, lz, 3 * s, 2.4 * s, 3 * s)
    L('cone', 0x37905b, lx, 3.3 * s, lz, 2.3 * s, 2.1 * s, 2.3 * s)
    L('cone', 0x3fa266, lx, 4.4 * s, lz, 1.5 * s, 1.8 * s, 1.5 * s)
  } else if (kind < 0.66) {
    // Guayacán florecido: amarillo o rosado.
    const [a, b] = rand() < 0.5 ? [0xfacc15, 0xfde047] : [0xf472b6, 0xf9a8d4]
    L('cyl', TRUNK, lx, 1.2 * s, lz, 0.36 * s, 2.4 * s, 0.36 * s)
    L('sphere', a, lx, 3.1 * s, lz, 3 * s, 1.8 * s, 3 * s)
    L('sphere', b, lx + 0.7 * s, 3.6 * s, lz - 0.4 * s, 2 * s, 1.3 * s, 2 * s)
    L('sphere', b, lx - 0.8 * s, 3.4 * s, lz + 0.4 * s, 1.8 * s, 1.2 * s, 1.8 * s)
  } else if (kind < 0.8) {
    // Palma: tronco alto y hojas caídas alrededor.
    const top = 5 * s
    L('cyl', 0xa1845c, lx, top / 2, lz, 0.32 * s, top, 0.32 * s)
    L('sphere', 0x8b6b4a, lx, top, lz, 0.6 * s, 0.5 * s, 0.6 * s)
    for (let i = 0; i < 7; i++) {
      const a = (i / 7) * Math.PI * 2
      L('box', i % 2 ? 0x4ade80 : 0x22c55e, lx + Math.sin(a) * 1.1 * s, top - 0.15 * s, lz + Math.cos(a) * 1.1 * s, 0.55 * s, 0.08 * s, 2.6 * s, true, { yaw: a, tilt: 0.45 })
    }
  } else {
    // Arbusto bajo.
    for (const [dx, dz, r] of [[0, 0, 1.6], [0.8, 0.3, 1.2], [-0.7, -0.2, 1.3]]) {
      L('sphere', pick(rand, GREENS), lx + dx * s, 0.6 * s, lz + dz * s, r * s, r * 0.8 * s, r * s)
    }
  }
}

// ---------- Edificaciones (marco local: el frente mira a +z, hacia la calle) ----------

function windowAt(L, x, y, z, w = 0.9, h = 0.8) {
  L('box', WHITE, x, y, z, w + 0.25, h + 0.25, 0.05, false)
  L('glass', 0x9cc3f0, x, y, z + 0.03, w, h, 0.05, false)
  L('box', WHITE, x, y, z + 0.06, 0.06, h, 0.03, false)
  L('box', WHITE, x, y - h / 2 - 0.12, z + 0.1, w + 0.35, 0.08, 0.22, false)
}

function frontYard(L, rand) {
  L('box', 0xd6d3d1, 0, 0.06, 3, 1.2, 0.08, 1, false) // caminito
  if (rand() < 0.6) {
    for (const x of [-1.9, 1.9]) L('box', 0x4d9e63, x, 0.45, 3.2, 2.2, 0.9, 0.55)
    L('sphere', 0xf472b6, -2.6, 0.95, 3.2, 0.4, 0.3, 0.4, false)
    L('sphere', 0xfacc15, 2.4, 0.95, 3.2, 0.4, 0.3, 0.4, false)
  } else {
    for (const y of [0.45, 0.85]) {
      for (const x of [-1.9, 1.9]) L('box', WHITE, x, y, 3.3, 2.2, 0.08, 0.06, false)
    }
    for (const x of [-2.9, -0.9, 0.9, 2.9]) L('box', WHITE, x, 0.5, 3.3, 0.12, 1, 0.12)
  }
}

function house(L, rand, wall, roof) {
  L('box', 0xd6d3d1, 0, 0.15, 0, 5.4, 0.3, 5.4)
  L('box', wall, 0, 1.65, 0, 5, 3, 5)
  L('roof', roof, 0, 4.05, 0, 5.9, 1.8, 5.9)
  L('box', 0x9a3412, 1.4, 4.5, -0.8, 0.6, 1.5, 0.6)
  L('box', WHITE, 0, 1.15, 2.52, 1.3, 2.1, 0.05, false)
  L('box', pick(rand, DOORS), 0, 1.1, 2.56, 1, 1.85, 0.05, false)
  L('sphere', 0xfacc15, 0.35, 1.1, 2.62, 0.1, 0.1, 0.1, false)
  L('box', 0xd6d3d1, 0, 0.2, 2.85, 1.6, 0.2, 0.6, false)
  windowAt(L, -1.6, 1.95, 2.52)
  windowAt(L, 1.6, 1.95, 2.52)
  L('glass', 0x9cc3f0, 2.53, 1.95, 0, 0.05, 0.8, 1, false)
  L('glass', 0x9cc3f0, -2.53, 1.95, 0, 0.05, 0.8, 1, false)
  frontYard(L, rand)
}

function townhouse(L, rand, wall) {
  L('box', 0xd6d3d1, 0, 0.15, 0, 5.6, 0.3, 5.6)
  L('box', wall, 0, 2.95, 0, 5.4, 5.6, 5.4)
  L('box', 0xcbd5e1, 0, 5.85, 0, 5.7, 0.3, 5.7)
  L('cyl', 0x1e3a5f, -1.4, 6.5, -1.4, 1.1, 1.1, 1.1) // tanque de agua
  for (const x of [-1.5, 1.5]) windowAt(L, x, 1.9, 2.72)
  windowAt(L, -1.5, 4.4, 2.72)
  // Balcón con baranda en el segundo piso.
  L('box', 0x334155, 1.3, 3.6, 3.3, 2.4, 0.15, 1.2)
  L('box', 0x334155, 1.3, 4.05, 3.85, 2.4, 0.06, 0.06, false)
  for (const x of [0.2, 0.8, 1.4, 2, 2.4]) L('box', 0x334155, x, 3.8, 3.85, 0.05, 0.5, 0.05, false)
  L('glass', 0x9cc3f0, 1.3, 4.5, 2.73, 1.2, 1.6, 0.05, false)
  L('box', pick(rand, DOORS), 0, 1.05, 2.74, 1, 1.9, 0.05, false)
  L('box', 0x475569, 0, 2.2, 3.1, 1.6, 0.12, 0.8) // alero de la puerta
  L('box', 0xe5e7eb, 2.85, 2.4, -1, 0.5, 0.6, 0.9) // aire acondicionado
  frontYard(L, rand)
}

function apartment(L, rand) {
  const floors = 3 + Math.floor(rand() * 3)
  const h = floors * 2.7
  const wall = pick(rand, [0xf1f5f9, 0xe2e8f0, 0xdbeafe, 0xfef3c7, 0xfde2cf])
  L('box', 0x94a3b8, 0, 0.3, 0, 6.1, 0.6, 6.1)
  L('box', wall, 0, h / 2, 0, 5.8, h, 5.8)
  for (const x of [-2.9, 2.9]) L('box', 0xcbd5e1, x, h / 2, 2.9, 0.3, h, 0.3, false) // columnas
  for (let f = 0; f < floors; f++) {
    const y = 1.6 + f * 2.7
    L('glass', 0x93c5fd, 0, y, 2.93, 4.8, 1, 0.08, false)
    L('box', 0xcbd5e1, 0, y - 0.65, 2.95, 5.6, 0.12, 0.12, false)
    if (f > 0 && (f + Math.floor(rand() * 2)) % 2) {
      L('box', 0x64748b, -1.3, y - 0.8, 3.4, 2, 0.12, 1)
      L('box', 0x94a3b8, -1.3, y - 0.45, 3.88, 2, 0.6, 0.05, false)
    }
    L('glass', 0x93c5fd, 2.93, y, 0, 0.08, 1, 4, false)
  }
  L('box', 0x334155, 0, 2.2, 3.4, 2.2, 0.15, 1.2) // marquesina de la entrada
  L('box', 0x1e293b, 0, 1, 2.95, 1.6, 2, 0.06, false)
  L('box', 0x475569, 0, h + 0.15, 0, 6, 0.3, 6)
  L('cyl', 0x1e3a5f, 1.4, h + 1, -1.3, 1.4, 1.4, 1.4)
  L('cyl', 0x94a3b8, -1.8, h + 1.4, -1.8, 0.06, 2.4, 0.06)
}

function shop(L, rand) {
  const wall = pick(rand, WALLS)
  const awning = pick(rand, [0xef4444, 0x2563eb, 0x10b981, 0xf59e0b, 0x8b5cf6])
  L('box', 0xd6d3d1, 0, 0.15, 0, 6, 0.3, 5.2)
  L('box', wall, 0, 2, 0, 5.8, 3.7, 5)
  L('box', 0x334155, 0, 1.35, 2.5, 4.9, 2.1, 0.06, false)
  L('glass', 0xbfdbfe, -0.6, 1.35, 2.54, 3.4, 1.8, 0.05, false)
  L('box', 0x475569, 1.7, 1.2, 2.54, 0.9, 1.9, 0.05, false)
  // Toldo a rayas.
  for (let i = 0; i < 6; i++) {
    L('box', i % 2 ? WHITE : awning, -2.42 + i * 0.97, 2.75, 3.05, 0.97, 0.18, 1.3, true, { tilt: 0.25 })
  }
  L('box', awning, 0, 3.45, 2.56, 3.6, 0.6, 0.08, false)
  L('box', WHITE, 0, 3.45, 2.61, 2.6, 0.18, 0.03, false)
  L('box', 0x92400e, -2.3, 0.45, 3.1, 0.8, 0.6, 0.8) // matera
  L('sphere', 0x4d9e63, -2.3, 1, 3.1, 0.9, 0.8, 0.9)
}

function park(L, rand) {
  L('box', 0x9ee6b0, 0, 0.1, 0, 6.4, 0.2, LOT - 0.2, false)
  L('box', 0xe7dcc8, 0, 0.22, 0, 1.2, 0.04, LOT - 0.2, false)
  L('box', 0xe7dcc8, 0, 0.22, 0, 6.4, 0.04, 1.2, false)
  // Fuente central.
  L('cyl', 0xcbd5e1, 0, 0.35, 0, 2.2, 0.5, 2.2)
  L('cyl', 0x7dd3fc, 0, 0.55, 0, 1.8, 0.1, 1.8, false)
  L('cyl', 0xcbd5e1, 0, 1, 0, 0.3, 1.2, 0.3)
  L('sphere', 0x7dd3fc, 0, 1.65, 0, 0.5, 0.4, 0.5, false)
  // Bancas, faroles y flores.
  for (const [x, z, yaw] of [[2.1, -1.6, 0], [-2.1, 1.6, Math.PI]]) {
    L('box', 0x8b5e3c, x, 0.5, z, 1.6, 0.12, 0.5, true, { yaw })
    L('box', 0x8b5e3c, x, 0.8, z + (yaw ? 0.25 : -0.25), 1.6, 0.4, 0.08, true, { yaw })
    L('box', 0x334155, x, 0.25, z, 1.3, 0.5, 0.35, false, { yaw })
  }
  L('cyl', 0x334155, -2.6, 1.5, -2.8, 0.1, 3, 0.1)
  L('sphere', 0xfff7cc, -2.6, 3.1, -2.8, 0.45, 0.45, 0.45, false)
  for (const [x, z] of [[-2.4, -0.9], [2.4, 0.9]]) {
    L('box', 0x92400e, x, 0.3, z, 1.2, 0.2, 0.8, false)
    for (const dx of [-0.3, 0.3]) L('sphere', pick(rand, [0xf472b6, 0xfacc15, 0xef4444, 0xa78bfa]), x + dx, 0.55, z, 0.45, 0.35, 0.45, false)
  }
  tree(L, -2.2, -2.2, rand, 0.75)
  tree(L, 2.3, 2.4, rand, 0.7)
}

function warehouseMesh(B, site, front, name) {
  // Marco: +z hacia la calle; las puertas de muelle miran a la calle.
  const L = B.frame(site, front)
  L('box', 0xd6dbe4, 0, 0.1, 1, 17, 0.2, 15, false) // patio de maniobras
  L('box', WHITE, 0, 2.95, -1.5, 13, 5.5, 9)
  L('box', 0xdbe3f0, 0, 5.95, -1.5, 13.4, 0.5, 9.4)
  for (const x of [-4, 0, 4]) {
    L('box', BLUE, x, 1.9, 3.02, 2.6, 3.2, 0.12, false)
    for (let y = 0.6; y < 3.4; y += 0.45) L('box', 0x1d4ed8, x, y, 3.09, 2.6, 0.05, 0.03, false)
  }
  L('box', 0x94a3b8, 0, 0.6, 3.7, 13, 1, 1.4) // andén de carga
  for (const x of [-4.5, 0, 4.5]) L('glass', 0x93c5fd, x, 6.3, -1.5, 2, 0.3, 6, false) // claraboyas
  // Estibas con cajas en el patio.
  for (const [x, z] of [[-6.5, 6], [-5, 6.4], [6, 6.2]]) {
    L('box', 0xa16207, x, 0.25, z, 1.3, 0.2, 1.3)
    L('box', 0xc8a26b, x, 0.75, z, 1.1, 0.8, 1.1)
  }
  // Reja lateral del patio.
  for (const x of [-8.4, 8.4]) {
    L('box', 0x94a3b8, x, 0.9, 1, 0.08, 1.8, 15, false)
    for (let z = -6; z <= 8; z += 2) L('box', 0x64748b, x, 0.9, z, 0.15, 1.8, 0.15)
  }
  // Letrero en la fachada.
  const [texture, ratio] = boardTexture(name, 'WareTrack · Centro de distribución', '#2563eb')
  const sign = new THREE.Mesh(new THREE.PlaneGeometry(1.6 * ratio, 1.6), new THREE.MeshStandardMaterial({ map: texture }))
  sign.position.set(0, 4.7, 3.06)
  const g = new THREE.Group()
  g.add(sign)
  g.position.copy(site)
  g.rotation.y = Math.atan2(front.x, front.z)
  return g
}

function pin(color, text) {
  const g = new THREE.Group()
  const mat = new THREE.MeshStandardMaterial({ color, roughness: 0.4 })
  const head = new THREE.Mesh(new THREE.SphereGeometry(1.1, 20, 14), mat)
  const tip = new THREE.Mesh(new THREE.ConeGeometry(0.95, 1.8, 20), mat)
  tip.rotation.x = Math.PI
  tip.position.y = -1.1
  const dot = new THREE.Mesh(new THREE.SphereGeometry(0.45, 12, 8), new THREE.MeshBasicMaterial({ color: WHITE }))
  dot.position.z = 0.75
  g.add(head, tip, dot)
  const tag = pinLabel(text, color)
  tag.position.y = 2.6
  g.add(tag)
  g.scale.setScalar(0.75)
  return g
}

function boxMesh() {
  const g = new THREE.Group()
  const box = new THREE.Mesh(new THREE.BoxGeometry(0.62, 0.48, 0.5), new THREE.MeshStandardMaterial({ color: 0xc8a26b, roughness: 0.9 }))
  const tape = new THREE.Mesh(new THREE.BoxGeometry(0.64, 0.05, 0.14), new THREE.MeshStandardMaterial({ color: 0xece3cf }))
  tape.position.y = 0.245
  box.castShadow = true
  g.add(box, tape)
  return g
}

function pedestrian(rand) {
  const g = new THREE.Group()
  const mat = (color) => new THREE.MeshStandardMaterial({ color, roughness: 0.8 })
  const pants = mat(pick(rand, [0x1e293b, 0x1e3a8a, 0x44403c, 0x334155]))
  const shirt = mat(pick(rand, SHIRTS))
  const skin = mat(pick(rand, [0xf1c27d, 0xc68642, 0x8d5524, 0xe0ac69]))
  const limb = (material, w, h, x, y) => {
    const pivot = new THREE.Group()
    pivot.position.set(x, y, 0)
    const mesh = new THREE.Mesh(new THREE.BoxGeometry(w, h, w), material)
    mesh.position.y = -h / 2
    mesh.castShadow = true
    pivot.add(mesh)
    g.add(pivot)
    return pivot
  }
  const legs = [limb(pants, 0.2, 0.8, -0.12, 0.8), limb(pants, 0.2, 0.8, 0.12, 0.8)]
  const arms = [limb(shirt, 0.14, 0.7, -0.38, 1.52), limb(shirt, 0.14, 0.7, 0.38, 1.52)]
  const body = new THREE.Mesh(new THREE.BoxGeometry(0.6, 0.8, 0.32), shirt)
  body.position.y = 1.2
  const head = new THREE.Mesh(new THREE.SphereGeometry(0.22, 12, 9), skin)
  head.position.y = 1.85
  const hair = new THREE.Mesh(new THREE.SphereGeometry(0.235, 12, 9, 0, Math.PI * 2, 0, Math.PI / 2), mat(pick(rand, [0x1f2937, 0x78350f, 0xfbbf24, 0x44403c])))
  hair.position.y = 1.88
  for (const m of [body, head]) m.castShadow = true
  g.add(body, head, hair)
  g.userData.limbs = { legs, arms }
  return g
}

// Semáforo en la esquina, mirando hacia `facing` (los carros que llegan al cruce).
function trafficLight(B, position, facing, phase, lamps) {
  const L = B.frame(position, facing)
  L('cyl', 0x334155, 0, 2.2, 0, 0.24, 4.4, 0.24)
  L('box', 0x1f2937, 0, 4.6, 0, 0.75, 2, 0.5)
  L('box', 0x111827, 0, 5.65, 0.05, 0.8, 0.1, 0.6, false)
  L('box', 0xfacc15, 0, 4.6, -0.27, 0.8, 2.05, 0.04, false) // placa trasera
  ;['r', 'y', 'g'].forEach((color, i) => {
    lamps.push({ position: position.clone().addScaledVector(facing, 0.27).setY(5.2 - i * 0.6), color, phase })
    L('box', 0x111827, 0, 5.38 - i * 0.6, 0.38, 0.5, 0.06, 0.28, false) // visera
  })
}

const LAMP_COLORS = { r: new THREE.Color(0xff3b30), y: new THREE.Color(0xffcc00), g: new THREE.Color(0x22c55e), off: new THREE.Color(0x3a4150) }

// ---------- Ciudad ----------

export function createCity(network, route) {
  const group = new THREE.Group()
  const anim = { pulses: [], bobs: [], lamps: [], walkers: [], nightMats: [], lampSpots: [] }
  group.userData = anim
  const B = makeBatcher()
  const rand = seeded(7)
  const pos = positions(network)
  const byId = new Map(network.map((p) => [p.id, p]))
  const isAddress = (id) => byId.get(id)?.type === 'pickup_point'
  const found = route?.found && route.path.length > 0
  const textures = new Map()
  const cached = (key, make) => textures.get(key) ?? textures.set(key, make()).get(key)

  // Una sola calle por par de puntos; si existe la inversa es de doble sentido.
  const edges = new Map()
  const neighbors = new Map(network.map((p) => [p.id, new Set()]))
  for (const point of network) {
    for (const c of point.connections) {
      neighbors.get(point.id).add(c.destination_id)
      neighbors.get(c.destination_id)?.add(point.id)
      const key = [point.id, c.destination_id].sort().join('|')
      const entry = edges.get(key)
      if (entry) entry.twoWay = true
      else edges.set(key, { from: point.id, to: c.destination_id, cost: c.cost_km, twoWay: false })
    }
  }
  const edgeOf = (a, b) => edges.get([a, b].sort().join('|'))

  // Calles: conexiones entre cruces o bodegas. Las casas de clientes no abren calle propia.
  const streets = [...edges.values()]
    .filter((e) => !isAddress(e.from) && !isAddress(e.to))
    .map((e) => {
      const a = pos.get(e.from)
      const b = pos.get(e.to)
      const len = a.distanceTo(b)
      const dir = new THREE.Vector3().subVectors(b, a).normalize()
      return { ...e, a, b, len, dir, width: e.twoWay ? 6 : 4.4, name: sharedStreet(byId.get(e.from).name, byId.get(e.to).name) }
    })
  // Un mueble de acera solo va donde no pisa el asfalto de otra calle (cruces incluidos).
  const offRoad = (p, own, margin = 1.3) =>
    streets.every((o) => o === own || segmentDistance(p, o.a, o.b) > o.width / 2 + margin)
  const incident = new Map(network.map((p) => [p.id, []]))
  for (const s of streets) {
    incident.get(s.from).push({ street: s, out: s.dir.clone() })
    incident.get(s.to).push({ street: s, out: s.dir.clone().negate() })
  }

  // Dirección de cada cliente: la calle más cercana entre las que tocan a su cruce;
  // el camión se parquea en esa calle, frente a la casa.
  const addresses = new Map()
  for (const point of network.filter((p) => p.type === 'pickup_point')) {
    const p = pos.get(point.id)
    const around = neighbors.get(point.id)
    const near = streets.filter((s) => around.has(s.from) || around.has(s.to))
    const candidates = near.length ? near : streets
    if (!candidates.length) continue
    const s =
      streets.find((c) => around.has(c.from) && around.has(c.to)) ??
      candidates.reduce((best, c) => (segmentDistance(p, c.a, c.b) < segmentDistance(p, best.a, best.b) ? c : best))
    const t = THREE.MathUtils.clamp(new THREE.Vector3().subVectors(p, s.a).dot(s.dir) / s.len, 0.3, 0.7)
    const foot = s.a.clone().addScaledVector(s.dir, t * s.len)
    const n = rightOf(s.dir)
    if (n.dot(new THREE.Vector3().subVectors(p, foot)) < 0) n.negate()
    const number = crossNumber(byId.get(s.from).name, s.name)
    addresses.set(point.id, {
      street: s,
      park: foot.clone().addScaledVector(n, s.width / 2 - 1.3),
      site: foot.clone().addScaledVector(n, s.width / 2 + WALK + 0.6 + LOT / 2),
      front: n.clone().negate(),
      door: foot.clone().addScaledVector(n, s.width / 2 + WALK + 0.6 + LOT / 2 - 3.1),
      text: s.name && number ? `${s.name} # ${number}-${String(Math.round(t * 100)).padStart(2, '0')}` : null,
    })
  }

  // Bodega: se aparta de las calles que llegan a ella, con su patio de maniobras.
  const sites = new Map()
  for (const point of network.filter((p) => p.type === 'warehouse')) {
    const p = pos.get(point.id)
    const away = new THREE.Vector3()
    for (const n of neighbors.get(point.id)) away.add(new THREE.Vector3().subVectors(p, pos.get(n)).normalize())
    if (away.lengthSq() === 0) away.set(0, 0, -1)
    away.normalize()
    const site = p.clone().addScaledVector(away, 13)
    sites.set(point.id, { site, front: away.clone().negate(), door: site.clone().addScaledVector(away, -4.8) })
  }

  // ---- Calles: asfalto, aceras, cebras, marcas, costo pintado y señales ----
  const oneWayMats = [true, false].map((right) => new THREE.MeshStandardMaterial({ map: oneWayTexture(right) }))
  for (const s of streets) {
    const mid = new THREE.Vector3().addVectors(s.a, s.b).multiplyScalar(0.5)
    const L = B.frame(mid, s.dir)
    L('box', ASPHALT, 0, 0.05, 0, s.width, 0.1, s.len + CROSS, false)
    for (const side of [-1, 1]) {
      L('box', SIDEWALK, side * (s.width / 2 + WALK / 2), 0.15, 0, WALK, 0.3, Math.max(0, s.len - CROSS), false)
      L('box', 0xcfd5df, side * (s.width / 2 + 0.06), 0.17, 0, 0.12, 0.34, Math.max(0, s.len - CROSS), false) // bordillo
    }

    if (s.twoWay) {
      // Doble sentido: línea central amarilla discontinua.
      for (let z = -s.len / 2 + 5; z < s.len / 2 - 5; z += 3.2) L('box', 0xfacc15, 0, 0.11, z + 0.8, 0.22, 0.03, 1.6, false)
    } else {
      // Sentido único: flechas blancas pintadas y la señal "UNA VÍA" al inicio.
      for (const z of [-s.len / 4, s.len / 4]) {
        L('box', WHITE, 0, 0.11, z - 0.6, 0.35, 0.03, 1.8, false)
        L('tri', WHITE, 0, 0.11, z + 0.6, 1.3, 0.03, 1.3, false)
      }
      const base = s.a.clone().addScaledVector(s.dir, CROSS / 2 + 2.5).addScaledVector(rightOf(s.dir), s.width / 2 + WALK - 0.4)
      B.add('cyl', 0x94a3b8, base.x, 1.4, base.z, 0.14, 2.8, 0.14)
      // La placa va encima del poste: el poste no tapa la flecha ni el texto.
      const sign = new THREE.Group()
      for (const [mat, turn] of [[oneWayMats[0], 0], [oneWayMats[1], Math.PI]]) {
        const face = new THREE.Mesh(new THREE.PlaneGeometry(2.4, 0.9), mat)
        face.rotation.y = turn
        face.position.z = turn ? -0.02 : 0.02
        sign.add(face)
      }
      sign.position.copy(base).setY(3.25)
      sign.rotation.y = yawX(s.dir)
      group.add(sign)
    }

    // Cebras en los extremos que llegan a un cruce.
    for (const [node, end] of [[s.from, -1], [s.to, 1]]) {
      if (incident.get(node).length < 3) continue
      const z = end * (s.len / 2 - CROSS / 2 - 1.4)
      for (let x = -s.width / 2 + 0.6; x < s.width / 2 - 0.3; x += 1) L('box', WHITE, x, 0.11, z, 0.5, 0.03, 2.2, false)
    }

    // Costo de la conexión pintado en el asfalto, en el carril derecho.
    const paint = new THREE.Mesh(
      new THREE.PlaneGeometry(2.8, 1.8),
      new THREE.MeshStandardMaterial({ map: cached(`paint:${s.cost}`, () => paintTexture(`${s.cost} km`)), transparent: true, depthWrite: false }),
    )
    paint.position.copy(mid).addScaledVector(rightOf(s.dir), s.twoWay ? s.width / 4 : 0).setY(0.13)
    paint.rotation.order = 'YXZ'
    paint.rotation.set(-Math.PI / 2, yawX(rightOf(s.dir)), 0) // se lee en el sentido de la marcha, como las marcas viales
    group.add(paint)

    // Mobiliario: postes de luz y canecas en la acera.
    for (const side of [1, -1]) {
      const n = rightOf(s.dir).multiplyScalar(side)
      // El lado opuesto se corre media separación para alternar, sin pasar del final de la acera.
      for (let along = CROSS + 2 + (side > 0 ? 0 : 6); along < s.len - CROSS; along += 13) {
        const p = s.a.clone().addScaledVector(s.dir, along).addScaledVector(n, s.width / 2 + 0.45)
        if (!offRoad(p, s)) continue
        const F = B.frame(p, n.clone().negate())
        F('cyl', 0x475569, 0, 2.6, 0, 0.16, 5.2, 0.16)
        F('box', 0x475569, 0, 5.15, 0.6, 0.1, 0.1, 1.3, false)
        F('box', 0x1f2937, 0, 5.05, 1.2, 0.5, 0.15, 0.7, false)
        F('bulb', 0xfff7cc, 0, 4.96, 1.2, 0.4, 0.04, 0.55, false)
        anim.lampSpots.push(p.clone().addScaledVector(n, -1.2)) // suelo bajo la bombilla
        if (rand() < 0.4) F('cyl', 0x15803d, 0.9, 0.55, -0.2, 0.55, 0.8, 0.55)
        if (rand() < 0.15) {
          F('cyl', 0xdc2626, -0.9, 0.5, -0.2, 0.3, 0.7, 0.3)
          F('sphere', 0xdc2626, -0.9, 0.9, -0.2, 0.32, 0.3, 0.32, false)
        }
      }
    }

    // Peatones caminando por la acera (ida y vuelta).
    for (const side of [-1, 1]) {
      if (rand() < 0.45 || s.len < 16) continue
      const offset = rightOf(s.dir).multiplyScalar(side * (s.width / 2 + WALK / 2 + 0.2))
      const walker = pedestrian(rand)
      Object.assign(walker.userData, {
        from: s.a.clone().addScaledVector(s.dir, CROSS / 2 + 1).add(offset),
        to: s.b.clone().addScaledVector(s.dir, -(CROSS / 2 + 1)).add(offset),
        speed: 1.2 + rand() * 0.8,
        phase: rand() * 100,
      })
      anim.walkers.push(walker)
      group.add(walker)
    }
  }

  // ---- Esquinas: placas de nomenclatura y semáforos ----
  const signals = new Map() // cruce -> (punto del que llega el tráfico -> fase)
  for (const point of network) {
    const p = pos.get(point.id)
    const around = incident.get(point.id)
    // Cada nombre de calle que llega a la esquina, con la dirección en que sale.
    const named = new Map()
    for (const { street, out } of around) if (street.name && !named.has(street.name)) named.set(street.name, out)
    if (point.type === 'neighborhood' && named.size) {
      const [[name1, o1], second] = [...named]
      // La otra calle se busca hacia la derecha de la primera para dejar libre la esquina del semáforo.
      const o2 = second ? second[1] : rightOf(o1)
      const corner = p.clone().addScaledVector(o1, CROSS / 2 + WALK / 2 + 0.3).addScaledVector(o2, CROSS / 2 + WALK / 2 + 0.3)
      B.add('cyl', 0x334155, corner.x, 2, corner.z, 0.14, 4, 0.14)
      B.add('sphere', 0x334155, corner.x, 4.05, corner.z, 0.2, 0.2, 0.2, false)
      ;[[name1, o1, 3.75], ...(second ? [[second[0], second[1], 3.15]] : [])].forEach(([name, dir, y]) => {
        const [texture, ratio] = cached(`street:${name}`, () => streetSignTexture(name))
        const blade = plate(texture, 0.55 * ratio, 0.55)
        // Montada como bandera: sale del poste a lo largo de su calle.
        blade.position.copy(corner).addScaledVector(dir, (0.55 * ratio) / 2 + 0.12).setY(y)
        blade.rotation.y = yawX(dir)
        group.add(blade)
      })
    } else if (point.type === 'neighborhood' && !/\s+con\s+/i.test(point.name)) {
      // Punto sin nombre de cruce: un letrero propio en la acera.
      const [texture, ratio] = boardTexture(point.name, null, '#334155')
      const board = plate(texture, 0.9 * ratio, 0.9)
      const spot = p.clone().add(new THREE.Vector3(CROSS / 2 + 1, 0, CROSS / 2 + 1))
      B.add('cyl', 0x334155, spot.x, 1.3, spot.z, 0.12, 2.6, 0.12)
      board.position.copy(spot).setY(3)
      group.add(board)
    }

    // Un semáforo por cada calle por la que llega tráfico al cruce, a la derecha
    // de quien llega, con su línea de pare en el carril de llegada.
    if (around.length >= 3 && point.type === 'neighborhood') {
      const approaches = new Map()
      for (const { street, out } of around) {
        if (!street.twoWay && street.to !== point.id) continue
        const from = street.from === point.id ? street.to : street.from
        const phase = axisPhase(out)
        approaches.set(from, phase)
        const spot = p.clone().addScaledVector(out, CROSS / 2 + 2.4).addScaledVector(rightOf(out), -(street.width / 2 + WALK - 0.4))
        trafficLight(B, spot, out, phase, anim.lamps)
        const lane = street.twoWay ? street.width / 2 : street.width
        const line = p.clone().addScaledVector(out, STOP_LINE).addScaledVector(rightOf(out), street.twoWay ? -street.width / 4 : 0)
        B.frame(line, out)('box', WHITE, 0, 0.115, 0, lane - 0.3, 0.03, 0.45, false)
      }
      signals.set(point.id, approaches)
    }
  }

  // ---- Clientes y bodegas ----
  const occupied = [] // [centro, radio] de lo ya construido
  for (const point of network) {
    const address = addresses.get(point.id)
    const yard = sites.get(point.id)
    const lone = !address && !yard && point.type === 'pickup_point'
    if (address || lone) {
      const site = address?.site ?? pos.get(point.id)
      const front = address?.front ?? new THREE.Vector3(0, 0, 1)
      house(B.frame(site, front), rand, WHITE, BLUE)
      occupied.push([site, 3.6])
      // Letrero del cliente en el antejardín, mirando a la calle.
      const [texture, ratio] = boardTexture(point.name, address?.text ?? 'Cliente WareTrack', '#2563eb')
      const board = plate(texture, 0.95 * ratio, 0.95)
      const L = B.frame(site, front)
      L('cyl', 0x334155, 2.6, 0.9, 3.25, 0.1, 1.8, 0.1)
      board.position.copy(site).addScaledVector(front, 3.25).addScaledVector(new THREE.Vector3(front.z, 0, -front.x), 2.6 - (0.95 * ratio) / 2).setY(2.2)
      board.rotation.y = Math.atan2(front.x, front.z)
      group.add(board)
    } else if (yard) {
      group.add(warehouseMesh(B, yard.site, yard.front, point.name))
      occupied.push([yard.site, 9], [yard.site.clone().addScaledVector(yard.front, -6), 9])
    }
  }

  // ---- Lotes: casas, edificios, tiendas y parques a lado y lado de cada calle ----
  const nodes = [...pos.values()]
  const lotWidth = 6.8
  for (const s of streets) {
    for (const side of [1, -1]) {
      const n = rightOf(s.dir).multiplyScalar(side)
      const usable = s.len - CROSS - 2 * WALK
      const count = Math.floor(usable / lotWidth)
      for (let k = 0; k < count; k++) {
        const along = CROSS / 2 + WALK + (usable - count * lotWidth) / 2 + lotWidth * (k + 0.5)
        const center = s.a.clone().addScaledVector(s.dir, along).addScaledVector(n, s.width / 2 + WALK + 0.6 + LOT / 2)
        const blocked =
          occupied.some(([o, r]) => o.distanceTo(center) < r + 3.2) ||
          nodes.some((o) => o.distanceTo(center) < 7) ||
          streets.some((o) => o !== s && segmentDistance(center, o.a, o.b) < o.width / 2 + WALK + LOT / 2 - 0.2)
        if (blocked) continue
        occupied.push([center, 3.2])
        const L = B.frame(center, n.clone().negate())
        const roll = rand()
        if (roll < 0.36) house(L, rand, pick(rand, WALLS), pick(rand, ROOFS))
        else if (roll < 0.56) townhouse(L, rand, pick(rand, WALLS))
        else if (roll < 0.72) apartment(L, rand)
        else if (roll < 0.86) shop(L, rand)
        else park(L, rand)
      }
      // Árboles en la acera, entre los postes.
      for (let along = CROSS + 5; along < s.len - CROSS - 2; along += 8.5) {
        if (rand() < 0.35) continue
        const spot = s.a.clone().addScaledVector(s.dir, along).addScaledVector(n, s.width / 2 + WALK - 0.5)
        if (occupied.some(([o, r]) => o.distanceTo(spot) < r + 0.8) || !offRoad(spot, s)) continue
        B.add('cyl', 0x8b7355, spot.x, 0.33, spot.z, 1.1, 0.06, 1.1, 0, false) // alcorque
        tree(B.frame(spot, new THREE.Vector3(0, 0, 1)), 0, 0, rand, 0.65)
      }
    }
  }

  B.build(group)

  // Charcos de luz de los postes: un disco cálido sobre el suelo, todos en una InstancedMesh.
  if (anim.lampSpots.length) {
    const pools = new THREE.InstancedMesh(
      new THREE.PlaneGeometry(10, 10).rotateX(-Math.PI / 2),
      new THREE.MeshBasicMaterial({ map: glowTexture(128, 128, 64, 64, 64), color: 0xffcf7a, transparent: true, opacity: 0.55, blending: THREE.AdditiveBlending, depthWrite: false }),
      anim.lampSpots.length,
    )
    const m = new THREE.Matrix4()
    anim.lampSpots.forEach((spot, i) => pools.setMatrixAt(i, m.makeTranslation(spot.x, 0.33, spot.z)))
    pools.visible = false
    anim.pools = pools
    group.add(pools)
  }

  // Todas las luces de semáforo en una sola InstancedMesh; su color cambia cada cuadro.
  if (anim.lamps.length) {
    const lampMesh = new THREE.InstancedMesh(new THREE.SphereGeometry(0.2, 10, 8), new THREE.MeshBasicMaterial(), anim.lamps.length)
    const m = new THREE.Matrix4()
    anim.lamps.forEach((lamp, i) => {
      lampMesh.setMatrixAt(i, m.makeTranslation(lamp.position.x, lamp.position.y, lamp.position.z))
      lampMesh.setColorAt(i, LAMP_COLORS.off)
    })
    anim.lampMesh = lampMesh
    group.add(lampMesh)
  }

  // ---- Ruta del camión: por su carril, parqueando frente a la casa del cliente ----
  let tl = null
  if (found && route.path.length > 1) {
    const anchor = (id) => addresses.get(id)?.park ?? pos.get(id)
    const raw = route.path.map((p) => anchor(p.id).clone())
    // Si la casa queda en la calle por la que ya viene el camión, se parquea al pasar
    // frente a ella en vez de seguir hasta la esquina y devolverse.
    const n = route.path.length
    const home = addresses.get(route.path[n - 1].id)
    const ends = home ? [home.street.from, home.street.to] : []
    const parkOnTheWay = n >= 3 && ends.includes(route.path[n - 2].id) && ends.includes(route.path[n - 3].id)
    if (parkOnTheWay) raw[n - 2] = raw[n - 1].clone()
    const lanes = raw.slice(1).map((b, i) => {
      const a = raw[i]
      const e = edgeOf(route.path[i].id, route.path[i + 1].id)
      const offset = e?.twoWay && !isAddress(route.path[i].id) && !isAddress(route.path[i + 1].id) ? 1.5 : 0
      const dir = new THREE.Vector3().subVectors(b, a)
      return dir.lengthSq() < 1e-6 ? dir : rightOf(dir.normalize()).multiplyScalar(offset)
    })
    const points = raw.map((p, i) => {
      const before = lanes[i - 1] ?? lanes[i]
      const after = lanes[i] ?? lanes[i - 1]
      return p.clone().add(before.clone().add(after).multiplyScalar(0.5)).setY(0.1)
    })
    if (parkOnTheWay) points[n - 2] = points[n - 1].clone()
    tl = timeline(route, points)
    // Líneas de pare con semáforo que el camión encuentra en su recorrido.
    tl.signals = route.path
      .map((p, k) => {
        const from = k > 1 && isAddress(route.path[k - 1].id) ? route.path[k - 2].id : route.path[k - 1]?.id
        return { k, phase: k > 0 ? signals.get(p.id)?.get(from) : undefined }
      })
      .filter(({ k, phase }) => phase !== undefined && !(parkOnTheWay && k === n - 2))
      .map(({ k, phase }) => ({ d: tl.cum[k] - STOP_LINE - TRUCK_NOSE, phase }))
      .filter(({ d }) => d > 0)

    const ribbon = new THREE.MeshBasicMaterial({ color: BLUE, transparent: true, opacity: 0.75 })
    points.slice(1).forEach((b, i) => {
      const a = points[i]
      const len = a.distanceTo(b)
      const strip = new THREE.Mesh(new THREE.BoxGeometry(1.1, 0.04, len + 1.1), ribbon)
      strip.position.lerpVectors(a, b, 0.5).setY(0.14)
      strip.rotation.y = Math.atan2(b.x - a.x, b.z - a.z)
      group.add(strip)
    })
  }

  // Marcadores A, B y parada sobre el edificio o el cruce correspondiente.
  if (found) {
    const markerAt = (id) => addresses.get(id)?.site ?? sites.get(id)?.site ?? pos.get(id)
    const roles = [[route.path[0].id, 'A', BLUE], [route.path.at(-1).id, 'B', BLUE]]
    if (route.via_id) roles.push([route.via_id, 'Parada', ORANGE])
    for (const [id, text, color] of roles) {
      if (!pos.has(id)) continue
      const marker = pin(color, text)
      marker.position.copy(markerAt(id)).setY(sites.has(id) ? 13 : 10)
      marker.userData.baseY = marker.position.y
      anim.bobs.push(marker)
      group.add(marker)
    }
    if (route.via_id && tl && tl.stopIndex > 0) {
      const ring = new THREE.Mesh(new THREE.TorusGeometry(3.2, 0.22, 12, 48), new THREE.MeshBasicMaterial({ color: ORANGE }))
      ring.rotation.x = Math.PI / 2
      ring.position.copy(tl.points[tl.stopIndex]).setY(0.35)
      anim.pulses.push(ring)
      group.add(ring)
    }
  }

  let crew = null
  if (tl) {
    const n = route.path.length
    const dir0 = new THREE.Vector3().subVectors(tl.points[1], tl.points[0])
    if (dir0.lengthSq() < 1e-6) dir0.set(1, 0, 0)
    dir0.normalize()
    const origin = sites.get(route.path[0].id) ?? addresses.get(route.path[0].id)
    const dock = origin?.door ?? tl.points[0].clone().addScaledVector(rightOf(dir0), 6)
    const across = origin ? new THREE.Vector3(origin.front.z, 0, -origin.front.x) : dir0.clone()
    const rear = tl.points[0].clone().addScaledVector(dir0, -2.3)
    const loaders = [-1.4, 1.4].map((offset, i) => {
      const worker = { person: pedestrian(rand), box: boxMesh(), dock: dock.clone().addScaledVector(across, offset), rear: rear.clone().addScaledVector(rightOf(dir0), i ? 0.45 : -0.45) }
      group.add(worker.person, worker.box)
      return worker
    })
    const deliveries = []
    for (const [index, final] of [[tl.stopIndex, false], [n - 1, true]]) {
      if (index <= 0) continue
      const id = route.path[index].id
      const place = addresses.get(id) ?? sites.get(id)
      if (!place) continue
      const dropped = boxMesh()
      dropped.position.copy(place.door).addScaledVector(place.front, 0.35).setY(addresses.has(id) ? 0.54 : 0.44)
      dropped.visible = false
      const courier = { final, door: place.door, person: pedestrian(rand), box: boxMesh(), dropped }
      group.add(courier.person, courier.box, dropped)
      deliveries.push(courier)
    }
    for (const o of [...loaders, ...deliveries]) o.person.visible = o.box.visible = false
    crew = { loaders, deliveries }
  }

  const radius = Math.max(40, ...nodes.map((n) => Math.max(Math.abs(n.x), Math.abs(n.z))))
  return {
    group,
    crew,
    timeline: tl,
    radius,
    addresses: new Map([...addresses].filter(([, a]) => a.text).map(([id, a]) => [id, a.text])),
  }
}

function timeline(route, points) {
  const lengths = points.slice(1).map((p, i) => p.distanceTo(points[i]))
  const cum = [0]
  lengths.forEach((l) => cum.push(cum.at(-1) + l))
  const total = cum.at(-1)
  // La parada puede repetirse en path; cuenta su primera aparición intermedia.
  const stopIndex = route.via_id
    ? route.path.findIndex((p, i) => i > 0 && i < route.path.length - 1 && p.id === route.via_id)
    : -1
  return {
    points,
    lengths,
    cum,
    total,
    stopIndex,
    costs: route.connections.map((c) => Number(c.cost_km)),
    signals: [],
  }
}

// `focus` (opcional): los peatones lejos de la zona nítida no se animan ni se dibujan.
export function animateCity(group, time, focus = null) {
  const { pulses = [], bobs = [], lamps = [], walkers = [], lampMesh, nightMats = [] } = group.userData
  // Las ventanas se encienden poco a poco al oscurecer; los postes, de 6 p. m. a 6 a. m.
  const night = group.parent?.userData.night ?? 0
  const lightsOn = !!group.parent?.userData.lightsOn
  for (const [material, strength, kind] of nightMats) material.emissiveIntensity = (kind === 'bulb' ? Number(lightsOn) : night) * strength
  if (group.userData.pools) group.userData.pools.visible = lightsOn
  for (const o of pulses) o.scale.setScalar(1 + Math.sin(time * 4) * 0.12)
  for (const o of bobs) o.position.y = o.userData.baseY + Math.sin(time * 3) * 0.3
  if (lampMesh) {
    const active = [signalColor(0, time), signalColor(1, time)]
    lamps.forEach((lamp, i) => lampMesh.setColorAt(i, LAMP_COLORS[lamp.color === active[lamp.phase] ? lamp.color : 'off']))
    lampMesh.instanceColor.needsUpdate = true
  }
  const far = FOCUS_HALF + 20
  for (const w of walkers) {
    const { from, to, speed, phase, limbs } = w.userData
    if (focus) {
      w.visible = Math.abs((from.x + to.x) / 2 - focus.x) < far && Math.abs((from.z + to.z) / 2 - focus.z) < far
      if (!w.visible) continue
    }
    const len = from.distanceTo(to)
    const d = ((time + phase) * speed) % (2 * len)
    const forward = d < len
    w.position.lerpVectors(from, to, forward ? d / len : 2 - d / len)
    w.position.y = 0.3 + Math.abs(Math.sin(time * speed * 5)) * 0.05
    w.rotation.y = Math.atan2(to.x - from.x, to.z - from.z) + (forward ? 0 : Math.PI)
    const swing = Math.sin(time * speed * 5) * 0.5
    limbs.legs[0].rotation.x = swing
    limbs.legs[1].rotation.x = -swing
    limbs.arms[0].rotation.x = -swing
    limbs.arms[1].rotation.x = swing
  }
}

function truckLogo() {
  return canvasTexture(256, 96, (ctx) => {
    ctx.fillStyle = '#ffffff'
    ctx.fillRect(0, 0, 256, 96)
    ctx.fillStyle = '#2563eb'
    ctx.font = '800 44px Plus Jakarta Sans, system-ui, sans-serif'
    ctx.textBaseline = 'middle'
    ctx.fillText('WareTrack', 18, 46)
  })
}

export function makeTruck() {
  const g = new THREE.Group()
  const part = (w, h, d, color, x, y, z, glow = null) => {
    const material = new THREE.MeshStandardMaterial({ color, roughness: 0.55 })
    if (glow) material.emissive.set(glow)
    const mesh = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), material)
    mesh.position.set(x, y, z)
    mesh.castShadow = true
    g.add(mesh)
    return mesh
  }
  part(5.4, 0.4, 2.1, 0x1f2937, 0.3, 0.6, 0) // chasis
  part(4.2, 2.6, 2.4, 0xffffff, -0.5, 2.1, 0) // caja de carga
  part(4.22, 0.4, 2.42, 0x14b8a6, -0.5, 1.3, 0) // franja
  part(0.05, 2.4, 2.2, 0xe5e7eb, -2.62, 2.1, 0) // puerta trasera
  part(1.8, 2.1, 2.3, 0xffffff, 2.5, 1.85, 0) // cabina
  part(0.08, 0.9, 2, 0x1e293b, 3.42, 2.3, 0) // parabrisas
  part(1, 0.7, 0.05, 0x1e293b, 2.5, 2.35, 1.16) // ventanas laterales
  part(1, 0.7, 0.05, 0x1e293b, 2.5, 2.35, -1.16)
  part(0.2, 0.35, 2.3, 0x9ca3af, 3.5, 0.75, 0) // parachoques
  part(0.06, 0.5, 1.2, 0x374151, 3.43, 1.25, 0) // rejilla
  const heads = [0.85, -0.85].map((z) => part(0.06, 0.25, 0.4, 0xfff7cc, 3.44, 1.3, z, 0xfff1c8)) // farolas
  const tails = [0.9, -0.9].map((z) => part(0.06, 0.2, 0.3, 0xb91c1c, -2.65, 0.9, z, 0xff2d2d)) // stops
  // Foco real que alumbra el camino y un haz suave pintado en el suelo.
  const spot = new THREE.SpotLight(0xfff1c8, 120, 50, 0.6, 0.6, 1.4)
  spot.position.set(3.5, 1.3, 0)
  spot.target.position.set(14, 0, 0)
  const beam = new THREE.Mesh(
    new THREE.PlaneGeometry(16, 6).rotateX(-Math.PI / 2),
    new THREE.MeshBasicMaterial({ map: glowTexture(256, 96, 0, 48, 256), color: 0xfff1c8, transparent: true, opacity: 0.5, blending: THREE.AdditiveBlending, depthWrite: false }),
  )
  beam.position.set(11.5, 0.3, 0)
  g.add(spot, spot.target, beam)
  g.userData.lights = { heads, tails, spot, beam, on: null }
  part(0.15, 0.4, 0.1, 0x111827, 3.1, 2.4, 1.3) // espejos
  part(0.15, 0.4, 0.1, 0x111827, 3.1, 2.4, -1.3)
  const logoMat = new THREE.MeshStandardMaterial({ map: truckLogo() })
  for (const side of [1, -1]) {
    const logo = new THREE.Mesh(new THREE.PlaneGeometry(3, 1.1), logoMat)
    logo.position.set(-0.5, 2.4, side * 1.215)
    logo.rotation.y = side > 0 ? 0 : Math.PI
    g.add(logo)
  }
  const wheelGeo = new THREE.CylinderGeometry(0.5, 0.5, 0.4, 18)
  const wheelMat = new THREE.MeshStandardMaterial({ color: 0x111827 })
  const hubMat = new THREE.MeshStandardMaterial({ color: 0x9ca3af })
  for (const x of [-1.8, -0.6, 2.4]) {
    for (const z of [1.05, -1.05]) {
      const wheel = new THREE.Mesh(wheelGeo, wheelMat)
      wheel.rotation.x = Math.PI / 2
      wheel.position.set(x, 0.5, z)
      wheel.castShadow = true
      const hub = new THREE.Mesh(new THREE.CylinderGeometry(0.22, 0.22, 0.42, 10), hubMat)
      hub.rotation.x = Math.PI / 2
      hub.position.set(x, 0.5, z)
      g.add(wheel, hub)
    }
  }
  g.scale.setScalar(0.75)
  return g
}

// Recorrido simulado cuadro a cuadro: carga en A, avanza, frena en rojo, espera
// en la parada y entrega en B; luego vuelve a empezar.
export function createRun() {
  return { d: 0, v: 0, age: 0, phase: 'loading', timer: LOAD, passedStop: false, cleared: new Set(), waiting: false }
}

export function stepTruck(tl, run, dt, time) {
  const stopD = tl.stopIndex > 0 ? tl.cum[tl.stopIndex] : -1
  const moving = () => (stopD >= 0 && !run.passedStop ? 'toStop' : 'toDest')
  run.age += dt
  run.waiting = false
  if (run.phase === 'loading' || run.phase === 'stop' || run.phase === 'delivered') {
    run.timer -= dt
    if (run.timer <= 0) {
      if (run.phase === 'delivered') Object.assign(run, createRun())
      else run.phase = moving()
    }
  } else {
    // Próximo punto donde hay que detenerse: la parada, B o un semáforo que no deja pasar.
    let target = stopD >= 0 && !run.passedStop ? stopD : tl.total
    for (const [i, signal] of tl.signals.entries()) {
      if (signal.d < run.d - 0.05 || signal.d >= target || run.cleared.has(i)) continue
      const color = signalColor(signal.phase, time)
      const braking = (run.v * run.v) / (2 * DECEL)
      const gap = signal.d - run.d
      // En verde cerca de la línea, o en amarillo sin espacio para frenar, cruza y ya no vuelve a mirar ese semáforo.
      if ((color === 'g' && gap < braking + 1) || (color === 'y' && gap < braking * 0.6 && run.v > 1)) run.cleared.add(i)
      else if (color !== 'g') target = signal.d
      break
    }
    const gap = Math.max(0, target - run.d)
    const limit = Math.min(SPEED, Math.sqrt(2 * DECEL * gap))
    run.v = limit < run.v ? limit : Math.min(limit, run.v + ACCEL * dt)
    run.d = Math.min(target, run.d + run.v * dt)
    const arrived = target - run.d < 0.02
    if (arrived && target === tl.total) Object.assign(run, { phase: 'delivered', timer: END, v: 0 })
    else if (arrived && target === stopD && !run.passedStop) Object.assign(run, { phase: 'stop', timer: STOP, v: 0, passedStop: true })
    else {
      run.phase = moving()
      run.waiting = run.v < 0.5 && gap < 3
    }
  }
  return { ...poseAt(tl, run.d), phase: run.phase, waiting: run.waiting }
}

function poseAt(tl, d) {
  let i = 0
  while (i < tl.lengths.length - 1 && d > tl.cum[i + 1]) i++
  const frac = tl.lengths[i] ? (d - tl.cum[i]) / tl.lengths[i] : 0
  const a = tl.points[i]
  const b = tl.points[i + 1]
  // Un tramo de largo cero (parqueo en el camino) conserva el rumbo del tramo anterior.
  let j = i
  while (j > 0 && tl.lengths[j] < 1e-6) j--
  const [ha, hb] = [tl.points[j], tl.points[j + 1]]
  const left = tl.costs.slice(i + 1).reduce((s, c) => s + c, tl.costs[i] * (1 - frac))
  const remainingKm = d >= tl.total - 0.01 ? 0 : Math.max(0, left)
  return {
    position: new THREE.Vector3().lerpVectors(a, b, frac),
    heading: Math.atan2(hb.x - ha.x, hb.z - ha.z) - Math.PI / 2, // el frente del camión es +x
    segment: i,
    distance: d,
    remainingKm,
  }
}

// ---------- Cuadrilla: carga en A y entrega en la parada y en B ----------

const clamp01 = (x) => THREE.MathUtils.clamp(x, 0, 1)

function walkTo(person, from, to, u, time) {
  person.visible = true
  person.position.lerpVectors(from, to, u).setY(0.25)
  if (from.distanceToSquared(to) > 1e-4) person.rotation.y = Math.atan2(to.x - from.x, to.z - from.z)
  const swing = u > 0 && u < 1 ? Math.sin(time * 9) * 0.6 : 0
  const { legs, arms } = person.userData.limbs
  legs[0].rotation.x = swing
  legs[1].rotation.x = -swing
  arms[0].rotation.x = -swing
  arms[1].rotation.x = swing
}

function hold(person, box, carrying) {
  box.visible = carrying
  if (!carrying) return
  const a = person.rotation.y
  box.position.copy(person.position).add(new THREE.Vector3(Math.sin(a) * 0.45, 1.15, Math.cos(a) * 0.45))
  box.rotation.y = a
  for (const arm of person.userData.limbs.arms) arm.rotation.x = -1.2 // brazos al frente, sosteniendo la caja
}

// Entrega: [desde, hasta, ¿con caja?] por tramos de tiempo (s) desde que el camión se detiene.
const DELIVERY = [
  [0, 0.9, 'cab', 'rear', false], // se baja de la cabina y va atrás
  [0.9, 1.3, 'rear', 'rear', true], // saca la caja
  [1.3, 3.4, 'rear', 'door', true], // la lleva a la puerta
  [3.4, 3.8, 'door', 'door', false], // la deja
  [3.8, 5.6, 'door', 'cab', false], // vuelve a la cabina
]

export function animateCrew(crew, run, truck, time) {
  if (!crew) return
  // Carga: los operarios llevan una caja del muelle al camión y luego vuelven.
  crew.loaders.forEach((w, i) => {
    if (run.phase === 'loading') {
      const u = clamp01((LOAD - run.timer - i * 0.5) / (LOAD - 1))
      walkTo(w.person, w.dock, w.rear, u, time)
      hold(w.person, w.box, u < 1)
    } else if (run.age < LOAD + 3.5) {
      walkTo(w.person, w.rear, w.dock, clamp01((run.age - LOAD) / 3), time)
      hold(w.person, w.box, false)
    } else {
      w.person.visible = w.box.visible = false
    }
  })

  const forward = new THREE.Vector3(Math.cos(truck.rotation.y), 0, -Math.sin(truck.rotation.y))
  for (const c of crew.deliveries) {
    const active = c.final ? run.phase === 'delivered' : run.phase === 'stop'
    const e = active ? (c.final ? END : STOP) - run.timer : -1
    c.dropped.visible = c.final ? active && e > 3.6 : run.passedStop && (run.phase !== 'stop' || e > 3.6)
    if (!active || e > 5.6) {
      c.person.visible = c.box.visible = false
      continue
    }
    // El repartidor se baja por el lado de la casa.
    const side = rightOf(forward)
    if (side.dot(new THREE.Vector3().subVectors(c.door, truck.position)) < 0) side.negate()
    const spots = {
      cab: truck.position.clone().addScaledVector(forward, 1.2).addScaledVector(side, 1.4),
      rear: truck.position.clone().addScaledVector(forward, -2.5).addScaledVector(side, 0.8),
      door: c.door,
    }
    const [start, stop, from, to, carrying] = DELIVERY.find(([, end]) => e < end) ?? DELIVERY.at(-1)
    walkTo(c.person, spots[from], spots[to], stop > start ? clamp01((e - start) / (stop - start)) : 1, time)
    hold(c.person, c.box, carrying)
  }
}

// Coloca el camión girando suavemente hacia el rumbo nuevo.
export function placeTruck(truck, state, dt) {
  // Luces del camión encendidas de 6 p. m. a 6 a. m. (lo decide la escena según la hora).
  const lights = truck.userData.lights
  const on = !!truck.parent?.userData.lightsOn
  if (lights && lights.on !== on) {
    lights.on = on
    lights.spot.visible = lights.beam.visible = on
    for (const m of lights.heads) m.material.emissiveIntensity = on ? 2.5 : 0.15
    for (const m of lights.tails) m.material.emissiveIntensity = on ? 1.6 : 0.25
  }
  truck.position.copy(state.position)
  let diff = state.heading - truck.rotation.y
  diff = Math.atan2(Math.sin(diff), Math.cos(diff))
  truck.rotation.y += diff * Math.min(1, dt * 10)
}

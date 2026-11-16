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
const WALK = 2.2 // ancho de la acera
const CROSS = 6 // ancho que ocupa el cruce de una calle
const LOT = 7 // fondo de un lote
// Recorrido del camión: unidades por segundo y pausas en A, en la parada y en B.
const SPEED = 10
const LOAD = 2
const STOP = 2.2
const END = 2.5

const WALLS = [0xffffff, 0xfdf6e3, 0xfde2cf, 0xe0ecff, 0xe5e7eb, 0xf5e1c8, 0xe8f5e9]
const ROOFS = [0xb45309, 0x64748b, 0xd9603b, 0x8b5a3c, 0x9ca3af] // sin azul: el techo azul es del cliente
const GREENS = [0x7fd49a, 0x6cc58a, 0x94dca8]
const SHIRTS = [0xef4444, 0x2563eb, 0xf59e0b, 0x10b981, 0x8b5cf6, 0xec4899, 0x0ea5e9]

export function createStage(container) {
  const scene = new THREE.Scene()
  scene.background = new THREE.Color(0xeef2f8)
  scene.fog = new THREE.Fog(0xeef2f8, 170, 380)
  const camera = new THREE.PerspectiveCamera(40, 1, 0.5, 900)
  camera.position.set(55, 85, 115)
  const renderer = new THREE.WebGLRenderer({ antialias: true })
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
  renderer.shadowMap.enabled = true
  renderer.shadowMap.type = THREE.PCFSoftShadowMap
  container.appendChild(renderer.domElement)

  const controls = new OrbitControls(camera, renderer.domElement)
  controls.enableDamping = true
  controls.maxPolarAngle = Math.PI / 2.3
  controls.minDistance = 8
  controls.maxDistance = 260

  scene.add(new THREE.HemisphereLight(0xffffff, 0xb8c4dc, 1.8))
  const sun = new THREE.DirectionalLight(0xffffff, 1.5)
  sun.position.set(40, 90, 30)
  sun.castShadow = true
  Object.assign(sun.shadow.camera, { left: -120, right: 120, top: 120, bottom: -120, far: 320 })
  sun.shadow.mapSize.set(2048, 2048)
  sun.shadow.bias = -0.0005
  scene.add(sun)

  const ground = new THREE.Mesh(new THREE.PlaneGeometry(900, 900), new THREE.MeshStandardMaterial({ color: 0xeef1f6 }))
  ground.rotation.x = -Math.PI / 2
  ground.receiveShadow = true
  scene.add(ground)

  const resize = () => {
    const { clientWidth: w, clientHeight: h } = container
    if (!w || !h) return
    renderer.setSize(w, h)
    camera.aspect = w / h
    camera.updateProjectionMatrix()
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
      const loop = () => {
        frame = requestAnimationFrame(loop)
        const dt = Math.min(clock.getDelta(), 0.1)
        tick(clock.elapsedTime, dt)
        controls.update()
        renderer.render(scene, camera)
      }
      loop()
    },
    dispose() {
      cancelAnimationFrame(frame)
      observer.disconnect()
      controls.dispose()
      disposeObject(scene)
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

// Las piezas repetidas (cajas, conos, esferas...) se dibujan en pocas InstancedMesh.
function makeBatcher() {
  const items = new Map()
  const geometries = {
    box: () => new THREE.BoxGeometry(1, 1, 1),
    roof: () => new THREE.ConeGeometry(Math.SQRT1_2, 1, 4).rotateY(Math.PI / 4),
    sphere: () => new THREE.SphereGeometry(0.5, 12, 9),
    cyl: () => new THREE.CylinderGeometry(0.5, 0.5, 1, 10),
    tri: () => new THREE.CylinderGeometry(0.5, 0.5, 1, 3),
  }
  const add = (kind, color, x, y, z, sx, sy, sz, ry = 0, shadow = true) => {
    const key = `${kind}:${shadow}`
    if (!items.has(key)) items.set(key, [])
    items.get(key).push([color, x, y, z, sx, sy, sz, ry])
  }
  // Marco local de un lote: +z mira hacia `front`, +x a lo ancho.
  const frame = (origin, front) => {
    const r = new THREE.Vector3(front.z, 0, -front.x)
    const ry = Math.atan2(front.x, front.z)
    return (kind, color, lx, y, lz, sx, sy, sz, shadow = true) =>
      add(kind, color, origin.x + r.x * lx + front.x * lz, y, origin.z + r.z * lx + front.z * lz, sx, sy, sz, ry, shadow)
  }
  const build = (group) => {
    const m = new THREE.Matrix4()
    const q = new THREE.Quaternion()
    const up = new THREE.Vector3(0, 1, 0)
    const p = new THREE.Vector3()
    const s = new THREE.Vector3()
    const c = new THREE.Color()
    for (const [key, list] of items) {
      const [kind, shadow] = key.split(':')
      const mesh = new THREE.InstancedMesh(geometries[kind](), new THREE.MeshStandardMaterial({ roughness: 0.8 }), list.length)
      list.forEach(([color, x, y, z, sx, sy, sz, ry], i) => {
        mesh.setMatrixAt(i, m.compose(p.set(x, y, z), q.setFromAxisAngle(up, ry), s.set(sx, sy, sz)))
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
function sharedStreet(nameA, nameB) {
  const a = nameA.split(/\s+con\s+/i)
  const b = nameB.split(/\s+con\s+/i)
  return a.find((part) => b.includes(part)) ?? null
}

function crossNumber(cornerName, street) {
  const other = cornerName.split(/\s+con\s+/i).find((part) => part !== street)
  return other?.match(/\d+/)?.[0] ?? null
}

function label(text, { color = '#0f172a', bg = 'rgba(255,255,255,0.95)', size = 26 } = {}) {
  const canvas = document.createElement('canvas')
  const ctx = canvas.getContext('2d')
  const font = `700 ${size}px Plus Jakarta Sans, system-ui, sans-serif`
  ctx.font = font
  canvas.width = Math.ceil(ctx.measureText(text).width) + 24
  canvas.height = size + 18
  ctx.font = font
  ctx.fillStyle = bg
  ctx.beginPath()
  ctx.roundRect(0, 0, canvas.width, canvas.height, 10)
  ctx.fill()
  ctx.fillStyle = color
  ctx.textBaseline = 'middle'
  ctx.fillText(text, 12, canvas.height / 2 + 1)
  const texture = new THREE.CanvasTexture(canvas)
  texture.colorSpace = THREE.SRGBColorSpace
  const sprite = new THREE.Sprite(new THREE.SpriteMaterial({ map: texture, depthTest: false }))
  sprite.scale.set(canvas.width / 48, canvas.height / 48, 1)
  sprite.renderOrder = 10
  return sprite
}

// Señal reglamentaria de sentido único: rectángulo negro, flecha y "UNA VÍA" en blanco.
function oneWayTexture(pointsRight) {
  const canvas = document.createElement('canvas')
  canvas.width = 256
  canvas.height = 96
  const ctx = canvas.getContext('2d')
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
  const texture = new THREE.CanvasTexture(canvas)
  texture.colorSpace = THREE.SRGBColorSpace
  return texture
}

// ---------- Edificaciones (marco local: el frente mira a +z, hacia la calle) ----------

function house(L, wall, roof) {
  L('box', wall, 0, 1.5, 0, 5, 3, 5)
  L('roof', roof, 0, 3.9, 0, 5.8, 1.8, 5.8)
  L('box', 0x7c4a2d, 0, 0.9, 2.52, 1, 1.8, 0.1, false)
  L('box', 0x9cc3f0, -1.6, 1.8, 2.52, 0.9, 0.8, 0.1, false)
  L('box', 0x9cc3f0, 1.6, 1.8, 2.52, 0.9, 0.8, 0.1, false)
}

function townhouse(L, wall) {
  L('box', wall, 0, 2.8, 0, 5.4, 5.6, 5.4)
  L('box', 0xcbd5e1, 0, 5.72, 0, 5.6, 0.25, 5.6)
  for (const y of [1.6, 4.2]) {
    for (const x of [-1.5, 1.5]) L('box', 0x9cc3f0, x, y, 2.72, 1, 1, 0.1, false)
  }
  L('box', 0x334155, 0, 0.9, 2.72, 0.9, 1.8, 0.1, false)
}

function apartment(L, rand) {
  const floors = 3 + Math.floor(rand() * 2)
  const h = floors * 2.6
  L('box', [0xf1f5f9, 0xe2e8f0, 0xdbeafe, 0xfef3c7][Math.floor(rand() * 4)], 0, h / 2, 0, 5.8, h, 5.8)
  for (let f = 0; f < floors; f++) L('box', 0x93c5fd, 0, 1.5 + f * 2.6, 2.93, 4.8, 0.9, 0.08, false)
  L('box', 0x94a3b8, 1.3, h + 0.5, -1.2, 1.6, 1, 1.6)
  L('box', 0x475569, 0, 0.1 + h, 0, 5.9, 0.2, 5.9, false)
}

function shop(L, rand) {
  L('box', WALLS[Math.floor(rand() * WALLS.length)], 0, 1.8, 0, 5.8, 3.6, 5)
  L('box', 0xbfdbfe, 0, 1.2, 2.52, 4.6, 1.6, 0.08, false)
  L('box', [0xef4444, 0x2563eb, 0x10b981, 0xf59e0b][Math.floor(rand() * 4)], 0, 2.6, 3.05, 5.8, 0.22, 1.2)
  L('box', 0x1e293b, 0, 3.25, 2.56, 3, 0.55, 0.1, false)
}

function tree(L, lx, lz, rand, s = 1) {
  L('cyl', 0x8b6b4a, lx, 0.8 * s, lz, 0.35 * s, 1.6 * s, 0.35 * s)
  L('sphere', GREENS[Math.floor(rand() * GREENS.length)], lx, 2.6 * s, lz, 2.8 * s, 3.2 * s, 2.8 * s)
}

function park(L, rand) {
  L('box', 0x9ee6b0, 0, 0.1, 0, 6.4, 0.2, LOT - 0.2, false)
  L('box', 0xe7dcc8, 0, 0.22, 0, 1.2, 0.04, LOT - 0.2, false)
  tree(L, -2, -1.8, rand)
  tree(L, 2.2, 0.6, rand, 0.8)
  tree(L, -1.9, 2, rand, 0.7)
  L('box', 0x8b5e3c, 1.9, 0.55, -2.2, 1.6, 0.18, 0.6)
}

function warehouseMesh() {
  const g = new THREE.Group()
  const part = (w, h, d, color, x, y, z) => {
    const mesh = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), new THREE.MeshStandardMaterial({ color, roughness: 0.65 }))
    mesh.position.set(x, y, z)
    mesh.castShadow = mesh.receiveShadow = true
    g.add(mesh)
  }
  part(16, 0.2, 14, 0xd6dbe4, 0, 0.1, -1) // patio de maniobras
  part(13, 5.5, 9, 0xffffff, 0, 2.75, 1.5)
  part(13.4, 0.5, 9.4, 0xdbe3f0, 0, 5.75, 1.5)
  // Puertas de muelle azules hacia la calle (-z local).
  for (const x of [-4, 0, 4]) part(2.6, 3.2, 0.2, BLUE, x, 1.6, -3.05)
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
  const tag = label(text, { color: '#ffffff', bg: `#${color.toString(16).padStart(6, '0')}`, size: 30 })
  tag.position.y = 2.6
  g.add(tag)
  g.scale.setScalar(0.75)
  return g
}

function pedestrian(rand) {
  const g = new THREE.Group()
  const mat = (color) => new THREE.MeshStandardMaterial({ color, roughness: 0.8 })
  const legs = new THREE.Mesh(new THREE.BoxGeometry(0.45, 0.8, 0.3), mat(0x1e293b))
  legs.position.y = 0.4
  const body = new THREE.Mesh(new THREE.CylinderGeometry(0.3, 0.32, 0.8, 10), mat(SHIRTS[Math.floor(rand() * SHIRTS.length)]))
  body.position.y = 1.2
  const head = new THREE.Mesh(new THREE.SphereGeometry(0.24, 12, 9), mat([0xf1c27d, 0xc68642, 0x8d5524, 0xe0ac69][Math.floor(rand() * 4)]))
  head.position.y = 1.85
  for (const m of [legs, body, head]) m.castShadow = true
  g.add(legs, body, head)
  return g
}

// Semáforo en la esquina, mirando hacia `facing` (los carros que llegan al cruce).
function trafficLight(position, facing, phase, lamps, mats) {
  const g = new THREE.Group()
  const pole = new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.12, 4.2, 8), new THREE.MeshStandardMaterial({ color: 0x334155 }))
  pole.position.y = 2.1
  const housing = new THREE.Mesh(new THREE.BoxGeometry(0.7, 1.9, 0.5), new THREE.MeshStandardMaterial({ color: 0x1f2937 }))
  housing.position.y = 4.5
  pole.castShadow = housing.castShadow = true
  g.add(pole, housing)
  ;['r', 'y', 'g'].forEach((color, i) => {
    const lamp = new THREE.Mesh(new THREE.SphereGeometry(0.2, 10, 8), mats.off)
    lamp.position.set(0, 5.1 - i * 0.6, 0.27)
    lamp.userData = { color, phase }
    lamps.push(lamp)
    g.add(lamp)
  })
  g.position.copy(position)
  g.rotation.y = Math.atan2(facing.x, facing.z)
  return g
}

// ---------- Ciudad ----------

export function createCity(network, route) {
  const group = new THREE.Group()
  const anim = { pulses: [], bobs: [], lamps: [], walkers: [] }
  group.userData = anim
  const B = makeBatcher()
  const rand = seeded(7)
  const pos = positions(network)
  const byId = new Map(network.map((p) => [p.id, p]))
  const isAddress = (id) => byId.get(id)?.type === 'pickup_point'
  const found = route?.found && route.path.length > 0

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
  const degree = new Map()
  for (const s of streets) {
    degree.set(s.from, (degree.get(s.from) ?? 0) + 1)
    degree.set(s.to, (degree.get(s.to) ?? 0) + 1)
  }

  // Dirección de cada cliente: la calle más cercana entre las que tocan a su cruce;
  // el camión se parquea en esa calle, frente a la casa.
  const addresses = new Map()
  for (const point of network.filter((p) => p.type === 'pickup_point')) {
    const p = pos.get(point.id)
    const near = streets.filter((s) => neighbors.get(point.id).has(s.from) || neighbors.get(point.id).has(s.to))
    const candidates = near.length ? near : streets
    if (!candidates.length) continue
    const s = candidates.reduce((best, c) => (segmentDistance(p, c.a, c.b) < segmentDistance(p, best.a, best.b) ? c : best))
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
    sites.set(point.id, { site: p.clone().addScaledVector(away, 12), front: away.clone().negate() })
  }

  // ---- Calles, aceras, cebras, marcas y señales ----
  const signMats = [true, false].map((right) => new THREE.MeshStandardMaterial({ map: oneWayTexture(right) }))
  for (const s of streets) {
    const mid = new THREE.Vector3().addVectors(s.a, s.b).multiplyScalar(0.5)
    const L = B.frame(mid, s.dir)
    L('box', ASPHALT, 0, 0.05, 0, s.width, 0.1, s.len + CROSS, false)
    for (const side of [-1, 1]) L('box', SIDEWALK, side * (s.width / 2 + WALK / 2), 0.15, 0, WALK, 0.3, Math.max(0, s.len - CROSS), false)

    if (s.twoWay) {
      // Doble sentido: línea central amarilla discontinua.
      for (let z = -s.len / 2 + 5; z < s.len / 2 - 5; z += 3.2) L('box', 0xfacc15, 0, 0.11, z + 0.8, 0.22, 0.03, 1.6, false)
    } else {
      // Sentido único: flechas blancas pintadas y la señal "UNA VÍA" al inicio.
      for (const z of [-s.len / 4, s.len / 4]) {
        L('box', WHITE, 0, 0.11, z - 0.6, 0.35, 0.03, 1.8, false)
        L('tri', WHITE, 0, 0.11, z + 0.6, 1.3, 0.03, 1.3, false)
      }
      const base = s.a.clone().addScaledVector(s.dir, CROSS / 2 + 1.5).addScaledVector(rightOf(s.dir), s.width / 2 + WALK / 2)
      const sign = new THREE.Group()
      const pole = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.08, 3.2, 8), new THREE.MeshStandardMaterial({ color: 0x94a3b8 }))
      pole.position.y = 1.6
      pole.castShadow = true
      sign.add(pole)
      for (const [mat, turn] of [[signMats[0], 0], [signMats[1], Math.PI]]) {
        const plate = new THREE.Mesh(new THREE.PlaneGeometry(2.4, 0.9), mat)
        plate.position.y = 3.1
        plate.rotation.y = turn
        plate.position.z = turn ? -0.02 : 0.02
        sign.add(plate)
      }
      sign.position.copy(base)
      sign.rotation.y = Math.atan2(-s.dir.z, s.dir.x) // la flecha (+x de la placa) apunta en el sentido de la calle
      group.add(sign)
    }

    // Cebras en los extremos que llegan a un cruce.
    for (const [node, end] of [[s.from, -1], [s.to, 1]]) {
      if ((degree.get(node) ?? 0) < 3) continue
      const z = end * (s.len / 2 - CROSS / 2 - 1.4)
      for (let x = -s.width / 2 + 0.6; x < s.width / 2 - 0.3; x += 1) L('box', WHITE, x, 0.11, z, 0.5, 0.03, 2.2, false)
    }

    // Nombre de la calle y costo de la conexión.
    const tag = label(`${s.name ? `${s.name} · ` : ''}${s.cost} km${s.twoWay ? ' ⇄' : ''}`, { size: 22, color: '#334155' })
    tag.position.copy(mid).addScaledVector(rightOf(s.dir), s.width / 2 + WALK / 2).setY(1.6)
    group.add(tag)

    // Peatones caminando por la acera (ida y vuelta).
    for (const side of [-1, 1]) {
      if (rand() < 0.35 || s.len < 16) continue
      const offset = rightOf(s.dir).multiplyScalar(side * (s.width / 2 + WALK / 2))
      const walker = pedestrian(rand)
      walker.userData = {
        from: s.a.clone().addScaledVector(s.dir, CROSS / 2 + 1).add(offset),
        to: s.b.clone().addScaledVector(s.dir, -(CROSS / 2 + 1)).add(offset),
        speed: 1.2 + rand() * 0.8,
        phase: rand() * 100,
      }
      anim.walkers.push(walker)
      group.add(walker)
    }
  }

  // ---- Semáforos en los cruces de tres o más calles ----
  const lampMats = {
    off: new THREE.MeshStandardMaterial({ color: 0x374151 }),
    r: new THREE.MeshBasicMaterial({ color: 0xff3b30 }),
    y: new THREE.MeshBasicMaterial({ color: 0xffcc00 }),
    g: new THREE.MeshBasicMaterial({ color: 0x22c55e }),
  }
  anim.lampMats = lampMats
  for (const point of network) {
    if ((degree.get(point.id) ?? 0) < 3 || point.type !== 'neighborhood') continue
    const p = pos.get(point.id)
    const incident = streets.filter((s) => s.from === point.id || s.to === point.id).slice(0, 2)
    incident.forEach((s, i) => {
      const out = s.from === point.id ? s.dir.clone() : s.dir.clone().negate()
      const spot = p.clone().addScaledVector(out, CROSS / 2 + 1.2).addScaledVector(rightOf(out), -(s.width / 2 + 0.7))
      group.add(trafficLight(spot, out, i % 2, anim.lamps, lampMats))
    })
  }

  // ---- Clientes, bodegas y cruces con nombre propio ----
  const occupied = [] // [centro, radio] de lo ya construido
  for (const point of network) {
    const address = addresses.get(point.id)
    const yard = sites.get(point.id)
    if (address) {
      house(B.frame(address.site, address.front), WHITE, BLUE)
      occupied.push([address.site, 3.6])
      const tag = label(address.text ? `${point.name} · ${address.text}` : point.name, { size: 24 })
      tag.position.copy(address.site).setY(6.2)
      group.add(tag)
      const cost = [...edges.values()].find((e) => (e.from === point.id || e.to === point.id))?.cost
      if (cost) {
        const parkTag = label(`${cost} km`, { size: 20, color: '#475569' })
        parkTag.position.copy(address.park).setY(1.2)
        group.add(parkTag)
      }
    } else if (yard) {
      const w = warehouseMesh()
      w.position.copy(yard.site)
      w.rotation.y = Math.atan2(yard.front.x, yard.front.z) + Math.PI
      group.add(w)
      occupied.push([yard.site, 8], [yard.site.clone().addScaledVector(yard.front, -6), 8])
      const tag = label(point.name, { size: 26 })
      tag.position.copy(yard.site).setY(8.2)
      group.add(tag)
    } else if (point.type === 'pickup_point') {
      // Cliente sin calles en la red: la casa queda sola en su posición.
      house(B.frame(pos.get(point.id), new THREE.Vector3(0, 0, 1)), WHITE, BLUE)
      occupied.push([pos.get(point.id), 3.6])
      const tag = label(point.name, { size: 24 })
      tag.position.copy(pos.get(point.id)).setY(6.2)
      group.add(tag)
    } else if (!/\s+con\s+/i.test(point.name)) {
      const tag = label(point.name, { size: 18, bg: 'rgba(255,255,255,0.8)' })
      tag.position.copy(pos.get(point.id)).setY(2)
      group.add(tag)
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
        if (roll < 0.4) house(L, WALLS[Math.floor(rand() * WALLS.length)], ROOFS[Math.floor(rand() * ROOFS.length)])
        else if (roll < 0.6) townhouse(L, WALLS[Math.floor(rand() * WALLS.length)])
        else if (roll < 0.75) apartment(L, rand)
        else if (roll < 0.88) shop(L, rand)
        else park(L, rand)
      }
      // Árboles en la acera, entre lotes.
      for (let along = CROSS + 4; along < s.len - CROSS - 2; along += 9) {
        if (rand() < 0.4) continue
        const spot = s.a.clone().addScaledVector(s.dir, along).addScaledVector(n, s.width / 2 + WALK - 0.4)
        if (occupied.some(([o, r]) => o.distanceTo(spot) < r + 0.8)) continue
        tree(B.frame(spot, new THREE.Vector3(0, 0, 1)), 0, 0, rand, 0.7)
      }
    }
  }

  B.build(group)

  // ---- Ruta del camión: por su carril, parqueando frente a la casa del cliente ----
  let tl = null
  if (found && route.path.length > 1) {
    const anchor = (id) => addresses.get(id)?.park ?? pos.get(id)
    const raw = route.path.map((p) => anchor(p.id).clone())
    const lanes = raw.slice(1).map((b, i) => {
      const a = raw[i]
      const e = edgeOf(route.path[i].id, route.path[i + 1].id)
      const offset = e?.twoWay && !isAddress(route.path[i].id) && !isAddress(route.path[i + 1].id) ? 1.5 : 0
      return rightOf(new THREE.Vector3().subVectors(b, a).normalize()).multiplyScalar(offset)
    })
    const points = raw.map((p, i) => {
      const before = lanes[i - 1] ?? lanes[i]
      const after = lanes[i] ?? lanes[i - 1]
      return p.clone().add(before.clone().add(after).multiplyScalar(0.5)).setY(0.1)
    })
    tl = timeline(route, points)

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
      marker.position.copy(markerAt(id)).setY(sites.has(id) ? 12 : 10)
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

  return {
    group,
    timeline: tl,
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
    cycle: LOAD + total / SPEED + (stopIndex > 0 ? STOP : 0) + END,
  }
}

export function animateCity(group, time) {
  const { pulses = [], bobs = [], lamps = [], walkers = [], lampMats } = group.userData
  for (const o of pulses) o.scale.setScalar(1 + Math.sin(time * 4) * 0.12)
  for (const o of bobs) o.position.y = o.userData.baseY + Math.sin(time * 3) * 0.3
  // Ciclo de 10 s: verde 4, amarillo 1, rojo 5; la fase 1 va desfasada medio ciclo.
  for (const lamp of lamps) {
    const t = (time + lamp.userData.phase * 5) % 10
    const active = t < 4 ? 'g' : t < 5 ? 'y' : 'r'
    lamp.material = lamp.userData.color === active ? lampMats[active] : lampMats.off
  }
  for (const w of walkers) {
    const { from, to, speed, phase } = w.userData
    const len = from.distanceTo(to)
    const d = ((time + phase) * speed) % (2 * len)
    const forward = d < len
    w.position.lerpVectors(from, to, forward ? d / len : 2 - d / len)
    w.position.y = 0.3 + Math.abs(Math.sin(time * speed * 5)) * 0.06
    w.rotation.y = Math.atan2(to.x - from.x, to.z - from.z) + (forward ? 0 : Math.PI)
  }
}

export function makeTruck() {
  const g = new THREE.Group()
  const part = (w, h, d, color, x, y, z) => {
    const mesh = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), new THREE.MeshStandardMaterial({ color, roughness: 0.6 }))
    mesh.position.set(x, y, z)
    mesh.castShadow = true
    g.add(mesh)
  }
  part(5.4, 0.4, 2.1, 0x1f2937, 0.3, 0.6, 0) // chasis
  part(4.2, 2.6, 2.4, 0xffffff, -0.5, 2.1, 0) // caja de carga
  part(4.22, 0.4, 2.42, 0x14b8a6, -0.5, 1.3, 0) // franja WareTrack
  part(1.8, 2.1, 2.3, 0xffffff, 2.5, 1.85, 0) // cabina
  part(0.08, 0.9, 2, 0x1e293b, 3.42, 2.3, 0) // parabrisas
  const wheelGeo = new THREE.CylinderGeometry(0.5, 0.5, 0.4, 18)
  const wheelMat = new THREE.MeshStandardMaterial({ color: 0x111827 })
  for (const x of [-1.8, -0.6, 2.4]) {
    for (const z of [1.05, -1.05]) {
      const wheel = new THREE.Mesh(wheelGeo, wheelMat)
      wheel.rotation.x = Math.PI / 2
      wheel.position.set(x, 0.5, z)
      wheel.castShadow = true
      g.add(wheel)
    }
  }
  g.scale.setScalar(0.75)
  return g
}

// Estado del camión en el instante `time` del ciclo: posición, rumbo, fase y km restantes.
export function truckState(tl, time) {
  let t = time % tl.cycle
  let d
  let phase
  const stopD = tl.stopIndex > 0 ? tl.cum[tl.stopIndex] : -1
  const firstLeg = (stopD >= 0 ? stopD : tl.total) / SPEED
  if (t < LOAD) {
    d = 0
    phase = 'loading'
  } else if ((t -= LOAD) < firstLeg) {
    d = t * SPEED
    phase = stopD >= 0 ? 'toStop' : 'toDest'
  } else if (stopD >= 0 && t < firstLeg + STOP) {
    d = stopD
    phase = 'stop'
  } else {
    d = stopD >= 0 ? stopD + (t - firstLeg - STOP) * SPEED : tl.total
    phase = 'toDest'
  }
  if (d >= tl.total) {
    d = tl.total
    phase = 'delivered'
  }
  let i = 0
  while (i < tl.lengths.length - 1 && d > tl.cum[i + 1]) i++
  const frac = tl.lengths[i] ? (d - tl.cum[i]) / tl.lengths[i] : 0
  const a = tl.points[i]
  const b = tl.points[i + 1]
  const remainingKm = tl.costs.slice(i + 1).reduce((s, c) => s + c, tl.costs[i] * (1 - frac))
  return {
    position: new THREE.Vector3().lerpVectors(a, b, frac),
    heading: Math.atan2(b.x - a.x, b.z - a.z) - Math.PI / 2, // el frente del camión es +x
    phase,
    segment: i,
    distance: d,
    remainingKm,
  }
}

// Coloca el camión girando suavemente hacia el rumbo nuevo.
export function placeTruck(truck, state, dt) {
  truck.position.copy(state.position)
  let diff = state.heading - truck.rotation.y
  diff = Math.atan2(Math.sin(diff), Math.cos(diff))
  truck.rotation.y += diff * Math.min(1, dt * 10)
}

// Escena 3D de WareTrack compartida por el mapa del panel (T13) y la página de
// seguimiento. Solo dibuja datos del backend: posiciones x, y de GET /network y
// la ruta ya calculada por GET /shortest-path (con parada `via`, CAMBIO-REQUISITO-F4).
import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'

export const SCALE = 24
const BLUE = 0x2563eb
const ORANGE = 0xf97316
const ROAD = 0xd5ddeb
// Recorrido del camión: unidades por segundo y pausas en A, en la parada y en B.
const SPEED = 9
const LOAD = 2
const STOP = 2.2
const END = 2.5

export function createStage(container) {
  const scene = new THREE.Scene()
  scene.background = new THREE.Color(0xeef2f8)
  scene.fog = new THREE.Fog(0xeef2f8, 160, 340)
  const camera = new THREE.PerspectiveCamera(40, 1, 0.5, 900)
  camera.position.set(45, 70, 95)
  const renderer = new THREE.WebGLRenderer({ antialias: true })
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
  renderer.shadowMap.enabled = true
  renderer.shadowMap.type = THREE.PCFSoftShadowMap
  container.appendChild(renderer.domElement)

  const controls = new OrbitControls(camera, renderer.domElement)
  controls.enableDamping = true
  controls.maxPolarAngle = Math.PI / 2.3
  controls.minDistance = 8
  controls.maxDistance = 240

  scene.add(new THREE.HemisphereLight(0xffffff, 0xb8c4dc, 1.8))
  const sun = new THREE.DirectionalLight(0xffffff, 1.5)
  sun.position.set(40, 90, 30)
  sun.castShadow = true
  Object.assign(sun.shadow.camera, { left: -110, right: 110, top: 110, bottom: -110, far: 300 })
  sun.shadow.mapSize.set(2048, 2048)
  sun.shadow.bias = -0.0005
  scene.add(sun)

  const ground = new THREE.Mesh(new THREE.PlaneGeometry(900, 900), new THREE.MeshStandardMaterial({ color: 0xf4f6fb }))
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
  })
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

function box(w, h, d, color, x = 0, y = 0, z = 0) {
  const mesh = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), new THREE.MeshStandardMaterial({ color, roughness: 0.65 }))
  mesh.position.set(x, y, z)
  mesh.castShadow = mesh.receiveShadow = true
  return mesh
}

function warehouse() {
  const g = new THREE.Group()
  g.add(box(12, 5, 9, 0xffffff, 0, 2.5, 0), box(12.4, 0.5, 9.4, 0xdbe3f0, 0, 5.25, 0))
  // Puertas de muelle azules hacia la calle (-z local).
  for (const x of [-3.6, 0, 3.6]) g.add(box(2.4, 3, 0.2, BLUE, x, 1.5, -4.55))
  return g
}

function house() {
  const g = new THREE.Group()
  g.add(box(4, 3, 4, 0xffffff, 0, 1.5, 0))
  const roof = new THREE.Mesh(new THREE.ConeGeometry(3.4, 2, 4), new THREE.MeshStandardMaterial({ color: 0x93b4f5 }))
  roof.rotation.y = Math.PI / 4
  roof.position.y = 4
  roof.castShadow = true
  g.add(roof)
  return g
}

function tree(x, z) {
  const g = new THREE.Group()
  g.add(box(0.4, 1.6, 0.4, 0x9a7b5a, 0, 0.8, 0))
  const crown = new THREE.Mesh(new THREE.SphereGeometry(1.4, 14, 10), new THREE.MeshStandardMaterial({ color: 0x7fd49a, roughness: 0.9 }))
  crown.position.y = 2.6
  crown.scale.y = 1.2
  crown.castShadow = true
  g.add(crown)
  g.position.set(x, 0, z)
  return g
}

function pin(color, text) {
  const g = new THREE.Group()
  const mat = new THREE.MeshStandardMaterial({ color, roughness: 0.4 })
  const head = new THREE.Mesh(new THREE.SphereGeometry(1.1, 20, 14), mat)
  const tip = new THREE.Mesh(new THREE.ConeGeometry(0.95, 1.8, 20), mat)
  tip.rotation.x = Math.PI
  tip.position.y = -1.1
  const dot = new THREE.Mesh(new THREE.SphereGeometry(0.45, 12, 8), new THREE.MeshBasicMaterial({ color: 0xffffff }))
  dot.position.z = 0.75
  g.add(head, tip, dot)
  const tag = label(text, { color: '#ffffff', bg: `#${color.toString(16).padStart(6, '0')}`, size: 24 })
  tag.position.y = 2.4
  g.add(tag)
  g.userData.bob = true
  g.scale.setScalar(0.65)
  return g
}

function road(a, b, oneWay, cost, onRoute) {
  const g = new THREE.Group()
  const dir = new THREE.Vector3().subVectors(b, a)
  const length = dir.length()
  const mid = new THREE.Vector3().addVectors(a, b).multiplyScalar(0.5)
  const angle = Math.atan2(dir.x, dir.z)
  const width = oneWay ? 3 : 4.6
  const strip = (w, h, len, color, y, basic = false) => {
    const material = basic
      ? new THREE.MeshBasicMaterial({ color, transparent: true, opacity: 0.9 })
      : new THREE.MeshStandardMaterial({ color })
    const mesh = new THREE.Mesh(new THREE.BoxGeometry(w, h, len), material)
    mesh.position.copy(mid).setY(y)
    mesh.rotation.y = angle
    mesh.receiveShadow = true
    return mesh
  }
  g.add(strip(width, 0.1, length + width, ROAD, 0.05))

  if (oneWay) {
    // Sentido único: flechas azules en la dirección de la conexión.
    const mat = new THREE.MeshBasicMaterial({ color: BLUE })
    for (let t = 0.25; t < 0.8; t += 0.25) {
      const arrow = new THREE.Mesh(new THREE.ConeGeometry(0.7, 1.4, 3), mat)
      arrow.position.lerpVectors(a, b, t).setY(0.14)
      arrow.rotation.order = 'YXZ'
      arrow.rotation.set(Math.PI / 2, angle, 0)
      arrow.scale.z = 0.15 // flecha plana pintada sobre la calle
      g.add(arrow)
    }
  } else {
    // Doble sentido: línea central discontinua.
    const n = Math.max(1, Math.floor(length / 3.5))
    for (let i = 0; i < n; i++) {
      const dash = new THREE.Mesh(new THREE.BoxGeometry(0.22, 0.04, 1.4), new THREE.MeshBasicMaterial({ color: 0xffffff }))
      dash.position.lerpVectors(a, b, (i + 0.5) / n).setY(0.12)
      dash.rotation.y = angle
      g.add(dash)
    }
  }
  if (onRoute) g.add(strip(1.3, 0.06, length, BLUE, 0.16, true))

  const tag = label(`${cost} km${oneWay ? '' : ' ⇄'}`, {
    color: onRoute ? '#ffffff' : '#475569',
    bg: onRoute ? '#2563eb' : 'rgba(255,255,255,0.9)',
    size: 20,
  })
  tag.position.copy(mid).setY(1.4)
  g.add(tag)
  return g
}

function timeline(route, pos) {
  const points = route.path.map((p) => pos.get(p.id).clone())
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

export function createCity(network, route) {
  const group = new THREE.Group()
  const pos = positions(network)
  const found = route?.found && route.path.length > 0
  const routeEdges = new Set((found ? route.connections : []).map((c) => `${c.origin_id}>${c.destination_id}`))

  // Una sola calle por par de puntos; si existe la inversa es de doble sentido.
  const edges = new Map()
  const neighbors = new Map(network.map((p) => [p.id, []]))
  for (const point of network) {
    for (const c of point.connections) {
      neighbors.get(point.id).push(c.destination_id)
      neighbors.get(c.destination_id)?.push(point.id)
      const key = [point.id, c.destination_id].sort().join('|')
      const entry = edges.get(key)
      if (entry) entry.twoWay = true
      else edges.set(key, { from: point.id, to: c.destination_id, cost: c.cost_km, twoWay: false })
    }
  }
  for (const e of edges.values()) {
    const onRoute = routeEdges.has(`${e.from}>${e.to}`) || routeEdges.has(`${e.to}>${e.from}`)
    group.add(road(pos.get(e.from), pos.get(e.to), !e.twoWay, e.cost, onRoute))
  }

  // Árboles a los lados de cada calle, lejos de los puntos.
  const nodes = [...pos.values()]
  for (const e of edges.values()) {
    const a = pos.get(e.from)
    const b = pos.get(e.to)
    const side = new THREE.Vector3(b.z - a.z, 0, a.x - b.x).normalize().multiplyScalar(5)
    for (const [t, s] of [[0.3, 1], [0.7, -1]]) {
      const p = new THREE.Vector3().lerpVectors(a, b, t).addScaledVector(side, s)
      if (nodes.every((n) => n.distanceTo(p) > 6)) group.add(tree(p.x, p.z))
    }
  }

  const role = (id) => {
    if (!found) return null
    if (id === route.path[0].id) return ['A', BLUE]
    if (id === route.path.at(-1).id) return ['B', BLUE]
    if (id === route.via_id) return ['Parada', ORANGE]
    return null
  }

  for (const point of network) {
    const p = pos.get(point.id)
    let site = p.clone()
    if (point.type !== 'neighborhood') {
      // El edificio se aparta de las calles que llegan al punto, con un acceso.
      const away = new THREE.Vector3()
      for (const n of neighbors.get(point.id)) away.add(new THREE.Vector3().subVectors(p, pos.get(n)).normalize())
      const offset = point.type === 'warehouse' ? 9 : 3
      if (away.lengthSq() > 0) site = p.clone().addScaledVector(away.normalize(), offset)
      const b = point.type === 'warehouse' ? warehouse() : house()
      b.position.copy(site)
      b.lookAt(p.x, 0, p.z)
      b.rotateY(Math.PI) // las puertas (-z) miran hacia la calle
      group.add(b)
      if (site.distanceTo(p) > 0.1) {
        const drive = new THREE.Mesh(new THREE.BoxGeometry(2.4, 0.08, site.distanceTo(p)), new THREE.MeshStandardMaterial({ color: ROAD }))
        drive.position.lerpVectors(p, site, 0.5).setY(0.04)
        drive.rotation.y = Math.atan2(site.x - p.x, site.z - p.z)
        drive.receiveShadow = true
        group.add(drive)
      }
    }
    const isCorner = point.type === 'neighborhood'
    const tag = label(point.name, { size: isCorner ? 18 : 24, bg: isCorner ? 'rgba(255,255,255,0.75)' : 'rgba(255,255,255,0.95)' })
    tag.position.copy(site).setY(point.type === 'warehouse' ? 7.5 : isCorner ? 2 : 5.8)
    group.add(tag)

    const r = role(point.id)
    if (r) {
      const marker = pin(r[1], r[0])
      marker.position.copy(site).setY(point.type === 'warehouse' ? 11 : 9)
      group.add(marker)
    }
  }

  if (found && route.via_id && pos.has(route.via_id)) {
    const ring = new THREE.Mesh(new THREE.TorusGeometry(3.4, 0.22, 12, 48), new THREE.MeshBasicMaterial({ color: ORANGE }))
    ring.rotation.x = Math.PI / 2
    ring.position.copy(pos.get(route.via_id)).setY(0.3)
    ring.userData.pulse = true
    group.add(ring)
  }

  return { group, timeline: found && route.path.length > 1 ? timeline(route, pos) : null }
}

export function animateCity(group, time) {
  for (const o of group.children) {
    if (o.userData.pulse) o.scale.setScalar(1 + Math.sin(time * 4) * 0.12)
    if (o.userData.bob) o.position.y += Math.sin(time * 3) * 0.01
  }
}

export function makeTruck() {
  const g = new THREE.Group()
  g.add(
    box(5.4, 0.4, 2.1, 0x1f2937, 0.3, 0.6, 0), // chasis
    box(4.2, 2.6, 2.4, 0xffffff, -0.5, 2.1, 0), // caja de carga
    box(4.22, 0.4, 2.42, 0x14b8a6, -0.5, 1.3, 0), // franja WareTrack
    box(1.8, 2.1, 2.3, 0xffffff, 2.5, 1.85, 0), // cabina
    box(0.08, 0.9, 2, 0x1e293b, 3.42, 2.3, 0), // parabrisas
  )
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
  g.scale.setScalar(0.8)
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

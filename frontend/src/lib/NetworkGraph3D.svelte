<script>
  // T13 (Mariana): la red de GET /network en 3D, como una ciudad de WareTrack.
  // Solo dibuja datos del backend: posiciones x, y (T11), conexiones y la ruta
  // ya calculada por GET /shortest-path (con parada `via`, CAMBIO-REQUISITO-F4).
  import * as THREE from 'three'
  import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'
  import { onMount } from 'svelte'

  let { network, route = null } = $props()

  let container
  let scene, camera, renderer, controls, world, truck
  let frame = 0
  let truckPath = null // { points: Vector3[], stopIndex, lengths, total }

  const SCALE = 14
  const COLORS = { warehouse: 0xf59e0b, neighborhood: 0x6366f1, pickup_point: 0x10b981 }

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
      const r = SCALE * 2.5
      map.set(p.id, new THREE.Vector3(Math.cos(a) * r, 0, Math.sin(a) * r))
    })
    return map
  }

  function label(text, color = '#0f172a', bg = 'rgba(255,255,255,0.92)', size = 30) {
    const canvas = document.createElement('canvas')
    const ctx = canvas.getContext('2d')
    ctx.font = `700 ${size}px Plus Jakarta Sans, sans-serif`
    const w = Math.ceil(ctx.measureText(text).width) + 24
    canvas.width = w
    canvas.height = size + 18
    ctx.font = `700 ${size}px Plus Jakarta Sans, sans-serif`
    ctx.fillStyle = bg
    ctx.beginPath()
    ctx.roundRect(0, 0, w, canvas.height, 10)
    ctx.fill()
    ctx.fillStyle = color
    ctx.textBaseline = 'middle'
    ctx.fillText(text, 12, canvas.height / 2 + 1)
    const texture = new THREE.CanvasTexture(canvas)
    texture.colorSpace = THREE.SRGBColorSpace
    const sprite = new THREE.Sprite(new THREE.SpriteMaterial({ map: texture, depthTest: false }))
    sprite.scale.set(w / 40, canvas.height / 40, 1)
    sprite.renderOrder = 10
    return sprite
  }

  function building(point) {
    const color = COLORS[point.type] ?? 0x94a3b8
    const group = new THREE.Group()
    const mat = new THREE.MeshStandardMaterial({ color, roughness: 0.55 })
    if (point.type === 'warehouse') {
      const body = new THREE.Mesh(new THREE.BoxGeometry(5, 3, 4), mat)
      body.position.y = 1.5
      const roof = new THREE.Mesh(
        new THREE.CylinderGeometry(2, 2, 5, 3, 1, false),
        new THREE.MeshStandardMaterial({ color: 0x92580a }),
      )
      roof.rotation.z = Math.PI / 2
      roof.position.y = 3.6
      group.add(body, roof)
    } else if (point.type === 'pickup_point') {
      const body = new THREE.Mesh(new THREE.BoxGeometry(2.4, 2, 2.4), mat)
      body.position.y = 1
      const roof = new THREE.Mesh(new THREE.ConeGeometry(2, 1.4, 4), new THREE.MeshStandardMaterial({ color: 0x0a7253 }))
      roof.rotation.y = Math.PI / 4
      roof.position.y = 2.7
      group.add(body, roof)
    } else {
      const disc = new THREE.Mesh(new THREE.CylinderGeometry(1, 1, 0.3, 24), mat)
      disc.position.y = 0.15
      group.add(disc)
    }
    group.traverse((o) => (o.castShadow = o.receiveShadow = true))
    return group
  }

  function makeTruck() {
    const group = new THREE.Group()
    const cargo = new THREE.Mesh(new THREE.BoxGeometry(2.6, 1.6, 1.4), new THREE.MeshStandardMaterial({ color: 0xffffff }))
    cargo.position.set(-0.4, 1.2, 0)
    const cab = new THREE.Mesh(new THREE.BoxGeometry(1, 1.2, 1.4), new THREE.MeshStandardMaterial({ color: 0x5b4cf0 }))
    cab.position.set(1.4, 1, 0)
    group.add(cargo, cab)
    const wheelGeo = new THREE.CylinderGeometry(0.35, 0.35, 0.3, 16)
    const wheelMat = new THREE.MeshStandardMaterial({ color: 0x111827 })
    for (const [x, z] of [[-1.2, 0.7], [-1.2, -0.7], [1.3, 0.7], [1.3, -0.7]]) {
      const wheel = new THREE.Mesh(wheelGeo, wheelMat)
      wheel.rotation.x = Math.PI / 2
      wheel.position.set(x, 0.35, z)
      group.add(wheel)
    }
    group.traverse((o) => (o.castShadow = true))
    return group
  }

  function road(a, b, oneWay, cost, onRoute) {
    const group = new THREE.Group()
    const dir = new THREE.Vector3().subVectors(b, a)
    const length = dir.length()
    const mid = new THREE.Vector3().addVectors(a, b).multiplyScalar(0.5)
    const angle = Math.atan2(dir.x, dir.z)

    const asphalt = new THREE.Mesh(
      new THREE.BoxGeometry(oneWay ? 1.4 : 2.2, 0.08, length),
      new THREE.MeshStandardMaterial({ color: oneWay ? 0x475569 : 0x334155 }),
    )
    asphalt.position.copy(mid).setY(0.04)
    asphalt.rotation.y = angle
    asphalt.receiveShadow = true
    group.add(asphalt)

    // Sentido único: flechas en la dirección de la conexión. Doble sentido: línea central.
    if (oneWay) {
      const arrowMat = new THREE.MeshStandardMaterial({ color: 0xfbbf24, emissive: 0x7c4a03 })
      for (const t of [0.35, 0.65]) {
        const cone = new THREE.Mesh(new THREE.ConeGeometry(0.45, 1, 3), arrowMat)
        cone.position.lerpVectors(a, b, t).setY(0.3)
        cone.rotation.set(Math.PI / 2, 0, 0)
        cone.rotation.order = 'YXZ'
        cone.rotation.y = angle
        group.add(cone)
      }
    } else {
      const line = new THREE.Mesh(new THREE.BoxGeometry(0.12, 0.1, length * 0.8), new THREE.MeshBasicMaterial({ color: 0xffffff }))
      line.position.copy(mid).setY(0.06)
      line.rotation.y = angle
      group.add(line)
    }

    if (onRoute) {
      const glow = new THREE.Mesh(
        new THREE.BoxGeometry(0.6, 0.12, length),
        new THREE.MeshBasicMaterial({ color: 0x8b5cf6, transparent: true, opacity: 0.85 }),
      )
      glow.position.copy(mid).setY(0.14)
      glow.rotation.y = angle
      group.add(glow)
    }

    const tag = label(`${cost} km${oneWay ? '' : ' ⇄'}`, onRoute ? '#ffffff' : '#334155', onRoute ? '#5b4cf0' : 'rgba(255,255,255,0.9)', 26)
    tag.position.copy(mid).setY(1.6)
    group.add(tag)
    return group
  }

  function build() {
    if (!scene) return
    if (world) {
      scene.remove(world)
      world.traverse((o) => {
        o.geometry?.dispose()
        o.material?.map?.dispose()
        o.material?.dispose()
      })
    }
    world = new THREE.Group()
    scene.add(world)
    truckPath = null
    if (truck) truck.visible = false
    if (!network.length) return

    const pos = positions(network)
    const routeEdges = new Set((route?.found ? route.connections : []).map((c) => `${c.origin_id}>${c.destination_id}`))

    // Una sola calle por par de puntos; si existe la inversa es de doble sentido.
    const edges = new Map()
    for (const point of network) {
      for (const c of point.connections) {
        const key = [point.id, c.destination_id].sort().join('|')
        const entry = edges.get(key)
        if (entry) entry.twoWay = true
        else edges.set(key, { from: point.id, to: c.destination_id, cost: c.cost_km, twoWay: false })
      }
    }
    for (const e of edges.values()) {
      const onRoute = routeEdges.has(`${e.from}>${e.to}`) || routeEdges.has(`${e.to}>${e.from}`)
      world.add(road(pos.get(e.from), pos.get(e.to), !e.twoWay, e.cost, onRoute))
    }

    const routeIds = new Set((route?.path ?? []).map((p) => p.id))
    for (const point of network) {
      const b = building(point)
      b.position.copy(pos.get(point.id))
      world.add(b)
      let role = ''
      if (route?.found) {
        if (point.id === route.path[0].id) role = 'A · '
        else if (point.id === route.path.at(-1).id) role = 'B · '
        else if (point.id === route.via_id) role = 'Parada · '
      }
      const tag = label(role + point.name, role ? '#ffffff' : '#0f172a', role ? '#0a0f1e' : 'rgba(255,255,255,0.92)', point.type === 'neighborhood' && !role ? 22 : 28)
      tag.position.copy(pos.get(point.id)).setY(point.type === 'warehouse' ? 6 : point.type === 'pickup_point' ? 4.6 : 2.2)
      if (point.type === 'neighborhood' && !routeIds.has(point.id)) tag.material.opacity = 0.75
      world.add(tag)
    }

    // Marcador de parada obligatoria: un anillo pulsante sobre el punto `via`.
    if (route?.found && route.via_id && pos.has(route.via_id)) {
      const ring = new THREE.Mesh(new THREE.TorusGeometry(2.4, 0.18, 12, 48), new THREE.MeshBasicMaterial({ color: 0xf43f5e }))
      ring.rotation.x = Math.PI / 2
      ring.position.copy(pos.get(route.via_id)).setY(0.3)
      ring.userData.pulse = true
      world.add(ring)
    }

    if (route?.found && route.path.length > 1) {
      const points = route.path.map((p) => pos.get(p.id).clone().setY(0.1))
      const lengths = points.slice(1).map((p, i) => p.distanceTo(points[i]))
      // La parada puede repetirse en path; se usa su primera aparición después del origen.
      const stopIndex = route.via_id ? route.path.findIndex((p, i) => i > 0 && p.id === route.via_id) : -1
      truckPath = { points, lengths, total: lengths.reduce((s, l) => s + l, 0), stopIndex }
      truck.visible = true
    }
  }

  // Avance del camión: 9 unidades/s, pausa de 1.2 s en la parada y 1.5 s en B.
  const SPEED = 9
  const STOP = 1.2
  const END = 1.5
  function placeTruck(time) {
    const { points, lengths, total, stopIndex } = truckPath
    const stopAt = stopIndex > 0 ? lengths.slice(0, stopIndex).reduce((s, l) => s + l, 0) : -1
    const cycle = total / SPEED + (stopAt >= 0 ? STOP : 0) + END
    let t = time % cycle
    let d
    if (stopAt >= 0 && t > stopAt / SPEED) d = t < stopAt / SPEED + STOP ? stopAt : (t - STOP) * SPEED
    else d = t * SPEED
    d = Math.min(d, total)
    let i = 0
    while (i < lengths.length - 1 && d > lengths[i]) d -= lengths[i++]
    const a = points[i]
    const b = points[i + 1]
    truck.position.lerpVectors(a, b, lengths[i] ? d / lengths[i] : 0)
    truck.rotation.y = Math.atan2(b.x - a.x, b.z - a.z) - Math.PI / 2
  }

  onMount(() => {
    scene = new THREE.Scene()
    scene.background = new THREE.Color(0xe8ecf5)
    scene.fog = new THREE.Fog(0xe8ecf5, 90, 180)
    camera = new THREE.PerspectiveCamera(45, 1, 0.1, 500)
    camera.position.set(20, 30, 34)
    renderer = new THREE.WebGLRenderer({ antialias: true })
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
    renderer.shadowMap.enabled = true
    container.appendChild(renderer.domElement)

    controls = new OrbitControls(camera, renderer.domElement)
    controls.enableDamping = true
    controls.maxPolarAngle = Math.PI / 2.2

    scene.add(new THREE.HemisphereLight(0xffffff, 0x8090b0, 1.6))
    const sun = new THREE.DirectionalLight(0xffffff, 1.8)
    sun.position.set(30, 50, 20)
    sun.castShadow = true
    Object.assign(sun.shadow.camera, { left: -60, right: 60, top: 60, bottom: -60 })
    sun.shadow.mapSize.set(2048, 2048)
    scene.add(sun)

    const ground = new THREE.Mesh(new THREE.PlaneGeometry(300, 300), new THREE.MeshStandardMaterial({ color: 0xd9e2d0 }))
    ground.rotation.x = -Math.PI / 2
    ground.receiveShadow = true
    scene.add(ground)
    scene.add(new THREE.GridHelper(300, 60, 0xc6d0bd, 0xc6d0bd))

    truck = makeTruck()
    truck.visible = false
    scene.add(truck)
    build()

    const resize = () => {
      const { clientWidth: w, clientHeight: h } = container
      renderer.setSize(w, h)
      camera.aspect = w / h
      camera.updateProjectionMatrix()
    }
    const observer = new ResizeObserver(resize)
    observer.observe(container)
    resize()

    const clock = new THREE.Clock()
    const loop = () => {
      frame = requestAnimationFrame(loop)
      const time = clock.getElapsedTime()
      if (truckPath) placeTruck(time)
      world?.children.forEach((o) => o.userData.pulse && o.scale.setScalar(1 + Math.sin(time * 4) * 0.12))
      controls.update()
      renderer.render(scene, camera)
    }
    loop()

    return () => {
      cancelAnimationFrame(frame)
      observer.disconnect()
      controls.dispose()
      renderer.dispose()
      renderer.domElement.remove()
    }
  })

  $effect(() => {
    // Se redibuja cuando cambia la red o la ruta.
    network
    route
    build()
  })
</script>

<section>
  <h2>Mapa 3D de la ciudad</h2>
  {#if network.length === 0}
    <p class="empty">La red está vacía. Crea puntos y conexiones para ver la ciudad en 3D.</p>
  {/if}
  <div class="stage" class:hidden={network.length === 0} bind:this={container}></div>
  {#if network.length > 0}
    <ul class="legend">
      <li><span class="sw warehouse"></span>Bodega</li>
      <li><span class="sw neighborhood"></span>Cruce / barrio</li>
      <li><span class="sw pickup"></span>Punto de entrega</li>
      <li><span class="sw oneway"></span>Sentido único (flechas)</li>
      <li><span class="sw twoway"></span>Doble sentido (⇄)</li>
      <li><span class="sw route"></span>Ruta del camión</li>
      <li><span class="sw via"></span>Parada obligatoria</li>
    </ul>
    <p class="hint">
      {#if route?.found && route.path.length > 1}
        El camión recorre la ruta A → B{route.via_id ? ' deteniéndose en la parada' : ''}: {route.total_cost_km} km.
      {:else}
        Calcula una ruta para ver el camión recorrerla. Arrastra para girar y usa la rueda para acercar.
      {/if}
    </p>
  {/if}
</section>

<style>
  .stage {
    height: 520px;
    border-radius: 14px;
    overflow: hidden;
    border: 1px solid var(--border);
    cursor: grab;
  }
  .stage.hidden {
    display: none;
  }
  .empty {
    margin: 0;
    padding: 18px;
    border-radius: 12px;
    border: 1.5px dashed var(--border-strong);
    background: var(--surface-2);
    color: var(--muted);
    text-align: center;
  }
  .legend {
    display: flex;
    flex-wrap: wrap;
    gap: 8px 18px;
    margin: 14px 0 0;
    padding: 0;
    list-style: none;
    font-size: 0.85rem;
    color: var(--muted);
  }
  .legend li {
    display: flex;
    align-items: center;
    gap: 6px;
  }
  .sw {
    width: 14px;
    height: 14px;
    border-radius: 4px;
  }
  .sw.warehouse { background: var(--warehouse); }
  .sw.neighborhood { background: var(--neighborhood); }
  .sw.pickup { background: var(--pickup); }
  .sw.oneway { background: #fbbf24; }
  .sw.twoway { background: #334155; }
  .sw.route { background: #8b5cf6; }
  .sw.via { background: #f43f5e; border-radius: 50%; }
  .hint {
    margin: 8px 0 0;
    font-size: 0.88rem;
    color: var(--muted);
  }
  @media (max-width: 700px) {
    .stage { height: 380px; }
  }
</style>

<script setup>
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { computed, nextTick, onMounted, onUnmounted, ref } from 'vue'

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8104/ws/couriers'
const TRACKING_PRODUCER_API_URL =
  import.meta.env.VITE_TRACKING_PRODUCER_API_URL || 'http://localhost:8000'
const SPB_CENTER = [59.9386, 30.3141]
const COURIER_NAMES = [
  'Артём Курьеров',
  'Максим Быстров',
  'Илья Самокатин',
  'Даниил Петров',
  'Егор Лисицын',
  'Никита Волков',
  'Алексей Морозов',
  'Кирилл Соколов',
  'Роман Орлов',
  'Сергей Крылов',
  'Антон Смирнов',
  'Михаил Федоров',
  'Павел Новиков',
  'Денис Васильев',
  'Владимир Кузнецов',
  'Андрей Беляев',
  'Тимур Громов',
  'Руслан Егоров',
  'Станислав Миронов',
  'Георгий Захаров',
]

const couriers = ref({})
const selectedCourierId = ref(null)
const connectionStatus = ref('connecting')
const connectionError = ref('')
const simulationStatus = ref('')
const simulationRunning = ref(false)

let socket = null
let reconnectTimer = null
let map = null
let markersLayer = null
let routesLayer = null
const markers = new Map()
const routes = new Map()

const couriersList = computed(() => {
  return Object.values(couriers.value).sort((a, b) => a.courier_id.localeCompare(b.courier_id))
})

const selectedCourier = computed(() => {
  if (!selectedCourierId.value) return couriersList.value[0] || null
  return couriers.value[selectedCourierId.value] || couriersList.value[0] || null
})

const connectionLabel = computed(() => {
  if (connectionStatus.value === 'connected') return 'WebSocket подключен'
  if (connectionStatus.value === 'reconnecting') return 'Переподключение'
  if (connectionStatus.value === 'closed') return 'Отключено'
  return 'Подключение'
})

function statusLabel(status) {
  const labels = {
    courier_searching: 'Ищем курьера',
    courier_found: 'Курьер найден',
    courier_arrived_to_darkstore: 'Курьер у даркстора',
    delivering: 'В пути',
    completed: 'Доставлен',
  }
  return labels[status] || status || 'нет статуса'
}

function statusColor(status) {
  if (status === 'delivering') return '#06b87d'
  if (status === 'courier_arrived_to_darkstore') return '#f59e0b'
  if (status === 'courier_found') return '#38bdf8'
  if (status === 'completed') return '#a3e635'
  return '#c084fc'
}

function courierNumber(courierId) {
  const match = String(courierId).match(/(\d+)$/)
  return match ? Number(match[1]) : 0
}

function courierLabel(courierId) {
  const number = courierNumber(courierId)
  const name = COURIER_NAMES[(number - 1) % COURIER_NAMES.length] || 'Курьер'
  return number ? `${number}. ${name}` : name
}

function formatTime(value) {
  if (!value) return 'нет данных'
  return new Intl.DateTimeFormat('ru-RU', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  }).format(new Date(value))
}

function normalizePoint(item) {
  const lat = Number(item.lat)
  const lon = Number(item.lon)
  if (!Number.isFinite(lat) || !Number.isFinite(lon)) return null
  return { lat, lon }
}

function initMap() {
  map = L.map('couriers-map', {
    zoomControl: false,
  }).setView(SPB_CENTER, 11)

  L.control.zoom({ position: 'bottomright' }).addTo(map)
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; OpenStreetMap',
  }).addTo(map)

  routesLayer = L.layerGroup().addTo(map)
  markersLayer = L.layerGroup().addTo(map)
}

function upsertCourier(item) {
  const point = normalizePoint(item)
  if (!point) return

  const previous = couriers.value[item.courier_id]
  const trail = [...(previous?.trail || []), [point.lat, point.lon]].slice(-12)
  const nextCourier = {
    ...previous,
    ...item,
    lat: point.lat,
    lon: point.lon,
    trail,
    seen_at: new Date().toISOString(),
  }

  couriers.value = {
    ...couriers.value,
    [item.courier_id]: nextCourier,
  }

  if (!selectedCourierId.value) {
    selectedCourierId.value = item.courier_id
  }

  drawCourier(nextCourier)
}

function drawCourier(courier) {
  const latlng = [courier.lat, courier.lon]
  const color = statusColor(courier.status)
  const tooltip = `${courierLabel(courier.courier_id)} | ${statusLabel(courier.status)}`

  let marker = markers.get(courier.courier_id)
  if (!marker) {
    marker = L.circleMarker(latlng, {
      radius: 8,
      color: '#111827',
      weight: 2,
      fillColor: color,
      fillOpacity: 0.95,
    })
      .addTo(markersLayer)
      .on('click', () => {
        selectedCourierId.value = courier.courier_id
      })
    markers.set(courier.courier_id, marker)
  }

  marker.setLatLng(latlng)
  marker.setStyle({ fillColor: color })
  marker.bindTooltip(tooltip, { direction: 'top', offset: [0, -8] })

  let route = routes.get(courier.courier_id)
  if (!route) {
    route = L.polyline(courier.trail, {
      color,
      weight: 3,
      opacity: 0.65,
    }).addTo(routesLayer)
    routes.set(courier.courier_id, route)
  }
  route.setLatLngs(courier.trail)
  route.setStyle({ color })
}

function handleMessage(rawMessage) {
  let message
  try {
    message = JSON.parse(rawMessage.data)
  } catch {
    return
  }
  if (
    message.type !== 'couriers_snapshot' ||
    !Array.isArray(message.items) ||
    message.items.length === 0
  ) {
    return
  }

  message.items.forEach(upsertCourier)
}

function clearMapState() {
  couriers.value = {}
  selectedCourierId.value = null

  markers.clear()
  routes.clear()
  markersLayer?.clearLayers()
  routesLayer?.clearLayers()
}

function connectWebSocket() {
  clearTimeout(reconnectTimer)
  connectionStatus.value = 'connecting'
  connectionError.value = ''
  socket = new WebSocket(WS_URL)

  socket.addEventListener('open', () => {
    connectionStatus.value = 'connected'
    connectionError.value = ''
  })

  socket.addEventListener('message', handleMessage)

  socket.addEventListener('error', () => {
    connectionError.value = 'Не удалось подключиться к Delivery Analytics API'
  })

  socket.addEventListener('close', () => {
    connectionStatus.value = 'reconnecting'
    reconnectTimer = setTimeout(connectWebSocket, 1500)
  })
}

async function startSimulation() {
  clearMapState()
  simulationRunning.value = true
  simulationStatus.value = 'Публикуем события в Kafka...'

  try {
    const response = await fetch(`${TRACKING_PRODUCER_API_URL}/delivery-tracking/simulate`, {
      method: 'POST',
    })

    if (!response.ok) {
      const error = await response.json().catch(() => null)
      throw new Error(error?.detail || 'Симуляция не запустилась')
    }

    simulationStatus.value = 'Симуляция завершена'
  } catch (error) {
    simulationStatus.value = error.message || 'Ошибка запуска симуляции'
  } finally {
    simulationRunning.value = false
  }
}

function focusCourier(courier) {
  selectedCourierId.value = courier.courier_id
  map?.flyTo([courier.lat, courier.lon], 14, { duration: 0.5 })
}

onMounted(async () => {
  await nextTick()
  initMap()
  connectWebSocket()
})

onUnmounted(() => {
  clearTimeout(reconnectTimer)
  socket?.close()
  map?.remove()
})
</script>

<template>
  <main class="dashboard">
    <section class="map-pane">
      <div id="couriers-map" class="map"></div>
    </section>

    <aside class="control-panel">
      <header class="panel-header">
        <div>
          <p class="eyebrow">Delivery Analytics</p>
          <h1>Курьеры на карте</h1>
        </div>
        <span class="status-pill" :class="connectionStatus">{{ connectionLabel }}</span>
      </header>

      <button class="primary-button" type="button" :disabled="simulationRunning" @click="startSimulation">
        {{ simulationRunning ? 'События идут...' : 'Запустить симуляцию' }}
      </button>

      <p v-if="simulationStatus" class="notice">{{ simulationStatus }}</p>
      <p v-if="connectionError" class="error">{{ connectionError }}</p>

      <section v-if="selectedCourier" class="selected">
        <p class="eyebrow">Выбранный курьер</p>
        <h2>{{ courierLabel(selectedCourier.courier_id) }}</h2>
        <dl>
          <div>
            <dt>Статус</dt>
            <dd>{{ statusLabel(selectedCourier.status) }}</dd>
          </div>
          <div>
            <dt>Заказ</dt>
            <dd>#{{ selectedCourier.order_id || selectedCourier.delivery_id }}</dd>
          </div>
          <div>
            <dt>Адрес</dt>
            <dd>{{ selectedCourier.destination_address || 'нет адреса' }}</dd>
          </div>
          <div>
            <dt>Координаты</dt>
            <dd>{{ selectedCourier.lat.toFixed(5) }}, {{ selectedCourier.lon.toFixed(5) }}</dd>
          </div>
        </dl>
      </section>

      <section class="courier-list">
        <button
          v-for="courier in couriersList"
          :key="courier.courier_id"
          class="courier-row"
          :class="{ active: courier.courier_id === selectedCourier?.courier_id }"
          type="button"
          @click="focusCourier(courier)"
        >
          <span class="dot" :style="{ backgroundColor: statusColor(courier.status) }"></span>
          <span>
            <strong>{{ courierLabel(courier.courier_id) }}</strong>
            <small>{{ statusLabel(courier.status) }} | {{ formatTime(courier.recorded_at) }}</small>
          </span>
        </button>
      </section>
    </aside>
  </main>
</template>

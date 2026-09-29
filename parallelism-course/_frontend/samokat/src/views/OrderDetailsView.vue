<script setup>
import { onMounted, onUnmounted, ref } from 'vue'
import { useRoute } from 'vue-router'

import StatusBlock from '../components/StatusBlock.vue'
import { getApiError } from '../services/api'
import { samokatApi } from '../services/samokatApi'
import { getStatusLabel } from '../services/statusLabels'

const route = useRoute()
const order = ref(null)
const loading = ref(true)
const error = ref('')
let pollingTimer = null

function stopPolling() {
  clearInterval(pollingTimer)
  pollingTimer = null
}

function isCompleted() {
  return order.value?.status === 'completed' || order.value?.delivery?.status === 'completed'
}

async function loadOrder() {
  try {
    order.value = await samokatApi.order(route.params.id)

    if (isCompleted()) {
      stopPolling()
    }
  } catch (err) {
    error.value = getApiError(err)
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await loadOrder()

  if (!isCompleted()) {
    pollingTimer = setInterval(loadOrder, 5000)
  }
})

onUnmounted(() => {
  stopPolling()
})
</script>

<template>
  <section>
    <StatusBlock :loading="loading" :error="error" />

    <div v-if="order" class="stack">
      <div class="page-heading">
        <h1>Заказ #{{ order.id }}</h1>
        <span>{{ getStatusLabel(order.status) }}</span>
      </div>

      <div class="summary">
        <p>{{ order.address_text }}</p>
        <p>Доставка: {{ getStatusLabel(order.delivery?.status) }}</p>
        <p class="price">Итого: {{ order.total_price }} ₽</p>
      </div>

      <div v-for="item in order.items" :key="item.product_id" class="row-card">
        <div>
          <h3>{{ item.product_title }}</h3>
          <p>{{ item.price }} ₽ x {{ item.quantity }}</p>
        </div>
        <strong>{{ item.total_price }} ₽</strong>
      </div>
    </div>
  </section>
</template>

<script setup>
import { onMounted, ref } from 'vue'

import StatusBlock from '../components/StatusBlock.vue'
import { getApiError } from '../services/api'
import { samokatApi } from '../services/samokatApi'
import { getStatusLabel } from '../services/statusLabels'

const orders = ref([])
const loading = ref(true)
const error = ref('')

onMounted(async () => {
  try {
    orders.value = await samokatApi.orders()
  } catch (err) {
    error.value = getApiError(err)
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <section>
    <div class="page-heading">
      <h1>Заказы</h1>
      <span>{{ orders.length }} шт.</span>
    </div>

    <StatusBlock :loading="loading" :error="error" :empty="!orders.length ? 'Заказов нет' : ''" />

    <div v-if="orders.length" class="stack">
      <RouterLink
        v-for="order in orders"
        :key="order.id"
        class="row-card link-card"
        :to="`/orders/${order.id}`"
      >
        <div>
          <h3>Заказ #{{ order.id }}</h3>
          <p>{{ order.address_text }}</p>
        </div>
        <div class="right">
          <strong>{{ order.total_price }} ₽</strong>
          <span>{{ getStatusLabel(order.status) }}</span>
        </div>
      </RouterLink>
    </div>
  </section>
</template>

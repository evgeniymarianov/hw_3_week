<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import StatusBlock from '../components/StatusBlock.vue'
import { getApiError } from '../services/api'
import { samokatApi } from '../services/samokatApi'

const router = useRouter()
const cart = ref(null)
const preview = ref(null)
const loading = ref(true)
const error = ref('')

async function loadCart() {
  error.value = ''
  loading.value = true

  try {
    cart.value = await samokatApi.cart()
    preview.value = null
  } catch (err) {
    error.value = getApiError(err)
  } finally {
    loading.value = false
  }
}

async function changeQuantity(item, delta) {
  const quantity = Math.max(0, item.quantity + delta)

  try {
    await samokatApi.changeQuantity(item.product_id, quantity)
    await loadCart()
  } catch (err) {
    error.value = getApiError(err)
  }
}

async function previewOrder() {
  try {
    preview.value = await samokatApi.previewOrder()
  } catch (err) {
    error.value = getApiError(err)
  }
}

async function createOrder() {
  try {
    const order = await samokatApi.createOrder(preview.value.darkstore_reservation_id)
    router.push(`/orders/${order.order_id}`)
  } catch (err) {
    error.value = getApiError(err)
  }
}

onMounted(loadCart)
</script>

<template>
  <section>
    <div class="page-heading">
      <h1>Корзина</h1>
      <span v-if="cart">{{ cart.products_price }} ₽</span>
    </div>

    <StatusBlock
      :loading="loading"
      :error="error"
      :empty="cart && !cart.items.length ? 'Корзина пустая' : ''"
    />

    <div v-if="cart?.items.length" class="stack">
      <div v-for="item in cart.items" :key="item.product_id" class="row-card">
        <div>
          <h3>{{ item.title }}</h3>
          <p>{{ item.price }} ₽ x {{ item.quantity }} = {{ item.total_price }} ₽</p>
        </div>

        <div class="counter">
          <button type="button" @click="changeQuantity(item, -1)">-</button>
          <span>{{ item.quantity }}</span>
          <button type="button" @click="changeQuantity(item, 1)">+</button>
        </div>
      </div>

      <div class="summary">
        <p>Товары: {{ cart.products_price }} ₽</p>
        <p v-if="preview">Доставка: {{ preview.delivery_price }} ₽</p>
        <p v-if="preview" class="price">Итого: {{ preview.total_price }} ₽</p>

        <button v-if="!preview" class="button" type="button" @click="previewOrder">
          Оформить
        </button>
        <button v-else class="button" type="button" @click="createOrder">
          Создать заказ
        </button>
      </div>
    </div>
  </section>
</template>

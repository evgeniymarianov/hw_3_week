<script setup>
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'

import ProductIcon from '../components/ProductIcon.vue'
import StatusBlock from '../components/StatusBlock.vue'
import { getApiError } from '../services/api'
import { samokatApi } from '../services/samokatApi'

const route = useRoute()
const product = ref(null)
const loading = ref(true)
const error = ref('')

async function addToCart() {
  try {
    await samokatApi.addToCart(product.value.id)
  } catch (err) {
    error.value = getApiError(err)
  }
}

onMounted(async () => {
  try {
    product.value = await samokatApi.product(route.params.id)
  } catch (err) {
    error.value = getApiError(err)
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <section>
    <StatusBlock :loading="loading" :error="error" />

    <div v-if="product" class="details-layout">
      <ProductIcon />

      <div>
        <h1>{{ product.title }}</h1>
        <p class="lead">{{ product.description || 'Описание пока не добавлено' }}</p>
        <p class="price">{{ product.price }} ₽</p>
        <button class="button" type="button" :disabled="!product.is_active" @click="addToCart">
          Добавить
        </button>
      </div>
    </div>
  </section>
</template>

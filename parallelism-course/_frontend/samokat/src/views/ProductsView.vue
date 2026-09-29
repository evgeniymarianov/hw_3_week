<script setup>
import { onMounted, ref } from 'vue'

import ProductCard from '../components/ProductCard.vue'
import StatusBlock from '../components/StatusBlock.vue'
import { getApiError } from '../services/api'
import { samokatApi } from '../services/samokatApi'

const categories = ref([])
const products = ref([])
const cartQuantities = ref({})
const activeCategory = ref(null)
const loading = ref(false)
const error = ref('')

function getProductQuantity(productId) {
  return cartQuantities.value[productId] || 0
}

async function loadProducts(categoryId = null) {
  activeCategory.value = categoryId
  error.value = ''
  loading.value = true

  try {
    products.value = await samokatApi.products(categoryId)
  } catch (err) {
    error.value = getApiError(err)
  } finally {
    loading.value = false
  }
}

async function addToCart(product) {
  try {
    await samokatApi.addToCart(product.id)
    cartQuantities.value = {
      ...cartQuantities.value,
      [product.id]: getProductQuantity(product.id) + 1,
    }
  } catch (err) {
    error.value = getApiError(err)
  }
}

async function changeCartQuantity(product, quantity) {
  const nextQuantity = Math.max(0, quantity)

  try {
    await samokatApi.changeQuantity(product.id, nextQuantity)

    const nextQuantities = { ...cartQuantities.value }

    if (nextQuantity > 0) {
      nextQuantities[product.id] = nextQuantity
    } else {
      delete nextQuantities[product.id]
    }

    cartQuantities.value = nextQuantities
  } catch (err) {
    error.value = getApiError(err)
  }
}

async function loadCartQuantities() {
  try {
    const cart = await samokatApi.cart()
    cartQuantities.value = Object.fromEntries(
      cart.items
        .filter((item) => item.quantity > 0)
        .map((item) => [item.product_id, item.quantity]),
    )
  } catch (err) {
    error.value = getApiError(err)
  }
}

onMounted(async () => {
  try {
    categories.value = await samokatApi.categories()
  } catch {
    categories.value = []
  }

  await Promise.all([loadProducts(), loadCartQuantities()])
})
</script>

<template>
  <section>
    <div class="page-heading">
      <h1>Все товары</h1>
      <span>{{ products.length }} шт.</span>
    </div>

    <div class="category-row">
      <button :class="{ active: activeCategory === null }" type="button" @click="loadProducts()">
        Все
      </button>
      <button
        v-for="category in categories"
        :key="category.id"
        :class="{ active: activeCategory === category.id }"
        type="button"
        @click="loadProducts(category.id)"
      >
        {{ category.title }}
      </button>
    </div>

    <StatusBlock :loading="loading" :error="error" :empty="!products.length ? 'Товаров нет' : ''" />

    <div v-if="!loading && products.length" class="product-grid">
      <ProductCard
        v-for="product in products"
        :key="product.id"
        :product="product"
        :quantity="getProductQuantity(product.id)"
        @add="addToCart"
        @change-quantity="changeCartQuantity"
      />
    </div>
  </section>
</template>

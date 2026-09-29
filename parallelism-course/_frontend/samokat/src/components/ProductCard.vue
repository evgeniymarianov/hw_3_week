<script setup>
import ProductIcon from './ProductIcon.vue'

defineProps({
  product: {
    type: Object,
    required: true,
  },
  quantity: {
    type: Number,
    default: 0,
  },
})

defineEmits(['add', 'changeQuantity'])
</script>

<template>
  <article class="product-card">
    <RouterLink class="product-link" :to="`/products/${product.id}`">
      <ProductIcon />
      <div>
        <h3>{{ product.title }}</h3>
      </div>
    </RouterLink>

    <div class="product-card-footer">
      <strong>{{ product.price }} ₽</strong>
      <div v-if="quantity > 0" class="counter product-counter">
        <button
          type="button"
          :disabled="!product.is_active"
          @click="$emit('changeQuantity', product, quantity - 1)"
        >
          -
        </button>
        <span>{{ quantity }}</span>
        <button
          type="button"
          :disabled="!product.is_active"
          @click="$emit('changeQuantity', product, quantity + 1)"
        >
          +
        </button>
      </div>
      <button
        v-else
        class="button"
        type="button"
        :disabled="!product.is_active"
        @click="$emit('add', product)"
      >
        Добавить
      </button>
    </div>
  </article>
</template>

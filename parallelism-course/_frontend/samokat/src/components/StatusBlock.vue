<script setup>
defineProps({
  loading: Boolean,
  error: String,
  empty: String,
})
</script>

<template>
  <p v-if="loading" class="muted">Загрузка...</p>
  <p v-else-if="error" class="error">{{ error }}</p>
  <p v-else-if="empty" class="muted">{{ empty }}</p>
</template>

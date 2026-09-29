<script setup>
import { onMounted, ref, watch } from 'vue'

import StatusBlock from '../components/StatusBlock.vue'
import { getApiError } from '../services/api'
import { samokatApi } from '../services/samokatApi'

const activeAddress = ref(null)
const query = ref('')
const suggestions = ref([])
const loading = ref(true)
const searching = ref(false)
const error = ref('')
let searchTimer = null

async function loadActiveAddress() {
  try {
    activeAddress.value = await samokatApi.activeAddress()
  } catch (err) {
    error.value = getApiError(err)
  } finally {
    loading.value = false
  }
}

async function searchAddress() {
  const searchQuery = query.value.trim()

  if (!searchQuery) {
    suggestions.value = []
    return
  }

  error.value = ''
  searching.value = true

  try {
    suggestions.value = await samokatApi.addressSuggestions(searchQuery)
  } catch (err) {
    error.value = getApiError(err)
  } finally {
    searching.value = false
  }
}

async function addAddress(suggestion) {
  try {
    await samokatApi.addAddress(suggestion.id)
    suggestions.value = []
    query.value = ''
    await loadActiveAddress()
  } catch (err) {
    error.value = getApiError(err)
  }
}

onMounted(loadActiveAddress)

watch(query, () => {
  clearTimeout(searchTimer)

  searchTimer = setTimeout(() => {
    searchAddress()
  }, 350)
})
</script>

<template>
  <section>
    <div class="page-heading">
      <h1>Адрес</h1>
    </div>

    <StatusBlock :loading="loading" :error="error" />

    <div class="summary">
      <p class="muted">Текущий адрес</p>
      <p>{{ activeAddress?.address_text || 'Адрес пока не выбран' }}</p>
    </div>

    <form class="form search-form" @submit.prevent="searchAddress">
      <label>
        Найти адрес
        <input v-model.trim="query" placeholder="Например, Москва, Тверская 1" />
      </label>
      <button class="button" type="submit" :disabled="searching">
        {{ searching ? 'Ищу...' : 'Найти' }}
      </button>
    </form>

    <div v-if="suggestions.length" class="stack">
      <button
        v-for="suggestion in suggestions"
        :key="suggestion.id"
        class="row-card address-button"
        type="button"
        @click="addAddress(suggestion)"
      >
        {{ suggestion.address_text }}
      </button>
    </div>
  </section>
</template>

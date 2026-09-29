<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

import { getApiError } from '../services/api'
import { auth } from '../services/auth'
import { samokatApi } from '../services/samokatApi'

const router = useRouter()
const mode = ref('login')
const username = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function submit() {
  error.value = ''
  loading.value = true

  try {
    const payload = { username: username.value, password: password.value }
    const isRegistering = mode.value === 'register'

    if (isRegistering) {
      await samokatApi.register(payload)
    }

    const tokens = await samokatApi.login(payload)
    auth.setTokens(tokens)
    auth.setUser(await samokatApi.me())
    router.push(isRegistering ? '/address' : '/products')
  } catch (err) {
    error.value = getApiError(err)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <section class="auth-page">
    <div class="auth-box">
      <h1>{{ mode === 'login' ? 'Войти' : 'Регистрация' }}</h1>

      <div class="tabs">
        <button :class="{ active: mode === 'login' }" type="button" @click="mode = 'login'">
          Вход
        </button>
        <button :class="{ active: mode === 'register' }" type="button" @click="mode = 'register'">
          Регистрация
        </button>
      </div>

      <form class="form" autocomplete="off" @submit.prevent="submit">
        <label>
          Логин
          <input v-model.trim="username" autocomplete="new-password" required />
        </label>

        <label>
          Пароль
          <input
            v-model="password"
            autocomplete="new-password"
            required
            type="password"
          />
        </label>

        <p v-if="error" class="error">{{ error }}</p>

        <button class="button" type="submit" :disabled="loading">
          {{ loading ? 'Подождите...' : mode === 'login' ? 'Войти' : 'Зарегистрироваться' }}
        </button>
      </form>
    </div>
  </section>
</template>

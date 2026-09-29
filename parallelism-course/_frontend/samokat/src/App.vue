<script setup>
import { ClipboardList, LogIn, LogOut, MapPin, ShoppingBasket, ShoppingCart } from '@lucide/vue'
import { useRoute, useRouter } from 'vue-router'

import { auth } from './services/auth'

const route = useRoute()
const router = useRouter()

const navItems = [
  {
    to: '/products',
    label: 'Каталог',
    icon: ShoppingBasket,
    isActive: (path) => path.startsWith('/products'),
  },
  {
    to: '/cart',
    label: 'Корзина',
    icon: ShoppingCart,
    isActive: (path) => path.startsWith('/cart'),
  },
  {
    to: '/orders',
    label: 'Заказы',
    icon: ClipboardList,
    isActive: (path) => path.startsWith('/orders'),
  },
  {
    to: '/address',
    label: 'Адреса',
    icon: MapPin,
    isActive: (path) => path.startsWith('/address'),
  },
]

function logout() {
  auth.clear()
  router.push('/login')
}

function isRouteActive(item) {
  return item.isActive(route.path)
}
</script>

<template>
  <div class="app-shell">
    <aside class="sidebar">
      <RouterLink class="brand" to="/products">Самокат</RouterLink>

      <nav class="nav">
        <RouterLink
          v-for="item in navItems"
          :key="item.to"
          class="nav-link"
          :class="{ active: isRouteActive(item) }"
          :to="item.to"
        >
          <component :is="item.icon" :size="18" :stroke-width="2" />
          <span>{{ item.label }}</span>
        </RouterLink>
      </nav>

      <div class="profile">
        <span v-if="auth.user">{{ auth.user.username }}</span>
        <RouterLink
          v-if="!auth.isLoggedIn()"
          class="nav-link profile-action"
          :class="{ active: route.path === '/login' }"
          to="/login"
        >
          <LogIn :size="18" :stroke-width="2" />
          <span>Войти</span>
        </RouterLink>
        <button v-else class="nav-link profile-action" type="button" @click="logout">
          <LogOut :size="18" :stroke-width="2" />
          <span>Выйти</span>
        </button>
      </div>
    </aside>

    <main class="content">
      <RouterView />
    </main>
  </div>
</template>

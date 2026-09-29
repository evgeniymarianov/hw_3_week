import { createRouter, createWebHistory } from 'vue-router'

import { auth } from './services/auth'
import AddressView from './views/AddressView.vue'
import AuthView from './views/AuthView.vue'
import CartView from './views/CartView.vue'
import OrderDetailsView from './views/OrderDetailsView.vue'
import OrdersView from './views/OrdersView.vue'
import ProductDetailsView from './views/ProductDetailsView.vue'
import ProductsView from './views/ProductsView.vue'

const routes = [
  { path: '/', redirect: '/products' },
  { path: '/login', component: AuthView },
  { path: '/products', component: ProductsView, meta: { requiresAuth: true } },
  { path: '/products/:id', component: ProductDetailsView },
  { path: '/cart', component: CartView, meta: { requiresAuth: true } },
  { path: '/orders', component: OrdersView, meta: { requiresAuth: true } },
  { path: '/orders/:id', component: OrderDetailsView, meta: { requiresAuth: true } },
  { path: '/address', component: AddressView, meta: { requiresAuth: true } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  if (to.meta.requiresAuth && !auth.isLoggedIn()) {
    return '/login'
  }
})

export default router

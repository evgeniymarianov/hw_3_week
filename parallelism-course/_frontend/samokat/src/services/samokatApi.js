import { apiFetch } from './api'

export const samokatApi = {
  register: (payload) => apiFetch('/auth/register', { method: 'POST', body: payload }),
  login: (payload) => apiFetch('/auth/login', { method: 'POST', body: payload }),
  me: () => apiFetch('/auth/users/me'),

  categories: () => apiFetch('/products/categories'),
  products: (categoryId) => {
    const query = categoryId ? `?category_id=${categoryId}` : ''
    return apiFetch(`/products/${query}`)
  },
  product: (id) => apiFetch(`/products/${id}`),

  cart: () => apiFetch('/cart/items'),
  addToCart: (productId, quantity = 1) =>
    apiFetch('/cart/', { method: 'POST', body: { product_id: productId, quantity } }),
  changeQuantity: (productId, quantity) =>
    apiFetch(`/cart/items/${productId}`, { method: 'POST', body: { quantity } }),

  activeAddress: () => apiFetch('/addresses/active'),
  addressSuggestions: (query) =>
    apiFetch(`/addresses/suggestions?query=${encodeURIComponent(query)}`),
  addAddress: (selectedAddressId) =>
    apiFetch('/addresses/', { method: 'POST', body: { selected_address_id: selectedAddressId } }),
  changeAddress: (addressId) =>
    apiFetch('/addresses/', { method: 'PUT', body: { address_id: addressId } }),

  orders: () => apiFetch('/orders/'),
  order: (id) => apiFetch(`/orders/${id}`),
  previewOrder: () => apiFetch('/orders/preview', { method: 'POST' }),
  createOrder: (darkstoreReservationId) =>
    apiFetch('/orders/', {
      method: 'POST',
      body: { darkstore_reservation_id: darkstoreReservationId },
    }),
}

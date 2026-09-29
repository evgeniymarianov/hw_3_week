import { reactive } from 'vue'

const ACCESS_TOKEN_KEY = 'samokat_access_token'
const REFRESH_TOKEN_KEY = 'samokat_refresh_token'
const USER_KEY = 'samokat_user'

export const auth = reactive({
  accessToken: localStorage.getItem(ACCESS_TOKEN_KEY),
  refreshToken: localStorage.getItem(REFRESH_TOKEN_KEY),
  user: readUser(),

  isLoggedIn() {
    return Boolean(this.accessToken)
  },

  setTokens(tokens) {
    this.accessToken = tokens.access_token
    this.refreshToken = tokens.refresh_token
    localStorage.setItem(ACCESS_TOKEN_KEY, tokens.access_token)
    localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token)
  },

  setUser(user) {
    this.user = user
    localStorage.setItem(USER_KEY, JSON.stringify(user))
  },

  clear() {
    this.accessToken = null
    this.refreshToken = null
    this.user = null
    localStorage.removeItem(ACCESS_TOKEN_KEY)
    localStorage.removeItem(REFRESH_TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
  },
})

function readUser() {
  try {
    return JSON.parse(localStorage.getItem(USER_KEY))
  } catch {
    return null
  }
}

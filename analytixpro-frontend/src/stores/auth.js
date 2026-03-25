import { defineStore } from "pinia"
import { ref, computed } from "vue"
import { authService } from "@/services/api"

export const useAuthStore = defineStore("auth", () => {
  const user         = ref(null)
  const accessToken  = ref(localStorage.getItem("access_token") || "")
  const refreshToken = ref(localStorage.getItem("refresh_token") || "")

  const isLoggedIn = computed(() => !!accessToken.value)

  function setTokens(access, refresh) {
    accessToken.value  = access
    refreshToken.value = refresh
    localStorage.setItem("access_token",  access)
    localStorage.setItem("refresh_token", refresh)
  }

  function clearAuth() {
    user.value         = null
    accessToken.value  = ""
    refreshToken.value = ""
    localStorage.removeItem("access_token")
    localStorage.removeItem("refresh_token")
  }

  async function login(credentials) {
    const { data } = await authService.login(credentials)
    setTokens(data.access, data.refresh)
    await fetchMe()
  }

  async function register(payload) {
    const { data } = await authService.register(payload)
    // Backend returns tokens on register
    if (data.tokens) {
      setTokens(data.tokens.access, data.tokens.refresh)
      await fetchMe()
    }
    return data
  }

  async function fetchMe() {
    try {
      const { data } = await authService.me()
      user.value = data
    } catch {
      clearAuth()
    }
  }

  function logout() {
    clearAuth()
  }

  // Hydrate on app boot if token exists
  if (accessToken.value && !user.value) {
    fetchMe()
  }

  return { user, accessToken, isLoggedIn, login, register, logout, fetchMe, clearAuth }
})

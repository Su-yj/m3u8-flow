import { ref } from 'vue'
import { defineStore } from 'pinia'

const ACCESS_TOKEN_KEY = 'access_token'
const REFRESH_TOKEN_KEY = 'refresh_token'

export const useAuthStore = defineStore('auth', () => {
  const accessToken = ref<string | null>(localStorage.getItem(ACCESS_TOKEN_KEY))
  const refreshToken = ref<string | null>(localStorage.getItem(REFRESH_TOKEN_KEY))

  function setTokens(access_token: string, refresh_token: string) {
    accessToken.value = access_token
    refreshToken.value = refresh_token
    localStorage.setItem(ACCESS_TOKEN_KEY, access_token)
    localStorage.setItem(REFRESH_TOKEN_KEY, refresh_token)
  }

  function clearTokens() {
    accessToken.value = null
    refreshToken.value = null
    localStorage.removeItem(ACCESS_TOKEN_KEY)
    localStorage.removeItem(REFRESH_TOKEN_KEY)
  }

  return { accessToken, refreshToken, setTokens, clearTokens }
})


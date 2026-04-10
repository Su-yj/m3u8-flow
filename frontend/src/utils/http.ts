import axios, { type AxiosError, type AxiosRequestConfig } from 'axios'
import type { Pinia } from 'pinia'
import type { Router } from 'vue-router'

import { useAuthStore } from '@/stores/auth'

type TokenResponse = {
  code: number
  message?: string
  data?: {
    access_token: string
    refresh_token: string
  }
}

function isSkipRefreshUrl(url?: string) {
  if (!url) return false
  return url.includes('/api/auth/login') || url.includes('/api/auth/refresh')
}

export function setupAxiosInterceptors(pinia: Pinia, router: Router) {
  const raw = axios.create()

  let refreshing: Promise<void> | null = null

  axios.interceptors.request.use((config) => {
    const auth = useAuthStore(pinia)
    const token = auth.accessToken

    if (token) {
      config.headers = config.headers ?? {}
      if (!('Authorization' in config.headers)) {
        ;(config.headers as Record<string, string>).Authorization = `Bearer ${token}`
      }
    }

    return config
  })

  axios.interceptors.response.use(
    (resp) => resp,
    async (err: AxiosError) => {
      const status = err.response?.status
      const config = err.config as (AxiosRequestConfig & { _retry?: boolean }) | undefined

      if (status !== 401 || !config?.url || isSkipRefreshUrl(config.url) || config._retry) {
        return Promise.reject(err)
      }

      const auth = useAuthStore(pinia)
      if (!auth.refreshToken) {
        auth.clearTokens()
        await router.replace({ name: 'login' })
        return Promise.reject(err)
      }

      config._retry = true

      try {
        if (!refreshing) {
          refreshing = (async () => {
            const { data } = await raw.post<TokenResponse>('/api/auth/refresh', {
              refresh_token: auth.refreshToken,
            })
            if (data.code !== 0 || !data.data) {
              throw new Error(data.message || '刷新 token 失败')
            }
            auth.setTokens(data.data.access_token, data.data.refresh_token)
          })().finally(() => {
            refreshing = null
          })
        }

        await refreshing

        config.headers = config.headers ?? {}
        ;(config.headers as Record<string, string>).Authorization = `Bearer ${useAuthStore(pinia).accessToken}`

        return axios(config)
      } catch (e) {
        auth.clearTokens()
        await router.replace({ name: 'login' })
        return Promise.reject(e)
      }
    },
  )
}


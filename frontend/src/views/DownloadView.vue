<template>
  <UiCard class="h-full">
    <template #header>
      <div class="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div class="flex flex-wrap items-center justify-between gap-2">
          <div class="flex flex-wrap items-center gap-2">
            <span class="text-base font-semibold text-[var(--color-text)]">下载管理</span>
            <UiTag variant="info" effect="plain">任务数 {{ tasks.length }}</UiTag>
          </div>
          <div class="flex items-center gap-2 md:hidden">
            <UiSwitch v-model="isDark" />
            <UiButton
              v-if="authStore.accessToken"
              variant="ghost"
              size="sm"
              class="text-red-600 dark:text-red-400"
              @click="logout"
            >
              退出
            </UiButton>
          </div>
        </div>
        <div class="flex flex-col gap-2 sm:flex-row sm:flex-wrap">
          <UiButton variant="primary" class="w-full sm:w-auto" @click="openCreateDialog"
            >添加任务</UiButton
          >
          <UiButton
            variant="warning"
            class="w-full sm:w-auto"
            :disabled="tasks.length === 0 || allActionLoading"
            :loading="allActionLoading && allActionType === 'stop'"
            @click="stopAll"
          >
            全部暂停
          </UiButton>
          <UiButton
            variant="success"
            class="w-full sm:w-auto"
            :disabled="tasks.length === 0 || allActionLoading"
            :loading="allActionLoading && allActionType === 'start'"
            @click="startAll"
          >
            全部开始
          </UiButton>
        </div>
      </div>
    </template>

    <div v-if="tasks.length === 0" class="py-8">
      <UiEmpty description="暂无下载中/等待中/暂停任务" />
    </div>
    <div v-else class="flex flex-col gap-3">
      <DownloadItem v-for="task in tasks" :key="task.id" :task="task" />
    </div>
  </UiCard>
  <CreateTaskDialog v-model="createDialogVisible" />
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import axios from 'axios'
import { fetchEventSource } from '@microsoft/fetch-event-source'
import { useDark } from '@vueuse/core'

import CreateTaskDialog from '@/components/CreateTaskDialog.vue'
import DownloadItem from '@/components/DownloadItem.vue'
import UiButton from '@/components/ui/UiButton.vue'
import UiCard from '@/components/ui/UiCard.vue'
import UiEmpty from '@/components/ui/UiEmpty.vue'
import UiTag from '@/components/ui/UiTag.vue'
import UiSwitch from '@/components/ui/UiSwitch.vue'
import type { TaskModel } from '@/types/models'
import { toast } from '@/utils/toast'
import { useAuthStore } from '@/stores/auth'
import router from '@/router'

const tasks = ref<TaskModel[]>([])
const allActionLoading = ref(false)
const allActionType = ref<'start' | 'stop' | null>(null)
const authStore = useAuthStore()
const isDark = useDark()
let abortController: AbortController | null = null
let reconnectTimer: number | null = null
let reconnectAttempt = 0
let disposed = false
let lastSseDataAt = 0
let idleCheckTimer: number | null = null
const SSE_IDLE_MS = 8000
const IDLE_CHECK_INTERVAL_MS = 3000
const createDialogVisible = ref(false)

async function logout() {
  authStore.clearTokens()
  await router.replace({ name: 'login' })
}

const stopIdleWatchdog = () => {
  if (idleCheckTimer !== null) {
    window.clearInterval(idleCheckTimer)
    idleCheckTimer = null
  }
}

const startIdleWatchdog = () => {
  stopIdleWatchdog()
  idleCheckTimer = window.setInterval(() => {
    if (disposed || !abortController) return
    if (Date.now() - lastSseDataAt <= SSE_IDLE_MS) return
    connectProgressSSE()
  }, IDLE_CHECK_INTERVAL_MS)
}

const cleanupSSE = () => {
  stopIdleWatchdog()
  if (reconnectTimer !== null) {
    window.clearTimeout(reconnectTimer)
    reconnectTimer = null
  }
  if (abortController) {
    abortController.abort()
    abortController = null
  }
}

const scheduleReconnect = () => {
  if (disposed) return
  if (reconnectTimer !== null) return

  reconnectAttempt += 1
  const baseDelayMs = 1000
  const maxDelayMs = 15000
  const expDelay = Math.min(maxDelayMs, baseDelayMs * 2 ** Math.min(reconnectAttempt, 10))
  const jitter = Math.floor(Math.random() * 300)
  const delayMs = expDelay + jitter

  reconnectTimer = window.setTimeout(() => {
    reconnectTimer = null
    connectProgressSSE()
  }, delayMs)
}

const connectProgressSSE = () => {
  cleanupSSE()
  if (disposed) return

  abortController = new AbortController()

  void fetchEventSource('/api/tasks/progress', {
    signal: abortController.signal,
    headers: authStore.accessToken ? { Authorization: `Bearer ${authStore.accessToken}` } : {},
    async onopen(response) {
      if (response.ok) {
        reconnectAttempt = 0
        lastSseDataAt = Date.now()
        startIdleWatchdog()
        return
      }

      if (response.status === 401) {
        try {
          if (!authStore.refreshToken) throw new Error('no refresh token')
          const { data } = await axios.post('/api/auth/refresh', {
            refresh_token: authStore.refreshToken,
          })
          if (!data || data.code !== 0 || !data.data)
            throw new Error(data?.message || 'refresh failed')
          authStore.setTokens(data.data.access_token, data.data.refresh_token)
          connectProgressSSE()
          return
        } catch {
          authStore.clearTokens()
          await router.replace({ name: 'login' })
          throw new Error('unauthorized')
        }
      }

      throw new Error(`SSE open failed: ${response.status}`)
    },
    onmessage(event) {
      if (!event.data) return
      lastSseDataAt = Date.now()
      try {
        const data = JSON.parse(event.data) as TaskModel[]
        tasks.value = Array.isArray(data) ? data : []
      } catch (error) {
        console.log({ event, data: event.data })
        console.error('SSE data parse error:', error)
      }
    },
    onerror(error) {
      if (disposed) return
      console.error('SSE connection error:', error)
      stopIdleWatchdog()
      scheduleReconnect()
    },
    onclose() {
      if (disposed) return
      stopIdleWatchdog()
      scheduleReconnect()
    },
  })
}

const openCreateDialog = () => {
  createDialogVisible.value = true
}

const stopAll = async () => {
  if (allActionLoading.value) return
  allActionLoading.value = true
  allActionType.value = 'stop'
  try {
    await axios.post('/api/tasks/stop_all')
    toast.success('已发送全部暂停指令')
  } catch (error) {
    console.error(error)
    toast.error('全部暂停失败')
  } finally {
    allActionLoading.value = false
    allActionType.value = null
  }
}

const startAll = async () => {
  if (allActionLoading.value) return
  allActionLoading.value = true
  allActionType.value = 'start'
  try {
    await axios.post('/api/tasks/start_all')
    toast.success('已发送全部开始指令')
  } catch (error) {
    console.error(error)
    toast.error('全部开始失败')
  } finally {
    allActionLoading.value = false
    allActionType.value = null
  }
}

onMounted(() => {
  connectProgressSSE()
})

onUnmounted(() => {
  disposed = true
  cleanupSSE()
})
</script>

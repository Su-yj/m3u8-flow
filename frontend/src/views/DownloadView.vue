<template>
  <el-card class="download-view-wrapper">
    <template #header>
      <div class="card-header">
        <div class="header-title">
          <span>下载管理</span>
          <el-tag type="info" effect="plain">任务数 {{ tasks.length }}</el-tag>
        </div>
        <div class="header-actions">
          <el-button type="primary" @click="openCreateDialog">添加任务</el-button>
          <el-button
            type="warning"
            plain
            :disabled="tasks.length === 0 || allActionLoading"
            :loading="allActionLoading && allActionType === 'stop'"
            @click="stopAll"
          >
            全部暂停
          </el-button>
          <el-button
            type="success"
            plain
            :disabled="tasks.length === 0 || allActionLoading"
            :loading="allActionLoading && allActionType === 'start'"
            @click="startAll"
          >
            全部开始
          </el-button>
        </div>
      </div>
    </template>
    <div v-if="tasks.length === 0" class="empty-wrap">
      <el-empty description="暂无下载中/等待中/暂停任务" />
    </div>
    <div v-else class="task-list">
      <DownloadItem v-for="task in tasks" :key="task.id" :task="task" />
    </div>
  </el-card>
  <CreateTaskDialog v-model="createDialogVisible" />
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import type { TaskModel } from '@/types/models'
import DownloadItem from '@/components/DownloadItem.vue'
import CreateTaskDialog from '@/components/CreateTaskDialog.vue'
import { fetchEventSource } from '@microsoft/fetch-event-source'
import { useAuthStore } from '@/stores/auth'
import router from '@/router'

const tasks = ref<TaskModel[]>([])
const allActionLoading = ref(false)
const allActionType = ref<'start' | 'stop' | null>(null)
let abortController: AbortController | null = null
let reconnectTimer: number | null = null
let reconnectAttempt = 0
let disposed = false
/** 最近一次收到 SSE 数据的时间（用于检测「半开」连接：后端重启后可能长期不触发 onerror） */
let lastSseDataAt = 0
let idleCheckTimer: number | null = null
/** 后端约 1s 推送一次，超过该时间无数据视为断线，主动重连 */
const SSE_IDLE_MS = 8000
const IDLE_CHECK_INTERVAL_MS = 3000
const createDialogVisible = ref(false)

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
  const auth = useAuthStore()

  void fetchEventSource('/api/tasks/progress', {
    signal: abortController.signal,
    headers: auth.accessToken ? { Authorization: `Bearer ${auth.accessToken}` } : {},
    async onopen(response) {
      if (response.ok) {
        reconnectAttempt = 0
        lastSseDataAt = Date.now()
        startIdleWatchdog()
        return
      }

      if (response.status === 401) {
        // 401：尝试刷新 token 后重连
        try {
          if (!auth.refreshToken) throw new Error('no refresh token')
          const { data } = await axios.post('/api/auth/refresh', {
            refresh_token: auth.refreshToken,
          })
          if (!data || data.code !== 0 || !data.data) throw new Error(data?.message || 'refresh failed')
          auth.setTokens(data.data.access_token, data.data.refresh_token)
          connectProgressSSE()
          return
        } catch {
          auth.clearTokens()
          await router.replace({ name: 'login' })
          throw new Error('unauthorized')
        }
      }

      throw new Error(`SSE open failed: ${response.status}`)
    },
    onmessage(event) {
      lastSseDataAt = Date.now()
      try {
        const data = JSON.parse(event.data) as TaskModel[]
        tasks.value = Array.isArray(data) ? data : []
      } catch (error) {
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
    ElMessage.success('已发送全部暂停指令')
  } catch (error) {
    console.error(error)
    ElMessage.error('全部暂停失败')
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
    ElMessage.success('已发送全部开始指令')
  } catch (error) {
    console.error(error)
    ElMessage.error('全部开始失败')
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

<style scoped lang="scss">
.download-view-wrapper {
  box-sizing: border-box;
  height: 100%;
  width: 100%;

  .card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .header-actions {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .header-title {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .task-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .empty-wrap {
    padding: 20px 0;
  }
}
</style>

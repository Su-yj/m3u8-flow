<template>
  <UiCard class="h-full">
    <template #header>
      <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <span class="text-base font-semibold">全局配置</span>
        <div class="flex flex-wrap gap-2">
          <UiButton
            :loading="resetLoading"
            :disabled="loading || saveLoading"
            @click="openResetDialog"
          >
            重置
          </UiButton>
          <UiButton
            variant="primary"
            :loading="saveLoading"
            :disabled="loading || resetLoading"
            @click="saveGlobalConfig"
          >
            保存
          </UiButton>
        </div>
      </div>
    </template>

    <div class="relative max-w-3xl px-4 sm:px-0">
      <UiLoadingOverlay :show="loading" />
      <UiSkeleton v-if="loading" :rows="8" />
      <form v-else class="flex flex-col gap-4" @submit.prevent="saveGlobalConfig">
        <UiFormRow label="下载目录" :error="errors.download_dir">
          <UiInput
            v-model="form.download_dir"
            placeholder="例如：downloads"
            @blur="errors.download_dir = ''"
          />
        </UiFormRow>

        <UiFormRow label="任务并发数" :error="errors.task_concurrency">
          <div class="flex flex-wrap items-center gap-2">
            <UiNumberInput v-model="form.task_concurrency" :min="1" :max="32" class="max-w-xs" />
            <span class="text-xs text-[var(--color-text-muted)]">最多同时下载任务数</span>
          </div>
        </UiFormRow>

        <UiFormRow label="片段并发数" :error="errors.concurrency">
          <div class="flex flex-wrap items-center gap-2">
            <UiNumberInput v-model="form.concurrency" :min="1" :max="64" class="max-w-xs" />
            <span class="text-xs text-[var(--color-text-muted)]">单任务并发下载线程数</span>
          </div>
        </UiFormRow>

        <UiFormRow label="速度限制">
          <div class="flex flex-wrap items-center gap-2">
            <UiNumberInput
              v-model="form.speed_limit_value"
              class="max-w-xs min-w-[8rem]"
              :min="0.01"
              :step="0.01"
              :precision="2"
              placeholder="不限速"
            />
            <UiSelect
              v-model="form.speed_limit_unit"
              :options="[
                { label: 'KB/s', value: 'KB' },
                { label: 'MB/s', value: 'MB' },
              ]"
            />
            <span class="text-xs text-[var(--color-text-muted)]">留空表示不限速</span>
          </div>
        </UiFormRow>

        <UiFormRow label="分块大小">
          <div class="flex flex-wrap items-center gap-2">
            <UiNumberInput
              v-model="form.chunk_size_value"
              class="max-w-xs min-w-[8rem]"
              :min="0.01"
              :step="0.01"
              :precision="2"
              placeholder="默认"
            />
            <UiSelect
              v-model="form.chunk_size_unit"
              :options="[
                { label: 'KB', value: 'KB' },
                { label: 'MB', value: 'MB' },
              ]"
            />
            <span class="text-xs text-[var(--color-text-muted)]">留空表示默认分块大小</span>
          </div>
        </UiFormRow>

        <UiFormRow label="代理地址">
          <UiInput v-model="proxyStr" placeholder="例如：http://127.0.0.1:7890" />
        </UiFormRow>

        <UiFormRow label="FFmpeg 路径">
          <UiInput v-model="ffmpegStr" placeholder="例如：/usr/bin/ffmpeg" />
        </UiFormRow>

        <UiFormRow label="请求头(JSON)" :error="errors.headers_json">
          <UiTextarea
            v-model="form.headers_json"
            :rows="5"
            placeholder='例如：{"Authorization":"Bearer xxxxx"}'
            @blur="errors.headers_json = ''"
          />
        </UiFormRow>

        <UiFormRow label="任务完成后合并">
          <UiSwitch v-model="form.merge_video" />
        </UiFormRow>

        <UiFormRow label="任务完成后清理缓存">
          <UiSwitch v-model="form.delete_cache" />
        </UiFormRow>
      </form>
    </div>
  </UiCard>

  <UiModal v-model="resetDialogVisible" title="确认重置" width-class="w-full max-w-md">
    <p class="text-sm text-[var(--color-text-muted)]">重置后将恢复默认值，且无法撤销。是否继续？</p>
    <template #footer>
      <UiButton variant="secondary" @click="resetDialogVisible = false">取消</UiButton>
      <UiButton variant="warning" :loading="resetLoading" @click="confirmReset">确认重置</UiButton>
    </template>
  </UiModal>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import axios from 'axios'

import UiButton from '@/components/ui/UiButton.vue'
import UiCard from '@/components/ui/UiCard.vue'
import UiFormRow from '@/components/ui/UiFormRow.vue'
import UiInput from '@/components/ui/UiInput.vue'
import UiLoadingOverlay from '@/components/ui/UiLoadingOverlay.vue'
import UiModal from '@/components/ui/UiModal.vue'
import UiNumberInput from '@/components/ui/UiNumberInput.vue'
import UiSelect from '@/components/ui/UiSelect.vue'
import UiSkeleton from '@/components/ui/UiSkeleton.vue'
import UiSwitch from '@/components/ui/UiSwitch.vue'
import UiTextarea from '@/components/ui/UiTextarea.vue'
import type { ApiResponse } from '@/types/api'
import type { GlobalConfigModel } from '@/types/models'
import { headersJsonRule, validateModel } from '@/utils/formValidate'
import { toast } from '@/utils/toast'

const globalConfig = ref<GlobalConfigModel | null>(null)
const loading = ref(false)
const saveLoading = ref(false)
const resetLoading = ref(false)
const resetDialogVisible = ref(false)

const errors = reactive({
  download_dir: '',
  task_concurrency: '',
  concurrency: '',
  headers_json: '',
})

type GlobalConfigFormModel = {
  download_dir: string
  task_concurrency: number
  concurrency: number
  speed_limit_value: number | null
  speed_limit_unit: 'KB' | 'MB'
  chunk_size_value: number | null
  chunk_size_unit: 'KB' | 'MB'
  proxy: string | null
  ffmpeg_path: string | null
  headers_json: string
  merge_video: boolean
  delete_cache: boolean
}

const form = reactive<GlobalConfigFormModel>({
  download_dir: 'downloads',
  task_concurrency: 1,
  concurrency: 1,
  speed_limit_value: null,
  speed_limit_unit: 'KB',
  chunk_size_value: null,
  chunk_size_unit: 'KB',
  proxy: null,
  ffmpeg_path: null,
  headers_json: '',
  merge_video: true,
  delete_cache: true,
})

const proxyStr = computed({
  get: () => form.proxy ?? '',
  set: (v: string) => {
    form.proxy = v.trim() ? v : null
  },
})

const ffmpegStr = computed({
  get: () => form.ffmpeg_path ?? '',
  set: (v: string) => {
    form.ffmpeg_path = v.trim() ? v : null
  },
})

const BYTES_IN_KB = 1024
const BYTES_IN_MB = 1024 * 1024

const bytesToDisplay = (bytes: number | null): { value: number | null; unit: 'KB' | 'MB' } => {
  if (!bytes) {
    return { value: null, unit: 'KB' }
  }
  if (bytes >= BYTES_IN_MB) {
    return {
      value: Number((bytes / BYTES_IN_MB).toFixed(2)),
      unit: 'MB',
    }
  }
  return {
    value: Number((bytes / BYTES_IN_KB).toFixed(2)),
    unit: 'KB',
  }
}

const displayToBytes = (value: number | null, unit: 'KB' | 'MB'): number | null => {
  if (value === null || value === undefined || Number.isNaN(value) || value <= 0) {
    return null
  }
  const multiplier = unit === 'MB' ? BYTES_IN_MB : BYTES_IN_KB
  return Math.round(value * multiplier)
}

const patchFormFromConfig = (config: GlobalConfigModel) => {
  form.download_dir = config.download_dir
  form.task_concurrency = config.task_concurrency
  form.concurrency = config.concurrency
  const speedLimitDisplay = bytesToDisplay(config.speed_limit)
  form.speed_limit_value = speedLimitDisplay.value
  form.speed_limit_unit = speedLimitDisplay.unit
  const chunkSizeDisplay = bytesToDisplay(config.chunk_size)
  form.chunk_size_value = chunkSizeDisplay.value
  form.chunk_size_unit = chunkSizeDisplay.unit
  form.proxy = config.proxy
  form.ffmpeg_path = config.ffmpeg_path
  form.headers_json = config.headers ? JSON.stringify(config.headers, null, 2) : ''
  form.merge_video = config.merge_video
  form.delete_cache = config.delete_cache
}

const getGlobalConfig = async () => {
  loading.value = true
  try {
    const response = await axios.get<ApiResponse<GlobalConfigModel>>('/api/global_config/')
    if (response.status === 200 && response.data.data) {
      globalConfig.value = response.data.data
      patchFormFromConfig(response.data.data)
    }
  } catch (error) {
    console.error(error)
    toast.error('获取全局配置失败')
  } finally {
    loading.value = false
  }
}

const saveGlobalConfig = async () => {
  errors.download_dir = ''
  errors.task_concurrency = ''
  errors.concurrency = ''
  errors.headers_json = ''

  const r = validateModel(form as unknown as Record<string, unknown>, {
    download_dir: [{ required: true, message: '请输入下载目录' }],
    task_concurrency: [{ required: true, message: '请输入任务并发数' }],
    concurrency: [{ required: true, message: '请输入片段并发数' }],
    headers_json: [headersJsonRule()],
  })
  if (!r.valid) {
    const msg = r.message
    if (msg.includes('下载目录')) errors.download_dir = msg
    else if (msg.includes('任务并发')) errors.task_concurrency = msg
    else if (msg.includes('片段并发')) errors.concurrency = msg
    else if (msg.includes('请求头') || msg.includes('JSON')) errors.headers_json = msg
    else toast.error(msg)
    return
  }

  let headers: Record<string, string> | null = null
  if (form.headers_json.trim()) {
    headers = JSON.parse(form.headers_json) as Record<string, string>
  }

  const payload = {
    download_dir: form.download_dir,
    task_concurrency: form.task_concurrency,
    concurrency: form.concurrency,
    speed_limit: displayToBytes(form.speed_limit_value, form.speed_limit_unit),
    chunk_size: displayToBytes(form.chunk_size_value, form.chunk_size_unit),
    proxy: form.proxy?.trim() || null,
    ffmpeg_path: form.ffmpeg_path?.trim() || null,
    headers,
    merge_video: form.merge_video,
    delete_cache: form.delete_cache,
  }

  saveLoading.value = true
  try {
    const response = await axios.patch<ApiResponse<GlobalConfigModel>>(
      '/api/global_config/',
      payload,
    )
    if (response.status === 200 && response.data.data) {
      globalConfig.value = response.data.data
      patchFormFromConfig(response.data.data)
      toast.success('全局配置保存成功')
      return
    }
    toast.error(response.data.message || '保存全局配置失败')
  } catch (error) {
    console.error(error)
    toast.error('保存全局配置失败')
  } finally {
    saveLoading.value = false
  }
}

function openResetDialog() {
  resetDialogVisible.value = true
}

async function confirmReset() {
  resetDialogVisible.value = false
  resetLoading.value = true
  try {
    const response = await axios.post<ApiResponse<GlobalConfigModel>>('/api/global_config/reset')
    if (response.status === 200 && response.data.data) {
      globalConfig.value = response.data.data
      patchFormFromConfig(response.data.data)
      toast.success('全局配置已重置')
      return
    }
    toast.error(response.data.message || '重置全局配置失败')
  } catch (error) {
    console.error(error)
    toast.error('重置全局配置失败')
  } finally {
    resetLoading.value = false
  }
}

onMounted(() => {
  getGlobalConfig()
})
</script>

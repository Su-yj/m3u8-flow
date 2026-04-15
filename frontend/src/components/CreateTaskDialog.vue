<template>
  <UiModal v-model="dialogVisible" title="添加任务" width-class="w-full max-w-[720px]">
    <form class="flex flex-col gap-4" @submit.prevent="submitCreateTask">
      <UiFormRow label="任务名称">
        <UiInput v-model="createForm.name" placeholder="请输入任务名称" />
      </UiFormRow>
      <UiFormRow label="M3U8 地址">
        <UiInput v-model="createForm.m3u8_url" placeholder="请输入 m3u8 URL" />
      </UiFormRow>
      <UiFormRow label="下载目录">
        <UiInput v-model="createForm.download_dir" placeholder="例如：downloads" />
      </UiFormRow>
      <UiFormRow label="片段并发数">
        <UiNumberInput v-model="createForm.concurrency" :min="1" :max="64" />
      </UiFormRow>
      <UiFormRow label="速度限制">
        <div class="flex flex-wrap items-center gap-2">
          <UiNumberInput
            v-model="createForm.speed_limit_value"
            class="min-w-[8rem] flex-1"
            :min="0.01"
            :step="0.01"
            :precision="2"
            placeholder="不限速"
          />
          <UiSelect
            v-model="createForm.speed_limit_unit"
            :options="[
              { label: 'KB/s', value: 'KB' },
              { label: 'MB/s', value: 'MB' },
            ]"
          />
        </div>
      </UiFormRow>
      <UiFormRow label="分块大小">
        <div class="flex flex-wrap items-center gap-2">
          <UiNumberInput
            v-model="createForm.chunk_size_value"
            class="min-w-[8rem] flex-1"
            :min="0.01"
            :step="0.01"
            :precision="2"
            placeholder="默认"
          />
          <UiSelect
            v-model="createForm.chunk_size_unit"
            :options="[
              { label: 'KB', value: 'KB' },
              { label: 'MB', value: 'MB' },
            ]"
          />
        </div>
      </UiFormRow>
      <UiFormRow label="代理地址">
        <UiInput v-model="proxyStr" placeholder="例如：http://127.0.0.1:7890" />
      </UiFormRow>
      <UiFormRow label="请求头">
        <HeadersEditor ref="headersEditorRef" v-model="createForm.headers_json" />
      </UiFormRow>
      <UiFormRow label="完成后合并">
        <UiSwitch v-model="createForm.merge_video" />
      </UiFormRow>
      <UiFormRow label="完成后清理缓存">
        <UiSwitch v-model="createForm.delete_cache" />
      </UiFormRow>
    </form>
    <template #footer>
      <UiButton variant="secondary" @click="dialogVisible = false">取消</UiButton>
      <UiButton variant="primary" :loading="createLoading" @click="submitCreateTask"
        >创建任务</UiButton
      >
    </template>
  </UiModal>
</template>

<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import axios from 'axios'

import HeadersEditor from '@/components/HeadersEditor.vue'
import UiButton from '@/components/ui/UiButton.vue'
import UiFormRow from '@/components/ui/UiFormRow.vue'
import UiInput from '@/components/ui/UiInput.vue'
import UiModal from '@/components/ui/UiModal.vue'
import UiNumberInput from '@/components/ui/UiNumberInput.vue'
import UiSelect from '@/components/ui/UiSelect.vue'
import UiSwitch from '@/components/ui/UiSwitch.vue'
import type { ApiResponse } from '@/types/api'
import type { GlobalConfigModel, TaskModel } from '@/types/models'
import { headersJsonRule, validateModel } from '@/utils/formValidate'
import { toast } from '@/utils/toast'

const props = defineProps<{
  modelValue: boolean
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
}>()

const dialogVisible = computed({
  get: () => props.modelValue,
  set: (value: boolean) => emit('update:modelValue', value),
})

const createLoading = ref(false)
const headersEditorRef = ref<InstanceType<typeof HeadersEditor> | null>(null)

type CreateTaskFormModel = {
  name: string
  m3u8_url: string
  download_dir: string
  concurrency: number
  speed_limit_value: number | null
  speed_limit_unit: 'KB' | 'MB'
  chunk_size_value: number | null
  chunk_size_unit: 'KB' | 'MB'
  proxy: string | null
  headers_json: string
  merge_video: boolean
  delete_cache: boolean
}

const buildCreateFormDefaults = (): CreateTaskFormModel => ({
  name: '',
  m3u8_url: '',
  download_dir: 'downloads',
  concurrency: 1,
  speed_limit_value: null,
  speed_limit_unit: 'KB',
  chunk_size_value: null,
  chunk_size_unit: 'KB',
  proxy: null,
  headers_json: '',
  merge_video: true,
  delete_cache: true,
})
const createForm = ref<CreateTaskFormModel>(buildCreateFormDefaults())

const proxyStr = computed({
  get: () => createForm.value.proxy ?? '',
  set: (v: string) => {
    createForm.value.proxy = v.trim() ? v : null
  },
})

const BYTES_IN_KB = 1024
const BYTES_IN_MB = 1024 * 1024

const bytesToDisplay = (bytes: number | null): { value: number | null; unit: 'KB' | 'MB' } => {
  if (!bytes) {
    return { value: null, unit: 'KB' }
  }
  if (bytes >= BYTES_IN_MB) {
    return { value: Number((bytes / BYTES_IN_MB).toFixed(2)), unit: 'MB' }
  }
  return { value: Number((bytes / BYTES_IN_KB).toFixed(2)), unit: 'KB' }
}

const displayToBytes = (value: number | null, unit: 'KB' | 'MB'): number | null => {
  if (value === null || value === undefined || Number.isNaN(value) || value <= 0) {
    return null
  }
  const multiplier = unit === 'MB' ? BYTES_IN_MB : BYTES_IN_KB
  return Math.round(value * multiplier)
}

const applyGlobalConfigAsDefaults = (globalConfig: GlobalConfigModel) => {
  createForm.value.download_dir = globalConfig.download_dir
  createForm.value.concurrency = globalConfig.concurrency
  const speedLimitDisplay = bytesToDisplay(globalConfig.speed_limit)
  createForm.value.speed_limit_value = speedLimitDisplay.value
  createForm.value.speed_limit_unit = speedLimitDisplay.unit
  const chunkSizeDisplay = bytesToDisplay(globalConfig.chunk_size)
  createForm.value.chunk_size_value = chunkSizeDisplay.value
  createForm.value.chunk_size_unit = chunkSizeDisplay.unit
  createForm.value.proxy = globalConfig.proxy
  createForm.value.headers_json = globalConfig.headers
    ? JSON.stringify(globalConfig.headers, null, 2)
    : ''
  createForm.value.merge_video = globalConfig.merge_video
  createForm.value.delete_cache = globalConfig.delete_cache
}

const fetchGlobalConfigDefaults = async () => {
  try {
    const response = await axios.get<ApiResponse<GlobalConfigModel>>('/api/global_config/')
    if (response.status === 200 && response.data.data) {
      applyGlobalConfigAsDefaults(response.data.data)
    }
  } catch (error) {
    console.error(error)
    toast.error('加载全局配置默认值失败')
  }
}

const resetCreateForm = () => {
  createForm.value = buildCreateFormDefaults()
}

const submitCreateTask = async () => {
  headersEditorRef.value?.flush()
  await nextTick()

  const r = validateModel(createForm.value as unknown as Record<string, unknown>, {
    name: [{ required: true, message: '请输入任务名称' }],
    m3u8_url: [{ required: true, message: '请输入 m3u8 URL' }],
    download_dir: [{ required: true, message: '请输入下载目录' }],
    concurrency: [{ required: true, message: '请输入片段并发数' }],
    headers_json: [headersJsonRule()],
  })
  if (!r.valid) {
    toast.error(r.message)
    return
  }

  let headers: Record<string, string> | null = null
  if (createForm.value.headers_json.trim()) {
    headers = JSON.parse(createForm.value.headers_json) as Record<string, string>
  }

  createLoading.value = true
  try {
    const payload = {
      name: createForm.value.name.trim(),
      m3u8_url: createForm.value.m3u8_url.trim(),
      download_dir: createForm.value.download_dir.trim(),
      concurrency: createForm.value.concurrency,
      speed_limit: displayToBytes(
        createForm.value.speed_limit_value,
        createForm.value.speed_limit_unit,
      ),
      chunk_size: displayToBytes(
        createForm.value.chunk_size_value,
        createForm.value.chunk_size_unit,
      ),
      proxy: createForm.value.proxy?.trim() || null,
      headers,
      merge_video: createForm.value.merge_video,
      delete_cache: createForm.value.delete_cache,
    }
    const response = await axios.post<ApiResponse<TaskModel>>('/api/tasks/', payload)
    if (response.status === 200) {
      toast.success('任务创建成功')
      dialogVisible.value = false
      return
    }
    toast.error(response.data.message || '任务创建失败')
  } catch (error) {
    console.error(error)
    toast.error('任务创建失败')
  } finally {
    createLoading.value = false
  }
}

watch(
  dialogVisible,
  async (visible) => {
    if (visible) {
      resetCreateForm()
      await fetchGlobalConfigDefaults()
      return
    }
    createLoading.value = false
  },
  { immediate: true },
)
</script>

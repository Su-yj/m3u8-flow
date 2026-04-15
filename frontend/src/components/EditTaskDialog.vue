<template>
  <UiModal v-model="dialogVisible" title="编辑任务" width-class="w-full max-w-[720px]">
    <form class="flex flex-col gap-4" @submit.prevent="submitEdit">
      <UiFormRow label="任务名称">
        <UiInput v-model="editForm.name" disabled />
      </UiFormRow>
      <UiFormRow label="M3U8 地址">
        <UiInput v-model="editForm.m3u8_url" disabled />
      </UiFormRow>
      <UiFormRow label="下载目录">
        <UiInput v-model="editForm.download_dir" disabled />
      </UiFormRow>
      <UiFormRow label="片段并发数">
        <UiNumberInput v-model="editForm.concurrency" :min="1" :max="64" />
      </UiFormRow>
      <UiFormRow label="速度限制">
        <div class="flex flex-wrap items-center gap-2">
          <UiNumberInput
            v-model="editForm.speed_limit_value"
            class="min-w-[8rem] flex-1"
            :min="0.01"
            :step="0.01"
            :precision="2"
            placeholder="不限速"
          />
          <UiSelect
            v-model="editForm.speed_limit_unit"
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
            v-model="editForm.chunk_size_value"
            class="min-w-[8rem] flex-1"
            :min="0.01"
            :step="0.01"
            :precision="2"
            placeholder="默认"
          />
          <UiSelect
            v-model="editForm.chunk_size_unit"
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
        <HeadersEditor ref="headersEditorRef" v-model="editForm.headers_json" />
      </UiFormRow>
      <UiFormRow label="完成后合并">
        <UiSwitch v-model="editForm.merge_video" disabled />
      </UiFormRow>
      <UiFormRow label="完成后清理缓存">
        <UiSwitch v-model="editForm.delete_cache" disabled />
      </UiFormRow>
    </form>
    <template #footer>
      <UiButton variant="secondary" @click="dialogVisible = false">取消</UiButton>
      <UiButton variant="primary" :loading="submitLoading" @click="submitEdit">确认修改</UiButton>
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
import type { TaskModel } from '@/types/models'
import { headersJsonRule, validateModel } from '@/utils/formValidate'
import { toast } from '@/utils/toast'

const props = defineProps<{
  modelValue: boolean
  task: TaskModel
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
}>()

const dialogVisible = computed({
  get: () => props.modelValue,
  set: (value: boolean) => emit('update:modelValue', value),
})

type EditTaskFormModel = {
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

const submitLoading = ref(false)
const headersEditorRef = ref<InstanceType<typeof HeadersEditor> | null>(null)
const editForm = ref<EditTaskFormModel>({
  name: '',
  m3u8_url: '',
  download_dir: '',
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

const proxyStr = computed({
  get: () => editForm.value.proxy ?? '',
  set: (v: string) => {
    editForm.value.proxy = v.trim() ? v : null
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

const hydrateFormFromTask = (task: TaskModel) => {
  editForm.value.name = task.name
  editForm.value.m3u8_url = task.m3u8_url
  editForm.value.download_dir = task.download_dir
  editForm.value.concurrency = task.concurrency

  const speedLimitDisplay = bytesToDisplay(task.speed_limit)
  editForm.value.speed_limit_value = speedLimitDisplay.value
  editForm.value.speed_limit_unit = speedLimitDisplay.unit

  const chunkSizeDisplay = bytesToDisplay(task.chunk_size)
  editForm.value.chunk_size_value = chunkSizeDisplay.value
  editForm.value.chunk_size_unit = chunkSizeDisplay.unit

  editForm.value.proxy = task.proxy
  editForm.value.headers_json = task.headers ? JSON.stringify(task.headers, null, 2) : ''
  editForm.value.merge_video = task.merge_video
  editForm.value.delete_cache = task.delete_cache
}

const submitEdit = async () => {
  headersEditorRef.value?.flush()
  await nextTick()

  const r = validateModel(editForm.value as unknown as Record<string, unknown>, {
    concurrency: [{ required: true, message: '请输入片段并发数' }],
    headers_json: [headersJsonRule()],
  })
  if (!r.valid) {
    toast.error(r.message)
    return
  }

  let headers: Record<string, string> | null = null
  if (editForm.value.headers_json.trim()) {
    headers = JSON.parse(editForm.value.headers_json) as Record<string, string>
  }

  submitLoading.value = true
  try {
    const payload = {
      concurrency: editForm.value.concurrency,
      speed_limit: displayToBytes(
        editForm.value.speed_limit_value,
        editForm.value.speed_limit_unit,
      ),
      chunk_size: displayToBytes(editForm.value.chunk_size_value, editForm.value.chunk_size_unit),
      proxy: editForm.value.proxy?.trim() || null,
      headers,
    }
    const response = await axios.put<ApiResponse>(`/api/tasks/${props.task.id}`, payload)
    if (response.status === 200 && response.data.code === 0) {
      toast.success('任务配置已更新')
      dialogVisible.value = false
      return
    }
    toast.error(response.data.message || '更新任务配置失败')
  } catch (error) {
    console.error(error)
    toast.error('更新任务配置失败')
  } finally {
    submitLoading.value = false
  }
}

watch(
  dialogVisible,
  async (visible) => {
    if (visible) {
      hydrateFormFromTask(props.task)
      return
    }
    submitLoading.value = false
  },
  { immediate: true },
)
</script>

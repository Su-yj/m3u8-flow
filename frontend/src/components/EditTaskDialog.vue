<template>
  <el-dialog v-model="dialogVisible" title="编辑任务" width="720px" destroy-on-close>
    <el-form
      ref="editFormRef"
      :model="editForm"
      :rules="editRules"
      label-width="130px"
      @submit.prevent
    >
      <el-form-item label="任务名称">
        <el-input v-model="editForm.name" disabled />
      </el-form-item>
      <el-form-item label="M3U8 地址">
        <el-input v-model="editForm.m3u8_url" disabled />
      </el-form-item>
      <el-form-item label="下载目录">
        <el-input v-model="editForm.download_dir" disabled />
      </el-form-item>
      <el-form-item label="片段并发数" prop="concurrency">
        <el-input-number v-model="editForm.concurrency" :min="1" :max="64" />
      </el-form-item>
      <el-form-item label="速度限制">
        <el-input-number
          v-model="editForm.speed_limit_value"
          :min="0.01"
          :step="1"
          :precision="2"
        />
        <el-select v-model="editForm.speed_limit_unit" class="unit-select">
          <el-option label="KB/s" value="KB" />
          <el-option label="MB/s" value="MB" />
        </el-select>
      </el-form-item>
      <el-form-item label="分块大小">
        <el-input-number
          v-model="editForm.chunk_size_value"
          :min="0.01"
          :step="1"
          :precision="2"
        />
        <el-select v-model="editForm.chunk_size_unit" class="unit-select">
          <el-option label="KB" value="KB" />
          <el-option label="MB" value="MB" />
        </el-select>
      </el-form-item>
      <el-form-item label="代理地址">
        <el-input v-model="editForm.proxy" clearable placeholder="例如：http://127.0.0.1:7890" />
      </el-form-item>
      <el-form-item label="请求头" prop="headers_json">
        <HeadersEditor ref="headersEditorRef" v-model="editForm.headers_json" />
      </el-form-item>
      <el-form-item label="完成后合并">
        <el-switch v-model="editForm.merge_video" disabled />
      </el-form-item>
      <el-form-item label="完成后清理缓存">
        <el-switch v-model="editForm.delete_cache" disabled />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="dialogVisible = false">取消</el-button>
      <el-button type="primary" :loading="submitLoading" @click="submitEdit">确认修改</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import axios from 'axios'
import HeadersEditor from '@/components/HeadersEditor.vue'
import type { ApiResponse } from '@/types/api'
import type { TaskModel } from '@/types/models'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'

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
const editFormRef = ref<FormInstance>()
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

const editRules: FormRules<EditTaskFormModel> = {
  concurrency: [{ required: true, message: '请输入片段并发数', trigger: 'blur' }],
  headers_json: [
    {
      validator: (_rule, value: string, callback) => {
        if (!value.trim()) {
          callback()
          return
        }
        try {
          const parsed = JSON.parse(value)
          if (parsed && typeof parsed === 'object' && !Array.isArray(parsed)) {
            callback()
            return
          }
          callback(new Error('请求头必须是 JSON 对象'))
        } catch {
          callback(new Error('请求头 JSON 格式不正确'))
        }
      },
      trigger: 'blur',
    },
  ],
}

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
  const valid = await editFormRef.value?.validate().catch(() => false)
  if (!valid) return

  let headers: Record<string, string> | null = null
  if (editForm.value.headers_json.trim()) {
    headers = JSON.parse(editForm.value.headers_json) as Record<string, string>
  }

  submitLoading.value = true
  try {
    const payload = {
      concurrency: editForm.value.concurrency,
      speed_limit: displayToBytes(editForm.value.speed_limit_value, editForm.value.speed_limit_unit),
      chunk_size: displayToBytes(editForm.value.chunk_size_value, editForm.value.chunk_size_unit),
      proxy: editForm.value.proxy?.trim() || null,
      headers,
    }
    const response = await axios.put<ApiResponse>(`/api/tasks/${props.task.id}`, payload)
    if (response.status === 200 && response.data.code === 0) {
      ElMessage.success('任务配置已更新')
      dialogVisible.value = false
      return
    }
    ElMessage.error(response.data.message || '更新任务配置失败')
  } catch (error) {
    console.error(error)
    ElMessage.error('更新任务配置失败')
  } finally {
    submitLoading.value = false
  }
}

watch(
  dialogVisible,
  async (visible) => {
    if (visible) {
      hydrateFormFromTask(props.task)
      await nextTick()
      editFormRef.value?.clearValidate()
      return
    }
    submitLoading.value = false
    await nextTick()
    editFormRef.value?.clearValidate()
  },
  { immediate: true },
)
</script>

<style scoped lang="scss">
.unit-select {
  margin-left: 8px;
  width: 100px;
}
</style>


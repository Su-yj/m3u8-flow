<template>
  <el-dialog v-model="dialogVisible" title="添加任务" width="720px" destroy-on-close>
    <el-form
      ref="createFormRef"
      :model="createForm"
      :rules="createRules"
      label-width="130px"
      @submit.prevent
    >
      <el-form-item label="任务名称" prop="name">
        <el-input v-model="createForm.name" placeholder="请输入任务名称" />
      </el-form-item>
      <el-form-item label="M3U8 地址" prop="m3u8_url">
        <el-input v-model="createForm.m3u8_url" placeholder="请输入 m3u8 URL" />
      </el-form-item>
      <el-form-item label="下载目录" prop="download_dir">
        <el-input v-model="createForm.download_dir" placeholder="例如：downloads" />
      </el-form-item>
      <el-form-item label="片段并发数" prop="concurrency">
        <el-input-number v-model="createForm.concurrency" :min="1" :max="64" />
      </el-form-item>
      <el-form-item label="速度限制">
        <el-input-number
          v-model="createForm.speed_limit_value"
          :min="0.01"
          :step="1"
          :precision="2"
        />
        <el-select v-model="createForm.speed_limit_unit" class="unit-select">
          <el-option label="KB/s" value="KB" />
          <el-option label="MB/s" value="MB" />
        </el-select>
      </el-form-item>
      <el-form-item label="分块大小">
        <el-input-number
          v-model="createForm.chunk_size_value"
          :min="0.01"
          :step="1"
          :precision="2"
        />
        <el-select v-model="createForm.chunk_size_unit" class="unit-select">
          <el-option label="KB" value="KB" />
          <el-option label="MB" value="MB" />
        </el-select>
      </el-form-item>
      <el-form-item label="代理地址">
        <el-input v-model="createForm.proxy" clearable placeholder="例如：http://127.0.0.1:7890" />
      </el-form-item>
      <el-form-item label="请求头" prop="headers_json">
        <HeadersEditor ref="headersEditorRef" v-model="createForm.headers_json" />
      </el-form-item>
      <el-form-item label="完成后合并">
        <el-switch v-model="createForm.merge_video" />
      </el-form-item>
      <el-form-item label="完成后清理缓存">
        <el-switch v-model="createForm.delete_cache" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="dialogVisible = false">取消</el-button>
      <el-button type="primary" :loading="createLoading" @click="submitCreateTask">创建任务</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import axios from 'axios'
import type { ApiResponse } from '@/types/api'
import HeadersEditor from '@/components/HeadersEditor.vue'
import type { GlobalConfigModel, TaskModel } from '@/types/models'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'

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
const createFormRef = ref<FormInstance>()
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

const createRules: FormRules<CreateTaskFormModel> = {
  name: [{ required: true, message: '请输入任务名称', trigger: 'blur' }],
  m3u8_url: [{ required: true, message: '请输入 m3u8 URL', trigger: 'blur' }],
  download_dir: [{ required: true, message: '请输入下载目录', trigger: 'blur' }],
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
    ElMessage.error('加载全局配置默认值失败')
  }
}

const resetCreateForm = () => {
  createForm.value = buildCreateFormDefaults()
}

const submitCreateTask = async () => {
  headersEditorRef.value?.flush()
  await nextTick()
  const valid = await createFormRef.value?.validate().catch(() => false)
  if (!valid) {
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
      speed_limit: displayToBytes(createForm.value.speed_limit_value, createForm.value.speed_limit_unit),
      chunk_size: displayToBytes(createForm.value.chunk_size_value, createForm.value.chunk_size_unit),
      proxy: createForm.value.proxy?.trim() || null,
      headers,
      merge_video: createForm.value.merge_video,
      delete_cache: createForm.value.delete_cache,
    }
    const response = await axios.post<ApiResponse<TaskModel>>('/api/tasks/', payload)
    if (response.status === 200) {
      ElMessage.success('任务创建成功')
      dialogVisible.value = false
      return
    }
    ElMessage.error(response.data.message || '任务创建失败')
  } catch (error) {
    console.error(error)
    ElMessage.error('任务创建失败')
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
      await nextTick()
      createFormRef.value?.clearValidate()
      return
    }
    createLoading.value = false
    await nextTick()
    createFormRef.value?.clearValidate()
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

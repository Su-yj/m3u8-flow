<template>
  <el-card class="global-config-wrapper">
    <template #header>
      <div class="card-header">
        <span>全局配置</span>
        <div class="actions">
          <el-button :loading="resetLoading" :disabled="loading || saveLoading" @click="resetGlobalConfig">
            重置
          </el-button>
          <el-button
            type="primary"
            :loading="saveLoading"
            :disabled="loading || resetLoading"
            @click="saveGlobalConfig"
          >
            保存
          </el-button>
        </div>
      </div>
    </template>
    <el-skeleton :loading="loading" animated :rows="8">
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="140px"
        class="config-form"
        @submit.prevent
      >
        <el-form-item label="下载目录" prop="download_dir">
          <el-input v-model="form.download_dir" placeholder="例如：downloads" />
        </el-form-item>

        <el-form-item label="任务并发数" prop="task_concurrency">
          <el-input-number v-model="form.task_concurrency" :min="1" :max="32" />
          <span class="hint">最多同时下载任务数</span>
        </el-form-item>

        <el-form-item label="片段并发数" prop="concurrency">
          <el-input-number v-model="form.concurrency" :min="1" :max="64" />
          <span class="hint">单任务并发下载线程数</span>
        </el-form-item>

        <el-form-item label="速度限制">
          <el-input-number
            v-model="form.speed_limit_value"
            :min="0.01"
            :step="1"
            :precision="2"
            placeholder="留空表示不限速"
          />
          <el-select v-model="form.speed_limit_unit" class="unit-select">
            <el-option label="KB/s" value="KB" />
            <el-option label="MB/s" value="MB" />
          </el-select>
          <span class="hint">留空表示不限速</span>
        </el-form-item>

        <el-form-item label="分块大小">
          <el-input-number
            v-model="form.chunk_size_value"
            :min="0.01"
            :step="1"
            :precision="2"
            placeholder="留空表示默认"
          />
          <el-select v-model="form.chunk_size_unit" class="unit-select">
            <el-option label="KB" value="KB" />
            <el-option label="MB" value="MB" />
          </el-select>
          <span class="hint">留空表示默认分块大小</span>
        </el-form-item>

        <el-form-item label="代理地址">
          <el-input v-model="form.proxy" placeholder="例如：http://127.0.0.1:7890" clearable />
        </el-form-item>

        <el-form-item label="FFmpeg 路径">
          <el-input v-model="form.ffmpeg_path" placeholder="例如：/usr/bin/ffmpeg" clearable />
        </el-form-item>

        <el-form-item label="请求头(JSON)" prop="headers_json">
          <el-input
            v-model="form.headers_json"
            type="textarea"
            :rows="5"
            placeholder='例如：{"Authorization":"Bearer xxxxx"}'
          />
        </el-form-item>

        <el-form-item label="任务完成后合并">
          <el-switch v-model="form.merge_video" />
        </el-form-item>

        <el-form-item label="任务完成后清理缓存">
          <el-switch v-model="form.delete_cache" />
        </el-form-item>
      </el-form>
    </el-skeleton>
  </el-card>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import type { GlobalConfigModel } from '@/types/models'
import axios from 'axios'
import type { ApiResponse } from '@/types/api'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'

const globalConfig = ref<GlobalConfigModel | null>(null)
const loading = ref(false)
const saveLoading = ref(false)
const resetLoading = ref(false)
const formRef = ref<FormInstance>()

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

const rules: FormRules<GlobalConfigFormModel> = {
  download_dir: [{ required: true, message: '请输入下载目录', trigger: 'blur' }],
  task_concurrency: [{ required: true, message: '请输入任务并发数', trigger: 'blur' }],
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

const bytesToDisplay = (
  bytes: number | null,
): { value: number | null; unit: 'KB' | 'MB' } => {
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
    ElMessage.error('获取全局配置失败')
  } finally {
    loading.value = false
  }
}

const saveGlobalConfig = async () => {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) {
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
      ElMessage.success('全局配置保存成功')
      return
    }
    ElMessage.error(response.data.message || '保存全局配置失败')
  } catch (error) {
    console.error(error)
    ElMessage.error('保存全局配置失败')
  } finally {
    saveLoading.value = false
  }
}

const resetGlobalConfig = async () => {
  try {
    await ElMessageBox.confirm('重置后将恢复默认值，且无法撤销。是否继续？', '确认重置', {
      confirmButtonText: '确认重置',
      cancelButtonText: '取消',
      type: 'warning',
    })
  } catch {
    return
  }

  resetLoading.value = true
  try {
    const response = await axios.post<ApiResponse<GlobalConfigModel>>('/api/global_config/reset')
    if (response.status === 200 && response.data.data) {
      globalConfig.value = response.data.data
      patchFormFromConfig(response.data.data)
      ElMessage.success('全局配置已重置')
      return
    }
    ElMessage.error(response.data.message || '重置全局配置失败')
  } catch (error) {
    console.error(error)
    ElMessage.error('重置全局配置失败')
  } finally {
    resetLoading.value = false
  }
}

onMounted(() => {
  getGlobalConfig()
})
</script>

<style scoped lang="scss">
.global-config-wrapper {
  height: 100%;
  width: 100%;
  box-sizing: border-box;

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .actions {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .config-form {
    max-width: 760px;
  }

  .hint {
    color: var(--el-text-color-secondary);
    font-size: 12px;
    margin-left: 8px;
  }

  .unit-select {
    margin-left: 8px;
    width: 100px;
  }
}
</style>

<template>
  <el-dialog
    :model-value="modelValue"
    title="任务信息"
    width="560px"
    append-to-body
    destroy-on-close
    @update:model-value="emit('update:modelValue', $event)"
  >
    <div class="task-info-list">
      <div class="task-info-row">
        <span class="task-info-label">任务名称</span>
        <span class="task-info-value">{{ task.name }}</span>
      </div>
      <div class="task-info-row">
        <span class="task-info-label">任务状态</span>
        <span class="task-info-value">
          <el-tag :type="statusTagType">{{ statusLabel }}</el-tag>
        </span>
      </div>
      <div class="task-info-row">
        <span class="task-info-label">M3U8 地址</span>
        <div class="task-info-value task-info-value--with-action">
          <span class="task-info-url">{{ task.m3u8_url }}</span>
          <el-button
            type="primary"
            link
            size="small"
            :icon="CopyDocument"
            class="task-info-copy-btn"
            @click="copyM3u8Url"
          >
            复制
          </el-button>
        </div>
      </div>
      <div class="task-info-row">
        <span class="task-info-label">片段</span>
        <div class="task-info-value task-info-value--segments">
          <el-text type="success" size="small">{{ task.downloaded_segments }}</el-text>
          <span class="task-info-sep">/</span>
          <el-text type="danger" size="small">{{ task.failed_segments }}</el-text>
          <span class="task-info-sep">/</span>
          <el-text size="small">{{ totalSegmentsDisplay }}</el-text>
        </div>
      </div>
      <div class="task-info-row">
        <span class="task-info-label">下载目录</span>
        <span class="task-info-value">{{ task.download_dir }}</span>
      </div>
      <div class="task-info-row">
        <span class="task-info-label">片段并发数</span>
        <span class="task-info-value">{{ task.concurrency }}</span>
      </div>
      <div class="task-info-row">
        <span class="task-info-label">速度限制</span>
        <span class="task-info-value">{{ speedLimitDisplay }}</span>
      </div>
      <div class="task-info-row">
        <span class="task-info-label">分块大小</span>
        <span class="task-info-value">{{ chunkSizeDisplay }}</span>
      </div>
      <div class="task-info-row">
        <span class="task-info-label">代理地址</span>
        <span class="task-info-value">{{ task.proxy || '—' }}</span>
      </div>
      <div class="task-info-row">
        <span class="task-info-label">请求头</span>
        <div class="task-info-value task-info-value--headers">
          <el-table
            v-if="headerEntries.length"
            :data="headerEntries"
            class="task-info-headers-table"
            size="small"
            border
          >
            <el-table-column prop="key" label="键" width="160" />
            <el-table-column prop="value" label="值" min-width="220" />
          </el-table>
          <span v-else>—</span>
        </div>
      </div>
      <div class="task-info-row">
        <span class="task-info-label">完成后合并</span>
        <span class="task-info-value">{{ task.merge_video ? '是' : '否' }}</span>
      </div>
      <div class="task-info-row">
        <span class="task-info-label">完成后清理缓存</span>
        <span class="task-info-value">{{ task.delete_cache ? '是' : '否' }}</span>
      </div>
      <div class="task-info-row">
        <span class="task-info-label">视频时长</span>
        <span class="task-info-value">{{ durationDisplay }}</span>
      </div>
      <div class="task-info-row">
        <span class="task-info-label">创建时间</span>
        <span class="task-info-value">{{ createdAtDisplay }}</span>
      </div>
    </div>
    <template #footer>
      <el-button type="primary" @click="emit('update:modelValue', false)">关闭</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { CopyDocument } from '@element-plus/icons-vue'
import type { TaskModel, TaskStatus } from '@/types/models'
import { ElMessage } from 'element-plus'

const props = defineProps<{
  modelValue: boolean
  task: TaskModel
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

const statusLabelMap: Record<TaskStatus, string> = {
  pending: '等待中',
  downloading: '下载中',
  merging: '合并中',
  completed: '已完成',
  failed: '失败',
  stopped: '已暂停',
}

const statusLabel = computed(() => statusLabelMap[props.task.status])

const statusTagType = computed(() => {
  switch (props.task.status) {
    case 'pending':
      return 'info'
    case 'downloading':
      return 'primary'
    case 'merging':
      return 'primary'
    case 'completed':
      return 'success'
    case 'stopped':
      return 'warning'
    case 'failed':
      return 'danger'
    default:
      return 'info'
  }
})

const formatDurationHms = (totalSeconds: number): string => {
  if (!Number.isFinite(totalSeconds) || totalSeconds < 0) {
    return '—'
  }
  const whole = Math.floor(totalSeconds)
  const s = whole % 60
  const m = Math.floor(whole / 60) % 60
  const h = Math.floor(whole / 3600)
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${pad(h)}:${pad(m)}:${pad(s)}`
}

const durationDisplay = computed(() => formatDurationHms(props.task.total_duration ?? 0))

const totalSegmentsDisplay = computed(() => {
  const n = props.task.total_segments
  if (n == null || Number.isNaN(n)) {
    return '—'
  }
  return n
})

const formatBytes = (bytes: number): string => {
  if (bytes < 1024) {
    return `${bytes} B`
  }
  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(2)} KB`
  }
  if (bytes < 1024 * 1024 * 1024) {
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`
  }
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`
}

const speedLimitDisplay = computed(() => {
  const limit = props.task.speed_limit
  if (limit == null) {
    return '不限速'
  }
  return `${formatBytes(limit)}/s`
})

const chunkSizeDisplay = computed(() => {
  const size = props.task.chunk_size
  if (size == null) {
    return '—'
  }
  return formatBytes(size)
})

const headerEntries = computed(() => {
  const h = props.task.headers
  if (h == null) {
    return [] as { key: string; value: string }[]
  }
  return Object.entries(h).map(([key, value]) => ({
    key,
    value: value === undefined || value === null ? '' : String(value),
  }))
})

const createdAtDisplay = computed(() => {
  const raw = props.task.created_at
  if (!raw) {
    return '—'
  }
  const d = new Date(raw)
  if (Number.isNaN(d.getTime())) {
    return raw
  }
  return d.toLocaleString('zh-CN', { hour12: false })
})

const copyM3u8Url = async () => {
  const url = props.task.m3u8_url
  if (!url) {
    ElMessage.warning('暂无链接')
    return
  }
  try {
    await navigator.clipboard.writeText(url)
    ElMessage.success('链接已复制到剪贴板')
  } catch {
    ElMessage.error('复制失败')
  }
}
</script>

<style scoped lang="scss">
.task-info-list {
  display: grid;
  grid-template-columns: max-content 1fr;
  column-gap: 12px;
  row-gap: 10px;
  align-items: start;
  font-size: 13px;

  .task-info-row {
    display: contents;
  }

  .task-info-label {
    color: var(--el-text-color-primary);
    font-weight: bolder;
    text-align: right;
    line-height: 1.5;
    white-space: nowrap;
  }

  .task-info-value {
    color: var(--el-text-color-primary);
    line-height: 1.5;
    word-break: break-all;

    &--with-action {
      display: flex;
      align-items: flex-start;
      gap: 8px;
      flex-wrap: wrap;

      .task-info-url {
        flex: 1;
        min-width: 0;
      }

      .task-info-copy-btn {
        flex-shrink: 0;
      }
    }

    &--headers {
      min-width: 0;

      .task-info-headers-table {
        width: 100%;

        :deep(.el-table__header-wrapper th.el-table__cell) {
          background: var(--el-fill-color-light);
          color: var(--el-text-color-primary);
        }

        :deep(.el-table__cell .cell) {
          line-height: 1.45;
        }
      }
    }

    &--segments {
      display: inline-flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 4px;

      .task-info-sep {
        color: var(--el-text-color-secondary);
        user-select: none;
      }
    }
  }
}
</style>

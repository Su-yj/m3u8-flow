<template>
  <UiModal
    :model-value="modelValue"
    title="任务信息"
    width-class="w-full max-w-[560px]"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <div class="grid grid-cols-[auto_1fr] gap-x-3 gap-y-2.5 text-sm">
      <span class="text-right font-semibold whitespace-nowrap text-[var(--color-text)]"
        >任务名称</span
      >
      <span class="break-all text-[var(--color-text)]">{{ task.name }}</span>

      <span class="text-right font-semibold whitespace-nowrap text-[var(--color-text)]"
        >任务状态</span
      >
      <span
        ><UiTag :variant="statusTagType">{{ statusLabel }}</UiTag></span
      >

      <span class="text-right font-semibold whitespace-nowrap text-[var(--color-text)]"
        >M3U8 地址</span
      >
      <div class="flex min-w-0 flex-wrap items-start gap-2">
        <span class="min-w-0 flex-1 break-all text-[var(--color-text)]">{{ task.m3u8_url }}</span>
        <UiButton variant="ghost" size="sm" class="shrink-0 px-1" @click="copyM3u8Url">
          <Copy class="size-3.5" />
          复制
        </UiButton>
      </div>

      <span class="text-right font-semibold whitespace-nowrap text-[var(--color-text)]">片段</span>
      <span class="inline-flex flex-wrap items-center gap-1">
        <span class="text-emerald-600 dark:text-emerald-400">{{ task.downloaded_segments }}</span>
        <span class="text-[var(--color-text-muted)]">/</span>
        <span class="text-red-600 dark:text-red-400">{{ task.failed_segments }}</span>
        <span class="text-[var(--color-text-muted)]">/</span>
        <span>{{ totalSegmentsDisplay }}</span>
      </span>

      <span class="text-right font-semibold whitespace-nowrap text-[var(--color-text)]"
        >下载目录</span
      >
      <span class="break-all">{{ task.download_dir }}</span>

      <span class="text-right font-semibold whitespace-nowrap text-[var(--color-text)]"
        >片段并发数</span
      >
      <span>{{ task.concurrency }}</span>

      <span class="text-right font-semibold whitespace-nowrap text-[var(--color-text)]"
        >速度限制</span
      >
      <span>{{ speedLimitDisplay }}</span>

      <span class="text-right font-semibold whitespace-nowrap text-[var(--color-text)]"
        >分块大小</span
      >
      <span>{{ chunkSizeDisplay }}</span>

      <span class="text-right font-semibold whitespace-nowrap text-[var(--color-text)]"
        >代理地址</span
      >
      <span>{{ task.proxy || '—' }}</span>

      <span class="self-start text-right font-semibold whitespace-nowrap text-[var(--color-text)]"
        >请求头</span
      >
      <div class="min-w-0 overflow-x-auto">
        <table
          v-if="headerEntries.length"
          class="w-full min-w-[280px] border-collapse overflow-hidden rounded-lg border border-[var(--color-border)] text-xs"
        >
          <thead>
            <tr class="bg-[var(--color-surface-muted)] text-left text-[var(--color-text)]">
              <th class="border-b border-[var(--color-border)] px-2 py-1.5 font-semibold">键</th>
              <th class="border-b border-[var(--color-border)] px-2 py-1.5 font-semibold">值</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(row, idx) in headerEntries"
              :key="idx"
              class="border-b border-[var(--color-border)] last:border-0"
            >
              <td class="max-w-[160px] px-2 py-1.5 align-top break-all">{{ row.key }}</td>
              <td class="px-2 py-1.5 align-top break-all">{{ row.value }}</td>
            </tr>
          </tbody>
        </table>
        <span v-else>—</span>
      </div>

      <span class="text-right font-semibold whitespace-nowrap text-[var(--color-text)]"
        >完成后合并</span
      >
      <span>{{ task.merge_video ? '是' : '否' }}</span>

      <span class="text-right font-semibold whitespace-nowrap text-[var(--color-text)]"
        >完成后清理缓存</span
      >
      <span>{{ task.delete_cache ? '是' : '否' }}</span>

      <span class="text-right font-semibold whitespace-nowrap text-[var(--color-text)]"
        >视频时长</span
      >
      <span>{{ durationDisplay }}</span>

      <span class="text-right font-semibold whitespace-nowrap text-[var(--color-text)]"
        >创建时间</span
      >
      <span>{{ createdAtDisplay }}</span>
    </div>
    <template #footer>
      <UiButton variant="primary" @click="emit('update:modelValue', false)">关闭</UiButton>
    </template>
  </UiModal>
</template>

<script setup lang="ts">
import { Copy } from 'lucide-vue-next'
import { computed } from 'vue'

import UiButton from '@/components/ui/UiButton.vue'
import UiModal from '@/components/ui/UiModal.vue'
import UiTag from '@/components/ui/UiTag.vue'
import type { TaskModel, TaskStatus } from '@/types/models'
import { toast } from '@/utils/toast'

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
      return 'info' as const
    case 'downloading':
    case 'merging':
      return 'primary' as const
    case 'completed':
      return 'success' as const
    case 'stopped':
      return 'warning' as const
    case 'failed':
      return 'danger' as const
    default:
      return 'info' as const
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
    toast.warning('暂无链接')
    return
  }
  try {
    await navigator.clipboard.writeText(url)
    toast.success('链接已复制到剪贴板')
  } catch {
    toast.error('复制失败')
  }
}
</script>

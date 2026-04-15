<template>
  <div
    class="rounded-[10px] border border-[var(--color-border)] bg-[var(--color-surface)] p-4 shadow-[0_3px_10px_rgba(0,0,0,0.04)] dark:shadow-[0_3px_10px_rgba(0,0,0,0.2)]"
  >
    <div class="mb-2.5 flex items-center justify-between gap-3">
      <div
        class="min-w-0 truncate text-base font-semibold text-emerald-600 dark:text-emerald-400"
        :title="task.name"
      >
        {{ task.name }}
      </div>
      <div class="flex shrink-0 items-center gap-2">
        <div class="flex flex-wrap items-center gap-1">
          <i
            v-if="showStart"
            class="iconfont icon-play action-icon action-icon--start"
            role="button"
            tabindex="0"
            :class="{ 'is-loading': startLoading }"
            :aria-busy="startLoading"
            aria-label="开始任务"
            title="开始"
            @click="handleStart"
            @keydown.enter.prevent="handleStart"
            @keydown.space.prevent="handleStart"
          />
          <i
            v-if="showStop"
            class="iconfont icon-pause action-icon action-icon--pause"
            role="button"
            tabindex="0"
            :class="{ 'is-loading': stopLoading }"
            :aria-busy="stopLoading"
            aria-label="暂停任务"
            title="暂停"
            @click="handleStop"
            @keydown.enter.prevent="handleStop"
            @keydown.space.prevent="handleStop"
          />
          <i
            v-if="showEdit"
            class="iconfont icon-edit1 action-icon action-icon--edit"
            role="button"
            tabindex="0"
            :class="{ 'is-loading': editLoading }"
            :aria-busy="editLoading"
            aria-label="编辑任务"
            title="编辑"
            @click="openEditDialog"
            @keydown.enter.prevent="openEditDialog"
            @keydown.space.prevent="openEditDialog"
          />
          <i
            class="iconfont icon-delete action-icon action-icon--delete"
            role="button"
            tabindex="0"
            :class="{ 'is-loading': deleteLoading }"
            :aria-busy="deleteLoading"
            aria-label="删除任务"
            title="删除"
            @click="openDeleteDialog"
            @keydown.enter.prevent="openDeleteDialog"
            @keydown.space.prevent="openDeleteDialog"
          />
        </div>
        <UiTag :variant="statusTagType" effect="solid">{{ statusLabel }}</UiTag>
      </div>
    </div>

    <div
      class="mb-2.5 flex flex-wrap items-center justify-between gap-3 text-xs text-[var(--color-text-muted)]"
    >
      <div class="flex min-w-0 flex-wrap items-center gap-1.5">
        <button
          type="button"
          class="shrink-0 cursor-pointer rounded text-brand-600 transition-opacity hover:opacity-85 focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:outline-none dark:text-brand-400"
          aria-label="查看创建任务时的信息"
          @click="taskInfoDialogVisible = true"
        >
          <Info class="size-[18px]" />
        </button>
        <span>已下载 {{ downloadedSizeText }}</span>
        <span class="ml-0.5 border-l border-[var(--color-border)] pl-2 whitespace-nowrap"
          >时长 {{ durationDisplay }}</span
        >
      </div>
      <span class="whitespace-nowrap">速度 {{ speedText }}</span>
    </div>

    <UiProgress :percentage="progressValue" :height="10" />

    <div
      class="mt-2 flex flex-wrap items-center justify-between gap-3 text-xs text-[var(--color-text-muted)]"
    >
      <span>进度 {{ progressValue.toFixed(1) }}%</span>
      <span class="inline-flex min-w-0 flex-wrap items-center gap-1">
        <span>片段：</span>
        <span class="inline-flex flex-wrap items-center gap-1">
          <span class="text-emerald-600 dark:text-emerald-400">{{ task.downloaded_segments }}</span>
          <span class="text-[var(--color-text-muted)]">/</span>
          <span class="text-red-600 dark:text-red-400">{{ task.failed_segments }}</span>
          <span class="text-[var(--color-text-muted)]">/</span>
          <span>{{ totalSegmentsDisplay }}</span>
        </span>
      </span>
    </div>

    <TaskInfoDialog v-model="taskInfoDialogVisible" :task="task" />
    <EditTaskDialog v-model="editDialogVisible" :task="task" />

    <UiModal
      v-model="deleteDialogVisible"
      title="删除任务"
      width-class="w-full max-w-[440px]"
      @update:model-value="onDeleteDialogClose"
    >
      <p class="mb-3 text-sm text-[var(--color-text-muted)]">
        请选择是否同时删除本地文件（删除后不可恢复）。
      </p>
      <div class="flex flex-col gap-2">
        <UiCheckbox v-model="deleteCacheChecked">删除缓存片段（.cache 目录）</UiCheckbox>
        <UiCheckbox v-model="deleteMergedChecked">删除合并后的视频及任务下载目录</UiCheckbox>
      </div>
      <template #footer>
        <UiButton variant="secondary" @click="deleteDialogVisible = false">取消</UiButton>
        <UiButton variant="danger" :loading="deleteLoading" @click="confirmDelete"
          >确定删除</UiButton
        >
      </template>
    </UiModal>
  </div>
</template>

<script setup lang="ts">
import { Info } from 'lucide-vue-next'
import { computed, ref } from 'vue'
import axios from 'axios'

import EditTaskDialog from '@/components/EditTaskDialog.vue'
import TaskInfoDialog from '@/components/TaskInfoDialog.vue'
import UiButton from '@/components/ui/UiButton.vue'
import UiCheckbox from '@/components/ui/UiCheckbox.vue'
import UiModal from '@/components/ui/UiModal.vue'
import UiProgress from '@/components/ui/UiProgress.vue'
import UiTag from '@/components/ui/UiTag.vue'
import type { TaskModel, TaskStatus } from '@/types/models'
import { toast } from '@/utils/toast'

const props = defineProps<{
  task: TaskModel
}>()

const startLoading = ref(false)
const stopLoading = ref(false)
const editLoading = ref(false)
const deleteLoading = ref(false)
const taskInfoDialogVisible = ref(false)
const editDialogVisible = ref(false)
const deleteDialogVisible = ref(false)
const deleteCacheChecked = ref(true)
const deleteMergedChecked = ref(true)

const showStart = computed(() => {
  return props.task.status === 'stopped' || props.task.status === 'failed'
})

const showStop = computed(() => {
  return props.task.status === 'pending' || props.task.status === 'downloading'
})

const showEdit = computed(() => {
  return props.task.status === 'stopped' || props.task.status === 'failed'
})

const resetDeleteOptions = () => {
  deleteCacheChecked.value = true
  deleteMergedChecked.value = true
}

const openDeleteDialog = () => {
  if (deleteLoading.value) return
  resetDeleteOptions()
  deleteDialogVisible.value = true
}

function onDeleteDialogClose(open: boolean) {
  if (!open) {
    resetDeleteOptions()
  }
}

const handleStart = async () => {
  if (startLoading.value) return
  startLoading.value = true
  try {
    await axios.post(`/api/tasks/${props.task.id}/start`)
    toast.success('任务已加入队列')
  } catch (error) {
    console.error(error)
    toast.error('开始任务失败')
  } finally {
    startLoading.value = false
  }
}

const handleStop = async () => {
  if (stopLoading.value) return
  stopLoading.value = true
  try {
    await axios.post(`/api/tasks/${props.task.id}/stop`)
    toast.success('任务已暂停')
  } catch (error) {
    console.error(error)
    toast.error('暂停任务失败')
  } finally {
    stopLoading.value = false
  }
}

const openEditDialog = () => {
  if (editLoading.value) return
  editDialogVisible.value = true
}

const confirmDelete = async () => {
  deleteLoading.value = true
  try {
    await axios.delete(`/api/tasks/${props.task.id}`, {
      data: {
        delete_cache: deleteCacheChecked.value,
        delete_downloaded_files: deleteMergedChecked.value,
      },
    })
    toast.success('任务已删除')
    deleteDialogVisible.value = false
  } catch (error) {
    console.error(error)
    toast.error('删除任务失败')
  } finally {
    deleteLoading.value = false
  }
}

const statusLabelMap: Record<TaskStatus, string> = {
  pending: '等待中',
  downloading: '下载中',
  merging: '合并中',
  completed: '已完成',
  failed: '失败',
  stopped: '已暂停',
}

const statusTagType = computed(() => {
  switch (props.task.status) {
    case 'pending':
      return 'info'
    case 'downloading':
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

const statusLabel = computed(() => {
  return statusLabelMap[props.task.status]
})

const progressValue = computed(() => {
  const progress = Number(props.task.progress) || 0
  return Math.min(100, Math.max(0, progress))
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

const downloadedSizeText = computed(() => {
  return formatBytes(Math.max(0, props.task.total_size || 0))
})

const speedText = computed(() => {
  const speed = Math.max(0, props.task.speed || 0)
  if (speed === 0) {
    return '--'
  }
  return `${formatBytes(speed)}/s`
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
</script>

<style scoped>
.action-icon {
  font-size: 18px;
  line-height: 1;
  padding: 4px;
  border-radius: 6px;
  cursor: pointer;
  user-select: none;
  transition: opacity 0.15s ease;
}
.action-icon:focus-visible {
  outline: 2px solid var(--color-brand-500, #2563eb);
  outline-offset: 2px;
}
.action-icon:hover:not(.is-loading) {
  opacity: 0.88;
}
.action-icon.is-loading {
  opacity: 0.45;
  cursor: wait;
  pointer-events: none;
}
.action-icon--start {
  color: #16a34a;
}
.action-icon--pause {
  color: #d97706;
}
.action-icon--edit {
  color: #2563eb;
}
.action-icon--delete {
  color: #dc2626;
}
</style>

<template>
  <div class="download-item">
    <div class="item-header">
      <div class="task-name" :title="task.name">{{ task.name }}</div>
      <div class="header-right">
        <div class="header-actions">
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
        <el-tag :type="statusTagType" effect="dark">{{ statusLabel }}</el-tag>
      </div>
    </div>

    <div class="item-meta">
      <div class="item-meta-start">
        <el-icon
          class="task-info-trigger"
          :size="18"
          aria-label="查看创建任务时的信息"
          role="button"
          tabindex="0"
          @click="taskInfoDialogVisible = true"
          @keydown.enter.prevent="taskInfoDialogVisible = true"
          @keydown.space.prevent="taskInfoDialogVisible = true"
        >
          <InfoFilled />
        </el-icon>
        <span>已下载 {{ downloadedSizeText }}</span>
        <span class="item-meta-duration">时长 {{ durationDisplay }}</span>
      </div>
      <span>速度 {{ speedText }}</span>
    </div>

    <el-progress :percentage="progressValue" :stroke-width="10" :show-text="false" />

    <div class="item-footer">
      <span>进度 {{ progressValue.toFixed(1) }}%</span>
      <span class="item-footer-segments">
        <span>片段：</span>
        <span class="task-info-value task-info-value--segments">
          <el-text type="success" size="small">{{ task.downloaded_segments }}</el-text>
          <span class="task-info-sep">/</span>
          <el-text type="danger" size="small">{{ task.failed_segments }}</el-text>
          <span class="task-info-sep">/</span>
          <el-text size="small">{{ totalSegmentsDisplay }}</el-text>
        </span>
      </span>
    </div>

    <TaskInfoDialog v-model="taskInfoDialogVisible" :task="task" />
    <EditTaskDialog v-model="editDialogVisible" :task="task" />

    <el-dialog
      v-model="deleteDialogVisible"
      title="删除任务"
      width="440px"
      destroy-on-close
      append-to-body
      @closed="resetDeleteOptions"
    >
      <p class="delete-hint">请选择是否同时删除本地文件（删除后不可恢复）。</p>
      <div class="delete-checks">
        <el-checkbox v-model="deleteCacheChecked">删除缓存片段（.cache 目录）</el-checkbox>
        <el-checkbox v-model="deleteMergedChecked">删除合并后的视频及任务下载目录</el-checkbox>
      </div>
      <template #footer>
        <el-button @click="deleteDialogVisible = false">取消</el-button>
        <el-button type="danger" :loading="deleteLoading" @click="confirmDelete"
          >确定删除</el-button
        >
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import axios from 'axios'
import { InfoFilled } from '@element-plus/icons-vue'
import TaskInfoDialog from '@/components/TaskInfoDialog.vue'
import EditTaskDialog from '@/components/EditTaskDialog.vue'
import type { TaskModel, TaskStatus } from '@/types/models'
import { ElMessage } from 'element-plus'

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

const handleStart = async () => {
  if (startLoading.value) return
  startLoading.value = true
  try {
    await axios.post(`/api/tasks/${props.task.id}/start`)
    ElMessage.success('任务已加入队列')
  } catch (error) {
    console.error(error)
    ElMessage.error('开始任务失败')
  } finally {
    startLoading.value = false
  }
}

const handleStop = async () => {
  if (stopLoading.value) return
  stopLoading.value = true
  try {
    await axios.post(`/api/tasks/${props.task.id}/stop`)
    ElMessage.success('任务已暂停')
  } catch (error) {
    console.error(error)
    ElMessage.error('暂停任务失败')
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
    ElMessage.success('任务已删除')
    deleteDialogVisible.value = false
  } catch (error) {
    console.error(error)
    ElMessage.error('删除任务失败')
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

<style scoped lang="scss">
.download-item {
  border: 1px solid var(--el-border-color-light);
  border-radius: 10px;
  padding: 14px 16px;
  background: var(--el-fill-color-blank);
  box-shadow: 0 3px 10px rgba(0, 0, 0, 0.04);

  .item-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    margin-bottom: 10px;

    .task-name {
      font-size: 16px;
      color: #32a637;
      font-weight: 600;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .header-right {
      display: flex;
      align-items: center;
      gap: 8px;
      flex-shrink: 0;

      .header-actions {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 4px;

        .action-icon {
          font-size: 18px;
          line-height: 1;
          padding: 4px;
          border-radius: 6px;
          cursor: pointer;
          user-select: none;
          transition: opacity 0.15s ease;

          &:focus-visible {
            outline: 2px solid var(--el-color-primary);
            outline-offset: 2px;
          }

          &:hover:not(.is-loading) {
            opacity: 0.88;
          }

          &.is-loading {
            opacity: 0.45;
            cursor: wait;
            pointer-events: none;
          }

          &.action-icon--start {
            color: var(--el-color-success);
          }

          &.action-icon--pause {
            color: var(--el-color-warning);
          }

          &.action-icon--edit {
            color: var(--el-color-primary);
          }

          &.action-icon--delete {
            color: var(--el-color-danger);
          }
        }
      }
    }
  }

  .item-meta {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    font-size: 12px;
    color: var(--el-text-color-secondary);
    margin-bottom: 10px;

    .item-meta-start {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      min-width: 0;
      flex-wrap: wrap;
    }

    .item-meta-duration {
      padding-left: 8px;
      margin-left: 2px;
      border-left: 1px solid var(--el-border-color-lighter);
      white-space: nowrap;
    }

    .task-info-trigger {
      flex-shrink: 0;
      cursor: pointer;
      color: var(--el-color-primary);
      transition: opacity 0.15s ease;

      &:hover {
        opacity: 0.85;
      }

      &:focus-visible {
        outline: 2px solid var(--el-color-primary);
        outline-offset: 2px;
        border-radius: 4px;
      }
    }
  }

  .item-footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    margin-top: 8px;
    font-size: 12px;
    color: var(--el-text-color-secondary);

    .item-footer-segments {
      display: inline-flex;
      align-items: center;
      flex-wrap: wrap;
      gap: 0;
      min-width: 0;
    }

    .task-info-value--segments {
      display: inline-flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 4px;
    }

    .task-info-sep {
      color: var(--el-text-color-secondary);
      user-select: none;
    }
  }
}

.delete-hint {
  margin: 0 0 12px;
  font-size: 13px;
  color: var(--el-text-color-regular);
}

.delete-checks {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
</style>

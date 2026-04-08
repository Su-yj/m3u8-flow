<template>
  <el-card class="completed-view" v-loading="loading">
    <template #header>
      <div class="card-header">
        <div class="header-title">
          <span>已完成</span>
          <el-tag type="success" effect="plain">共 {{ total }} 条</el-tag>
        </div>
        <div class="header-actions">
          <el-button
            type="danger"
            plain
            :icon="Delete"
            :disabled="loading || selection.length === 0"
            aria-label="删除所选"
            @click="openBulkDelete"
          >
            删除所选
          </el-button>
          <el-button
            type="primary"
            plain
            :icon="RefreshRight"
            :loading="loading"
            :disabled="loading"
            aria-label="刷新"
            @click="fetchTasks"
          >
            刷新
          </el-button>
        </div>
      </div>
    </template>

    <div v-if="!loading && tasks.length === 0" class="empty-wrap">
      <el-empty description="暂无已完成任务" />
    </div>

    <div v-else-if="tasks.length > 0" class="table-wrap">
      <el-table
        :data="tasks"
        class="completed-table"
        row-key="id"
        stripe
        @selection-change="onSelectionChange"
      >
        <el-table-column type="selection" align="center" width="48" />
        <el-table-column label="任务名称" min-width="300">
          <template #default="{ row }">
            <div class="task-name-cell">
              <div class="task-name-title">{{ row.name }}</div>
              <div class="task-name-url" :title="row.m3u8_url">{{ row.m3u8_url }}</div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="文件大小" width="150" align="left">
          <template #default="{ row }">
            {{ formatBytes(row.total_size) }}
          </template>
        </el-table-column>
        <el-table-column label="开始时间" width="180" align="left">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="结束时间" width="180" align="left">
          <template #default="{ row }">
            {{ formatDateTime(row.updated_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" align="center">
          <template #default="{ row }">
            <div class="action-cell">
              <i
                class="iconfont icon-play action-icon action-icon--play"
                role="button"
                tabindex="0"
                :class="{ 'is-loading': startLoadingId === row.id }"
                title="重新下载"
                aria-label="重新下载"
                @click="handleStart(row)"
                @keydown.enter.prevent="handleStart(row)"
                @keydown.space.prevent="handleStart(row)"
              />
              <el-icon
                class="action-icon action-icon--info"
                :size="18"
                role="button"
                tabindex="0"
                title="任务信息"
                aria-label="任务信息"
                @click="openTaskInfo(row)"
                @keydown.enter.prevent="openTaskInfo(row)"
              >
                <InfoFilled />
              </el-icon>
              <el-icon
                class="action-icon action-icon--delete"
                :size="18"
                role="button"
                tabindex="0"
                title="删除"
                aria-label="删除"
                :class="{ 'is-loading': deleteLoadingId === row.id }"
                @click="openDelete(row)"
                @keydown.enter.prevent="openDelete(row)"
              >
                <Delete />
              </el-icon>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-bar">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          background
          @current-change="fetchTasks"
          @size-change="handleSizeChange"
        />
      </div>
    </div>

    <TaskInfoDialog v-if="infoTask" v-model="taskInfoVisible" :task="infoTask" />

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
        <el-button type="danger" :loading="deleteSubmitting" @click="confirmDelete"
          >确定删除</el-button
        >
      </template>
    </el-dialog>

    <el-dialog
      v-model="bulkDeleteDialogVisible"
      title="批量删除任务"
      width="440px"
      destroy-on-close
      append-to-body
      @closed="resetBulkDeleteOptions"
    >
      <p class="delete-hint">
        将删除已勾选的 {{ selection.length }} 个任务。请选择是否同时删除本地文件（删除后不可恢复）。
      </p>
      <div class="delete-checks">
        <el-checkbox v-model="deleteCacheChecked">删除缓存片段（.cache 目录）</el-checkbox>
        <el-checkbox v-model="deleteMergedChecked">删除合并后的视频及任务下载目录</el-checkbox>
      </div>
      <template #footer>
        <el-button @click="bulkDeleteDialogVisible = false">取消</el-button>
        <el-button type="danger" :loading="bulkDeleteSubmitting" @click="confirmBulkDelete">
          确定删除
        </el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import axios from 'axios'
import { Delete, InfoFilled, RefreshRight } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import TaskInfoDialog from '@/components/TaskInfoDialog.vue'
import type { TaskModel } from '@/types/models'
import type { ApiPaginationResponse } from '@/types/api'

const tasks = ref<TaskModel[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const loading = ref(false)

const startLoadingId = ref<string | null>(null)
const deleteLoadingId = ref<string | null>(null)
const deleteSubmitting = ref(false)
const bulkDeleteDialogVisible = ref(false)
const bulkDeleteSubmitting = ref(false)

const taskInfoVisible = ref(false)
const infoTask = ref<TaskModel | null>(null)

const deleteDialogVisible = ref(false)
const deleteTarget = ref<TaskModel | null>(null)
const deleteCacheChecked = ref(true)
const deleteMergedChecked = ref(true)

const selection = ref<TaskModel[]>([])

const onSelectionChange = (rows: TaskModel[]) => {
  selection.value = rows
}

const formatBytes = (bytes: number): string => {
  const n = Math.max(0, bytes || 0)
  if (n < 1024) {
    return `${n} B`
  }
  if (n < 1024 * 1024) {
    return `${(n / 1024).toFixed(2)} KB`
  }
  if (n < 1024 * 1024 * 1024) {
    return `${(n / (1024 * 1024)).toFixed(2)} MB`
  }
  return `${(n / (1024 * 1024 * 1024)).toFixed(2)} GB`
}

const formatDateTime = (iso: string): string => {
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) {
    return '—'
  }
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const h = String(d.getHours()).padStart(2, '0')
  const min = String(d.getMinutes()).padStart(2, '0')
  const s = String(d.getSeconds()).padStart(2, '0')
  return `${y}/${m}/${day} ${h}:${min}:${s}`
}

const fetchTasks = async () => {
  loading.value = true
  try {
    const response = await axios.get<ApiPaginationResponse<TaskModel>>('/api/tasks/', {
      params: {
        status: 'completed',
        ordering: '-updated_at',
        page: page.value,
        page_size: pageSize.value,
      },
    })
    if (response.data.code !== 0) {
      ElMessage.error(response.data.message || '加载失败')
      return
    }
    tasks.value = response.data.data ?? []
    total.value = response.data.total ?? 0
  } catch (error) {
    console.error(error)
    ElMessage.error('加载已完成任务失败')
  } finally {
    loading.value = false
  }
}

const handleSizeChange = () => {
  page.value = 1
  fetchTasks()
}

const handleStart = async (row: TaskModel) => {
  if (startLoadingId.value) return
  startLoadingId.value = row.id
  try {
    await axios.post(`/api/tasks/${row.id}/restart`)
    ElMessage.success('任务已加入队列')
    await fetchTasks()
  } catch (error) {
    console.error(error)
    ElMessage.error('开始任务失败')
  } finally {
    startLoadingId.value = null
  }
}

const openTaskInfo = (row: TaskModel) => {
  infoTask.value = row
  taskInfoVisible.value = true
}

const resetDeleteCheckboxes = () => {
  deleteCacheChecked.value = true
  deleteMergedChecked.value = true
}

const resetDeleteOptions = () => {
  resetDeleteCheckboxes()
  deleteTarget.value = null
}

const resetBulkDeleteOptions = () => {
  resetDeleteCheckboxes()
}

const openBulkDelete = () => {
  if (loading.value || deleteLoadingId.value || deleteSubmitting.value || bulkDeleteSubmitting.value) return
  if (selection.value.length === 0) {
    ElMessage.warning('请先勾选要删除的任务')
    return
  }
  resetDeleteCheckboxes()
  bulkDeleteDialogVisible.value = true
}

const openDelete = (row: TaskModel) => {
  if (deleteLoadingId.value || deleteSubmitting.value) return
  resetDeleteCheckboxes()
  deleteTarget.value = row
  deleteDialogVisible.value = true
}

const confirmDelete = async () => {
  const row = deleteTarget.value
  if (!row) return
  deleteSubmitting.value = true
  deleteLoadingId.value = row.id
  try {
    await axios.delete(`/api/tasks/${row.id}`, {
      data: {
        delete_cache: deleteCacheChecked.value,
        delete_downloaded_files: deleteMergedChecked.value,
      },
    })
    ElMessage.success('任务已删除')
    deleteDialogVisible.value = false
    await fetchTasks()
  } catch (error) {
    console.error(error)
    ElMessage.error('删除任务失败')
  } finally {
    deleteSubmitting.value = false
    deleteLoadingId.value = null
  }
}

const confirmBulkDelete = async () => {
  if (bulkDeleteSubmitting.value) return
  const rows = [...selection.value]
  if (rows.length === 0) {
    ElMessage.warning('请先勾选要删除的任务')
    return
  }

  bulkDeleteSubmitting.value = true
  try {
    const results = await Promise.allSettled(
      rows.map((row) =>
        axios.delete(`/api/tasks/${row.id}`, {
          data: {
            delete_cache: deleteCacheChecked.value,
            delete_downloaded_files: deleteMergedChecked.value,
          },
        }),
      ),
    )
    const failCount = results.filter((r) => r.status === 'rejected').length
    if (failCount > 0) {
      ElMessage.error(`删除完成：成功 ${rows.length - failCount}，失败 ${failCount}`)
    } else {
      ElMessage.success(`已删除 ${rows.length} 个任务`)
    }
    bulkDeleteDialogVisible.value = false
    await fetchTasks()
    selection.value = []
  } catch (error) {
    console.error(error)
    ElMessage.error('批量删除失败')
  } finally {
    bulkDeleteSubmitting.value = false
  }
}

onMounted(() => {
  fetchTasks()
})
</script>

<style scoped lang="scss">
.completed-view {
  box-sizing: border-box;
  height: 100%;
  width: 100%;

  .card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .header-title {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .header-actions {
    display: inline-flex;
    align-items: center;
    gap: 8px;
  }

  .empty-wrap {
    padding: 32px 0;
  }

  .table-wrap {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .completed-table {
    width: 100%;

    :deep(.el-table__header-wrapper th.el-table__cell) {
      background: var(--el-fill-color-light);
      color: var(--el-text-color-secondary);
      font-weight: 600;
    }

    :deep(.el-table__header-wrapper th.el-table__cell),
    :deep(.el-table__body-wrapper td.el-table__cell) {
      padding: 14px 12px;
    }
  }

  .action-cell {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
  }

  .action-icon {
    cursor: pointer;
    user-select: none;
    transition: opacity 0.15s ease;
    line-height: 1;

    &:focus-visible {
      outline: 2px solid var(--el-color-primary);
      outline-offset: 2px;
      border-radius: 4px;
    }

    &:hover:not(.is-loading) {
      opacity: 0.88;
    }

    &.is-loading {
      opacity: 0.45;
      cursor: wait;
      pointer-events: none;
    }

    &.action-icon--play {
      font-size: 18px;
      padding: 2px;
      color: var(--el-color-success);
    }

    &.action-icon--info {
      color: var(--el-color-primary);
    }

    &.action-icon--delete {
      color: var(--el-color-danger);
    }
  }

  .task-name-cell {
    min-width: 0;
  }

  .task-name-title {
    font-weight: 600;
    font-size: 14px;
    color: var(--el-text-color-primary);
    line-height: 1.45;
    word-break: break-all;
  }

  .task-name-url {
    margin-top: 4px;
    font-size: 12px;
    color: var(--el-text-color-secondary);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .pagination-bar {
    display: flex;
    justify-content: flex-end;
    flex-wrap: wrap;
    gap: 8px;
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

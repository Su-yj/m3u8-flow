<template>
  <UiCard class="h-full">
    <template #header>
      <div class="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div class="flex flex-wrap items-center gap-2">
          <span class="text-base font-semibold">已完成</span>
          <UiTag variant="success" effect="plain">共 {{ total }} 条</UiTag>
        </div>
        <div class="flex flex-wrap gap-2">
          <UiButton
            variant="danger"
            class="border border-red-300 dark:border-red-800"
            :disabled="loading || selection.length === 0"
            aria-label="删除所选"
            @click="openBulkDelete"
          >
            <Trash2 class="size-4" />
            删除所选
          </UiButton>
          <UiButton
            variant="primary"
            :loading="loading"
            :disabled="loading"
            aria-label="刷新"
            @click="fetchTasks"
          >
            <RefreshCw class="size-4" />
            刷新
          </UiButton>
        </div>
      </div>
    </template>

    <div class="relative min-h-[200px]">
      <UiLoadingOverlay :show="loading" />

      <div v-if="!loading && tasks.length === 0" class="py-8">
        <UiEmpty description="暂无已完成任务" />
      </div>

      <div v-else-if="tasks.length > 0" class="flex flex-col gap-4">
        <div class="overflow-x-auto rounded-lg border border-[var(--color-border)]">
          <table class="completed-table w-full border-collapse text-sm">
            <thead>
              <tr class="border-b border-[var(--color-border)] bg-[var(--color-surface-muted)]">
                <th class="w-10 px-2 py-3 text-center">
                  <input
                    ref="selectAllRef"
                    type="checkbox"
                    class="size-4 rounded border-[var(--color-border)]"
                    :checked="allSelected"
                    aria-label="全选当前页"
                    @change="toggleSelectAll(($event.target as HTMLInputElement).checked)"
                  />
                </th>
                <th
                  class="min-w-32 px-3 py-3 text-center font-semibold text-[var(--color-text-muted)]"
                >
                  任务名称
                </th>
                <th
                  class="hidden min-w-64 px-3 py-3 text-center font-semibold text-[var(--color-text-muted)] md:table-cell"
                >
                  下载链接
                </th>
                <th
                  class="hidden w-36 px-3 py-3 text-center font-semibold text-[var(--color-text-muted)] md:table-cell"
                >
                  文件大小
                </th>
                <th
                  class="hidden w-44 px-3 py-3 text-center font-semibold text-[var(--color-text-muted)] md:table-cell"
                >
                  开始时间
                </th>
                <th
                  class="hidden w-44 px-3 py-3 text-center font-semibold text-[var(--color-text-muted)] md:table-cell"
                >
                  结束时间
                </th>
                <th class="w-32 px-3 py-3 text-center font-semibold text-[var(--color-text-muted)]">
                  操作
                </th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="row in tasks"
                :key="row.id"
                class="border-b border-[var(--color-border)] last:border-0 odd:bg-[var(--color-surface)] even:bg-[var(--color-surface-muted)]/40"
              >
                <td class="px-2 py-3 text-center align-middle">
                  <input
                    type="checkbox"
                    class="size-4 rounded border-[var(--color-border)]"
                    :checked="isRowSelected(row)"
                    @change="toggleRow(row, ($event.target as HTMLInputElement).checked)"
                  />
                </td>
                <td class="px-3 py-3 text-center align-middle whitespace-nowrap">
                  <div class="min-w-0">
                    <div class="break-all font-semibold text-center text-[var(--color-text)]">
                      {{ row.name }}
                    </div>
                  </div>
                </td>
                <td
                  class="hidden px-3 py-3 text-center align-middle whitespace-normal break-all text-xs md:table-cell"
                >
                  {{ row.m3u8_url }}
                </td>
                <td
                  class="hidden px-3 py-3 text-center align-middle whitespace-nowrap md:table-cell"
                >
                  {{ formatBytes(row.total_size) }}
                </td>
                <td
                  class="hidden px-3 py-3 text-center align-middle whitespace-nowrap md:table-cell"
                >
                  {{ formatDateTime(row.created_at) }}
                </td>
                <td
                  class="hidden px-3 py-3 text-center align-middle whitespace-nowrap md:table-cell"
                >
                  {{ formatDateTime(row.updated_at) }}
                </td>
                <td class="px-3 py-3 text-center align-middle">
                  <div class="inline-flex items-center justify-center gap-1">
                    <button
                      type="button"
                      class="iconfont icon-play action-icon text-emerald-600 dark:text-emerald-400"
                      :class="{ 'is-loading': startLoadingId === row.id }"
                      title="重新下载"
                      aria-label="重新下载"
                      @click="handleStart(row)"
                    />
                    <button
                      type="button"
                      class="cursor-pointer rounded p-1 text-brand-600 hover:bg-brand-500/10 dark:text-brand-400"
                      title="任务信息"
                      aria-label="任务信息"
                      @click="openTaskInfo(row)"
                    >
                      <Info class="size-[18px]" />
                    </button>
                    <button
                      type="button"
                      class="cursor-pointer rounded p-1 text-red-600 hover:bg-red-500/10 dark:text-red-400"
                      :class="{ 'is-loading': deleteLoadingId === row.id }"
                      title="删除"
                      aria-label="删除"
                      @click="openDelete(row)"
                    >
                      <Trash2 class="size-[18px]" />
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <UiPagination v-model:current-page="page" v-model:page-size="pageSize" :total="total" />
      </div>
    </div>

    <TaskInfoDialog v-if="infoTask" v-model="taskInfoVisible" :task="infoTask" />

    <UiModal
      v-model="deleteDialogVisible"
      title="删除任务"
      width-class="w-full max-w-[440px]"
      @update:model-value="onDeleteDialogToggle"
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
        <UiButton variant="danger" :loading="deleteSubmitting" @click="confirmDelete"
          >确定删除</UiButton
        >
      </template>
    </UiModal>

    <UiModal
      v-model="bulkDeleteDialogVisible"
      title="批量删除任务"
      width-class="w-full max-w-[440px]"
      @update:model-value="onBulkDialogToggle"
    >
      <p class="mb-3 text-sm text-[var(--color-text-muted)]">
        将删除已勾选的 {{ selection.length }} 个任务。请选择是否同时删除本地文件（删除后不可恢复）。
      </p>
      <div class="flex flex-col gap-2">
        <UiCheckbox v-model="deleteCacheChecked">删除缓存片段（.cache 目录）</UiCheckbox>
        <UiCheckbox v-model="deleteMergedChecked">删除合并后的视频及任务下载目录</UiCheckbox>
      </div>
      <template #footer>
        <UiButton variant="secondary" @click="bulkDeleteDialogVisible = false">取消</UiButton>
        <UiButton variant="danger" :loading="bulkDeleteSubmitting" @click="confirmBulkDelete"
          >确定删除</UiButton
        >
      </template>
    </UiModal>
  </UiCard>
</template>

<script setup lang="ts">
import { Info, RefreshCw, Trash2 } from 'lucide-vue-next'
import { computed, ref, watch } from 'vue'
import axios from 'axios'

import TaskInfoDialog from '@/components/TaskInfoDialog.vue'
import UiButton from '@/components/ui/UiButton.vue'
import UiCard from '@/components/ui/UiCard.vue'
import UiCheckbox from '@/components/ui/UiCheckbox.vue'
import UiEmpty from '@/components/ui/UiEmpty.vue'
import UiLoadingOverlay from '@/components/ui/UiLoadingOverlay.vue'
import UiModal from '@/components/ui/UiModal.vue'
import UiPagination from '@/components/ui/UiPagination.vue'
import UiTag from '@/components/ui/UiTag.vue'
import type { ApiPaginationResponse } from '@/types/api'
import type { TaskModel } from '@/types/models'
import { toast } from '@/utils/toast'

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
const selectAllRef = ref<HTMLInputElement | null>(null)

const allSelected = computed(
  () => tasks.value.length > 0 && selection.value.length === tasks.value.length,
)
const someSelected = computed(
  () => selection.value.length > 0 && selection.value.length < tasks.value.length,
)

watch([allSelected, someSelected], () => {
  const el = selectAllRef.value
  if (el) {
    el.indeterminate = someSelected.value && !allSelected.value
  }
})

function isRowSelected(row: TaskModel) {
  return selection.value.some((s) => s.id === row.id)
}

function toggleRow(row: TaskModel, checked: boolean) {
  if (checked) {
    if (!isRowSelected(row)) {
      selection.value = [...selection.value, row]
    }
  } else {
    selection.value = selection.value.filter((s) => s.id !== row.id)
  }
}

function toggleSelectAll(checked: boolean) {
  if (checked) {
    selection.value = [...tasks.value]
  } else {
    selection.value = []
  }
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
      toast.error(response.data.message || '加载失败')
      return
    }
    tasks.value = response.data.data ?? []
    total.value = response.data.total ?? 0
    selection.value = selection.value.filter((s) => tasks.value.some((t) => t.id === s.id))
  } catch (error) {
    console.error(error)
    toast.error('加载已完成任务失败')
  } finally {
    loading.value = false
  }
}

const handleStart = async (row: TaskModel) => {
  if (startLoadingId.value) return
  startLoadingId.value = row.id
  try {
    await axios.post(`/api/tasks/${row.id}/restart`)
    toast.success('任务已加入队列')
    await fetchTasks()
  } catch (error) {
    console.error(error)
    toast.error('开始任务失败')
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

function onDeleteDialogToggle(open: boolean) {
  if (!open) {
    resetDeleteOptions()
  }
}

function onBulkDialogToggle(open: boolean) {
  if (!open) {
    resetDeleteCheckboxes()
  }
}

const openBulkDelete = () => {
  if (
    loading.value ||
    deleteLoadingId.value ||
    deleteSubmitting.value ||
    bulkDeleteSubmitting.value
  )
    return
  if (selection.value.length === 0) {
    toast.warning('请先勾选要删除的任务')
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
    toast.success('任务已删除')
    deleteDialogVisible.value = false
    await fetchTasks()
  } catch (error) {
    console.error(error)
    toast.error('删除任务失败')
  } finally {
    deleteSubmitting.value = false
    deleteLoadingId.value = null
  }
}

const confirmBulkDelete = async () => {
  if (bulkDeleteSubmitting.value) return
  const rows = [...selection.value]
  if (rows.length === 0) {
    toast.warning('请先勾选要删除的任务')
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
      toast.error(`删除完成：成功 ${rows.length - failCount}，失败 ${failCount}`)
    } else {
      toast.success(`已删除 ${rows.length} 个任务`)
    }
    bulkDeleteDialogVisible.value = false
    await fetchTasks()
    selection.value = []
  } catch (error) {
    console.error(error)
    toast.error('批量删除失败')
  } finally {
    bulkDeleteSubmitting.value = false
  }
}

watch(
  [page, pageSize],
  () => {
    void fetchTasks()
  },
  { immediate: true },
)
</script>

<style scoped>
.action-icon {
  cursor: pointer;
  font-size: 18px;
  line-height: 1;
  padding: 4px;
  border-radius: 6px;
  user-select: none;
  transition: opacity 0.15s ease;
  background: transparent;
  border: none;
}
.action-icon:hover:not(.is-loading) {
  opacity: 0.88;
}
.action-icon.is-loading {
  opacity: 0.45;
  cursor: wait;
  pointer-events: none;
}
.action-icon:focus-visible {
  outline: 2px solid var(--color-brand-500, #2563eb);
  outline-offset: 2px;
}
</style>

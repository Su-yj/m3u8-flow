<template>
  <div class="w-full">
    <div class="mb-2">
      <UiSegmented
        v-model="mode"
        :options="[
          { label: '表格', value: 'table' },
          { label: '文本', value: 'text' },
        ]"
      />
    </div>

    <div
      v-show="mode === 'table'"
      class="overflow-x-auto rounded-lg border border-[var(--color-border)]"
    >
      <table class="w-full min-w-[400px] border-collapse text-sm">
        <thead>
          <tr class="border-b border-[var(--color-border)] bg-[var(--color-surface-muted)]">
            <th class="px-2 py-2 text-left font-semibold">键</th>
            <th class="px-2 py-2 text-left font-semibold">值</th>
            <th class="w-28 px-2 py-2 text-center font-semibold">
              <div class="flex items-center justify-center gap-2">
                <span>操作</span>
                <UiButton variant="ghost" size="sm" class="h-7 px-1 text-xs" @click="openAddDialog"
                  >添加</UiButton
                >
              </div>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="rows.length === 0">
            <td colspan="3" class="px-2 py-6 text-center text-[var(--color-text-muted)]">
              暂无请求头
            </td>
          </tr>
          <tr
            v-for="(row, $index) in rows"
            :key="$index"
            class="border-b border-[var(--color-border)] last:border-0"
          >
            <td class="max-w-[180px] px-2 py-1.5 align-top break-all">{{ row.key }}</td>
            <td class="px-2 py-1.5 align-top break-all">{{ row.value }}</td>
            <td class="px-2 py-1.5 text-center whitespace-nowrap">
              <UiButton
                variant="ghost"
                size="sm"
                class="h-7 px-1 text-amber-700 dark:text-amber-300"
                @click="openEditDialog($index)"
              >
                编辑
              </UiButton>
              <UiButton
                variant="ghost"
                size="sm"
                class="h-7 px-1 text-red-600 dark:text-red-400"
                @click="removeRow($index)"
              >
                删除
              </UiButton>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-show="mode === 'text'" class="w-full">
      <UiTextarea
        v-model="textContent"
        :rows="8"
        placeholder="每行一条，格式：键: 值（以第一个冒号分隔键与值）"
        @blur="syncTextToRows"
      />
    </div>

    <UiModal
      v-model="rowDialogVisible"
      :title="editingIndex === null ? '添加请求头' : '编辑请求头'"
      width-class="w-full max-w-[480px]"
      @update:model-value="onRowDialogClose"
    >
      <form class="flex flex-col gap-3" @submit.prevent="confirmRowDialog">
        <UiFormRow label="键">
          <UiInput v-model="rowDialogForm.key" placeholder="例如：Authorization" />
        </UiFormRow>
        <UiFormRow label="值">
          <UiTextarea v-model="rowDialogForm.value" :rows="4" placeholder="例如：Bearer xxx" />
        </UiFormRow>
      </form>
      <template #footer>
        <UiButton variant="secondary" @click="rowDialogVisible = false">取消</UiButton>
        <UiButton variant="primary" @click="confirmRowDialog">确定</UiButton>
      </template>
    </UiModal>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'

import UiButton from '@/components/ui/UiButton.vue'
import UiFormRow from '@/components/ui/UiFormRow.vue'
import UiInput from '@/components/ui/UiInput.vue'
import UiModal from '@/components/ui/UiModal.vue'
import UiSegmented from '@/components/ui/UiSegmented.vue'
import UiTextarea from '@/components/ui/UiTextarea.vue'
import { toast } from '@/utils/toast'

type HeaderRow = { key: string; value: string }

const props = defineProps<{
  modelValue: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const mode = ref<'table' | 'text'>('table')
const rows = ref<HeaderRow[]>([])
const textContent = ref('')

const rowDialogVisible = ref(false)
const editingIndex = ref<number | null>(null)
const rowDialogForm = ref<HeaderRow>({ key: '', value: '' })

function rowsFromJsonString(s: string): HeaderRow[] {
  if (!s?.trim()) {
    return []
  }
  try {
    const o = JSON.parse(s) as unknown
    if (typeof o !== 'object' || o === null || Array.isArray(o)) {
      return []
    }
    return Object.entries(o as Record<string, unknown>).map(([key, val]) => ({
      key,
      value: val === undefined || val === null ? '' : String(val),
    }))
  } catch {
    return []
  }
}

function jsonStringFromRows(list: HeaderRow[]): string {
  const o: Record<string, string> = {}
  for (const row of list) {
    const k = row.key.trim()
    if (k) {
      o[k] = row.value
    }
  }
  return Object.keys(o).length ? JSON.stringify(o) : ''
}

function canonJsonString(s: string): string {
  if (!s.trim()) {
    return ''
  }
  try {
    return JSON.stringify(JSON.parse(s))
  } catch {
    return s
  }
}

function serializeRowsToText(list: HeaderRow[]): string {
  return list
    .filter((r) => r.key.trim() !== '' || r.value !== '')
    .map((r) => `${r.key}: ${r.value}`)
    .join('\n')
}

function parseTextToRows(text: string): HeaderRow[] {
  const lines = text.split(/\r?\n/)
  const out: HeaderRow[] = []
  for (const line of lines) {
    const t = line.trimEnd()
    if (!t.trim()) {
      continue
    }
    const idx = t.indexOf(':')
    if (idx === -1) {
      out.push({ key: t.trim(), value: '' })
      continue
    }
    out.push({
      key: t.slice(0, idx).trim(),
      value: t.slice(idx + 1).trim(),
    })
  }
  return out
}

watch(
  () => props.modelValue,
  (v) => {
    if (canonJsonString(jsonStringFromRows(rows.value)) === canonJsonString(v)) {
      return
    }
    const next = rowsFromJsonString(v)
    rows.value = next
    if (mode.value === 'text') {
      textContent.value = serializeRowsToText(next)
    }
  },
  { immediate: true },
)

watch(
  rows,
  () => {
    const out = jsonStringFromRows(rows.value)
    if (canonJsonString(out) === canonJsonString(props.modelValue)) {
      return
    }
    emit('update:modelValue', out)
  },
  { deep: true },
)

watch(mode, (m, prev) => {
  if (m === 'text') {
    textContent.value = serializeRowsToText(rows.value)
  } else if (prev === 'text' && m === 'table') {
    rows.value = parseTextToRows(textContent.value)
  }
})

function syncTextToRows() {
  if (mode.value !== 'text') {
    return
  }
  rows.value = parseTextToRows(textContent.value)
}

function openAddDialog() {
  editingIndex.value = null
  rowDialogForm.value = { key: '', value: '' }
  rowDialogVisible.value = true
}

function openEditDialog(index: number) {
  const row = rows.value[index]
  if (!row) {
    return
  }
  editingIndex.value = index
  rowDialogForm.value = { key: row.key, value: row.value }
  rowDialogVisible.value = true
}

function removeRow(index: number) {
  rows.value.splice(index, 1)
}

function onRowDialogClose(open: boolean) {
  if (!open) {
    editingIndex.value = null
    rowDialogForm.value = { key: '', value: '' }
  }
}

function confirmRowDialog() {
  const key = rowDialogForm.value.key.trim()
  if (!key) {
    toast.warning('请输入键')
    return
  }
  const entry: HeaderRow = { key, value: rowDialogForm.value.value }
  if (editingIndex.value === null) {
    rows.value.push(entry)
  } else {
    rows.value.splice(editingIndex.value, 1, entry)
  }
  rowDialogVisible.value = false
}

function flush() {
  if (mode.value === 'text') {
    rows.value = parseTextToRows(textContent.value)
  }
}

defineExpose({ flush })
</script>

<template>
  <div class="headers-editor">
    <div class="headers-editor-toolbar">
      <el-radio-group v-model="mode" size="small">
        <el-radio-button label="table">表格</el-radio-button>
        <el-radio-button label="text">文本</el-radio-button>
      </el-radio-group>
    </div>

    <div v-show="mode === 'table'" class="headers-editor-table-wrap">
      <el-table
        :data="rows"
        border
        size="small"
        class="headers-editor-table"
        empty-text="暂无请求头"
      >
        <el-table-column prop="key" label="键" min-width="140" show-overflow-tooltip />
        <el-table-column prop="value" label="值" min-width="200" show-overflow-tooltip />
        <el-table-column width="100" align="center">
          <template #header>
            <div class="headers-editor-op-header">
              <span style="vertical-align: middle; margin-right: 8px">操作</span>
              <el-button type="primary" link size="small" @click="openAddDialog">添加</el-button>
            </div>
          </template>
          <template #default="{ $index }">
            <el-button type="warning" link size="small" @click="openEditDialog($index)"
              >编辑</el-button
            >
            <el-button type="danger" link size="small" @click="removeRow($index)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <div v-show="mode === 'text'" class="headers-editor-text-wrap">
      <el-input
        v-model="textContent"
        type="textarea"
        :rows="8"
        placeholder="每行一条，格式：键: 值（以第一个冒号分隔键与值）"
        @blur="syncTextToRows"
      />
    </div>

    <el-dialog
      v-model="rowDialogVisible"
      :title="editingIndex === null ? '添加请求头' : '编辑请求头'"
      width="480px"
      append-to-body
      destroy-on-close
      @closed="resetRowDialog"
    >
      <el-form label-width="48px" @submit.prevent>
        <el-form-item label="键" required>
          <el-input v-model="rowDialogForm.key" placeholder="例如：Authorization" />
        </el-form-item>
        <el-form-item label="值">
          <el-input
            v-model="rowDialogForm.value"
            type="textarea"
            :rows="4"
            placeholder="例如：Bearer xxx"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="rowDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmRowDialog">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'

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

function confirmRowDialog() {
  const key = rowDialogForm.value.key.trim()
  if (!key) {
    ElMessage.warning('请输入键')
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

function resetRowDialog() {
  editingIndex.value = null
  rowDialogForm.value = { key: '', value: '' }
}

/** 提交前调用：将文本模式同步为表格数据并发 JSON，避免未失焦时未写入 */
function flush() {
  if (mode.value === 'text') {
    rows.value = parseTextToRows(textContent.value)
  }
}

defineExpose({ flush })
</script>

<style scoped lang="scss">
.headers-editor {
  width: 100%;
}

.headers-editor-toolbar {
  margin-bottom: 8px;
}

.headers-editor-op-header {
  width: 100%;
}

.headers-editor-table {
  width: 100%;
}

.headers-editor-text-wrap {
  width: 100%;
}
</style>

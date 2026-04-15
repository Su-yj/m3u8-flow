<script setup lang="ts">
import { computed, ref, watch } from 'vue'

const props = withDefaults(
  defineProps<{
    total: number
    pageSize: number
    currentPage: number
    pageSizes?: number[]
  }>(),
  {
    pageSizes: () => [10, 20, 50, 100],
  },
)

const emit = defineEmits<{
  'update:currentPage': [page: number]
  'update:pageSize': [size: number]
}>()

const jumperVal = ref(1)

watch(
  () => props.currentPage,
  (c) => {
    jumperVal.value = c
  },
  { immediate: true },
)

const totalPages = computed(() => Math.max(1, Math.ceil(props.total / props.pageSize) || 1))

const displayPages = computed(() => {
  const cur = props.currentPage
  const tp = totalPages.value
  const delta = 2
  const pages: (number | '…')[] = []
  if (tp <= 7) {
    for (let i = 1; i <= tp; i++) pages.push(i)
    return pages
  }
  pages.push(1)
  const left = Math.max(2, cur - delta)
  const right = Math.min(tp - 1, cur + delta)
  if (left > 2) pages.push('…')
  for (let i = left; i <= right; i++) pages.push(i)
  if (right < tp - 1) pages.push('…')
  pages.push(tp)
  return pages
})

function go(p: number) {
  const next = Math.min(totalPages.value, Math.max(1, p))
  emit('update:currentPage', next)
}

function onSizeChange(e: Event) {
  const n = Number((e.target as HTMLSelectElement).value)
  emit('update:pageSize', n)
  emit('update:currentPage', 1)
}

function submitJumper() {
  go(jumperVal.value)
}
</script>

<template>
  <div
    class="flex flex-col flex-wrap items-stretch justify-end gap-2 text-sm text-[var(--color-text-muted)] sm:flex-row sm:items-center sm:gap-3"
  >
    <span class="hidden whitespace-nowrap sm:inline">共 {{ total }} 条</span>
    <label class="hidden items-center gap-1 whitespace-nowrap sm:inline-flex">
      <span>每页</span>
      <select
        class="h-8 rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] px-2 text-[var(--color-text)]"
        :value="pageSize"
        @change="onSizeChange"
      >
        <option v-for="s in pageSizes" :key="s" :value="s">{{ s }}</option>
      </select>
    </label>
    <div class="flex flex-wrap items-center gap-1">
      <button
        type="button"
        class="rounded-md border border-[var(--color-border)] px-2 py-1 hover:bg-[var(--color-surface-muted)] disabled:opacity-40"
        :disabled="currentPage <= 1"
        @click="go(currentPage - 1)"
      >
        上一页
      </button>
      <span class="px-2 text-xs text-[var(--color-text-muted)] sm:hidden">
        {{ currentPage }} / {{ totalPages }}
      </span>
      <template v-for="(p, idx) in displayPages" :key="idx">
        <span v-if="p === '…'" class="hidden px-1 sm:inline">…</span>
        <button
          v-else
          type="button"
          class="hidden min-w-8 rounded-md px-2 py-1 sm:inline-block"
          :class="
            p === currentPage
              ? 'bg-brand-600 text-white dark:bg-brand-500'
              : 'border border-transparent hover:bg-[var(--color-surface-muted)]'
          "
          @click="go(p)"
        >
          {{ p }}
        </button>
      </template>
      <button
        type="button"
        class="rounded-md border border-[var(--color-border)] px-2 py-1 hover:bg-[var(--color-surface-muted)] disabled:opacity-40"
        :disabled="currentPage >= totalPages"
        @click="go(currentPage + 1)"
      >
        下一页
      </button>
    </div>
    <label class="hidden items-center gap-1 whitespace-nowrap sm:inline-flex">
      <span>前往</span>
      <input
        v-model.number="jumperVal"
        type="number"
        min="1"
        :max="totalPages"
        class="w-14 rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] px-2 py-1 text-center text-[var(--color-text)]"
        @keydown.enter.prevent="submitJumper"
      />
      <span>页</span>
      <button
        type="button"
        class="rounded-md border border-[var(--color-border)] px-2 py-1 hover:bg-[var(--color-surface-muted)]"
        @click="submitJumper"
      >
        确定
      </button>
    </label>
  </div>
</template>

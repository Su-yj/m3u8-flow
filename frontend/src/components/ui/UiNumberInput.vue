<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    min?: number
    max?: number
    step?: number
    disabled?: boolean
    placeholder?: string
    id?: string
    /** 小数位数，仅用于展示格式化 */
    precision?: number
  }>(),
  {
    step: 1,
    precision: 0,
  },
)

const model = defineModel<number | null>({ default: null })

const str = computed({
  get: () => (model.value === null || model.value === undefined ? '' : String(model.value)),
  set: (s: string | number | null | undefined) => {
    const t = String(s ?? '').trim()
    if (t === '') {
      model.value = null
      return
    }
    const n = Number(t)
    if (Number.isNaN(n)) {
      return
    }
    model.value = props.precision ? Number(n.toFixed(props.precision)) : n
  },
})

function onBlur() {
  if (model.value === null || model.value === undefined) return
  let n = model.value
  if (props.min !== undefined) n = Math.max(props.min, n)
  if (props.max !== undefined) n = Math.min(props.max, n)
  if (props.precision) n = Number(n.toFixed(props.precision))
  model.value = n
}
</script>

<template>
  <input
    :id="id"
    v-model="str"
    type="number"
    :min="min"
    :max="max"
    :step="step"
    :disabled="disabled"
    :placeholder="placeholder"
    class="h-9 w-full min-w-0 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-3 text-sm text-[var(--color-text)] [appearance:textfield] placeholder:text-[var(--color-text-muted)] focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/25 disabled:opacity-50 [&::-webkit-inner-spin-button]:appearance-none [&::-webkit-outer-spin-button]:appearance-none"
    @blur="onBlur"
  />
</template>

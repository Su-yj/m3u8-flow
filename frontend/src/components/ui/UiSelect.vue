<script setup lang="ts">
const model = defineModel<string | number>({ required: true })

defineProps<{
  options: { label: string; value: string | number }[]
  disabled?: boolean
  id?: string
}>()
</script>

<template>
  <select
    :id="id"
    v-model="model"
    :disabled="disabled"
    class="h-9 min-w-[5rem] rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-2 text-sm text-[var(--color-text)] focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/25 disabled:opacity-50"
  >
    <option v-for="opt in options" :key="String(opt.value)" :value="opt.value">
      {{ opt.label }}
    </option>
  </select>
</template>

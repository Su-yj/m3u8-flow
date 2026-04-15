<script setup lang="ts">
const model = defineModel<boolean>({ default: false })

withDefaults(
  defineProps<{
    disabled?: boolean
    id?: string
  }>(),
  {},
)
</script>

<template>
  <label class="inline-flex cursor-pointer items-start gap-2 text-sm text-[var(--color-text)]">
    <input
      :id="id"
      v-model="model"
      type="checkbox"
      :disabled="disabled"
      class="mt-0.5 size-4 shrink-0 rounded border-[var(--color-border)] text-brand-600 focus:ring-brand-500 disabled:opacity-50"
    />
    <span><slot /></span>
  </label>
</template>

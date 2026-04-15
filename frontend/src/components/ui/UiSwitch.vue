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
  <button
    :id="id"
    type="button"
    role="switch"
    :aria-checked="model"
    :disabled="disabled"
    class="relative inline-flex h-7 w-12 shrink-0 cursor-pointer rounded-full border border-[var(--color-border)] transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-500 disabled:cursor-not-allowed disabled:opacity-50"
    :class="model ? 'bg-brand-600 dark:bg-brand-500' : 'bg-[var(--color-surface-muted)]'"
    @click="model = !model"
  >
    <span
      class="pointer-events-none absolute top-0.5 left-0.5 size-6 rounded-full bg-white shadow transition-transform dark:bg-zinc-200"
      :class="model ? 'translate-x-5' : 'translate-x-0'"
    />
  </button>
</template>

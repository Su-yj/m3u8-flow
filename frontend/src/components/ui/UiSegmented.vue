<script setup lang="ts">
const model = defineModel<string>({ required: true })

defineProps<{
  options: { label: string; value: string }[]
}>()
</script>

<template>
  <div
    class="inline-flex rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-muted)] p-0.5"
    role="tablist"
  >
    <button
      v-for="opt in options"
      :key="opt.value"
      type="button"
      role="tab"
      :aria-selected="model === opt.value"
      class="rounded-md px-3 py-1 text-xs font-medium transition-colors"
      :class="
        model === opt.value
          ? 'bg-[var(--color-surface)] text-[var(--color-text)] shadow-sm'
          : 'text-[var(--color-text-muted)] hover:text-[var(--color-text)]'
      "
      @click="model = opt.value"
    >
      {{ opt.label }}
    </button>
  </div>
</template>

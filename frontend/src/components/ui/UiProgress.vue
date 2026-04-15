<script setup lang="ts">
withDefaults(
  defineProps<{
    percentage: number
    height?: number
  }>(),
  {
    height: 10,
  },
)
</script>

<template>
  <div
    class="w-full overflow-hidden rounded-full bg-[var(--color-surface-muted)]"
    :style="{ height: `${height}px` }"
  >
    <div
      class="h-full rounded-full bg-gradient-to-r from-brand-500 to-brand-600 transition-[width] duration-300 dark:from-brand-400 dark:to-brand-500"
      :style="{ width: `${Math.min(100, Math.max(0, percentage))}%` }"
    />
  </div>
</template>

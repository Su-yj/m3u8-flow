<script setup lang="ts">
defineProps<{
  label?: string
  error?: string
  labelWidthClass?: string
}>()
</script>

<template>
  <div class="grid gap-1.5 md:grid-cols-[140px_1fr] md:items-start md:gap-3">
    <label
      v-if="label"
      class="pt-2 text-sm font-medium text-[var(--color-text)] md:text-right"
      :class="labelWidthClass"
    >
      {{ label }}
    </label>
    <div class="min-w-0">
      <slot />
      <p v-if="error" class="mt-1 text-xs text-red-600 dark:text-red-400">{{ error }}</p>
    </div>
  </div>
</template>

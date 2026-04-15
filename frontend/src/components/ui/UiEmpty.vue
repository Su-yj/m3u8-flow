<script setup lang="ts">
defineProps<{
  description?: string
}>()
</script>

<template>
  <div
    class="flex flex-col items-center justify-center gap-2 py-12 text-center text-[var(--color-text-muted)]"
  >
    <div class="text-4xl opacity-40" aria-hidden="true">📭</div>
    <p class="text-sm">{{ description }}</p>
  </div>
</template>

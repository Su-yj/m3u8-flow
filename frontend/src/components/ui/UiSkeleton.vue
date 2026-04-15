<script setup lang="ts">
withDefaults(
  defineProps<{
    rows?: number
  }>(),
  { rows: 6 },
)
</script>

<template>
  <div class="flex flex-col gap-3" aria-busy="true" aria-label="加载中">
    <div
      v-for="i in rows"
      :key="i"
      class="h-9 animate-pulse rounded-lg bg-[var(--color-surface-muted)]"
      :style="{ width: i === rows ? '60%' : '100%' }"
    />
  </div>
</template>

<script setup lang="ts">
defineProps<{
  padded?: boolean
}>()
</script>

<template>
  <section
    class="relative flex h-full min-h-0 w-full flex-col rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] shadow-sm"
  >
    <header
      v-if="$slots.header"
      class="shrink-0 border-b border-[var(--color-border)] px-4 py-3 md:px-5"
    >
      <slot name="header" />
    </header>
    <div class="min-h-0 flex-1" :class="padded !== false ? 'p-4 md:p-5' : ''">
      <slot />
    </div>
  </section>
</template>

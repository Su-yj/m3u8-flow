<script setup lang="ts">
defineProps<{
  show: boolean
}>()
</script>

<template>
  <Transition name="fade">
    <div
      v-if="show"
      class="absolute inset-0 z-10 flex items-center justify-center rounded-[inherit] bg-[var(--color-surface)]/70 backdrop-blur-[1px]"
    >
      <span
        class="inline-block size-8 animate-spin rounded-full border-2 border-brand-500 border-t-transparent"
        aria-label="加载中"
      />
    </div>
  </Transition>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>

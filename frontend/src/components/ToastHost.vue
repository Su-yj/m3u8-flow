<script setup lang="ts">
import { useToastState } from '@/utils/toast'

const state = useToastState()
</script>

<template>
  <Teleport to="body">
    <div
      class="pointer-events-none fixed inset-x-0 top-3 z-[200] flex flex-col items-center gap-2 px-3"
      aria-live="polite"
    >
      <TransitionGroup name="toast">
        <div
          v-for="t in state.list"
          :key="t.id"
          class="pointer-events-auto max-w-[min(100%,28rem)] rounded-lg border px-4 py-2.5 text-sm shadow-lg backdrop-blur-sm"
          :class="{
            'border-emerald-500/30 bg-emerald-950/90 text-emerald-50': t.type === 'success',
            'border-red-500/35 bg-red-950/90 text-red-50': t.type === 'error',
            'border-amber-500/35 bg-amber-950/90 text-amber-50': t.type === 'warning',
            'border-[var(--color-border)] bg-[var(--color-surface-muted)] text-[var(--color-text)]':
              t.type === 'info',
          }"
        >
          {{ t.message }}
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<style scoped>
.toast-enter-active,
.toast-leave-active {
  transition:
    opacity 0.2s ease,
    transform 0.2s ease;
}
.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}
</style>

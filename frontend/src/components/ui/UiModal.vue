<script setup lang="ts">
import { onMounted, onUnmounted, watch } from 'vue'

const props = withDefaults(
  defineProps<{
    modelValue: boolean
    title?: string
    widthClass?: string
  }>(),
  {
    widthClass: 'max-w-lg',
  },
)

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

function close() {
  emit('update:modelValue', false)
}

function onKey(e: KeyboardEvent) {
  if (e.key === 'Escape' && props.modelValue) {
    close()
  }
}

watch(
  () => props.modelValue,
  (v) => {
    if (v) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = ''
    }
  },
)

onMounted(() => window.addEventListener('keydown', onKey))
onUnmounted(() => {
  window.removeEventListener('keydown', onKey)
  document.body.style.overflow = ''
})
</script>

<template>
  <Teleport to="body">
    <Transition name="ui-modal">
      <div
        v-if="modelValue"
        class="fixed inset-0 z-[100] flex items-end justify-center p-0 sm:items-center sm:p-4"
        role="dialog"
        aria-modal="true"
      >
        <div
          class="absolute inset-0 bg-black/50 backdrop-blur-[1px]"
          aria-hidden="true"
          @click="close"
        />
        <div
          class="relative z-10 flex max-h-[min(100%,90vh)] w-full flex-col rounded-t-2xl border border-[var(--color-border)] bg-[var(--color-surface)] shadow-2xl sm:rounded-2xl"
          :class="widthClass"
        >
          <div
            v-if="title || $slots.title"
            class="flex shrink-0 items-center justify-between border-b border-[var(--color-border)] px-4 py-3"
          >
            <h2 class="text-base font-semibold text-[var(--color-text)]">
              <slot name="title">{{ title }}</slot>
            </h2>
            <button
              type="button"
              class="rounded-lg p-1 text-[var(--color-text-muted)] hover:bg-[var(--color-surface-muted)] hover:text-[var(--color-text)]"
              aria-label="关闭"
              @click="close"
            >
              <span class="text-lg leading-none">×</span>
            </button>
          </div>
          <div class="min-h-0 flex-1 overflow-y-auto px-4 py-3">
            <slot />
          </div>
          <div
            v-if="$slots.footer"
            class="flex shrink-0 justify-end gap-2 border-t border-[var(--color-border)] px-4 py-3"
          >
            <slot name="footer" />
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.ui-modal-enter-active,
.ui-modal-leave-active {
  transition: opacity 0.2s ease;
}
.ui-modal-enter-active .relative,
.ui-modal-leave-active .relative {
  transition: transform 0.2s ease;
}
.ui-modal-enter-from,
.ui-modal-leave-to {
  opacity: 0;
}
.ui-modal-enter-from .relative,
.ui-modal-leave-to .relative {
  transform: translateY(12px);
}
@media (min-width: 640px) {
  .ui-modal-enter-from .relative,
  .ui-modal-leave-to .relative {
    transform: scale(0.96);
  }
}
</style>

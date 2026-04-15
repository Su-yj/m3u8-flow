<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    variant?: 'primary' | 'secondary' | 'success' | 'warning' | 'danger' | 'ghost'
    size?: 'sm' | 'md' | 'lg'
    loading?: boolean
    disabled?: boolean
    block?: boolean
    type?: 'button' | 'submit'
  }>(),
  {
    variant: 'secondary',
    size: 'md',
    type: 'button',
  },
)

const cls = computed(() => {
  const base =
    'inline-flex cursor-pointer items-center justify-center gap-1.5 rounded-lg font-medium transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 disabled:pointer-events-none disabled:cursor-not-allowed disabled:opacity-50'
  const sizes = {
    sm: 'h-8 px-2.5 text-xs',
    md: 'h-9 px-3 text-sm',
    lg: 'h-11 px-4 text-base',
  }[props.size]
  const variants = {
    primary: 'bg-brand-500 text-white hover:bg-brand-600 focus-visible:outline-brand-500',
    secondary:
      'border border-[var(--color-border)] bg-[var(--color-surface-muted)] text-[var(--color-text)] hover:bg-[var(--color-surface)]',
    success: 'bg-emerald-500 text-white hover:bg-emerald-600 focus-visible:outline-emerald-500',
    warning: 'bg-amber-500 text-white hover:bg-amber-600 focus-visible:outline-amber-500',
    danger: 'bg-red-600 text-white hover:bg-red-700 focus-visible:outline-red-500',
    ghost: 'text-brand-700 hover:bg-brand-500/10 dark:text-brand-300',
  }[props.variant]
  const block = props.block ? 'w-full' : ''
  return [base, sizes, variants, block].join(' ')
})
</script>

<template>
  <button :type="type" :disabled="disabled || loading" :class="cls">
    <span
      v-if="loading"
      class="inline-block size-3.5 animate-spin rounded-full border-2 border-current border-t-transparent"
      aria-hidden="true"
    />
    <slot />
  </button>
</template>

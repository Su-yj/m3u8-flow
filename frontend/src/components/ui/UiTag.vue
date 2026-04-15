<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    variant?: 'info' | 'primary' | 'success' | 'warning' | 'danger'
    effect?: 'solid' | 'plain'
  }>(),
  {
    variant: 'info',
    effect: 'plain',
  },
)

const cls = computed(() => {
  const plain = {
    info: 'border-slate-500 text-slate-600 dark:text-slate-200',
    primary: 'border-brand-500 text-brand-600 dark:text-brand-200',
    success: 'border-emerald-500 text-emerald-600 dark:text-emerald-200',
    warning: 'border-amber-500 text-amber-600 dark:text-amber-100',
    danger: 'border-red-500 text-red-600 dark:text-red-200',
  }
  const solid = {
    info: 'border-transparent bg-slate-500 text-white',
    primary: 'border-transparent bg-brand-500 text-white dark:bg-brand-500',
    success: 'border-transparent bg-emerald-500 text-white',
    warning: 'border-transparent bg-amber-500 text-white',
    danger: 'border-transparent bg-red-500 text-white',
  }
  const map = props.effect === 'solid' ? solid : plain
  return `inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-medium ${map[props.variant]}`
})
</script>

<template>
  <span :class="cls">
    <slot />
  </span>
</template>

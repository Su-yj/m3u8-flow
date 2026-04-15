import { reactive } from 'vue'

export type ToastType = 'success' | 'error' | 'warning' | 'info'

export type ToastItem = {
  id: number
  message: string
  type: ToastType
}

const state = reactive<{ list: ToastItem[] }>({ list: [] })
let seq = 0

function remove(id: number) {
  const i = state.list.findIndex((t) => t.id === id)
  if (i >= 0) state.list.splice(i, 1)
}

export function showToast(message: string, type: ToastType = 'info', durationMs = 3600) {
  const id = ++seq
  state.list.push({ id, message, type })
  window.setTimeout(() => remove(id), durationMs)
}

export function useToastState() {
  return state
}

export const toast = {
  success: (m: string) => showToast(m, 'success'),
  error: (m: string) => showToast(m, 'error'),
  warning: (m: string) => showToast(m, 'warning'),
  info: (m: string) => showToast(m, 'info'),
}

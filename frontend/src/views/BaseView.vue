<script setup lang="ts">
import { useDark, useMediaQuery } from '@vueuse/core'
import { CircleCheck, Download, Moon, Settings, Sun } from 'lucide-vue-next'
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import UiButton from '@/components/ui/UiButton.vue'
import UiSwitch from '@/components/ui/UiSwitch.vue'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const isDark = useDark()
const isDesktop = useMediaQuery('(min-width: 768px)')

const activeDownload = computed(() => route.name === 'download-manage')
const activeCompleted = computed(() => route.name === 'completed')
const activeConfig = computed(() => route.name === 'global-config')

function navClass(active: boolean) {
  return active
    ? 'bg-brand-100 text-brand-500 dark:bg-brand-500 dark:text-brand-100'
    : 'text-[var(--color-text-muted)] hover:bg-[var(--color-surface)] hover:text-[var(--color-text)]'
}

function tabClass(active: boolean) {
  return active ? 'text-brand-600 dark:text-brand-400' : 'text-[var(--color-text-muted)]'
}

async function logout() {
  authStore.clearTokens()
  await router.replace({ name: 'login' })
}
</script>

<template>
  <div class="flex h-full min-h-0 w-full bg-[var(--color-surface)] text-[var(--color-text)]">
    <!-- 桌面侧栏 -->
    <aside
      v-if="isDesktop"
      class="flex w-64 shrink-0 flex-col border-r border-[var(--color-border)] bg-[var(--color-surface-muted)] shadow-[6px_0_18px_rgba(0,0,0,0.06)] dark:shadow-[6px_0_18px_rgba(0,0,0,0.25)]"
    >
      <div class="min-h-0 flex-1 overflow-auto p-4">
        <h1 class="mb-2 flex items-center justify-center gap-3 py-1">
          <img
            class="size-10 shrink-0 rounded-[10px] shadow-md ring-1 ring-slate-300/50 dark:shadow-[0_2px_14px_rgba(29,78,216,0.35)] dark:ring-sky-500/30"
            src="/favicon.svg"
            width="40"
            height="40"
            alt=""
          />
          <span class="flex min-w-0 flex-col items-start gap-0.5 pl-3.5">
            <span
              class="relative text-[13px] font-bold tracking-[0.2em] text-[var(--color-text-muted)] before:absolute before:top-0.5 before:bottom-0.5 before:-left-3.5 before:w-0.5 before:rounded-sm before:bg-gradient-to-b before:from-sky-300 before:to-blue-700"
            >
              M3U8
            </span>
            <span
              class="bg-gradient-to-r from-sky-400 via-blue-400 to-blue-800 bg-clip-text text-xl font-extrabold tracking-[0.14em] text-transparent"
            >
              FLOW
            </span>
          </span>
        </h1>

        <nav class="flex flex-col gap-1 py-2">
          <RouterLink
            :to="{ name: 'download-manage' }"
            class="flex items-center gap-3 rounded-lg px-3 py-2.5 text-base font-bold transition-colors"
            :class="navClass(activeDownload)"
          >
            <Download class="size-5 shrink-0" aria-hidden="true" />
            下载管理
          </RouterLink>
          <RouterLink
            :to="{ name: 'completed' }"
            class="flex items-center gap-3 rounded-lg px-3 py-2.5 text-base font-bold transition-colors"
            :class="navClass(activeCompleted)"
          >
            <CircleCheck class="size-5 shrink-0" aria-hidden="true" />
            已完成
          </RouterLink>
          <RouterLink
            :to="{ name: 'global-config' }"
            class="flex items-center gap-3 rounded-lg px-3 py-2.5 text-base font-bold transition-colors"
            :class="navClass(activeConfig)"
          >
            <Settings class="size-5 shrink-0" aria-hidden="true" />
            全局设置
          </RouterLink>
        </nav>

        <div class="my-4 h-px bg-[var(--color-border)]" />

        <div class="flex items-center justify-between gap-3 rounded-lg px-1 py-2">
          <span class="text-sm text-[var(--color-text-muted)]">主题</span>
          <div class="flex items-center gap-2">
            <Sun class="size-4 text-amber-500" />
            <UiSwitch v-model="isDark" />
            <Moon class="size-4 text-sky-600 dark:text-sky-300" />
          </div>
        </div>
      </div>

      <div
        v-if="authStore.accessToken"
        class="shrink-0 border-t border-[var(--color-border)] p-3 text-center"
      >
        <UiButton variant="ghost" class="text-red-600 dark:text-red-400" @click="logout"
          >退出</UiButton
        >
      </div>
    </aside>

    <!-- 主内容 -->
    <main
      class="min-h-0 min-w-0 flex-1 overflow-auto pb-[calc(4.5rem+env(safe-area-inset-bottom))] md:pb-0"
    >
      <RouterView />
    </main>

    <!-- 移动端底栏 -->
    <nav
      v-if="!isDesktop"
      class="fixed inset-x-0 bottom-0 z-40 flex border-t border-[var(--color-border)] bg-[var(--color-surface)]/95 pb-[env(safe-area-inset-bottom)] backdrop-blur-md"
    >
      <RouterLink
        :to="{ name: 'download-manage' }"
        class="flex flex-1 flex-col items-center gap-0.5 py-2 text-[10px] font-medium"
        :class="tabClass(activeDownload)"
      >
        <Download class="size-6" />
        下载
      </RouterLink>
      <RouterLink
        :to="{ name: 'completed' }"
        class="flex flex-1 flex-col items-center gap-0.5 py-2 text-[10px] font-medium"
        :class="tabClass(activeCompleted)"
      >
        <CircleCheck class="size-6" />
        已完成
      </RouterLink>
      <RouterLink
        :to="{ name: 'global-config' }"
        class="flex flex-1 flex-col items-center gap-0.5 py-2 text-[10px] font-medium"
        :class="tabClass(activeConfig)"
      >
        <Settings class="size-6" />
        设置
      </RouterLink>
    </nav>
  </div>
</template>

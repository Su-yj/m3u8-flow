<template>
  <div
    class="fixed inset-0 flex items-center justify-center bg-gradient-to-br from-slate-100 via-slate-50 to-slate-100 p-6 dark:from-slate-950 dark:via-slate-900 dark:to-slate-950"
  >
    <div
      class="w-full max-w-md rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-xl dark:shadow-[0_0_0_1px_rgba(56,189,248,0.12)]"
    >
      <h1 class="mb-6 text-center text-lg font-bold text-[var(--color-text)]">M3U8 Flow 登录</h1>

      <form class="flex flex-col gap-4" @submit.prevent="onSubmit">
        <UiFormRow label="用户名" :error="errors.username">
          <UiInput
            v-model="form.username"
            autocomplete="username"
            placeholder="用户名"
            @blur="clearFieldError('username')"
          />
        </UiFormRow>
        <UiFormRow label="密码" :error="errors.password">
          <UiInput
            v-model="form.password"
            type="password"
            autocomplete="current-password"
            placeholder="密码"
            @blur="clearFieldError('password')"
          />
        </UiFormRow>
        <UiButton type="submit" variant="primary" size="lg" block :loading="loading" class="mt-2">
          登录
        </UiButton>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
defineOptions({ name: 'LoginView' })

import axios from 'axios'
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useDark } from '@vueuse/core'

import UiButton from '@/components/ui/UiButton.vue'
import UiFormRow from '@/components/ui/UiFormRow.vue'
import UiInput from '@/components/ui/UiInput.vue'
import { useAuthStore } from '@/stores/auth'
import type { ApiResponse } from '@/types/api'
import { toast } from '@/utils/toast'
import { validateModel } from '@/utils/formValidate'

interface Token {
  access_token: string
  refresh_token: string
  token_type: string
}

const router = useRouter()
useDark()
const authStore = useAuthStore()

const loading = ref(false)

const form = reactive({
  username: '',
  password: '',
})

const errors = reactive({
  username: '',
  password: '',
})

function clearFieldError(key: 'username' | 'password') {
  errors[key] = ''
}

async function onSubmit() {
  const r = validateModel(form, {
    username: [{ required: true, message: '请输入用户名' }],
    password: [{ required: true, message: '请输入密码' }],
  })
  errors.username = ''
  errors.password = ''
  if (!r.valid) {
    const msg = r.message
    if (msg.includes('用户名')) errors.username = msg
    else if (msg.includes('密码')) errors.password = msg
    return
  }

  loading.value = true
  try {
    const body = new URLSearchParams()
    body.set('username', form.username)
    body.set('password', form.password)

    const { data } = await axios.post<ApiResponse<Token>>('/api/auth/login', body, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })

    if (data.code !== 0 || !data.data) {
      throw new Error(data.message || '登录失败')
    }

    authStore.setTokens(data.data.access_token, data.data.refresh_token)

    toast.success('登录成功')
    await router.replace({ name: 'download-manage' })
  } catch (e) {
    let msg = ''
    if (axios.isAxiosError(e)) {
      const data = e.response?.data as unknown
      if (
        data &&
        typeof data === 'object' &&
        'detail' in data &&
        typeof (data as Record<string, unknown>).detail === 'string'
      ) {
        msg = (data as { detail: string }).detail
      } else {
        msg = e.message
      }
    } else {
      msg = e instanceof Error ? e.message : '登录失败'
    }
    toast.error(msg || '登录失败')
  } finally {
    loading.value = false
  }
}
</script>

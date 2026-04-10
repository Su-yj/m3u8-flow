<template>
  <div class="login-page">
    <el-card class="login-card" shadow="always">
      <template #header>
        <div class="title">M3U8 Flow 登录</div>
      </template>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-position="top"
        @keyup.enter="onSubmit"
      >
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" size="large" autocomplete="username" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input
            v-model="form.password"
            type="password"
            show-password
            autocomplete="current-password"
            size="large"
          />
        </el-form-item>

        <el-button type="primary" :loading="loading" class="submit" size="large" @click="onSubmit">
          登录
        </el-button>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
defineOptions({ name: 'LoginView' })

import axios from 'axios'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useDark } from '@vueuse/core'

import type { ApiResponse } from '@/types/api'
import { useAuthStore } from '@/stores/auth'

interface Token {
  access_token: string
  refresh_token: string
  token_type: string
}

const router = useRouter()
useDark()
const authStore = useAuthStore()

const formRef = ref<FormInstance>()
const loading = ref(false)

const form = reactive({
  username: '',
  password: '',
})

const rules: FormRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

async function onSubmit() {
  const ok = await formRef.value?.validate().catch(() => false)
  if (!ok) return

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

    ElMessage.success('登录成功')
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
    ElMessage.error(msg || '登录失败')
  } finally {
    loading.value = false
  }
}
</script>

<style lang="scss" scoped>
.login-page {
  position: fixed;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: linear-gradient(135deg, #f5f7fa 0%, #eef2f7 40%, #f8fafc 100%);
  html.dark & {
    background:
      radial-gradient(
        1200px 600px at 20% 10%,
        rgba(64, 158, 255, 0.14) 0%,
        rgba(64, 158, 255, 0) 55%
      ),
      linear-gradient(135deg, #0b1220 0%, #0f172a 45%, #0b1220 100%) !important;
  }
}

.login-card {
  width: 420px;
  max-width: 100%;

  .title {
    font-size: 18px;
    font-weight: 700;
    text-align: center;
  }

  .submit {
    width: 100%;
  }
}
</style>

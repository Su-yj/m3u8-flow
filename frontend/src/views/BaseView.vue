<template>
  <el-container class="app">
    <el-aside width="256px" class="aside">
      <div class="aside-content">
        <h1>M3U8 Flow</h1>
        <el-menu router>
          <el-menu-item index="/" :route="{ name: 'download-manage' }">
            <el-icon><Download /></el-icon>
            <span>下载管理</span>
          </el-menu-item>
          <el-menu-item index="/completed" :route="{ name: 'completed' }">
            <el-icon><CircleCheck /></el-icon>
            <span>已完成</span>
          </el-menu-item>
          <el-menu-item index="/global-config" :route="{ name: 'global-config' }">
            <el-icon><Setting /></el-icon>
            <span>全局设置</span>
          </el-menu-item>
        </el-menu>
        <el-divider />
        <div class="theme-switch">
          <el-form>
            <el-form-item label="主题">
              <el-switch
                v-model="isDark"
                size="large"
                inline-prompt
                style="--el-switch-on-color: #2c2c2c; --el-switch-off-color: #f2f2f2"
              >
                <template #active-action>
                  <el-icon color="#D0D3DC"><Moon /></el-icon>
                </template>
                <template #inactive-action>
                  <el-icon color="#606266"><Sunny /></el-icon>
                </template>
              </el-switch>
            </el-form-item>
          </el-form>
        </div>
      </div>
      <div v-if="authStore.accessToken" class="aside-footer">
        <el-button type="danger" link @click="logout">退出</el-button>
      </div>
    </el-aside>
    <el-main>
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup lang="ts">
import { useDark } from '@vueuse/core'
import { CircleCheck, Download, Moon, Setting, Sunny } from '@element-plus/icons-vue'
import { computed } from 'vue'
import { useRouter } from 'vue-router'

import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()
const isDark = useDark()

const actionColor = computed(() => {
  return isDark.value ? '#2C2C2C' : '#F2F2F2'
})

async function logout() {
  authStore.clearTokens()
  await router.replace({ name: 'login' })
}
</script>

<style scoped lang="scss">
.app {
  height: 100%;
  width: 100%;
  .el-aside.aside {
    display: flex;
    flex-direction: column;
    height: 100%;
    padding: 16px;
    box-sizing: border-box;
    box-shadow: 6px 0 18px rgba(0, 0, 0, 0.1);
    z-index: 1;

    .aside-content {
      flex: 1 1 auto;
      min-height: 0;
      overflow: auto;
    }

    .aside-footer {
      flex-shrink: 0;
      margin-top: auto;
      padding: 10px;
      padding-top: 12px;
      text-align: center;
    }

    h1 {
      font-size: 22px;
      font-weight: bolder;
      text-align: center;
    }
    .el-menu {
      border-right: none;
      .el-menu-item {
        font-size: 16px;
        font-weight: bold;
      }
    }
    .theme-switch {
      :deep(.el-switch__action) {
        background-color: v-bind(actionColor) !important;
      }
    }
  }
}
</style>

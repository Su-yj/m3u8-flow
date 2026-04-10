import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/Login.vue'),
    },
    {
      path: '/',
      name: 'home',
      component: () => import('@/views/BaseView.vue'),
      children: [
        {
          path: '',
          name: 'download-manage',
          component: () => import('@/views/DownloadView.vue'),
        },
        {
          path: 'completed',
          name: 'completed',
          component: () => import('@/views/CompletedView.vue'),
        },
        {
          path: 'global-config',
          name: 'global-config',
          component: () => import('@/views/GlobalConfig.vue'),
        },
      ],
    },
  ],
})

export default router

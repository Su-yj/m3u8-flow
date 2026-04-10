import 'element-plus/dist/index.css'
import 'element-plus/theme-chalk/dark/css-vars.css'
import './assets/styles/css-vars.scss'
import './assets/font/iconfont.css'
import './assets/styles/base.scss'

import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'
import { setupAxiosInterceptors } from './utils/http'

const app = createApp(App)

const pinia = createPinia()
app.use(pinia)
app.use(router)

setupAxiosInterceptors(pinia, router)

app.mount('#app')

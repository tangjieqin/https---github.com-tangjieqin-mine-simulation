import { createApp } from 'vue'
import { createPinia } from 'pinia'
import './style.css'
import App from './App.vue'

// Pinia 必须先 use 再 mount，否则组件里调用 store 会报"没有 active pinia"
createApp(App).use(createPinia()).mount('#app')

import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import Home from './views/Home.vue'
import Result from './views/Result.vue'
import './style.css'

const routes = [
  { path: '/', component: Home },
  { path: '/result/:id', component: Result, props: true },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

createApp(App).use(router).mount('#app')

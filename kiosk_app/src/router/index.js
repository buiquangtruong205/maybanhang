import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import PayView from '../views/PayView.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: HomeView
  },
  {
    path: '/pay/:productId',
    name: 'PayView',
    component: PayView,
    props: true
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
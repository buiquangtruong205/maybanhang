import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  // === Customer routes ===
  {
    path: '/',
    name: 'Home',
    component: () => import('../views/HomeView.vue')
  },
  {
    path: '/payment/:productId',
    name: 'Payment',
    component: () => import('../views/PaymentView.vue'),
    props: true
  },
  {
    path: '/success',
    name: 'Success',
    component: () => import('../views/SuccessView.vue')
  },
  {
    path: '/cancel',
    name: 'Cancel',
    component: () => import('../views/CancelView.vue')
  },

  // === Admin routes ===
  {
    path: '/admin/login',
    name: 'AdminLogin',
    component: () => import('../views/admin/LoginView.vue')
  },
  {
    path: '/admin',
    component: () => import('../views/admin/AdminLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'AdminDashboard',
        component: () => import('../views/admin/DashboardView.vue'),
        meta: { title: 'Tổng quan' }
      },
      {
        path: 'products',
        name: 'AdminProducts',
        component: () => import('../views/admin/ProductsView.vue'),
        meta: { title: 'Sản phẩm' }
      },
      {
        path: 'orders',
        name: 'AdminOrders',
        component: () => import('../views/admin/OrdersView.vue'),
        meta: { title: 'Đơn hàng' }
      },
      {
        path: 'machines',
        name: 'AdminMachines',
        component: () => import('../views/admin/MachinesView.vue'),
        meta: { title: 'Máy bán hàng' }
      },
      {
        path: 'settings',
        name: 'AdminSettings',
        component: () => import('../views/admin/SettingsView.vue'),
        meta: { requiresAuth: true, requiresAdmin: true } // Only Admin
      },
      {
        path: 'slots',
        name: 'AdminSlots',
        component: () => import('../views/admin/SlotsView.vue'),
        meta: { title: 'Vị trí hàng' }
      },
      {
        path: 'users',
        name: 'AdminUsers',
        component: () => import('../views/admin/UsersView.vue'),
        meta: { title: 'Thành viên' }
      }
    ]
  },

  // === 404 ===
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('../views/NotFoundView.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Auth guard
router.beforeEach((to, from, next) => {
  if (to.matched.some(record => record.meta.requiresAuth)) {
    const token = localStorage.getItem('token')
    if (!token) {
      next({ name: 'AdminLogin' })
    } else {
      next()
    }
  } else {
    next()
  }
})

export default router
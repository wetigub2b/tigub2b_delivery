import { createRouter, createWebHistory } from 'vue-router';
import featureFlags from '@/config/features';

// Check if user is authenticated
function isAuthenticated(): boolean {
  const token = localStorage.getItem('delivery_token');
  return !!token;
}

// Check if admin is authenticated
function isAdminAuthenticated(): boolean {
  // Simple check using localStorage only to avoid store initialization issues
  const token = localStorage.getItem('admin_token');
  return !!token;
}

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'task-board',
      component: () => import('@/views/TaskBoard.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/orders/:orderSn',
      name: 'order-detail',
      component: () => import('@/views/OrderDetail.vue'),
      props: true,
      meta: { requiresAuth: true }
    },
    {
      path: '/route-planner',
      name: 'route-planner',
      component: () => import('@/views/RoutePlanner.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/profile',
      name: 'driver-profile',
      component: () => import('@/views/DriverProfile.vue'),
      meta: { requiresAuth: true }
    },
    // Prepare Goods routes (for Merchants)
    {
      path: '/prepare-goods',
      name: 'PrepareGoodsList',
      component: () => import('@/views/PrepareGoodsList.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/prepare-goods/create',
      name: 'PrepareGoodsCreate',
      component: () => import('@/views/PrepareGoodsCreate.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue')
    },
    // Admin routes
    {
      path: '/admin/login',
      name: 'admin-login',
      component: () => import('@/views/AdminLogin.vue')
    },
    {
      path: '/admin/dashboard',
      name: 'admin-dashboard',
      component: () => import('@/views/AdminDashboard.vue'),
      meta: { requiresAdminAuth: true }
    },
    {
      path: '/admin/drivers',
      name: 'admin-drivers',
      component: () => import('@/views/AdminDrivers.vue'),
      meta: { requiresAdminAuth: true }
    },
    {
      path: '/admin/orders',
      name: 'admin-orders',
      component: () => import('@/views/AdminOrders.vue'),
      meta: { requiresAdminAuth: true }
    },
    {
      path: '/admin/dispatch',
      name: 'admin-dispatch',
      component: () => import('@/views/AdminDispatch.vue'),
      meta: { requiresAdminAuth: true, requiresFeature: 'adminDispatch' }
    },
    {
      path: '/admin/reports',
      name: 'admin-reports',
      component: () => import('@/views/AdminReports.vue'),
      meta: { requiresAdminAuth: true, requiresFeature: 'adminReports' }
    },
    {
      path: '/admin/notifications',
      name: 'admin-notifications',
      component: () => import('@/views/AdminNotifications.vue'),
      meta: { requiresAdminAuth: true }
    },
    // Redirect /admin to dashboard
    {
      path: '/admin',
      redirect: '/admin/dashboard'
    }
  ]
});

// Navigation guard to protect routes
router.beforeEach((to, from, next) => {
  // Handle admin routes first
  if (to.path.startsWith('/admin')) {
    if (to.meta.requiresAdminAuth && !isAdminAuthenticated()) {
      next('/admin/login');
      return;
    }
    if (to.name === 'admin-login' && isAdminAuthenticated()) {
      next('/admin/dashboard');
      return;
    }
    // Check feature flag requirements
    if (to.meta.requiresFeature) {
      const featureName = to.meta.requiresFeature as keyof typeof featureFlags;
      if (!featureFlags[featureName]) {
        next('/admin/dashboard');
        return;
      }
    }
    next();
    return;
  }

  // Handle regular driver routes
  if (to.meta.requiresAuth && !isAuthenticated()) {
    next('/login');
    return;
  }

  if (to.name === 'login' && isAuthenticated()) {
    next('/');
    return;
  }

  // Default: allow navigation
  next();
});

export default router;

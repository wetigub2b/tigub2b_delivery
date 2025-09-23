import { createRouter, createWebHistory } from 'vue-router';

// Check if user is authenticated
function isAuthenticated(): boolean {
  const token = localStorage.getItem('delivery_token');
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
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue')
    }
  ]
});

// Navigation guard to protect routes
router.beforeEach((to, from, next) => {
  if (to.meta.requiresAuth && !isAuthenticated()) {
    next('/login');
  } else if (to.name === 'login' && isAuthenticated()) {
    next('/');
  } else {
    next();
  }
});

export default router;

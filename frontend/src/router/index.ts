// src/router/index.ts
import { createRouter, createWebHistory, type RouteLocationNormalized } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import LoginView from '../views/LoginView.vue'
import RegisterView from '../views/RegisterView.vue'
import DashboardView from '../views/DashboardView.vue'
import { useAuthStore } from '@/stores/auth' 

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView
    },
    {
      path: '/login',
      name: 'login',
      component: LoginView,
      meta: { guestOnly: true } // Маршрут только для неаутентифицированных
    },
    {
      path: '/register',
      name: 'register',
      component: RegisterView,
      meta: { guestOnly: true } // Маршрут только для неаутентифицированных
    },
    {
      path: '/dashboard',
      name: 'dashboard',
      component: DashboardView,
      meta: { requiresAuth: true } // Этот маршрут требует аутентификации
    }
  ]
})

// Navigation Guard
router.beforeEach((to: RouteLocationNormalized, from: RouteLocationNormalized, next: Function) => {
  const authStore = useAuthStore();
  const isLoggedIn = authStore.isLoggedIn;

  if (to.meta.requiresAuth && !isLoggedIn) {
    // Если маршрут требует аутентификации, а пользователь не залогинен,
    // перенаправляем на страницу входа.
    next({ name: 'login' });
  } else if (to.meta.guestOnly && isLoggedIn) {
    
    next({ name: 'dashboard' });
  } else {
    // В остальных случаях разрешаем переход.
    next();
  }
});

export default router
<script setup lang="ts">
import { RouterLink } from 'vue-router';
import { useAuthStore } from '@/stores/auth';

const authStore = useAuthStore();
</script>

<template>
  <div class="min-h-[calc(100vh-var(--navbar-height,64px))] bg-slate-900 text-slate-200 flex flex-col items-center justify-center p-4 sm:p-8">
    <div class="max-w-3xl w-full text-center">
      
      <div class="hero-section">
        <h1 class="text-5xl sm:text-6xl lg:text-7xl font-extrabold tracking-tight">
          <span class="block text-purple-500">Chii2-Vision</span>
          <span class="block text-slate-300 subtitle-spacing">Анализ поведения на видео</span>
        </h1>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-6 sm:gap-8 text-left cards-section">
        
        <div class="bg-slate-800 p-6 rounded-xl shadow-2xl transform hover:scale-105 transition-transform duration-300">
          <div class="flex items-center justify-center w-12 h-12 rounded-full bg-purple-600 text-white mb-4 shadow-lg">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
          </div>
          <h3 class="text-xl font-semibold text-slate-100 mb-2">1. Войдите или Зарегистрируйтесь</h3>
          <p class="text-slate-400 text-sm">
            Для доступа ко всем функциям системы необходима авторизация. Если у вас еще нет аккаунта, процесс регистрации займет всего минуту.
          </p>
        </div>

        <div class="bg-slate-800 p-6 rounded-xl shadow-2xl transform hover:scale-105 transition-transform duration-300">
          <div class="flex items-center justify-center w-12 h-12 rounded-full bg-purple-600 text-white mb-4 shadow-lg">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
            </svg>
          </div>
          <h3 class="text-xl font-semibold text-slate-100 mb-2">2. Укажите источник видео</h3>
          <p class="text-slate-400 text-sm">
            Перейдите в "Панель управления". Вы можете загрузить свой видеофайл (MP4, AVI и др.) или указать URL RTSP-потока с IP-камеры.
          </p>
        </div>

        <div class="bg-slate-800 p-6 rounded-xl shadow-2xl transform hover:scale-105 transition-transform duration-300">
          <div class="flex items-center justify-center w-12 h-12 rounded-full bg-purple-600 text-white mb-4 shadow-lg">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
          </div>
          <h3 class="text-xl font-semibold text-slate-100 mb-2">3. Наблюдайте за анализом</h3>
          <p class="text-slate-400 text-sm">
            Система начнет обработку. Вы увидите видеопоток с результатами детекции, а зафиксированные аномальные события будут доступны на вкладке "Аномалии".
          </p>
        </div>
      </div>

      <div>
        <RouterLink 
          :to="authStore.isLoggedIn ? '/dashboard' : '/login'" 
          class="inline-block px-12 py-5 text-xl font-medium text-slate-100 bg-slate-700 hover:bg-slate-600 border border-slate-600 hover:border-slate-500 rounded-lg shadow-lg focus:outline-none focus:ring-2 focus:ring-slate-500 focus:ring-offset-2 focus:ring-offset-slate-900 transform hover:scale-105 transition-all duration-300"
        >
          {{ authStore.isLoggedIn ? 'Перейти в Панель управления' : 'Начать работу' }}
        </RouterLink>
      </div>

    </div>
  </div>
</template>

<style scoped>
.hero-section {
  margin-bottom: 3.5rem;
}

.cards-section {
  margin-bottom: 3.5rem;
}

.subtitle-spacing {
  margin-top: 1rem;
}


</style>
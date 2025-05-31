<script setup lang="ts">
import { RouterLink } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import { computed, ref } from 'vue';

const authStore = useAuthStore();
const isMenuOpen = ref(false);

const isLoggedIn = computed(() => authStore.isLoggedIn);
const currentUser = computed(() => authStore.user);

const handleLogout = () => {
  authStore.logout();
  isMenuOpen.value = false;
};

const toggleMenu = () => {
  isMenuOpen.value = !isMenuOpen.value;
};
</script>

<template>
  <nav class="relative z-50 bg-black/20 backdrop-blur-xl border-b border-white/10 shadow-lg">
    <div class="container mx-auto px-6 py-4">
      <div class="flex justify-between items-center">
        <RouterLink to="/" class="group flex items-center space-x-2 transition-all duration-300 hover:scale-105">
          <div class="relative">
            <div class="absolute inset-0 bg-gradient-to-r from-purple-400 to-pink-400 rounded-full blur-lg opacity-75 group-hover:opacity-100 transition-opacity"></div>
            <div class="relative bg-black rounded-full p-2">
              <svg class="w-8 h-8 text-white" fill="currentColor" viewBox="0 0 20 20">
                <path d="M10 12a2 2 0 100-4 2 2 0 000 4z"/>
                <path fill-rule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clip-rule="evenodd"/>
              </svg>
            </div>
          </div>
          <span class="text-2xl font-bold">
            <span class="bg-gradient-to-r from-purple-400 via-pink-400 to-purple-400 bg-clip-text text-transparent">
              Chii2
            </span>
            <span class="text-white ml-1">Vision</span>
          </span>
        </RouterLink>

        <div class="hidden md:flex items-center space-x-1" v-if="isLoggedIn">
          <RouterLink to="/dashboard" 
            class="group relative px-6 py-3 text-white/80 hover:text-white font-medium rounded-xl transition-all duration-300 hover:bg-white/10 hover:shadow-lg hover:shadow-purple-500/25">
            <span class="relative z-10">Панель управления</span>
            <div class="absolute inset-0 bg-gradient-to-r from-purple-500/20 to-pink-500/20 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity"></div>
          </RouterLink>
          
          <RouterLink to="/anomalies"
            class="group relative px-6 py-3 text-white/80 hover:text-white font-medium rounded-xl transition-all duration-300 hover:bg-white/10 hover:shadow-lg hover:shadow-purple-500/25">
            <span class="relative z-10">Аномалии</span>
            <div class="absolute inset-0 bg-gradient-to-r from-purple-500/20 to-pink-500/20 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity"></div>
          </RouterLink>

          <div class="flex items-center space-x-4 ml-6 pl-6 border-l border-white/20">
            <div class="flex items-center space-x-3">
              <div class="relative">
                <div class="w-10 h-10 bg-gradient-to-r from-purple-400 to-pink-400 rounded-full flex items-center justify-center text-white font-bold shadow-lg">
                  {{ currentUser?.username?.charAt(0).toUpperCase() || 'U' }}
                </div>
                <div class="absolute -top-1 -right-1 w-4 h-4 bg-green-400 rounded-full border-2 border-black animate-pulse"></div>
              </div>
              <div class="text-white">
                <div class="font-medium">{{ currentUser?.username || 'Пользователь' }}</div>
                <div class="text-xs text-white/60">Онлайн</div>
              </div>
            </div>

            <button @click="handleLogout"
              class="group relative px-4 py-2 bg-red-500/20 hover:bg-red-500 text-red-300 hover:text-white font-medium rounded-xl border border-red-500/30 hover:border-red-400 transition-all duration-300 hover:shadow-lg hover:shadow-red-500/25">
              <span class="flex items-center space-x-2">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"/>
                </svg>
                <span>Выход</span>
              </span>
            </button>
          </div>
        </div>

        <div class="hidden md:flex items-center space-x-3" v-else>
          <RouterLink to="/login" 
            class="px-6 py-3 text-white/80 hover:text-white font-medium rounded-xl transition-all duration-300 hover:bg-white/10">
            Вход
          </RouterLink>
          <RouterLink to="/register"
            class="px-6 py-3 bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white font-medium rounded-xl shadow-lg hover:shadow-purple-500/25 transition-all duration-300 hover:scale-105">
            Регистрация
          </RouterLink>
        </div>

        <button @click="toggleMenu" class="md:hidden p-2 text-white hover:bg-white/10 rounded-lg transition-colors">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path v-if="!isMenuOpen" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"/>
            <path v-else stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
          </svg>
        </button>
      </div>

      <!-- Mobile menu -->
      <div v-show="isMenuOpen" class="md:hidden mt-4 pb-4 border-t border-white/10 pt-4">
        <div v-if="isLoggedIn" class="space-y-3">
          <RouterLink to="/dashboard" @click="isMenuOpen = false"
            class="block px-4 py-3 text-white/80 hover:text-white hover:bg-white/10 rounded-lg transition-colors">
            Панель управления
          </RouterLink>
          <RouterLink to="/anomalies" @click="isMenuOpen = false"
            class="block px-4 py-3 text-white/80 hover:text-white hover:bg-white/10 rounded-lg transition-colors">
            Аномалии
          </RouterLink>
          <div class="px-4 py-2 text-white/60 text-sm border-t border-white/10 mt-3 pt-3">
            Привет, {{ currentUser?.username || 'Пользователь' }}!
          </div>
          <button @click="handleLogout"
            class="block w-full text-left px-4 py-3 text-red-300 hover:text-red-100 hover:bg-red-500/20 rounded-lg transition-colors">
            Выход
          </button>
        </div>
        <div v-else class="space-y-3">
          <RouterLink to="/login" @click="isMenuOpen = false"
            class="block px-4 py-3 text-white/80 hover:text-white hover:bg-white/10 rounded-lg transition-colors">
            Вход
          </RouterLink>
          <RouterLink to="/register" @click="isMenuOpen = false"
            class="block px-4 py-3 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg transition-colors">
            Регистрация
          </RouterLink>
        </div>
      </div>
    </div>
  </nav>
</template>
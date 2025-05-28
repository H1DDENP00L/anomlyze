// src/components/Navbar.vue
<script setup lang="ts">
import { RouterLink } from 'vue-router';
import { useAuthStore } from '@/stores/auth'; 
import { computed } from 'vue'; 

const authStore = useAuthStore();

const isLoggedIn = computed(() => authStore.isLoggedIn);
const currentUser = computed(() => authStore.user); 


const handleLogout = () => {
  authStore.logout();
};
</script>

<template>
  <nav class="bg-white shadow-md">
    <div class="container mx-auto px-6 py-3 flex justify-between items-center">
      <RouterLink to="/" class="text-xl font-semibold text-gray-700">
        <span class="text-purple-600">Chii2</span> Vision
      </RouterLink>

      <div>
        <div v-if="isLoggedIn">
          <span v-if="currentUser && currentUser.username" class="text-gray-700 mr-4">
            Привет, {{ currentUser.username }}!
          </span>
          <span v-else-if="currentUser" class="text-gray-700 mr-4">
            Вы вошли (ID: {{ currentUser.id }}) 
          </span>
          <span v-else class="text-gray-700 mr-4">
            Вы вошли! 
          </span>
          
          <button 
            @click="handleLogout" 
            class="bg-red-500 hover:bg-red-700 text-white font-bold py-2 px-4 rounded text-sm"
          >
            Выход
          </button>
        </div>
        <div v-else>
          <RouterLink to="/login" class="text-gray-700 hover:text-purple-600 px-3 py-2 rounded-md text-sm font-medium">
            Вход
          </RouterLink>
          <RouterLink to="/register" class="ml-2 bg-purple-600 hover:bg-purple-700 text-white font-bold py-2 px-4 rounded text-sm">
            Регистрация
          </RouterLink>
        </div>
      </div>
    </div>
  </nav>
</template>
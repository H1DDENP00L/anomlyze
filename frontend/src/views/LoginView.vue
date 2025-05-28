<script setup lang="ts">
import { ref } from 'vue';
import { RouterLink } from 'vue-router';
import { useAuthStore } from '@/stores/auth'; 

const username = ref('');
const password = ref('');
const authStore = useAuthStore(); 
const errorMessage = ref<string | null>(null); // Для отображения ошибок с API

const handleSubmit = async () => {
  errorMessage.value = null; 
  if (!username.value || !password.value) {
    errorMessage.value = "Имя пользователя и пароль обязательны.";
    return;
  }

  const result = await authStore.login({ 
    username: username.value, 
    password: password.value 
  });

  if (!result.success) {
    errorMessage.value = result.error || "Ошибка входа. Попробуйте снова.";
  }
  
};
</script>

<template>
  <div class="flex items-center justify-center min-h-[calc(100vh-var(--navbar-height,64px))]">
    <div class="w-full max-w-md px-8 py-6 bg-white shadow-lg rounded-lg">
      <h3 class="text-2xl font-bold text-center text-gray-800">Войти в аккаунт</h3>
      <p class="mt-1 text-center text-sm text-gray-600">
        Или <router-link to="/register" class="font-medium text-purple-600 hover:text-purple-500">зарегистрируйтесь</router-link>
      </p>

      <form class="mt-8 space-y-6" @submit.prevent="handleSubmit">
        <div>
          <label for="username" class="block text-sm font-medium text-gray-700">Имя пользователя</label>
          <div class="mt-1">
            <input 
              id="username" 
              name="username" 
              type="text" 
              v-model="username"
              required 
              class="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-purple-500 focus:border-purple-500 sm:text-sm"
              placeholder="Ваше имя пользователя"
            />
          </div>
        </div>

        <div>
          <label for="password" class="block text-sm font-medium text-gray-700">Пароль</label>
          <div class="mt-1">
            <input 
              id="password" 
              name="password" 
              type="password" 
              v-model="password"
              required 
              class="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-purple-500 focus:border-purple-500 sm:text-sm"
              placeholder="Ваш пароль"
            />
          </div>
        </div>

        <div v-if="errorMessage" class="text-red-500 text-sm text-center">
          {{ errorMessage }}
        </div>
        <div v-if="authStore.authStatus === 'loading'" class="text-purple-600 text-sm text-center">
          Вход...
        </div>

        <div>
          <button 
            type="submit" 
            :disabled="authStore.authStatus === 'loading'"
            class="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-purple-600 hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500 disabled:opacity-50"
          >
            Войти
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<style scoped>
/* :root { --navbar-height: 64px; } */ 
</style>
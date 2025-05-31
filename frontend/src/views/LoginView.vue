<script setup lang="ts">
import { ref } from 'vue';
import { RouterLink } from 'vue-router';
import { useAuthStore } from '@/stores/auth'; 

const username = ref('');
const password = ref('');
const authStore = useAuthStore(); 
const errorMessage = ref<string | null>(null);

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
  <div class="min-h-screen bg-gradient-to-br from-purple-100 via-white to-indigo-100 flex items-center justify-center py-12 px-4">
    <div class="max-w-md w-full space-y-8">
      <div class="bg-white rounded-2xl shadow-xl p-8 border border-gray-100">
        <!-- Заголовок -->
        <div class="text-center mb-8">
          <h2 class="text-3xl font-bold text-gray-900 mb-2">Добро пожаловать</h2>
          <p class="text-gray-600">
            Войдите в свой аккаунт или 
            <router-link to="/register" class="font-semibold text-purple-600 hover:text-purple-800 transition-colors">
              создайте новый
            </router-link>
          </p>
        </div>

        <!-- Форма -->
        <form @submit.prevent="handleSubmit" class="space-y-6">
          <!-- Поле username -->
          <div>
            <label for="username" class="block text-sm font-semibold text-gray-800 mb-2">
              Имя пользователя
            </label>
            <input 
              id="username" 
              name="username" 
              type="text" 
              v-model="username"
              required 
              class="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:border-purple-500 focus:ring-0 transition-colors placeholder-gray-500 text-gray-900 bg-gray-50 focus:bg-white"
              placeholder="Введите имя пользователя"
            />
          </div>

          <!-- Поле password -->
          <div>
            <label for="password" class="block text-sm font-semibold text-gray-800 mb-2">
              Пароль
            </label>
            <input 
              id="password" 
              name="password" 
              type="password" 
              v-model="password"
              required 
              class="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:border-purple-500 focus:ring-0 transition-colors placeholder-gray-500 text-gray-900 bg-gray-50 focus:bg-white"
              placeholder="Введите пароль"
            />
          </div>

          <!-- Ошибка -->
          <div v-if="errorMessage" class="bg-red-50 border border-red-200 rounded-lg p-3">
            <p class="text-red-700 text-sm font-medium">{{ errorMessage }}</p>
          </div>

          <!-- Загрузка -->
          <div v-if="authStore.authStatus === 'loading'" class="bg-purple-50 border border-purple-200 rounded-lg p-3">
            <p class="text-purple-700 text-sm font-medium flex items-center justify-center">
              <svg class="animate-spin -ml-1 mr-3 h-4 w-4 text-purple-700" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Выполняется вход...
            </p>
          </div>

          <!-- Кнопка -->
          <button 
            type="submit" 
            :disabled="authStore.authStatus === 'loading'"
            class="w-full py-3 px-4 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white font-semibold rounded-lg shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 transition-all duration-200 disabled:opacity-50 disabled:transform-none disabled:hover:shadow-lg"
          >
            Войти в аккаунт
          </button>
        </form>
      </div>
      
      <!-- Дополнительная информация -->
      <div class="text-center">
        <p class="text-sm text-gray-600">
          Забыли пароль? 
          <a href="#" class="font-semibold text-purple-600 hover:text-purple-800 transition-colors">
            Восстановить
          </a>
        </p>
      </div>
    </div>
  </div>
</template>

<style scoped>
input:focus {
  outline: none;
  box-shadow: none;
}

button:active {
  transform: translateY(0);
}
</style>
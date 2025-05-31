<script setup lang="ts">
import { ref } from 'vue';
import { RouterLink } from 'vue-router';
import { useAuthStore } from '@/stores/auth'; 

const username = ref('');
const email = ref('');
const password = ref('');
const confirmPassword = ref('');
const authStore = useAuthStore();
const errorMessage = ref<string | null>(null);
const successMessage = ref<string | null>(null);

const handleSubmit = async () => {
  errorMessage.value = null;
  successMessage.value = null;

  if (!username.value || !email.value || !password.value || !confirmPassword.value) {
    errorMessage.value = "Все поля обязательны для заполнения.";
    return;
  }
  if (password.value !== confirmPassword.value) {
    errorMessage.value = "Пароли не совпадают!";
    return;
  }

  const result = await authStore.register({
    username: username.value,
    email: email.value,
    password: password.value
  });

  if (result.success) {
    successMessage.value = "Регистрация прошла успешно!";
  } else {
    errorMessage.value = result.error || "Ошибка регистрации. Попробуйте снова.";
  }
};
</script>

<template>
  <div class="min-h-screen bg-gradient-to-br from-emerald-100 via-white to-blue-100 flex items-center justify-center py-12 px-4">
    <div class="max-w-md w-full space-y-8">
      <div class="bg-white rounded-2xl shadow-xl p-8 border border-gray-100">
        <div class="text-center mb-8">
          <h2 class="text-3xl font-bold text-gray-900 mb-2">Создать аккаунт</h2>
          <p class="text-gray-600">
            Уже есть аккаунт? 
            <router-link to="/login" class="font-semibold text-emerald-600 hover:text-emerald-800 transition-colors">
              Войти
            </router-link>
          </p>
        </div>

        <form @submit.prevent="handleSubmit" class="space-y-5">
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
              class="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:border-emerald-500 focus:ring-0 transition-colors placeholder-gray-500 text-gray-900 bg-gray-50 focus:bg-white"
              placeholder="Придумайте имя пользователя"
            />
          </div>

          <div>
            <label for="email" class="block text-sm font-semibold text-gray-800 mb-2">
              Email адрес
            </label>
            <input 
              id="email" 
              name="email" 
              type="email" 
              v-model="email"
              required 
              class="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:border-emerald-500 focus:ring-0 transition-colors placeholder-gray-500 text-gray-900 bg-gray-50 focus:bg-white"
              placeholder="you@example.com"
            />
          </div>

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
              class="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:border-emerald-500 focus:ring-0 transition-colors placeholder-gray-500 text-gray-900 bg-gray-50 focus:bg-white"
              placeholder="Минимум 6 символов"
            />
          </div>

          <div>
            <label for="confirm-password" class="block text-sm font-semibold text-gray-800 mb-2">
              Повторите пароль
            </label>
            <input 
              id="confirm-password" 
              name="confirm-password" 
              type="password" 
              v-model="confirmPassword"
              required 
              class="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:border-emerald-500 focus:ring-0 transition-colors placeholder-gray-500 text-gray-900 bg-gray-50 focus:bg-white"
              placeholder="Повторите пароль"
            />
          </div>

          <div v-if="errorMessage" class="bg-red-50 border border-red-200 rounded-lg p-3">
            <p class="text-red-700 text-sm font-medium">{{ errorMessage }}</p>
          </div>

          <div v-if="successMessage" class="bg-green-50 border border-green-200 rounded-lg p-3">
            <p class="text-green-700 text-sm font-medium">{{ successMessage }}</p>
          </div>

          <div v-if="authStore.authStatus === 'loading'" class="bg-emerald-50 border border-emerald-200 rounded-lg p-3">
            <p class="text-emerald-700 text-sm font-medium flex items-center justify-center">
              <svg class="animate-spin -ml-1 mr-3 h-4 w-4 text-emerald-700" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Создание аккаунта...
            </p>
          </div>

          <button 
            type="submit" 
            :disabled="authStore.authStatus === 'loading'"
            class="w-full py-3 px-4 bg-gradient-to-r from-emerald-600 to-blue-600 hover:from-emerald-700 hover:to-blue-700 text-white font-semibold rounded-lg shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 transition-all duration-200 disabled:opacity-50 disabled:transform-none disabled:hover:shadow-lg"
          >
            Создать аккаунт
          </button>
        </form>
      </div>
      
      <div class="text-center">
        <p class="text-sm text-gray-600">
          Нажимая "Создать аккаунт", вы соглашаетесь с 
          <a href="#" class="font-semibold text-emerald-600 hover:text-emerald-800 transition-colors">
            условиями использования
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
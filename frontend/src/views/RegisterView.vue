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
   
  } else {
    errorMessage.value = result.error || "Ошибка регистрации. Попробуйте снова.";
  }
};
</script>

<template>
  <div class="flex items-center justify-center min-h-[calc(100vh-var(--navbar-height,64px))]">
    <div class="w-full max-w-md px-8 py-6 bg-white shadow-lg rounded-lg">
      <h3 class="text-2xl font-bold text-center text-gray-800">Создать аккаунт</h3>
      <p class="mt-1 text-center text-sm text-gray-600">
        Уже есть аккаунт? <router-link to="/login" class="font-medium text-purple-600 hover:text-purple-500">Войти</router-link>
      </p>

      <form class="mt-8 space-y-6" @submit.prevent="handleSubmit">
        <div>
          <label for="username" class="block text-sm font-medium text-gray-700">Имя пользователя</label>
          <input id="username" name="username" type="text" v-model="username" required class="mt-1 appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-purple-500 focus:border-purple-500 sm:text-sm" placeholder="Придумайте имя пользователя"/>
        </div>

        <div>
          <label for="email" class="block text-sm font-medium text-gray-700">Email адрес</label>
          <input id="email" name="email" type="email" v-model="email" required class="mt-1 appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-purple-500 focus:border-purple-500 sm:text-sm" placeholder="you@example.com"/>
        </div>

        <div>
          <label for="password" class="block text-sm font-medium text-gray-700">Пароль</label>
          <input id="password" name="password" type="password" v-model="password" required class="mt-1 appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-purple-500 focus:border-purple-500 sm:text-sm" placeholder="Придумайте пароль (мин. 6 символов)"/>
        </div>

        <div>
          <label for="confirm-password" class="block text-sm font-medium text-gray-700">Повторите пароль</label>
          <input id="confirm-password" name="confirm-password" type="password" v-model="confirmPassword" required class="mt-1 appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-purple-500 focus:border-purple-500 sm:text-sm" placeholder="Повторите пароль"/>
        </div>

        <div v-if="errorMessage" class="text-red-500 text-sm text-center">
          {{ errorMessage }}
        </div>
        <div v-if="successMessage" class="text-green-500 text-sm text-center">
          {{ successMessage }}
        </div>
        <div v-if="authStore.authStatus === 'loading'" class="text-purple-600 text-sm text-center">
          Регистрация...
        </div>

        <div>
          <button type="submit" :disabled="authStore.authStatus === 'loading'" class="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-purple-600 hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500 disabled:opacity-50">
            Зарегистрироваться
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<style scoped>
/* :root { --navbar-height: 64px; } */
</style>
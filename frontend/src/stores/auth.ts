import { defineStore } from 'pinia'
import axios from 'axios' 
import router from '@/router' 

const API_URL = '/auth' 

interface User {
  id: number;
  username: string;
  email: string; 
}

interface AuthState {
  token: string | null;
  user: User | null; // Информация о залогиненном пользователе
  status: 'idle' | 'loading' | 'succeeded' | 'failed'; // Статус запроса
  error: string | null; // Сообщение об ошибке
}

export const useAuthStore = defineStore('auth', {
    state: (): AuthState => ({
      token: localStorage.getItem('authToken') || null,
      // Загружаем user из localStorage, если он там был сохранен
      user: JSON.parse(localStorage.getItem('authUser') || 'null'), 
      status: 'idle',
      error: null,
    }),

  getters: {
    isLoggedIn: (state) => !!state.token, // Проверяем, есть ли токен
    authStatus: (state) => state.status,
    getUser: (state) => state.user,
    getToken: (state) => state.token,
    getError: (state) => state.error,
  },

  actions: {
    async fetchCurrentUser() {
      if (!this.token) {
        return; // Нет токена - нет пользователя
      }
      this.status = 'loading'; 
      try {
        const response = await axios.get(`${API_URL}/me`); 
        this.user = response.data as User; 
        localStorage.setItem('authUser', JSON.stringify(this.user));
        this.status = 'succeeded';
      } catch (error: any) {
        console.error('Failed to fetch user data:', error);
        this.error = error.response?.data?.error || error.message || 'Failed to fetch user data';
        this.logout(); 
        this.status = 'failed';
      }
    },

    async register(payload: any) {
      this.status = 'loading';
      this.error = null;
      try {
        const response = await axios.post(`${API_URL}/register`, payload);
        const { access_token, user_id, message } = response.data;
        
        this.token = access_token;
        localStorage.setItem('authToken', access_token);
        axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;

        const registeredUser: User = { 
            id: user_id, 
            username: payload.username, 
            email: payload.email.toLowerCase() 
        };
        this.user = registeredUser;
        localStorage.setItem('authUser', JSON.stringify(registeredUser));

        this.status = 'succeeded';
        router.push('/dashboard');
        return { success: true, message: message || "Registration successful" };
      } catch (error: any) {
        this.status = 'failed';
        const errorMessage = error.response?.data?.error || error.message || 'Registration failed';
        this.error = errorMessage;
        console.error('Registration error:', error);
        return { success: false, error: errorMessage, message: undefined };
      }
    },

    async login(payload: any) {
      this.status = 'loading';
      this.error = null;
      try {
        const response = await axios.post(`${API_URL}/login`, payload);
        const { access_token } = response.data;

        this.token = access_token;
        localStorage.setItem('authToken', access_token);
        axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
        
        await this.fetchCurrentUser(); 

        // Редирект только если пользователь успешно загружен (т.е. fetchCurrentUser не вызвал logout)
        if (this.isLoggedIn) { 
            this.status = 'succeeded';
            router.push('/dashboard');
            return { success: true };
        } else {

            return { success: false, error: this.error || "Login succeeded but failed to fetch user data." };
        }

      } catch (error: any) {
        this.status = 'failed';
        const errorMessage = error.response?.data?.error || error.message || 'Login failed';
        this.error = errorMessage;
        console.error('Login error:', error);
        return { success: false, error: errorMessage };
      }
    },

    logout() {
        this.token = null;
        this.user = null;
        localStorage.removeItem('authToken');
        localStorage.removeItem('authUser');
        delete axios.defaults.headers.common['Authorization'];
        this.status = 'idle';
        router.push('/login');
      },
  
      async initializeAuth() {
        const token = localStorage.getItem('authToken');
        
        if (token) {
          this.token = token;
          axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
          await this.fetchCurrentUser(); 
          // Если токен невалидный, fetchCurrentUser вызовет logout и очистит состояние.
        }
      }
    },
  })
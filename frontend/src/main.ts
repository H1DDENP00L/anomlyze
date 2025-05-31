// src/main.ts
import './assets/main.css'
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import { useAuthStore } from './stores/auth' 
import axios from 'axios';
import type { AxiosResponse, AxiosError } from 'axios'; 

axios.defaults.baseURL = 'http://localhost:5000'; 
axios.defaults.headers.post['Content-Type'] = 'application/json';
axios.interceptors.response.use(
  (response: AxiosResponse) => response,
  (error: AxiosError) => {
    if (error.response && error.response.status === 401) {
      console.error('Axios interceptor: 401 Unauthorized.');
 
    }
    return Promise.reject(error);
  }
);

const app = createApp(App)

app.use(createPinia()) 
app.use(router)      


const authStore = useAuthStore(); 
authStore.initializeAuth().then(() => {
  app.mount('#app'); 
}).catch(error => {
  console.error("Failed to initialize auth state:", error);
  app.mount('#app'); 
});
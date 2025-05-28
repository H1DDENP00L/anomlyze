<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, watch } from 'vue';
import { useAuthStore } from '@/stores/auth';
import axios from 'axios'; 

// --- Состояние компонента ---
const authStore = useAuthStore();
const videoFile = ref<File | null>(null);
const rtspUrl = ref('');
const processingStatus = ref<any>(null); // Будет содержать ответ от /status
const currentError = ref<string | null>(null);
const currentSourceInfo = ref<string | null>(null); 

const isLoading = ref(false); 

const isProcessing = computed(() => processingStatus.value?.is_running === true);
const videoStreamUrl = computed(() => {
  if (isProcessing.value && authStore.token) {
    // Передаем токен как query-параметр для MJPEG стрима
    return `http://localhost:5000/video_feed?token=${authStore.token}`;
  }
  return null;
});

const handleFileChange = (event: Event) => {
  const target = event.target as HTMLInputElement;
  if (target.files && target.files[0]) {
    videoFile.value = target.files[0];
    rtspUrl.value = ''; // Очищаем RTSP, если выбран файл
    currentError.value = null;
  }
};

const clearFileInput = () => {
  videoFile.value = null;
  const fileInput = document.getElementById('videoFile') as HTMLInputElement;
  if (fileInput) {
    fileInput.value = ''; 
  }
}

const uploadVideo = async () => {
  if (!videoFile.value) {
    currentError.value = "Пожалуйста, выберите видеофайл для загрузки.";
    return;
  }
  isLoading.value = true;
  currentError.value = null;
  const formData = new FormData();
  formData.append('file', videoFile.value);

  try {
    const response = await axios.post('http://localhost:5000/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data', 
      }
    });
    
    currentSourceInfo.value = `Обрабатывается файл: ${response.data.source.split('\\').pop().split('/').pop()}`; 
    clearFileInput(); 
  } catch (error: any) {
    currentError.value = error.response?.data?.error || error.message || "Ошибка загрузки видео.";
    console.error('Upload error:', error);
  } finally {
    isLoading.value = false;
  }
};

const startRtspStream = async () => {
  if (!rtspUrl.value.trim()) {
    currentError.value = "Пожалуйста, введите RTSP URL.";
    return;
  }
  if (!rtspUrl.value.startsWith('rtsp://')) {
    currentError.value = "RTSP URL должен начинаться с rtsp://";
    return;
  }
  isLoading.value = true;
  currentError.value = null;
  try {
    const response = await axios.post('http://localhost:5000/start_rtsp', { rtsp_url: rtspUrl.value });
    // console.log('RTSP start response:', response.data);
    currentSourceInfo.value = `Подключено к камере: ${rtspUrl.value}`;
    // fetchStatus();
  } catch (error: any) {
    currentError.value = error.response?.data?.error || error.message || "Ошибка подключения к RTSP.";
    console.error('RTSP start error:', error);
  } finally {
    isLoading.value = false;
  }
};

const stopProcessing = async () => {
  isLoading.value = true;
  currentError.value = null;
  try {
    await axios.post('http://localhost:5000/stop');
    // console.log('Stop response:', response.data);
    currentSourceInfo.value = null; 
    // fetchStatus(); // Статус обновится автоматически
  } catch (error: any) {
    currentError.value = error.response?.data?.error || error.message || "Ошибка остановки обработки.";
    console.error('Stop error:', error);
  } finally {
    isLoading.value = false;
  }
};

let statusInterval: number | undefined;

const fetchStatus = async () => {
  if (!authStore.isLoggedIn) return; // Не делаем запросы, если не залогинены
  try {
    const response = await axios.get('http://localhost:5000/status');
    processingStatus.value = response.data;
    if (response.data.is_running) {
      if (response.data.source_type === 'file') {
        currentSourceInfo.value = `Обрабатывается файл: ${response.data.input_path?.split('\\').pop().split('/').pop()}`;
      } else if (response.data.source_type === 'rtsp') {
        currentSourceInfo.value = `Подключено к камере: ${response.data.input_path}`;
      }
    } else {
        if(processingStatus.value?.error) { 
            currentError.value = `Ошибка на сервере: ${processingStatus.value.error}`;
        } else if (currentSourceInfo.value && !response.data.is_running){
            currentSourceInfo.value += " (Завершено)";
        }
    }
  } catch (error: any) {
    console.error('Error fetching status:', error);
    currentError.value = "Не удалось получить статус обработки.";
  }
};

// --- Lifecycle Hooks ---
onMounted(() => {
  fetchStatus(); 
  statusInterval = window.setInterval(fetchStatus, 3000); 
});

onUnmounted(() => {
  if (statusInterval) {
    clearInterval(statusInterval); 
  }
});

// Следим за ошибкой в processingStatus от сервера
watch(() => processingStatus.value?.error, (newError) => {
    if (newError) {
        currentError.value = `Ошибка от сервера: ${newError}`;
    }
});

</script>

<template>
  <div class="p-4 md:p-8 space-y-8">
    <h1 class="text-3xl font-bold text-gray-800">Выявление аномалий с камер</h1>
    <p class="text-gray-600">Здесь вы можете загрузить ваше видео либо подключиться к камере.</p>

    <!-- Секция управления -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6 items-start">
      <!-- Левая колонка: Загрузка и RTSP -->
      <div class="space-y-6 bg-white p-6 shadow-md rounded-lg">
        <div>
          <label for="videoFile" class="block text-sm font-medium text-gray-700 mb-1">Загрузить видео (MP4, AVI, MOV, MKV)</label>
          <input 
            type="file" 
            id="videoFile"
            @change="handleFileChange" 
            accept=".mp4,.avi,.mov,.mkv"
            class="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-purple-50 file:text-purple-700 hover:file:bg-purple-100 disabled:opacity-50"
            :disabled="isProcessing || isLoading"
          />
          <button 
            @click="uploadVideo" 
            :disabled="!videoFile || isProcessing || isLoading"
            class="mt-3 w-full sm:w-auto inline-flex justify-center items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-purple-600 hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500 disabled:bg-gray-300"
          >
            <span v-if="isLoading && videoFile">Загрузка...</span>
            <span v-else>Загрузить и обработать</span>
          </button>
        </div>

        <div class="text-center text-gray-500">ИЛИ</div>

        <div>
          <label for="rtspUrl" class="block text-sm font-medium text-gray-700 mb-1">Подключиться к камере (RTSP URL)</label>
          <input 
            type="text" 
            id="rtspUrl"
            v-model="rtspUrl" 
            placeholder="rtsp://..."
            class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-purple-500 focus:border-purple-500 sm:text-sm disabled:bg-gray-50"
            :disabled="isProcessing || isLoading"
            @input="videoFile = null; clearFileInput()" 
          />
          <button 
            @click="startRtspStream" 
            :disabled="!rtspUrl.trim() || isProcessing || isLoading"
            class="mt-3 w-full sm:w-auto inline-flex justify-center items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-teal-600 hover:bg-teal-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-teal-500 disabled:bg-gray-300"
          >
            <span v-if="isLoading && rtspUrl.trim()">Подключение...</span>
            <span v-else>Подключиться и обработать</span>
          </button>
        </div>
      </div>

      <!-- Правая колонка: Статус и кнопка Стоп -->
      <div class="space-y-4 bg-white p-6 shadow-md rounded-lg">
        <h2 class="text-xl font-semibold text-gray-700">Статус обработки</h2>
        <div v-if="currentSourceInfo" class="text-sm text-gray-700 bg-indigo-50 p-3 rounded-md">
          <p class="font-medium">Текущий источник:</p>
          <p class="break-all">{{ currentSourceInfo }}</p>
        </div>
        <div v-if="isProcessing" class="flex items-center text-green-600">
          <svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-green-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          Обработка в процессе...
        </div>
        <div v-else-if="!isProcessing && processingStatus && processingStatus.input_path" class="text-blue-600">
          Обработка завершена.
        </div>
         <div v-else-if="!isProcessing && !processingStatus?.input_path && !currentError" class="text-gray-500">
          Система готова к работе.
        </div>

        <div v-if="currentError" class="mt-2 text-sm text-red-600 bg-red-50 p-3 rounded-md">
          <p class="font-medium">Ошибка:</p>
          <p>{{ currentError }}</p>
        </div>

        <button 
          v-if="isProcessing"
          @click="stopProcessing" 
          :disabled="isLoading"
          class="mt-4 w-full inline-flex justify-center items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:bg-gray-300"
        >
          <span v-if="isLoading">Остановка...</span>
          <span v-else>Остановить обработку</span>
        </button>
      </div>
    </div>

    <!-- Секция видео -->
    <div class="mt-8 bg-black rounded-lg shadow-xl overflow-hidden">
      <h2 class="text-xl font-semibold text-white p-4 bg-gray-800 rounded-t-lg">Видеопоток</h2>
      <div class="aspect-w-16 aspect-h-9">
        <img 
          v-if="videoStreamUrl" 
          :src="videoStreamUrl" 
          alt="Видеопоток" 
          class="w-full h-full object-contain"
          @error="currentError = 'Ошибка загрузки видеопотока. Убедитесь, что обработка запущена и сервер доступен.'"
        />
        <div v-else class="flex items-center justify-center h-full bg-gray-700 min-h-[300px]">
          <p class="text-gray-400">Видеопоток неактивен. Запустите обработку.</p>
        </div>
      </div>
    </div>

  </div>
</template>

<style scoped>

.aspect-w-16 { --tw-aspect-w: 16; }
.aspect-h-9 { --tw-aspect-h: 9; }
@supports (aspect-ratio: 16 / 9) {
  .aspect-w-16.aspect-h-9 {
    aspect-ratio: 16 / 9;
    --tw-aspect-w: auto; 
    --tw-aspect-h: auto;
  }
}
.aspect-w-16 {
    position: relative;
    padding-bottom: calc(var(--tw-aspect-h, 9) / var(--tw-aspect-w, 16) * 100%);
}
.aspect-w-16 > * {
    position: absolute;
    height: 100%;
    width: 100%;
    top: 0px;
    right: 0px;
    bottom: 0px;
    left: 0px;
}

input[type="file"]::-webkit-file-upload-button,
input[type="file"]::file-selector-button {
}
</style>
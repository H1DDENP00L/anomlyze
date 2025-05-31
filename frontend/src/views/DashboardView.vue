<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, watch } from 'vue';
import { useAuthStore } from '@/stores/auth';
import axios from 'axios'; 

// --- Состояние компонента ---
const authStore = useAuthStore();
const videoFile = ref<File | null>(null);
const rtspUrl = ref('');
const processingStatus = ref<any>(null);
const currentError = ref<string | null>(null);
const currentSourceInfo = ref<string | null>(null); 
const isLoading = ref(false); 
const dragOver = ref(false);

const isProcessing = computed(() => processingStatus.value?.is_running === true);
const videoStreamUrl = computed(() => {
  if (isProcessing.value && authStore.token) {
    return `http://localhost:5000/video_feed?token=${authStore.token}`;
  }
  return null;
});

// Drag & Drop handlers
const handleDragOver = (e: DragEvent) => {
  e.preventDefault();
  dragOver.value = true;
};

const handleDragLeave = (e: DragEvent) => {
  e.preventDefault();
  dragOver.value = false;
};

const handleDrop = (e: DragEvent) => {
  e.preventDefault();
  dragOver.value = false;
  const files = e.dataTransfer?.files;
  if (files && files[0]) {
    videoFile.value = files[0];
    rtspUrl.value = '';
    currentError.value = null;
  }
};

const handleFileChange = (event: Event) => {
  const target = event.target as HTMLInputElement;
  if (target.files && target.files[0]) {
    videoFile.value = target.files[0];
    rtspUrl.value = '';
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
    currentSourceInfo.value = `Подключено к камере: ${rtspUrl.value}`;
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
    currentSourceInfo.value = null; 
  } catch (error: any) {
    currentError.value = error.response?.data?.error || error.message || "Ошибка остановки обработки.";
    console.error('Stop error:', error);
  } finally {
    isLoading.value = false;
  }
};

let statusInterval: number | undefined;

const fetchStatus = async () => {
  if (!authStore.isLoggedIn) return;
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

onMounted(() => {
  fetchStatus(); 
  statusInterval = window.setInterval(fetchStatus, 3000); 
});

onUnmounted(() => {
  if (statusInterval) {
    clearInterval(statusInterval); 
  }
});

watch(() => processingStatus.value?.error, (newError) => {
    if (newError) {
        currentError.value = `Ошибка от сервера: ${newError}`;
    }
});
</script>

<template>
  <div class="min-h-screen bg-gray-50 p-4">
    <div class="max-w-7xl mx-auto space-y-4">
      <div class="text-center space-y-2">
        <div class="inline-flex items-center space-x-2 px-3 py-1.5 bg-green-100 rounded-full border border-green-200">
          <div class="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
          <span class="text-green-700 text-sm font-medium">Система активна</span>
        </div>
        <h1 class="text-2xl md:text-3xl font-bold text-gray-800">
          Выявление аномалий
        </h1>
        <p class="text-gray-600 text-sm max-w-2xl mx-auto">
          Загрузите видео или подключитесь к камере для обнаружения аномалий
        </p>
      </div>

      <!-- Основные контролы -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <!-- Загрузка файла -->
        <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <div class="flex items-center space-x-2 mb-3">
            <div class="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
              <svg class="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"/>
              </svg>
            </div>
            <h2 class="text-lg font-semibold text-gray-800">Загрузка файла</h2>
          </div>

          <!-- зона загрузки -->
          <div 
            @dragover="handleDragOver"
            @dragleave="handleDragLeave"
            @drop="handleDrop"
            :class="[
              'relative border-2 border-dashed rounded-lg p-4 text-center transition-all cursor-pointer text-sm',
              dragOver 
                ? 'border-blue-400 bg-blue-50' 
                : 'border-gray-300 hover:border-blue-400 hover:bg-gray-50'
            ]"
          >
            <input 
              type="file" 
              id="videoFile"
              @change="handleFileChange" 
              accept=".mp4,.avi,.mov,.mkv"
              class="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              :disabled="isProcessing || isLoading"
            />
            
            <div class="space-y-2">
              <div class="w-10 h-10 mx-auto bg-blue-100 rounded-full flex items-center justify-center">
                <svg class="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"/>
                </svg>
              </div>
              
              <div v-if="videoFile" class="text-gray-700">
                <div class="font-medium">✅ {{ videoFile.name }}</div>
                <div class="text-xs text-gray-500">{{ (videoFile.size / 1024 / 1024).toFixed(2) }} MB</div>
              </div>
              <div v-else class="text-gray-500">
                <div class="font-medium">Перетащите файл или кликните</div>
                <div class="text-xs">MP4, AVI, MOV, MKV</div>
              </div>
            </div>
          </div>

          <button 
            @click="uploadVideo" 
            :disabled="!videoFile || isProcessing || isLoading"
            class="w-full mt-3 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-medium rounded-lg transition-colors text-sm"
          >
            <div v-if="isLoading && videoFile" class="flex items-center justify-center space-x-2">
              <svg class="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="m4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <span>Загружаем...</span>
            </div>
            <span v-else>Загрузить и обработать</span>
          </button>
        </div>

        <!-- RTSP подключение -->
        <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <div class="flex items-center space-x-2 mb-3">
            <div class="w-8 h-8 bg-red-100 rounded-lg flex items-center justify-center">
              <svg class="w-4 h-4 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"/>
              </svg>
            </div>
            <h2 class="text-lg font-semibold text-gray-800">Подключение к камере</h2>
          </div>

          <div class="space-y-3">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">RTSP URL</label>
              <input
                type="text"
                v-model="rtspUrl"
                placeholder="rtsp://username:password@ip:port/stream"
                class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm text-gray-900 placeholder-gray-600 focus:border-red-500 focus:ring-1 focus:ring-red-500 focus:outline-none"
                :disabled="isProcessing || isLoading"
                @input="videoFile = null; clearFileInput()"
              />
              <div class="mt-1 text-xs text-gray-800">
                Пример: rtsp://admin:12345@192.168.1.100:554/stream1
              </div>
            </div>

            <button 
              @click="startRtspStream" 
              :disabled="!rtspUrl.trim() || isProcessing || isLoading"
              class="w-full px-4 py-2 bg-red-600 hover:bg-red-700 disabled:bg-gray-400 text-white font-medium rounded-lg transition-colors text-sm"
            >
              <div v-if="isLoading && rtspUrl.trim()" class="flex items-center justify-center space-x-2">
                <svg class="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="m4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <span>Подключаемся...</span>
              </div>
              <span v-else>Подключиться и обработать</span>
            </button>
          </div>
        </div>
      </div>

      <!-- Компактный статус -->
      <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <div class="flex items-center justify-between mb-3">
          <div class="flex items-center space-x-2">
            <div class="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center">
              <svg class="w-4 h-4 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
              </svg>
            </div>
            <h2 class="text-lg font-semibold text-gray-800">Статус системы</h2>
          </div>
          
          <button 
            v-if="isProcessing"
            @click="stopProcessing" 
            :disabled="isLoading"
            class="px-4 py-2 bg-red-600 hover:bg-red-700 disabled:bg-gray-400 text-white font-medium rounded-lg transition-colors text-sm"
          >
            <div v-if="isLoading" class="flex items-center space-x-2">
              <svg class="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="m4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <span>Остановка...</span>
            </div>
            <span v-else>Остановить</span>
          </button>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
          <!-- Источник -->
          <div class="bg-gray-50 border border-gray-200 rounded-lg p-3">
            <h3 class="text-xs font-medium text-gray-600 mb-1">Источник</h3>
            <div v-if="currentSourceInfo" class="text-sm text-gray-800 font-medium break-all">
              {{ currentSourceInfo }}
            </div>
            <div v-else class="text-sm text-gray-400">
              Не выбран
            </div>
          </div>

          <!-- Статус -->
          <div class="bg-gray-50 border border-gray-200 rounded-lg p-3">
            <h3 class="text-xs font-medium text-gray-600 mb-1">Обработка</h3>
            <div v-if="isProcessing" class="flex items-center text-green-600 text-sm">
              <svg class="animate-spin w-3 h-3 mr-1" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="m4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <span class="font-medium">Активна</span>
            </div>
            <div v-else-if="!isProcessing && processingStatus && processingStatus.input_path" class="text-blue-600 font-medium text-sm">
              ✅ Завершено
            </div>
            <div v-else class="text-gray-600 text-sm">
              🟡 Ожидание
            </div>
          </div>

          <!-- Система -->
          <div class="bg-gray-50 border border-gray-200 rounded-lg p-3">
            <h3 class="text-xs font-medium text-gray-600 mb-1">Система</h3>
            <div class="flex items-center text-green-600 text-sm">
              <div class="w-2 h-2 bg-green-500 rounded-full mr-1 animate-pulse"></div>
              <span class="font-medium">Онлайн</span>
            </div>
          </div>
        </div>

        <!-- Ошибки -->
        <div v-if="currentError" class="mt-3 p-3 bg-red-50 border border-red-200 rounded-lg">
          <div class="flex items-start space-x-2">
            <svg class="w-4 h-4 text-red-500 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
            </svg>
            <div>
              <h4 class="text-red-700 font-medium text-sm">Ошибка</h4>
              <p class="text-red-600 text-xs mt-1">{{ currentError }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Компактный видеопоток -->
      <div class="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <div class="flex items-center justify-between p-3 border-b border-gray-200">
          <div class="flex items-center space-x-2">
            <div class="w-8 h-8 bg-orange-100 rounded-lg flex items-center justify-center">
              <svg class="w-4 h-4 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"/>
              </svg>
            </div>
            <h2 class="text-lg font-semibold text-gray-800">Видеопоток</h2>
          </div>
          
          <div v-if="videoStreamUrl" class="flex items-center space-x-1 text-red-600">
            <div class="w-2 h-2 bg-red-500 rounded-full animate-pulse"></div>
            <span class="text-xs font-medium">LIVE</span>
          </div>
        </div>

        <div class="relative bg-gray-900 aspect-video">
          <img 
            v-if="videoStreamUrl" 
            :src="videoStreamUrl" 
            alt="Видеопоток" 
            class="w-full h-full object-contain"
            @error="currentError = 'Ошибка загрузки видеопотока'"
          />
          <div v-else class="absolute inset-0 flex flex-col items-center justify-center text-gray-400 space-y-2">
            <svg class="w-12 h-12 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"/>
            </svg>
            <div class="text-center">
              <div class="font-medium">Видеопоток неактивен</div>
              <div class="text-sm text-gray-500">Запустите обработку для просмотра</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.aspect-video {
  aspect-ratio: 16 / 9;
}

.animate-pulse {
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: .5;
  }
}
</style>
<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue';
import SafeImage from '@/components/SafeImage.vue';
import axios from 'axios';
import { useAuthStore } from '@/stores/auth';

interface ApiAnomaly {
    id: number;
    user_id: number;
    timestamp_detected: string;
    source_type: string;  
    source_identifier: string;
    image_url: string;
    detected_class: string | null;
    description: string | null;
    is_reviewed: boolean;
}

interface AnomaliesApiResponse {
    anomalies: ApiAnomaly[];
    total: number;
    pages: number;
    current_page: number;
    has_next: boolean;
    has_prev: boolean;
}

const authStore = useAuthStore();
const anomalies = ref<ApiAnomaly[]>([]);
const isLoading = ref(true);
const apiError = ref<string | null>(null);

const currentPage = ref(1);
const itemsPerPage = ref(5);
const totalAnomaliesCount = ref(0);

const totalPages = computed(() => {
    if (totalAnomaliesCount.value === 0 || itemsPerPage.value === 0) return 1;
    return Math.ceil(totalAnomaliesCount.value / itemsPerPage.value);
});

const fetchAnomalies = async (pageToFetch = 1) => {
    if (!authStore.isLoggedIn) {
        return;
    }
    isLoading.value = true;
    apiError.value = null;
    try {
        const response = await axios.get<AnomaliesApiResponse>('/api/anomalies', {
            params: {
                page: pageToFetch,
                per_page: itemsPerPage.value,
            }
        });
        anomalies.value = response.data.anomalies;
        totalAnomaliesCount.value = response.data.total;
        currentPage.value = response.data.current_page;
    } catch (err: any) {
        apiError.value = err.response?.data?.error || err.message || "Ошибка загрузки списка аномалий.";
        console.error("Error fetching anomalies:", err);
    } finally {
        isLoading.value = false;
    }
};

const goToPage = (pageNumber: number) => {
    if (pageNumber >= 1 && pageNumber <= totalPages.value && pageNumber !== currentPage.value) {
        fetchAnomalies(pageNumber);
    }
};

onMounted(() => {
    fetchAnomalies(currentPage.value);
});

const formatDateTime = (isoString: string) => {
    if (!isoString) return 'N/A';
    try {
        return new Date(isoString).toLocaleString('ru-RU', {
            year: 'numeric', month: 'short', day: 'numeric',
            hour: '2-digit', minute: '2-digit', second: '2-digit'
        });
    } catch (e) {
        return isoString;
    }
};

const markAsReviewed = async (anomalyId: number) => {
    try {
        await axios.put(`/api/anomalies/${anomalyId}/review`);
        const anomalyToUpdate = anomalies.value.find(a => a.id === anomalyId);
        if (anomalyToUpdate) {
            anomalyToUpdate.is_reviewed = true;
        }
    } catch (err) {
        console.error("Error marking anomaly as reviewed:", err);
        alert("Не удалось обновить статус аномалии. Попробуйте позже.");
    }
};

const getAnomalyTypeColor = (detectedClass: string | null) => {
    if (!detectedClass) return 'bg-slate-100 text-slate-600';
    
    const colors: Record<string, string> = {
        'fire': 'bg-red-100 text-red-700 border-red-200',
        'smoke': 'bg-gray-100 text-gray-700 border-gray-200', 
        'person': 'bg-blue-100 text-blue-700 border-blue-200',
        'vehicle': 'bg-green-100 text-green-700 border-green-200',
        'weapon': 'bg-orange-100 text-orange-700 border-orange-200'
    };
    
    return colors[detectedClass.toLowerCase()] || 'bg-indigo-100 text-indigo-700 border-indigo-200';
};
</script>

<template>
    <div class="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
        <!-- Header Section -->
        <div class="bg-white/70 backdrop-blur-sm border-b border-slate-200/60 sticky top-0 z-10">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
                <div class="flex items-center justify-between">
                    <div>
                        <h1 class="text-3xl font-bold bg-gradient-to-r from-slate-800 to-slate-600 bg-clip-text text-transparent">
                            Аномалии системы
                        </h1>
                        <p class="mt-1 text-slate-600">Обнаруженные нарушения и подозрительная активность</p>
                    </div>
                    <div class="flex items-center space-x-4">
                        <div class="bg-white rounded-full px-4 py-2 shadow-sm border border-slate-200">
                            <span class="text-sm font-medium text-slate-600">Всего: </span>
                            <span class="text-sm font-bold text-slate-800">{{ totalAnomaliesCount }}</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <!-- Loading State -->
            <div v-if="isLoading && anomalies.length === 0" 
                 class="flex flex-col items-center justify-center py-16">
                <div class="relative">
                    <div class="w-16 h-16 border-4 border-slate-200 border-t-indigo-500 rounded-full animate-spin"></div>
                    <div class="absolute inset-0 w-16 h-16 border-4 border-transparent border-r-indigo-300 rounded-full animate-ping"></div>
                </div>
                <p class="mt-4 text-slate-600 font-medium">Загрузка аномалий...</p>
            </div>

            <!-- Error State -->
            <div v-else-if="apiError" 
                 class="bg-red-50 border border-red-200 rounded-2xl p-6 shadow-sm">
                <div class="flex items-start space-x-3">
                    <div class="flex-shrink-0">
                        <svg class="w-6 h-6 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                                  d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
                        </svg>
                    </div>
                    <div>
                        <h3 class="text-red-800 font-semibold">Ошибка загрузки</h3>
                        <p class="text-red-700 mt-1">{{ apiError }}</p>
                    </div>
                </div>
            </div>

            <!-- Empty State -->
            <div v-else-if="anomalies && Array.isArray(anomalies) && anomalies.length === 0"
                 class="text-center py-16">
                <div class="mx-auto w-24 h-24 bg-gradient-to-br from-slate-100 to-slate-200 rounded-full flex items-center justify-center mb-6">
                    <svg class="w-12 h-12 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                              d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
                    </svg>
                </div>
                <h3 class="text-xl font-semibold text-slate-700 mb-2">Аномалий пока не обнаружено</h3>
                <p class="text-slate-500 max-w-md mx-auto">
                    Система мониторинга активна. Все обнаруженные нарушения будут отображены здесь.
                </p>
            </div>

            <!-- Anomalies List -->
            <div v-else-if="anomalies && anomalies.length > 0" class="space-y-6">
                <div v-for="anomaly in anomalies" :key="anomaly.id"
                     class="group bg-white/80 backdrop-blur-sm rounded-2xl shadow-sm border border-slate-200/60 hover:shadow-lg hover:border-slate-300/60 transition-all duration-300">
                    <div class="p-6">
                        <div class="flex flex-col lg:flex-row lg:space-x-8">
                            <!-- Image Section -->
                            <div class="lg:w-80 flex-shrink-0 mb-6 lg:mb-0">
                                <div class="relative overflow-hidden rounded-xl border border-slate-200 bg-slate-50">
                                    <a :href="anomaly.image_url" target="_blank" 
                                       class="block aspect-video group-hover:scale-[1.02] transition-transform duration-300">
                                        <SafeImage 
                                            :src="anomaly.image_url"
                                            :alt="`Аномалия ${anomaly.id} - ${anomaly.detected_class || 'Неизвестно'}`"
                                            placeholderSrc="https://via.placeholder.com/400x225.png?text=Ошибка+загрузки"
                                            class="w-full h-full object-cover"
                                        />
                                    </a>
                                    <!-- Overlay icon -->
                                    <div class="absolute top-3 right-3 bg-white/90 backdrop-blur-sm rounded-full p-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                                        <svg class="w-4 h-4 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                                                  d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"/>
                                        </svg>
                                    </div>
                                </div>
                            </div>

                            <!-- Content Section -->
                            <div class="flex-1 space-y-4">
                                <!-- Header -->
                                <div class="flex items-start justify-between">
                                    <div class="flex items-center space-x-3">
                                        <h3 class="text-xl font-bold text-slate-800">
                                            Аномалия #{{ anomaly.id }}
                                        </h3>
                                        <span v-if="anomaly.detected_class"
                                              :class="`inline-flex items-center px-3 py-1 text-xs font-semibold rounded-full border ${getAnomalyTypeColor(anomaly.detected_class)}`">
                                            {{ anomaly.detected_class }}
                                        </span>
                                    </div>

                                    <!-- Status Badge -->
                                    <div class="flex items-center space-x-2">
                                        <span :class="[
                                            'inline-flex items-center px-3 py-1 text-xs font-semibold rounded-full border',
                                            anomaly.is_reviewed 
                                                ? 'bg-emerald-50 text-emerald-700 border-emerald-200' 
                                                : 'bg-amber-50 text-amber-700 border-amber-200'
                                        ]">
                                            <span :class="[
                                                'w-2 h-2 rounded-full mr-2',
                                                anomaly.is_reviewed ? 'bg-emerald-400' : 'bg-amber-400'
                                            ]"></span>
                                            {{ anomaly.is_reviewed ? 'Просмотрено' : 'Требует внимания' }}
                                        </span>
                                    </div>
                                </div>

                                <!-- Details Grid -->
                                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    <div class="bg-slate-50/50 rounded-lg p-3 border border-slate-100">
                                        <div class="flex items-center space-x-2 mb-1">
                                            <svg class="w-4 h-4 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                                                      d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
                                            </svg>
                                            <span class="text-xs font-medium text-slate-500 uppercase tracking-wide">Время обнаружения</span>
                                        </div>
                                        <p class="text-sm font-semibold text-slate-700">{{ formatDateTime(anomaly.timestamp_detected) }}</p>
                                    </div>

                                    <div class="bg-slate-50/50 rounded-lg p-3 border border-slate-100">
                                        <div class="flex items-center space-x-2 mb-1">
                                            <svg class="w-4 h-4 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                                                      d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"/>
                                            </svg>
                                            <span class="text-xs font-medium text-slate-500 uppercase tracking-wide">Источник</span>
                                        </div>
                                        <p class="text-sm font-semibold text-slate-700 break-all">{{ anomaly.source_identifier }}</p>
                                        <p class="text-xs text-slate-500 mt-1">{{ anomaly.source_type }}</p>
                                    </div>
                                </div>

                                <!-- Description -->
                                <div v-if="anomaly.description" 
                                     class="bg-blue-50/50 rounded-lg p-4 border border-blue-100">
                                    <div class="flex items-start space-x-2">
                                        <svg class="w-4 h-4 text-blue-500 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                                                  d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
                                        </svg>
                                        <div>
                                            <p class="text-xs font-medium text-blue-600 uppercase tracking-wide mb-1">Описание</p>
                                            <p class="text-sm text-blue-800 leading-relaxed">{{ anomaly.description }}</p>
                                        </div>
                                    </div>
                                </div>

                                <!-- Actions -->
                                <div class="flex items-center justify-between pt-2 border-t border-slate-100">
                                    <div class="flex items-center space-x-2">
                                        <button v-if="!anomaly.is_reviewed" 
                                                @click="markAsReviewed(anomaly.id)"
                                                class="inline-flex items-center px-4 py-2 text-sm font-medium text-indigo-700 bg-indigo-50 border border-indigo-200 rounded-lg hover:bg-indigo-100 hover:border-indigo-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-1 transition-colors duration-200">
                                            <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                                            </svg>
                                            Отметить как просмотрено
                                        </button>
                                        <span v-else class="inline-flex items-center text-sm font-medium text-emerald-700">
                                            <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                                            </svg>
                                            Просмотрено
                                        </span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Pagination -->
            <div v-if="totalPages > 1" class="flex justify-center items-center space-x-2 mt-12">
                <button @click="goToPage(currentPage - 1)" 
                        :disabled="currentPage === 1 || isLoading"
                        class="inline-flex items-center px-4 py-2 text-sm font-medium text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200">
                    <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
                    </svg>
                    Назад
                </button>

                <div class="flex space-x-1">
                    <button v-for="pageNumber in totalPages" 
                            :key="pageNumber"
                            @click="goToPage(pageNumber)" 
                            :class="[
                                'px-4 py-2 text-sm font-medium rounded-lg transition-colors duration-200',
                                pageNumber === currentPage 
                                    ? 'bg-indigo-600 text-white shadow-sm' 
                                    : 'text-slate-700 bg-white border border-slate-300 hover:bg-slate-50'
                            ]" 
                            :disabled="isLoading">
                        {{ pageNumber }}
                    </button>
                </div>

                <button @click="goToPage(currentPage + 1)" 
                        :disabled="currentPage === totalPages || isLoading"
                        class="inline-flex items-center px-4 py-2 text-sm font-medium text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200">
                    Вперед
                    <svg class="w-4 h-4 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
                    </svg>
                </button>
            </div>
        </div>
    </div>
</template>

<style scoped>
.aspect-video {
    aspect-ratio: 16 / 9;
}

@keyframes pulse-scale {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.05); }
}

.group:hover .pulse-on-hover {
    animation: pulse-scale 2s infinite;
}
</style>
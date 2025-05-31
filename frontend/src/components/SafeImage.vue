<script setup lang="ts">
import { ref, watch } from 'vue';

const props = defineProps<{
  src?: string | null;
  alt?: string;
  placeholderSrc?: string;
}>();

const isLoading = ref(true);
const hasError = ref(false);
const currentSrc = ref(props.src);

watch(() => props.src, (newSrc) => {
  currentSrc.value = newSrc;
  hasError.value = false; 
  isLoading.value = true; 
});

const onError = () => {
  if (props.placeholderSrc && !hasError.value) { 
    currentSrc.value = props.placeholderSrc;
  }
  hasError.value = true;
  isLoading.value = false;
};

const onLoad = () => {
  isLoading.value = false;
};
</script>

<template>
  <div class="image-container relative">
    <img 
      v-if="currentSrc"
      :src="currentSrc" 
      :alt="alt"
      @load="onLoad"
      @error="onError" 
      class="w-full h-auto object-cover" 
    />
    <div v-else-if="!currentSrc && !isLoading" class="flex items-center justify-center w-full h-full bg-gray-200 text-gray-500">
      Нет изображения
    </div>
    <div v-if="isLoading && !hasError" class="absolute inset-0 flex items-center justify-center bg-gray-100 opacity-75">
      <svg class="animate-spin h-8 w-8 text-purple-600" viewBox="0 0 24 24">...</svg>
    </div>
  </div>
</template>
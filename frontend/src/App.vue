// src/App.vue
<script setup lang="ts">
import { RouterView } from 'vue-router'
import Navbar from './components/Navbar.vue'
</script>

// src/App.vue
<template>
  <div id="app-container" class="flex flex-col min-h-screen bg-gray-100 text-gray-800"> 
    <Navbar /> 
    <div class="flex-grow flex items-center justify-center py-4 px-4 sm:px-6 lg:px-8"> 
      <div class="bg-white shadow-md rounded-lg p-6 w-full max-w-4xl">
        <RouterView />
      </div>
    </div>
  </div>
</template>
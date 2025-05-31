<script setup lang="ts">
import { RouterView } from 'vue-router'
import Navbar from './components/Navbar.vue'
</script>

<template>
  <div id="app-container" class="flex flex-col min-h-screen"> 
    <Navbar class="relative z-20" /> 
    
    <div class="flex-grow relative z-10"> 
      <RouterView />
    </div>
  </div>
</template>

<style scoped>
#app-container {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

html {
  scroll-behavior: smooth;
}

body, html {
  margin: 0;
  padding: 0;
  overflow-x: hidden;
}
</style>
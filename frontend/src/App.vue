<template>
  <div class="layout">
    <AppNavigation />
    <main class="layout__main">
      <RouterView />
    </main>
    <PWAInstallPrompt />
  </div>
</template>

<script setup lang="ts">
import { RouterView } from 'vue-router';
import PWAInstallPrompt from '@/components/PWAInstallPrompt.vue';
import AppNavigation from '@/components/AppNavigation.vue';
import { useI18nHead } from '@/composables/useI18n';

// Initialize i18n head updates
useI18nHead();
</script>

<style scoped>
.layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f4f6f8;
  color: #0f172a;
}

.layout__main {
  flex: 1;
  padding: 24px;
}

@media (max-width: 768px) {
  .layout__main {
    padding: 16px;
  }
}
</style>

<template>
  <div class="layout">
    <AppNavigation v-if="!isAdminRoute" />
    <main class="layout__main" :class="{ 'admin-layout': isAdminRoute }">
      <RouterView />
    </main>
    <PWAInstallPrompt />
  </div>
</template>

<script setup lang="ts">
import { RouterView, useRoute } from 'vue-router';
import { computed } from 'vue';
import PWAInstallPrompt from '@/components/PWAInstallPrompt.vue';
import AppNavigation from '@/components/AppNavigation.vue';
import { useI18nHead } from '@/composables/useI18n';

// Initialize i18n head updates
useI18nHead();

const route = useRoute();

// Check if current route is an admin route
const isAdminRoute = computed(() => {
  return route.path.startsWith('/admin');
});
</script>

<style scoped>
.layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--color-bg-light);
  color: var(--color-text-primary);
}

.layout__main {
  flex: 1;
  padding: var(--spacing-xl);
}

.layout__main.admin-layout {
  padding: 0;
}

@media (max-width: 768px) {
  .layout__main {
    padding: var(--spacing-lg);
    padding-bottom: calc(var(--mobile-nav-height) + var(--spacing-lg));
  }

  .layout__main.admin-layout {
    padding: 0;
  }
}
</style>

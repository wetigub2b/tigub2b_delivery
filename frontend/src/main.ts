import { createApp } from 'vue';
import { createPinia } from 'pinia';
import App from './App.vue';
import router from '@/router';
import i18n from '@/i18n';
import '@/styles/main.css';
import { initializeMobile } from '@/utils/mobile';

const app = createApp(App);

// Setup in correct order
app.use(createPinia());
app.use(i18n);
app.use(router);

// Initialize admin store after everything is set up
import { useAdminStore } from '@/store/admin';
const adminStore = useAdminStore();
adminStore.checkAuthStatus();

// Initialize mobile features
initializeMobile().then(() => {
  console.log('Mobile features initialized');
}).catch(error => {
  console.error('Failed to initialize mobile features:', error);
});

app.mount('#app');

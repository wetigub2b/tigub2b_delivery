import { createApp } from 'vue';
import { createPinia } from 'pinia';
import App from './App.vue';
import router from '@/router';
import i18n from '@/i18n';
import '@/styles/main.css';
import { initializeMobile } from '@/utils/mobile';

const app = createApp(App);

app.use(createPinia());
app.use(router);
app.use(i18n);

// Initialize mobile features
initializeMobile().then(() => {
  console.log('Mobile features initialized');
}).catch(error => {
  console.error('Failed to initialize mobile features:', error);
});

app.mount('#app');

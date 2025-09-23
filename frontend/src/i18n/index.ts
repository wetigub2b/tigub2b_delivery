import { createI18n } from 'vue-i18n';
import en from '@/locales/en.json';
import zh from '@/locales/zh.json';

// Get saved language or detect browser language
function getDefaultLocale(): string {
  // Check localStorage first
  const savedLocale = localStorage.getItem('app-locale');
  if (savedLocale && ['en', 'zh'].includes(savedLocale)) {
    return savedLocale;
  }

  // Detect browser language
  const browserLocale = navigator.language.toLowerCase();
  if (browserLocale.startsWith('zh')) {
    return 'zh';
  }

  // Default to English
  return 'en';
}

// Create i18n instance
const i18n = createI18n({
  locale: getDefaultLocale(),
  fallbackLocale: 'en',
  legacy: false, // Use Composition API mode
  globalInjection: true, // Enable global $t
  messages: {
    en,
    zh
  }
});

// Helper function to change language
export function setLocale(locale: string) {
  if (i18n.mode === 'legacy') {
    i18n.global.locale = locale;
  } else {
    (i18n.global.locale as any).value = locale;
  }
  localStorage.setItem('app-locale', locale);
  document.documentElement.lang = locale;
}

// Helper function to get current locale
export function getCurrentLocale(): string {
  if (i18n.mode === 'legacy') {
    return i18n.global.locale;
  } else {
    return (i18n.global.locale as any).value;
  }
}

// Helper function to get available locales
export function getAvailableLocales() {
  return [
    { code: 'en', name: 'English', nativeName: 'English' },
    { code: 'zh', name: 'Chinese', nativeName: '中文' }
  ];
}

// Set initial document language
document.documentElement.lang = getCurrentLocale();

export default i18n;
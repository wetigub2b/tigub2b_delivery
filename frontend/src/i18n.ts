import { createI18n } from 'vue-i18n';
import en from '@/locales/en.json';
import zh from '@/locales/zh.json';

// Get saved locale or default to English
const savedLocale = localStorage.getItem('user-locale') || 'en';

const i18n = createI18n({
  legacy: false, // Use composition API
  locale: savedLocale, // Use saved locale or default
  fallbackLocale: 'en',
  messages: {
    en,
    zh
  }
});

// Set document language on initialization
document.documentElement.lang = savedLocale;

// Export utility functions for the LanguageSwitcher
export function setLocale(locale: string) {
  i18n.global.locale.value = locale;
  localStorage.setItem('user-locale', locale);
  // Update document language attribute
  document.documentElement.lang = locale;
}

export function getCurrentLocale(): string {
  return i18n.global.locale.value;
}

export function getAvailableLocales() {
  return [
    { code: 'en', name: 'English' },
    { code: 'zh', name: '中文' }
  ];
}

export default i18n;
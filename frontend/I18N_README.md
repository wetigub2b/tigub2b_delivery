# Internationalization (i18n) Implementation

This document explains the i18n setup for the Tigu Delivery application supporting English and Chinese languages.

## 🌍 Features

### Supported Languages
- **English (en)** - Default language
- **Chinese (zh)** - Simplified Chinese

### Auto-Detection
- Browser language detection
- Persistent language preference
- Fallback to English if unsupported language

### User Interface
- Language switcher in navigation
- Real-time language switching
- Mobile-friendly language selector

## 🛠️ Implementation

### Core Setup

**Dependencies:**
```json
{
  "vue-i18n": "^9.14.5"
}
```

**File Structure:**
```
src/
├── i18n/
│   └── index.ts           # i18n configuration
├── locales/
│   ├── en.json           # English translations
│   └── zh.json           # Chinese translations
├── composables/
│   └── useI18n.ts        # i18n utilities
└── components/
    └── LanguageSwitcher.vue
```

### Configuration (`src/i18n/index.ts`)

```typescript
import { createI18n } from 'vue-i18n';
import en from '@/locales/en.json';
import zh from '@/locales/zh.json';

const i18n = createI18n({
  locale: getDefaultLocale(), // Auto-detect or saved preference
  fallbackLocale: 'en',
  legacy: false,              // Composition API mode
  globalInjection: true,      // Enable global $t
  messages: { en, zh }
});
```

### Language Detection Logic

1. **Saved Preference**: Check `localStorage` for 'app-locale'
2. **Browser Language**: Detect `navigator.language`
3. **Fallback**: Default to English

### Translation Files

**English (`src/locales/en.json`)**
```json
{
  "app": {
    "title": "Tigu Delivery Console",
    "name": "Tigu Delivery"
  },
  "navigation": {
    "taskBoard": "Task Board",
    "routePlanner": "Route Planner"
  }
}
```

**Chinese (`src/locales/zh.json`)**
```json
{
  "app": {
    "title": "梯谷配送控制台",
    "name": "梯谷配送"
  },
  "navigation": {
    "taskBoard": "任务看板",
    "routePlanner": "路线规划"
  }
}
```

## 🎛️ Language Switcher Component

**Features:**
- Dropdown selection with native language names
- Click outside to close
- Keyboard navigation (Escape key)
- Mobile-optimized interface
- Haptic feedback on mobile devices

**Usage in Navigation:**
```vue
<template>
  <LanguageSwitcher />
</template>
```

## 📝 Using Translations in Components

### Template Usage
```vue
<template>
  <h1>{{ $t('app.title') }}</h1>
  <p>{{ $t('navigation.taskBoard') }}</p>
</template>
```

### Composition API Usage
```vue
<script setup>
import { useI18n } from 'vue-i18n';

const { t, locale } = useI18n();

const title = computed(() => t('app.title'));
</script>
```

### JavaScript Usage
```typescript
import { getCurrentLocale, setLocale } from '@/i18n';

// Get current language
const currentLang = getCurrentLocale();

// Change language
setLocale('zh');
```

## 🔧 Utility Functions

### Language Management
```typescript
import { setLocale, getCurrentLocale, getAvailableLocales } from '@/i18n';

// Change language and persist
setLocale('zh');

// Get current language code
const lang = getCurrentLocale(); // 'en' or 'zh'

// Get all available languages
const languages = getAvailableLocales();
// [
//   { code: 'en', name: 'English', nativeName: 'English' },
//   { code: 'zh', name: 'Chinese', nativeName: '中文' }
// ]
```

### Error Messages
```typescript
import { useI18nError } from '@/composables/useI18n';

const { getErrorMessage } = useI18nError();

// Localized error handling
try {
  await apiCall();
} catch (error) {
  const message = getErrorMessage(error);
  // Returns localized error message
}
```

### Mobile Messages
```typescript
import { useI18nMobile } from '@/composables/useI18n';

const { getMobileMessage } = useI18nMobile();

// Get localized mobile-specific messages
const locationMsg = getMobileMessage('location');
// EN: "Location permission required"
// ZH: "需要位置权限"
```

## 🏗️ Dynamic Updates

### Document Title & Meta
The app automatically updates:
- Document title (`<title>`)
- Meta description
- HTML `lang` attribute
- PWA manifest information

### Real-time Switching
- No page reload required
- Instant UI updates
- Persistent language preference
- Maintains application state

## 📱 Mobile & PWA Support

### PWA Manifests
- **English**: `/manifest.json`
- **Chinese**: `/manifest-zh.json`

### Mobile Features
- Touch-optimized language switcher
- Haptic feedback on selection
- Responsive dropdown design
- Native-like language selection

### Capacitor Integration
Language switching works seamlessly in:
- Progressive Web Apps
- Android Capacitor apps
- iOS Capacitor apps

## 🎯 Best Practices

### Translation Keys
Use nested structure for organization:
```json
{
  "common": {
    "loading": "Loading...",
    "error": "Error"
  },
  "pages": {
    "taskBoard": {
      "title": "Task Board",
      "description": "Manage tasks"
    }
  }
}
```

### Component Integration
Always wrap user-facing text:
```vue
<!-- ❌ Bad -->
<button>Save</button>

<!-- ✅ Good -->
<button>{{ $t('common.save') }}</button>
```

### Error Handling
Use the error utility for consistent messages:
```typescript
// ❌ Bad
throw new Error('Network error');

// ✅ Good
const { getErrorMessage } = useI18nError();
throw new Error(getErrorMessage(error));
```

## 🧪 Testing

### Manual Testing
1. Open app in browser
2. Check default language (English or browser-detected)
3. Use language switcher to change to Chinese
4. Verify all text updates immediately
5. Refresh page - language should persist
6. Test on mobile for responsive behavior

### Automated Testing
```typescript
import { setLocale, getCurrentLocale } from '@/i18n';

// Test language switching
test('language switching', () => {
  setLocale('zh');
  expect(getCurrentLocale()).toBe('zh');

  setLocale('en');
  expect(getCurrentLocale()).toBe('en');
});
```

## 🔄 Adding New Languages

### 1. Create Translation File
Create `/src/locales/[code].json` with translations.

### 2. Update i18n Config
```typescript
import newLang from '@/locales/newLang.json';

const i18n = createI18n({
  messages: {
    en,
    zh,
    newLang // Add new language
  }
});
```

### 3. Update Available Locales
```typescript
export function getAvailableLocales() {
  return [
    { code: 'en', name: 'English', nativeName: 'English' },
    { code: 'zh', name: 'Chinese', nativeName: '中文' },
    { code: 'newLang', name: 'New Language', nativeName: 'Native Name' }
  ];
}
```

### 4. Add PWA Manifest
Create `/public/manifest-[code].json` for PWA support.

## 📊 Translation Coverage

### Current Coverage
- ✅ Navigation components
- ✅ Route planner
- ✅ PWA install prompts
- ✅ Error messages
- ✅ Mobile-specific messages
- ✅ Common UI elements

### Pending Translation
- Task board components
- Order details
- Login forms
- Settings pages

## 🚀 Performance

### Bundle Size
- Vue I18n adds ~70KB to bundle
- Translation files lazy-loaded
- Tree-shaking for unused translations

### Optimization
- Messages stored in separate JSON files
- Lazy loading for additional languages
- Efficient re-rendering on language change

## 🔍 Debugging

### Debug Mode
Enable i18n debugging in development:
```typescript
const i18n = createI18n({
  // ... other options
  silentTranslationWarn: false, // Show missing translation warnings
  silentFallbackWarn: false     // Show fallback warnings
});
```

### Missing Translations
Missing keys will:
1. Show the key path in development
2. Fall back to English
3. Log warnings in console

## 📚 Resources

- [Vue I18n Documentation](https://vue-i18n.intlify.dev/)
- [JavaScript Intl API](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Intl)
- [ICU Message Format](https://unicode-org.github.io/icu/userguide/format_parse/messages/)
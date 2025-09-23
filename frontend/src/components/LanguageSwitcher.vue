<template>
  <div class="language-switcher">
    <button
      class="language-switcher__button"
      @click="toggleDropdown"
      :aria-expanded="showDropdown"
      :title="$t('language.switch')"
    >
      <span class="language-switcher__current">
        {{ getCurrentLanguageDisplay() }}
      </span>
      <span class="language-switcher__arrow" :class="{ 'language-switcher__arrow--open': showDropdown }">
        ↓
      </span>
    </button>

    <div
      v-if="showDropdown"
      class="language-switcher__dropdown"
      @click.stop
    >
      <div
        v-for="locale in availableLocales"
        :key="locale.code"
        class="language-switcher__option"
        :class="{ 'language-switcher__option--active': locale.code === currentLocale }"
        @click="changeLanguage(locale.code)"
      >
        <span class="language-switcher__option-native">{{ locale.nativeName }}</span>
        <span class="language-switcher__option-name">{{ locale.name }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useI18n } from 'vue-i18n';
import { setLocale, getCurrentLocale, getAvailableLocales } from '@/i18n';

const { locale } = useI18n();
const showDropdown = ref(false);

const currentLocale = computed(() => getCurrentLocale());
const availableLocales = getAvailableLocales();

const getCurrentLanguageDisplay = () => {
  const current = availableLocales.find(l => l.code === currentLocale.value);
  return current ? current.nativeName : 'EN';
};

const toggleDropdown = () => {
  showDropdown.value = !showDropdown.value;
};

const changeLanguage = (localeCode: string) => {
  setLocale(localeCode);
  showDropdown.value = false;

  // Optional: Add haptic feedback for mobile
  if ('vibrate' in navigator) {
    navigator.vibrate(50);
  }
};

// Close dropdown when clicking outside
const handleClickOutside = (event: Event) => {
  const target = event.target as HTMLElement;
  if (!target.closest('.language-switcher')) {
    showDropdown.value = false;
  }
};

onMounted(() => {
  document.addEventListener('click', handleClickOutside);
});

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside);
});

// Close dropdown on escape key
const handleKeydown = (event: KeyboardEvent) => {
  if (event.key === 'Escape') {
    showDropdown.value = false;
  }
};

onMounted(() => {
  document.addEventListener('keydown', handleKeydown);
});

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown);
});
</script>

<style scoped>
.language-switcher {
  position: relative;
  display: inline-block;
}

.language-switcher__button {
  display: flex;
  align-items: center;
  gap: 6px;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: #ffffff;
  padding: 6px 12px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s ease;
  min-width: 60px;
  justify-content: center;
}

.language-switcher__button:hover {
  background: rgba(255, 255, 255, 0.15);
  border-color: rgba(255, 255, 255, 0.3);
}

.language-switcher__current {
  font-weight: 500;
}

.language-switcher__arrow {
  font-size: 12px;
  transition: transform 0.2s ease;
}

.language-switcher__arrow--open {
  transform: rotate(180deg);
}

.language-switcher__dropdown {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 4px;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  z-index: 1000;
  min-width: 150px;
  overflow: hidden;
  animation: slideDown 0.2s ease;
}

.language-switcher__option {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 12px 16px;
  cursor: pointer;
  transition: background-color 0.2s ease;
  border-bottom: 1px solid #f1f5f9;
}

.language-switcher__option:last-child {
  border-bottom: none;
}

.language-switcher__option:hover {
  background: #f8fafc;
}

.language-switcher__option--active {
  background: #eff6ff;
  color: #3b82f6;
}

.language-switcher__option--active:hover {
  background: #dbeafe;
}

.language-switcher__option-native {
  font-weight: 500;
  font-size: 14px;
  color: #0f172a;
}

.language-switcher__option--active .language-switcher__option-native {
  color: #3b82f6;
}

.language-switcher__option-name {
  font-size: 12px;
  color: #64748b;
}

.language-switcher__option--active .language-switcher__option-name {
  color: #60a5fa;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Mobile styles */
@media (max-width: 768px) {
  .language-switcher__button {
    padding: 8px 12px;
    min-width: 50px;
  }

  .language-switcher__dropdown {
    right: 0;
    left: auto;
    min-width: 120px;
  }

  .language-switcher__option {
    padding: 14px 16px;
  }
}

/* Dark mode compatibility */
@media (prefers-color-scheme: dark) {
  .language-switcher__dropdown {
    background: #1e293b;
    border-color: #334155;
  }

  .language-switcher__option {
    border-color: #334155;
  }

  .language-switcher__option:hover {
    background: #334155;
  }

  .language-switcher__option-native {
    color: #f1f5f9;
  }

  .language-switcher__option-name {
    color: #94a3b8;
  }
}
</style>
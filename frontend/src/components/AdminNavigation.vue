<template>
  <nav class="admin-nav">
    <div class="nav-container">
      <div class="nav-brand">
        <router-link to="/admin/dashboard" class="brand-link">
          🚚 {{ $t('admin.nav.title') }}
        </router-link>
      </div>

      <div class="nav-menu" :class="{ 'active': showMobileMenu }">
        <router-link
          to="/admin/dashboard"
          class="nav-link"
          @click="closeMobileMenu"
        >
          <span class="nav-icon">📊</span>
          {{ $t('admin.nav.dashboard') }}
        </router-link>

        <router-link
          to="/admin/drivers"
          class="nav-link"
          @click="closeMobileMenu"
        >
          <span class="nav-icon">👥</span>
          {{ $t('admin.nav.drivers') }}
        </router-link>

        <router-link
          to="/admin/orders"
          class="nav-link"
          @click="closeMobileMenu"
        >
          <span class="nav-icon">📋</span>
          {{ $t('admin.nav.orders') }}
        </router-link>

        <router-link
          to="/admin/dispatch"
          class="nav-link"
          @click="closeMobileMenu"
        >
          <span class="nav-icon">🚀</span>
          {{ $t('admin.nav.dispatch') }}
        </router-link>

        <router-link
          to="/admin/reports"
          class="nav-link"
          @click="closeMobileMenu"
        >
          <span class="nav-icon">📈</span>
          {{ $t('admin.nav.reports') }}
        </router-link>
      </div>

      <div class="nav-actions">
        <LanguageSwitcher />
        <button @click="logout" class="logout-button">
          <span class="logout-icon">🚪</span>
          {{ $t('admin.nav.logout') }}
        </button>
      </div>

      <button
        class="mobile-menu-toggle"
        @click="toggleMobileMenu"
        :aria-expanded="showMobileMenu"
      >
        <span></span>
        <span></span>
        <span></span>
      </button>
    </div>
  </nav>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useAdminStore } from '@/store/admin';
import { useI18n } from '@/composables/useI18n';
import LanguageSwitcher from '@/components/LanguageSwitcher.vue';

const { t } = useI18n();
const router = useRouter();
const adminStore = useAdminStore();

const showMobileMenu = ref(false);

const toggleMobileMenu = () => {
  showMobileMenu.value = !showMobileMenu.value;
};

const closeMobileMenu = () => {
  showMobileMenu.value = false;
};

const logout = () => {
  adminStore.logout();
  router.push('/admin/login');
};
</script>

<style scoped>
.admin-nav {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  position: sticky;
  top: 0;
  z-index: 1000;
}

.nav-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 70px;
}

.nav-brand {
  flex-shrink: 0;
}

.brand-link {
  color: white;
  text-decoration: none;
  font-size: 24px;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 8px;
}

.nav-menu {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  justify-content: center;
}

.nav-link {
  color: rgba(255, 255, 255, 0.9);
  text-decoration: none;
  padding: 10px 16px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
  transition: all 0.2s ease;
  white-space: nowrap;
}

.nav-link:hover {
  background: rgba(255, 255, 255, 0.1);
  color: white;
}

.nav-link.router-link-active {
  background: rgba(255, 255, 255, 0.2);
  color: white;
  font-weight: 600;
}

.nav-icon {
  font-size: 16px;
}

.nav-actions {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-shrink: 0;

  /* Language switcher styling for purple gradient background */
  --lang-switcher-bg: rgba(255, 255, 255, 0.1);
  --lang-switcher-border: rgba(255, 255, 255, 0.2);
  --lang-switcher-color: #ffffff;
  --lang-switcher-hover-bg: rgba(255, 255, 255, 0.15);
  --lang-switcher-hover-border: rgba(255, 255, 255, 0.3);
  --lang-switcher-hover-color: #ffffff;
}

.logout-button {
  background: rgba(255, 255, 255, 0.1);
  color: white;
  border: 2px solid rgba(255, 255, 255, 0.2);
  border-radius: 8px;
  padding: 8px 16px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
  transition: all 0.2s ease;
}

.logout-button:hover {
  background: rgba(255, 255, 255, 0.2);
  border-color: rgba(255, 255, 255, 0.3);
}

.logout-icon {
  font-size: 16px;
}

.mobile-menu-toggle {
  display: none;
  flex-direction: column;
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px;
  gap: 4px;
}

.mobile-menu-toggle span {
  width: 24px;
  height: 3px;
  background: white;
  border-radius: 2px;
  transition: all 0.3s ease;
}

.mobile-menu-toggle[aria-expanded="true"] span:nth-child(1) {
  transform: rotate(45deg) translate(6px, 6px);
}

.mobile-menu-toggle[aria-expanded="true"] span:nth-child(2) {
  opacity: 0;
}

.mobile-menu-toggle[aria-expanded="true"] span:nth-child(3) {
  transform: rotate(-45deg) translate(6px, -6px);
}

@media (max-width: 768px) {
  .nav-container {
    padding: 0 16px;
  }

  .mobile-menu-toggle {
    display: flex;
  }

  .nav-menu {
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    flex-direction: column;
    align-items: stretch;
    padding: 20px;
    gap: 4px;
    transform: translateY(-100%);
    opacity: 0;
    visibility: hidden;
    transition: all 0.3s ease;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  }

  .nav-menu.active {
    transform: translateY(0);
    opacity: 1;
    visibility: visible;
  }

  .nav-link {
    padding: 12px 16px;
    justify-content: flex-start;
  }

  .nav-actions {
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 20px;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
    justify-content: space-between;
    transform: translateY(-100%);
    opacity: 0;
    visibility: hidden;
    transition: all 0.3s ease 0.1s;
  }

  .nav-menu.active ~ .nav-actions {
    transform: translateY(0);
    opacity: 1;
    visibility: visible;
  }

  .logout-button {
    padding: 10px 16px;
    flex: 1;
    justify-content: center;
    max-width: 120px;
  }
}

@media (max-width: 480px) {
  .brand-link {
    font-size: 20px;
  }

  .nav-container {
    height: 60px;
  }
}
</style>
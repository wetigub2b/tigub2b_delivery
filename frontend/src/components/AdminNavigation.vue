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
  background: var(--color-white);
  box-shadow: var(--shadow-header);
  position: sticky;
  top: 0;
  z-index: var(--z-sticky);
  border-bottom: 1px solid var(--color-gray-lighter);
}

.nav-container {
  max-width: var(--container-wide-max-width);
  margin: 0 auto;
  padding: var(--spacing-md) var(--spacing-xl);
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: var(--nav-height);
}

.nav-brand {
  flex-shrink: 0;
}

.brand-link {
  color: var(--color-primary);
  text-decoration: none;
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-bold);
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  transition: color var(--transition-base);
}

.brand-link:hover {
  color: var(--color-primary-dark);
}

.nav-menu {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  flex: 1;
  justify-content: center;
}

.nav-link {
  color: var(--color-black);
  text-decoration: none;
  padding: var(--spacing-sm) var(--spacing-lg);
  border-radius: var(--radius-full);
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  font-weight: var(--font-weight-medium);
  font-size: var(--font-size-md);
  transition: all var(--transition-base);
  white-space: nowrap;
  border: 1px solid transparent;
}

.nav-link:hover {
  color: var(--color-primary);
  border-color: var(--color-primary);
}

.nav-link.router-link-active {
  color: var(--color-primary);
  border-color: var(--color-primary);
  border-bottom-width: 2px;
}

.nav-icon {
  font-size: var(--font-size-md);
}

.nav-actions {
  display: flex;
  align-items: center;
  gap: var(--spacing-lg);
  flex-shrink: 0;
}

.logout-button {
  background: transparent;
  color: var(--color-black);
  border: 1px solid var(--color-gray-light);
  border-radius: var(--radius-full);
  padding: var(--spacing-sm) var(--spacing-lg);
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  font-weight: var(--font-weight-medium);
  font-size: var(--font-size-md);
  font-family: var(--font-family-base);
  transition: all var(--transition-base);
}

.logout-button:hover {
  color: var(--color-primary);
  border-color: var(--color-primary);
}

.logout-icon {
  font-size: var(--font-size-md);
}

.mobile-menu-toggle {
  display: none;
  flex-direction: column;
  background: none;
  border: none;
  cursor: pointer;
  padding: var(--spacing-sm);
  gap: var(--spacing-xs);
}

.mobile-menu-toggle span {
  width: 24px;
  height: 2px;
  background: var(--color-black);
  border-radius: 2px;
  transition: all var(--transition-slow);
  transform-origin: center;
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
    padding: var(--spacing-md);
    height: var(--header-height-mobile);
  }

  .mobile-menu-toggle {
    display: flex;
  }

  .nav-menu {
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    background: var(--color-white);
    flex-direction: column;
    align-items: stretch;
    padding: var(--spacing-lg);
    gap: var(--spacing-xs);
    transform: translateY(-100%);
    opacity: 0;
    visibility: hidden;
    transition: all var(--transition-slow);
    box-shadow: var(--shadow-lg);
    border-top: 1px solid var(--color-gray-lighter);
  }

  .nav-menu.active {
    transform: translateY(0);
    opacity: 1;
    visibility: visible;
  }

  .nav-link {
    padding: var(--spacing-md);
    justify-content: flex-start;
    border-bottom: 1px solid var(--color-gray-lighter);
  }

  .nav-link:last-child {
    border-bottom: none;
  }

  .nav-actions {
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    background: var(--color-white);
    padding: var(--spacing-lg);
    border-top: 1px solid var(--color-gray-lighter);
    justify-content: space-between;
    transform: translateY(-100%);
    opacity: 0;
    visibility: hidden;
    transition: all var(--transition-slow) 0.1s;
  }

  .nav-menu.active ~ .nav-actions {
    transform: translateY(0);
    opacity: 1;
    visibility: visible;
  }

  .logout-button {
    padding: var(--spacing-sm) var(--spacing-lg);
    flex: 1;
    justify-content: center;
    max-width: 120px;
  }
}

@media (max-width: 480px) {
  .brand-link {
    font-size: var(--font-size-lg);
  }
}
</style>
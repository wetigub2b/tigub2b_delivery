<template>
  <nav class="nav">
    <div class="nav__content">
      <!-- Home/Logo -->
      <router-link to="/" class="nav__home">
        <img alt="Tigu Delivery" class="nav__logo" src="/favicon.svg" />
        <span class="nav__title">Tigu Delivery</span>
      </router-link>

      <!-- Navigation Links -->
      <div class="nav__links">
        <router-link
          to="/"
          class="nav__link"
          :class="{ 'nav__link--active': $route.name === 'task-board' }"
        >
          📋 {{ $t('navigation.taskBoard') }}
        </router-link>
        <router-link
          to="/route-planner"
          class="nav__link"
          :class="{ 'nav__link--active': $route.name === 'route-planner' }"
        >
          🗺️ {{ $t('navigation.routePlanner') }}
        </router-link>
        <LanguageSwitcher />
        <button
          class="nav__logout"
          @click="handleLogout"
        >
          🚪 {{ $t('navigation.logout') }}
        </button>
      </div>

      <!-- Mobile Menu Button -->
      <button
        class="nav__mobile-toggle"
        :class="{ 'nav__mobile-toggle--active': showMobileMenu }"
        @click="toggleMobileMenu"
      >
        <span></span>
        <span></span>
        <span></span>
      </button>
    </div>

    <!-- Mobile Menu -->
    <div
      class="nav__mobile-menu"
      :class="{ 'nav__mobile-menu--open': showMobileMenu }"
    >
      <router-link
        to="/"
        class="nav__mobile-link"
        @click="closeMobileMenu"
      >
        📋 {{ $t('navigation.taskBoard') }}
      </router-link>
      <router-link
        to="/route-planner"
        class="nav__mobile-link"
        @click="closeMobileMenu"
      >
        🗺️ {{ $t('navigation.routePlanner') }}
      </router-link>
      <button
        class="nav__mobile-link nav__mobile-logout"
        @click="handleLogout"
      >
        🚪 {{ $t('navigation.logout') }}
      </button>
      <div class="nav__mobile-language">
        <LanguageSwitcher />
      </div>
    </div>
  </nav>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useOrdersStore } from '@/store/orders';
import LanguageSwitcher from '@/components/LanguageSwitcher.vue';

const showMobileMenu = ref(false);
const router = useRouter();
const ordersStore = useOrdersStore();

const toggleMobileMenu = () => {
  showMobileMenu.value = !showMobileMenu.value;
};

const closeMobileMenu = () => {
  showMobileMenu.value = false;
};

const handleLogout = () => {
  ordersStore.logout();
  closeMobileMenu();
  router.push('/login');
};

// Close mobile menu when route changes
router.afterEach(() => {
  closeMobileMenu();
});
</script>

<style scoped>
.nav {
  background: #0f172a;
  color: #ffffff;
  box-shadow: 0 2px 8px rgba(15, 23, 42, 0.3);
  position: sticky;
  top: 0;
  z-index: 100;
}

.nav__content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 24px;
  max-width: 1200px;
  margin: 0 auto;
}

.nav__home {
  display: flex;
  align-items: center;
  gap: 12px;
  text-decoration: none;
  color: inherit;
  font-weight: 600;
  font-size: 18px;
}

.nav__logo {
  width: 32px;
  height: 32px;
}

.nav__title {
  font-weight: 700;
}

.nav__links {
  display: flex;
  gap: 24px;
  align-items: center;
}

.nav__link {
  text-decoration: none;
  color: #cbd5e1;
  padding: 8px 16px;
  border-radius: 6px;
  transition: all 0.2s ease;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 8px;
}

.nav__link:hover {
  color: #ffffff;
  background: rgba(255, 255, 255, 0.1);
}

.nav__link--active {
  color: #ffffff;
  background: #3b82f6;
}

.nav__logout {
  background: transparent;
  border: none;
  text-decoration: none;
  color: #cbd5e1;
  padding: 8px 16px;
  border-radius: 6px;
  transition: all 0.2s ease;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-size: inherit;
  font-family: inherit;
}

.nav__logout:hover {
  color: #ffffff;
  background: rgba(239, 68, 68, 0.2);
}

/* Mobile Menu Toggle */
.nav__mobile-toggle {
  display: none;
  flex-direction: column;
  gap: 4px;
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 8px;
}

.nav__mobile-toggle span {
  width: 24px;
  height: 2px;
  background: #ffffff;
  transition: all 0.3s ease;
  transform-origin: center;
}

.nav__mobile-toggle--active span:nth-child(1) {
  transform: rotate(45deg) translate(6px, 6px);
}

.nav__mobile-toggle--active span:nth-child(2) {
  opacity: 0;
}

.nav__mobile-toggle--active span:nth-child(3) {
  transform: rotate(-45deg) translate(6px, -6px);
}

/* Mobile Menu */
.nav__mobile-menu {
  display: none;
  background: #1e293b;
  border-top: 1px solid #334155;
  padding: 16px 24px;
}

.nav__mobile-menu--open {
  display: block;
}

.nav__mobile-link {
  display: block;
  text-decoration: none;
  color: #cbd5e1;
  padding: 12px 0;
  border-bottom: 1px solid #334155;
  font-weight: 500;
  transition: color 0.2s ease;
}

.nav__mobile-link:last-child {
  border-bottom: none;
}

.nav__mobile-link:hover {
  color: #ffffff;
}

.nav__mobile-logout {
  background: transparent;
  border: none;
  text-align: left;
  font-size: inherit;
  font-family: inherit;
  cursor: pointer;
  width: 100%;
}

.nav__mobile-logout:hover {
  color: #ffffff;
  background: rgba(239, 68, 68, 0.1);
}

.nav__mobile-language {
  padding: 12px 0;
  border-top: 1px solid #334155;
  margin-top: 8px;
  display: flex;
  justify-content: center;
}

/* Responsive */
@media (max-width: 768px) {
  .nav__links {
    display: none;
  }

  .nav__mobile-toggle {
    display: flex;
  }

  .nav__title {
    display: none;
  }
}

@media (max-width: 480px) {
  .nav__content {
    padding: 12px 16px;
  }
}
</style>
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
  background: var(--color-white);
  color: var(--color-black);
  box-shadow: var(--shadow-header);
  position: sticky;
  top: 0;
  z-index: var(--z-sticky);
  border-bottom: 1px solid var(--color-gray-lighter);
}

.nav__content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-md) var(--spacing-xl);
  max-width: var(--container-wide-max-width);
  margin: 0 auto;
  height: var(--nav-height);
}

.nav__home {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  text-decoration: none;
  color: var(--color-primary);
  font-weight: var(--font-weight-bold);
  font-size: var(--font-size-xl);
  transition: color var(--transition-base);
}

.nav__home:hover {
  color: var(--color-primary-dark);
}

.nav__logo {
  width: 36px;
  height: 36px;
}

.nav__title {
  font-weight: var(--font-weight-bold);
}

.nav__links {
  display: flex;
  gap: var(--spacing-sm);
  align-items: center;
}

.nav__link {
  text-decoration: none;
  color: var(--color-black);
  padding: var(--spacing-sm) var(--spacing-lg);
  border-radius: var(--radius-full);
  transition: all var(--transition-base);
  font-weight: var(--font-weight-medium);
  font-size: var(--font-size-md);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-sm);
  border: 1px solid transparent;
}

.nav__link:hover {
  color: var(--color-primary);
  border-color: var(--color-primary);
  background: transparent;
}

.nav__link--active {
  color: var(--color-primary);
  border-color: var(--color-primary);
  border-bottom-width: 2px;
}

.nav__logout {
  background: transparent;
  border: 1px solid var(--color-gray-light);
  text-decoration: none;
  color: var(--color-black);
  padding: var(--spacing-sm) var(--spacing-lg);
  border-radius: var(--radius-full);
  transition: all var(--transition-base);
  font-weight: var(--font-weight-medium);
  font-size: var(--font-size-md);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-sm);
  cursor: pointer;
  font-family: var(--font-family-base);
}

.nav__logout:hover {
  color: var(--color-primary);
  border-color: var(--color-primary);
  background: transparent;
}

/* Mobile Menu Toggle */
.nav__mobile-toggle {
  display: none;
  flex-direction: column;
  gap: var(--spacing-xs);
  background: transparent;
  border: none;
  cursor: pointer;
  padding: var(--spacing-sm);
}

.nav__mobile-toggle span {
  width: 24px;
  height: 2px;
  background: var(--color-black);
  transition: all var(--transition-slow);
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
  background: var(--color-white);
  border-top: 1px solid var(--color-gray-lighter);
  padding: var(--spacing-lg) var(--spacing-xl);
}

.nav__mobile-menu--open {
  display: block;
}

.nav__mobile-link {
  display: block;
  text-decoration: none;
  color: var(--color-black);
  padding: var(--spacing-md) 0;
  border-bottom: 1px solid var(--color-gray-lighter);
  font-weight: var(--font-weight-medium);
  font-size: var(--font-size-md);
  transition: color var(--transition-base);
}

.nav__mobile-link:last-child {
  border-bottom: none;
}

.nav__mobile-link:hover {
  color: var(--color-primary);
}

.nav__mobile-logout {
  background: transparent;
  border: none;
  text-align: left;
  font-size: var(--font-size-md);
  font-family: var(--font-family-base);
  cursor: pointer;
  width: 100%;
}

.nav__mobile-logout:hover {
  color: var(--color-primary);
}

.nav__mobile-language {
  padding: var(--spacing-md) 0;
  border-top: 1px solid var(--color-gray-lighter);
  margin-top: var(--spacing-sm);
  display: flex;
  justify-content: center;
}

/* Responsive */
@media (max-width: 768px) {
  .nav__content {
    padding: var(--spacing-md);
    height: var(--header-height-mobile);
  }

  .nav__links {
    display: none;
  }

  .nav__mobile-toggle {
    display: flex;
  }

  .nav__title {
    font-size: var(--font-size-lg);
  }
}

@media (max-width: 480px) {
  .nav__content {
    padding: var(--spacing-sm) var(--spacing-md);
  }

  .nav__title {
    display: none;
  }
}
</style>
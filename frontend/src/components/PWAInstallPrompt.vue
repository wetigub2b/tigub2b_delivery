<template>
  <div v-if="showInstallPrompt" class="pwa-install-banner">
    <div class="install-content">
      <div class="install-icon">📱</div>
      <div class="install-text">
        <h3>{{ $t('pwa.installTitle') }}</h3>
        <p>{{ $t('pwa.installDescription') }}</p>
      </div>
      <div class="install-actions">
        <button @click="installApp" class="install-btn">{{ $t('pwa.installButton') }}</button>
        <button @click="dismissPrompt" class="dismiss-btn">{{ $t('pwa.laterButton') }}</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';

const showInstallPrompt = ref(false);
let deferredPrompt: any = null;

onMounted(() => {
  // Listen for the beforeinstallprompt event
  window.addEventListener('beforeinstallprompt', (e) => {
    // Prevent the mini-infobar from appearing on mobile
    e.preventDefault();
    // Store the event so it can be triggered later
    deferredPrompt = e;
    // Show the install prompt
    showInstallPrompt.value = true;
  });

  // Listen for app installation
  window.addEventListener('appinstalled', () => {
    console.log('PWA was installed');
    showInstallPrompt.value = false;
    deferredPrompt = null;
  });

  // Check if app is already installed
  if (window.matchMedia('(display-mode: standalone)').matches) {
    console.log('App is running in standalone mode');
  }
});

const installApp = async () => {
  if (deferredPrompt) {
    // Show the install prompt
    deferredPrompt.prompt();

    // Wait for the user to respond to the prompt
    const { outcome } = await deferredPrompt.userChoice;

    if (outcome === 'accepted') {
      console.log('User accepted the install prompt');
    } else {
      console.log('User dismissed the install prompt');
    }

    // Clear the deferredPrompt
    deferredPrompt = null;
    showInstallPrompt.value = false;
  }
};

const dismissPrompt = () => {
  showInstallPrompt.value = false;
  // Store dismissal in localStorage to avoid showing again soon
  localStorage.setItem('pwa-install-dismissed', Date.now().toString());
};

// Check if user has recently dismissed the prompt
onMounted(() => {
  const lastDismissed = localStorage.getItem('pwa-install-dismissed');
  if (lastDismissed) {
    const daysSinceDismissal = (Date.now() - parseInt(lastDismissed)) / (1000 * 60 * 60 * 24);
    if (daysSinceDismissal < 7) { // Don't show for 7 days after dismissal
      showInstallPrompt.value = false;
    }
  }
});
</script>

<style scoped>
.pwa-install-banner {
  position: fixed;
  bottom: 20px;
  left: 20px;
  right: 20px;
  background: #1976d2;
  color: white;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
  z-index: 1000;
  animation: slideUp 0.3s ease-out;
}

.install-content {
  display: flex;
  align-items: center;
  padding: 16px;
  gap: 12px;
}

.install-icon {
  font-size: 24px;
  flex-shrink: 0;
}

.install-text {
  flex: 1;
}

.install-text h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.install-text p {
  margin: 4px 0 0 0;
  font-size: 14px;
  opacity: 0.9;
}

.install-actions {
  display: flex;
  gap: 8px;
}

.install-btn, .dismiss-btn {
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;
}

.install-btn {
  background: white;
  color: #1976d2;
}

.install-btn:hover {
  background: #f5f5f5;
}

.dismiss-btn {
  background: rgba(255, 255, 255, 0.2);
  color: white;
}

.dismiss-btn:hover {
  background: rgba(255, 255, 255, 0.3);
}

@keyframes slideUp {
  from {
    transform: translateY(100px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

@media (min-width: 768px) {
  .pwa-install-banner {
    max-width: 400px;
    left: auto;
    right: 20px;
  }
}
</style>
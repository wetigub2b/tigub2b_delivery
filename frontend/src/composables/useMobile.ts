import { ref, onMounted, onUnmounted } from 'vue';
import { mobileUtils } from '@/utils/mobile';

export function useMobile() {
  const isOnline = ref(true);
  const appState = ref({ isActive: true });
  const currentPosition = ref<{ latitude: number; longitude: number } | null>(null);

  // Network status monitoring
  const updateNetworkStatus = async () => {
    try {
      const status = await mobileUtils.getNetworkStatus();
      isOnline.value = status.connected;
    } catch (error) {
      console.warn('Failed to get network status:', error);
    }
  };

  // App state monitoring
  const handleAppStateChange = (state: { isActive: boolean }) => {
    appState.value = state;
  };

  // Get current location
  const getCurrentLocation = async () => {
    try {
      const position = await mobileUtils.getCurrentPosition();
      currentPosition.value = position;
      return position;
    } catch (error) {
      console.error('Failed to get location:', error);
      throw error;
    }
  };

  // Haptic feedback helper
  const vibrate = (style: 'light' | 'medium' | 'heavy' = 'medium') => {
    return mobileUtils.triggerHaptic(style);
  };

  // Keyboard helpers
  const showKeyboard = () => mobileUtils.showKeyboard();
  const hideKeyboard = () => mobileUtils.hideKeyboard();

  onMounted(() => {
    // Initialize network monitoring
    updateNetworkStatus();

    // Set up app state monitoring
    mobileUtils.onAppStateChange(handleAppStateChange);

    // Listen for online/offline events (web fallback)
    window.addEventListener('online', updateNetworkStatus);
    window.addEventListener('offline', updateNetworkStatus);
  });

  onUnmounted(() => {
    window.removeEventListener('online', updateNetworkStatus);
    window.removeEventListener('offline', updateNetworkStatus);
  });

  return {
    // State
    isOnline,
    appState,
    currentPosition,

    // Platform info
    isNative: mobileUtils.isNative,
    isAndroid: mobileUtils.isAndroid,
    isIOS: mobileUtils.isIOS,

    // Methods
    getCurrentLocation,
    vibrate,
    showKeyboard,
    hideKeyboard,
    updateNetworkStatus
  };
}
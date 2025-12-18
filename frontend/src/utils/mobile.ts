import { Capacitor } from '@capacitor/core';
import { StatusBar, Style } from '@capacitor/status-bar';
import { SplashScreen } from '@capacitor/splash-screen';
import { App } from '@capacitor/app';
import { Haptics, ImpactStyle } from '@capacitor/haptics';
import { Keyboard } from '@capacitor/keyboard';
import { Network } from '@capacitor/network';
import { Geolocation } from '@capacitor/geolocation';

export interface MobileUtils {
  isNative: boolean;
  isAndroid: boolean;
  isIOS: boolean;
  hideSplashScreen(): Promise<void>;
  setStatusBarStyle(style: 'dark' | 'light'): Promise<void>;
  triggerHaptic(style?: 'light' | 'medium' | 'heavy'): Promise<void>;
  showKeyboard(): Promise<void>;
  hideKeyboard(): Promise<void>;
  getNetworkStatus(): Promise<{ connected: boolean; connectionType: string }>;
  getCurrentPosition(): Promise<{ latitude: number; longitude: number }>;
  onAppStateChange(callback: (state: { isActive: boolean }) => void): void;
}

class MobileUtilsImpl implements MobileUtils {
  public readonly isNative = Capacitor.isNativePlatform();
  public readonly isAndroid = Capacitor.getPlatform() === 'android';
  public readonly isIOS = Capacitor.getPlatform() === 'ios';

  async hideSplashScreen(): Promise<void> {
    if (this.isNative) {
      await SplashScreen.hide();
    }
  }

  async setStatusBarStyle(style: 'dark' | 'light'): Promise<void> {
    if (this.isNative) {
      await StatusBar.setStyle({
        style: style === 'dark' ? Style.Dark : Style.Light
      });
    }
  }

  async triggerHaptic(style: 'light' | 'medium' | 'heavy' = 'medium'): Promise<void> {
    if (this.isNative) {
      const impactStyle = {
        light: ImpactStyle.Light,
        medium: ImpactStyle.Medium,
        heavy: ImpactStyle.Heavy
      }[style];

      await Haptics.impact({ style: impactStyle });
    }
  }

  async showKeyboard(): Promise<void> {
    if (this.isNative) {
      await Keyboard.show();
    }
  }

  async hideKeyboard(): Promise<void> {
    if (this.isNative) {
      await Keyboard.hide();
    }
  }

  async getNetworkStatus(): Promise<{ connected: boolean; connectionType: string }> {
    if (this.isNative) {
      const status = await Network.getStatus();
      return {
        connected: status.connected,
        connectionType: status.connectionType
      };
    }
    return {
      connected: navigator.onLine,
      connectionType: 'unknown'
    };
  }

  async getCurrentPosition(): Promise<{ latitude: number; longitude: number }> {
    if (this.isNative) {
      const coordinates = await Geolocation.getCurrentPosition({
        enableHighAccuracy: true,
        timeout: 15000
      });
      return {
        latitude: coordinates.coords.latitude,
        longitude: coordinates.coords.longitude
      };
    } else {
      return new Promise((resolve, reject) => {
        navigator.geolocation.getCurrentPosition(
          (position) => {
            resolve({
              latitude: position.coords.latitude,
              longitude: position.coords.longitude
            });
          },
          reject,
          { enableHighAccuracy: true, timeout: 30000, maximumAge: 60000 }
        );
      });
    }
  }

  onAppStateChange(callback: (state: { isActive: boolean }) => void): void {
    if (this.isNative) {
      App.addListener('appStateChange', callback);
    } else {
      // Web fallback
      document.addEventListener('visibilitychange', () => {
        callback({ isActive: !document.hidden });
      });
    }
  }
}

export const mobileUtils = new MobileUtilsImpl();

// Initialize mobile features
export async function initializeMobile(): Promise<void> {
  if (mobileUtils.isNative) {
    // Hide splash screen after app loads
    await mobileUtils.hideSplashScreen();

    // Set status bar style
    await mobileUtils.setStatusBarStyle('dark');

    // Setup keyboard behavior
    if (mobileUtils.isIOS) {
      Keyboard.addListener('keyboardWillShow', () => {
        document.body.style.paddingBottom = '0px';
      });

      Keyboard.addListener('keyboardWillHide', () => {
        document.body.style.paddingBottom = '0px';
      });
    }

    // Setup network monitoring
    Network.addListener('networkStatusChange', (status) => {
      console.log('Network status changed:', status);
      // You can dispatch this to your store if needed
    });
  }
}
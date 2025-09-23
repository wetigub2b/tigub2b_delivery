# Mobile & PWA Setup Guide

This document explains how the Vue.js frontend has been converted into a PWA-ready application with Capacitor support for Android and iOS.

## 🎯 Features Added

### Progressive Web App (PWA)
- ✅ Service Worker for offline functionality
- ✅ Web App Manifest for installability
- ✅ Install prompt component
- ✅ Caching strategy for API calls
- ✅ Offline-first architecture

### Mobile App Support (Capacitor)
- ✅ Android platform support
- ✅ iOS platform support
- ✅ Native plugins integration
- ✅ Mobile-specific utilities

### Native Features Available
- 📱 **Status Bar** - Control status bar appearance
- 🎆 **Splash Screen** - Custom splash screen with branding
- 📶 **Network Detection** - Monitor connectivity status
- 📍 **Geolocation** - Get user's current location
- 📳 **Haptic Feedback** - Provide tactile feedback
- ⌨️ **Keyboard Management** - Control soft keyboard
- 🔄 **App State** - Monitor app foreground/background state

## 🛠️ Development Commands

### Web Development
```bash
npm run dev          # Start development server
npm run build        # Build for production
npm run preview      # Preview production build
```

### Mobile Development
```bash
npm run mobile:build       # Build and sync with Capacitor
npm run mobile:android     # Build and run on Android
npm run mobile:ios         # Build and run on iOS
npm run mobile:android:dev # Android with live reload
npm run mobile:ios:dev     # iOS with live reload
```

### Capacitor Commands
```bash
npx cap add android        # Add Android platform
npx cap add ios           # Add iOS platform
npx cap sync             # Sync web assets to native platforms
npx cap run android      # Run on Android device/emulator
npx cap run ios          # Run on iOS device/simulator
npx cap open android     # Open Android project in Android Studio
npx cap open ios         # Open iOS project in Xcode
```

## 📱 Mobile Utilities

### Using Mobile Features in Components
```typescript
import { useMobile } from '@/composables/useMobile';

export default {
  setup() {
    const {
      isNative,
      isAndroid,
      isIOS,
      isOnline,
      getCurrentLocation,
      vibrate
    } = useMobile();

    const handleLocationClick = async () => {
      try {
        const position = await getCurrentLocation();
        console.log('Current position:', position);
        await vibrate('light'); // Haptic feedback
      } catch (error) {
        console.error('Failed to get location:', error);
      }
    };

    return {
      isNative,
      isOnline,
      handleLocationClick
    };
  }
};
```

### Direct Mobile Utils Access
```typescript
import { mobileUtils } from '@/utils/mobile';

// Check platform
if (mobileUtils.isNative) {
  // Running in mobile app
}

if (mobileUtils.isAndroid) {
  // Android-specific code
}

// Use features
await mobileUtils.triggerHaptic('medium');
await mobileUtils.setStatusBarStyle('dark');
const networkStatus = await mobileUtils.getNetworkStatus();
```

## 🎨 PWA Features

### Install Prompt
The app automatically shows an install prompt for supported browsers. Users can:
- Install the app to their home screen
- Run it in standalone mode
- Access it offline

### Service Worker
Automatically caches:
- App shell (HTML, CSS, JS)
- API responses (with network-first strategy)
- Static assets

### Offline Support
- App works offline with cached resources
- API calls fall back to cache when offline
- Network status monitoring available

## 🏗️ Build Process

### For Web (PWA)
1. `npm run build` - Creates optimized build in `dist/`
2. Service worker and manifest are automatically generated
3. Deploy `dist/` folder to web server with HTTPS

### For Mobile Apps
1. `npm run build` - Build web assets
2. `npx cap sync` - Copy to native platforms
3. `npx cap run android/ios` - Build and run on device

## 📋 Prerequisites for Mobile Development

### Android
- Android Studio
- Android SDK (API level 22+)
- Java Development Kit (JDK) 8+

### iOS (macOS only)
- Xcode 13+
- iOS SDK
- CocoaPods (`sudo gem install cocoapods`)

## 🎯 Configuration

### Capacitor Config (`capacitor.config.ts`)
```typescript
const config: CapacitorConfig = {
  appId: 'com.tigu.delivery',
  appName: 'Tigu Delivery',
  webDir: 'dist',
  server: {
    androidScheme: 'https'
  },
  plugins: {
    SplashScreen: {
      launchShowDuration: 2000,
      backgroundColor: "#1976d2"
    }
  }
};
```

### PWA Manifest (`public/manifest.json`)
```json
{
  "name": "Tigu Delivery Console",
  "short_name": "TiguDelivery",
  "display": "standalone",
  "theme_color": "#1976d2",
  "background_color": "#ffffff"
}
```

## 🚀 Deployment

### Web (PWA)
1. Build: `npm run build`
2. Deploy `dist/` to HTTPS server
3. App will be installable on supported devices

### Android
1. Build: `npm run mobile:build`
2. Open in Android Studio: `npx cap open android`
3. Build APK/AAB for Play Store

### iOS
1. Build: `npm run mobile:build`
2. Open in Xcode: `npx cap open ios`
3. Build for App Store

## 📱 Testing

### PWA Testing
1. Run `npm run preview`
2. Open in Chrome/Edge
3. Check PWA audit in DevTools
4. Test install prompt

### Mobile Testing
1. Connect Android device or start emulator
2. Run `npm run mobile:android:dev`
3. App will install and run with live reload

## 🔧 Troubleshooting

### Common Issues
1. **Build fails**: Check Node.js version (16+)
2. **Android build fails**: Verify Android Studio setup
3. **iOS build fails**: Check Xcode and CocoaPods
4. **PWA not installable**: Ensure HTTPS and valid manifest

### Debugging
- Chrome DevTools for PWA features
- Android Studio for Android debugging
- Xcode for iOS debugging
- Safari DevTools for iOS web debugging

## 📚 Resources

- [Capacitor Documentation](https://capacitorjs.com/docs)
- [PWA Documentation](https://web.dev/progressive-web-apps/)
- [Vite PWA Plugin](https://vite-pwa-org.netlify.app/)